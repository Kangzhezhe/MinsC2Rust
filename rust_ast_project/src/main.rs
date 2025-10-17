use proc_macro2::Span;
use serde::Serialize;
use std::cmp::Ordering;
use std::env;
use std::fs;
use std::path::Path;
use syn::{parse_file, spanned::Spanned, Item, Type};
use walkdir::{DirEntry, WalkDir};

#[derive(Serialize, Clone)]
struct SymbolMatch {
    name: String,
    kind: String,
    file: String,
    code: String,
    start_line: usize,
    end_line: usize,
}

#[derive(Serialize)]
struct SymbolExtraction {
    symbol: String,
    matches: Vec<SymbolMatch>,
}

#[derive(Debug)]
enum Mode<'a> {
    PerFile {
        source: &'a Path,
        output: &'a Path,
    },
    Project {
        project_root: &'a Path,
        symbol: &'a str,
        output: &'a Path,
    },
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mode = match determine_mode(&args) {
        Ok(mode) => mode,
        Err(usage) => {
            eprintln!("{}", usage);
            std::process::exit(1);
        }
    };

    match mode {
        Mode::PerFile { source, output } => match extract_definitions_per_file(source) {
            Ok(definitions) => match serde_json::to_string_pretty(&definitions) {
                Ok(serialized) => {
                    if let Err(err) = fs::write(output, serialized) {
                        eprintln!("Failed to write output: {}", err);
                        std::process::exit(1);
                    }
                }
                Err(err) => {
                    eprintln!("Failed to serialize definitions: {}", err);
                    std::process::exit(1);
                }
            },
            Err(err) => {
                eprintln!("Error extracting function definitions: {}", err);
                std::process::exit(1);
            }
        },
        Mode::Project {
            project_root,
            symbol,
            output,
        } => match extract_symbol_from_project(project_root, symbol) {
            Ok(result) => match serde_json::to_string_pretty(&result) {
                Ok(serialized) => {
                    if let Err(err) = fs::write(output, serialized) {
                        eprintln!("Failed to write output: {}", err);
                        std::process::exit(1);
                    }
                }
                Err(err) => {
                    eprintln!("Failed to serialize extraction: {}", err);
                    std::process::exit(1);
                }
            },
            Err(err) => {
                eprintln!("Error extracting symbol: {}", err);
                std::process::exit(1);
            }
        },
    }
}

fn determine_mode(args: &[String]) -> Result<Mode<'_>, String> {
    match args.len() {
        3 => {
            let source = Path::new(&args[1]);
            let output = Path::new(&args[2]);
            Ok(Mode::PerFile { source, output })
        }
        4 => {
            let project_root = Path::new(&args[1]);
            let symbol = args[2].as_str();
            let output = Path::new(&args[3]);
            Ok(Mode::Project {
                project_root,
                symbol,
                output,
            })
        }
        _ => Err(format!(
            "Usage:\n  {0} <path_to_rust_file> <output_json_file>\n  {0} <project_root> <symbol_name> <output_json_file>",
            args.first().map_or("binary", String::as_str)
        )),
    }
}

fn compute_line_starts(content: &str) -> Vec<usize> {
    let mut starts = Vec::with_capacity(content.lines().count() + 2);
    starts.push(0);
    for (idx, ch) in content.char_indices() {
        if ch == '\n' {
            starts.push(idx + 1);
        }
    }
    if !content.is_empty() && !content.ends_with('\n') {
        starts.push(content.len());
    }
    starts
}

fn span_to_range(span: Span, line_starts: &[usize], content_len: usize) -> (usize, usize) {
    let start = span.start();
    let end = span.end();

    let start_offset = line_col_to_offset(start.line, start.column, line_starts, content_len);
    let end_offset = line_col_to_offset(end.line, end.column, line_starts, content_len);

    (start_offset.min(content_len), end_offset.min(content_len))
}

fn line_col_to_offset(
    line: usize,
    column: usize,
    line_starts: &[usize],
    content_len: usize,
) -> usize {
    if line == 0 {
        return column.min(content_len);
    }
    let idx = line.saturating_sub(1);
    let base = *line_starts
        .get(idx)
        .unwrap_or_else(|| line_starts.last().unwrap_or(&0));
    (base + column).min(content_len)
}

fn slice_span(span: Span, content: &str, line_starts: &[usize]) -> String {
    let (mut start, mut end) = span_to_range(span, line_starts, content.len());
    if start > end {
        std::mem::swap(&mut start, &mut end);
    }

    let mut end_adjusted = end;
    if end_adjusted <= start {
        if let Some(next_newline) = content[start..].find('\n') {
            end_adjusted = start + next_newline + 1;
        } else {
            end_adjusted = content.len();
        }
    } else if end_adjusted < content.len() {
        if let Some(next_newline) = content[end_adjusted..].find('\n') {
            end_adjusted = end_adjusted + next_newline + 1;
        }
    }

    let snippet = &content[start..end_adjusted.min(content.len())];
    snippet.trim_end_matches('\r').to_string()
}

fn record_match(
    results: &mut Vec<SymbolMatch>,
    ident: &str,
    kind: &str,
    file_path: &Path,
    content: &str,
    line_starts: &[usize],
    span: Span,
    project_root: Option<&Path>,
) {
    let code = slice_span(span, content, line_starts);
    let file = project_root
        .and_then(|root| file_path.strip_prefix(root).ok())
        .unwrap_or(file_path)
        .to_string_lossy()
        .to_string();
    let start_line = span.start().line;
    let end_line = span.end().line;

    results.push(SymbolMatch {
        name: ident.to_string(),
        kind: kind.to_string(),
        file,
        code,
        start_line,
        end_line,
    });
}

fn type_matches_target(ty: &Type, target: &str) -> bool {
    match ty {
        Type::Path(path) => path
            .path
            .segments
            .last()
            .map(|segment| segment.ident == target)
            .unwrap_or(false),
        Type::Reference(reference) => type_matches_target(&reference.elem, target),
        Type::Group(group) => type_matches_target(&group.elem, target),
        Type::Paren(paren) => type_matches_target(&paren.elem, target),
        _ => false,
    }
}

fn merge_adjacent_impls(matches: &mut Vec<SymbolMatch>) {
    matches.sort_by(|a, b| {
        let file_ord = a.file.cmp(&b.file);
        if file_ord == Ordering::Equal {
            a.start_line.cmp(&b.start_line)
        } else {
            file_ord
        }
    });

    let mut merged: Vec<SymbolMatch> = Vec::with_capacity(matches.len());
    let mut idx = 0;

    while idx < matches.len() {
        let current = matches[idx].clone();

        if current.kind == "Struct" {
            let mut combined = current;
            let mut next_idx = idx + 1;

            while next_idx < matches.len() {
                let candidate = &matches[next_idx];
                if candidate.kind == "Impl"
                    && candidate.name == combined.name
                    && candidate.file == combined.file
                {
                    if !combined.code.ends_with('\n') {
                        combined.code.push('\n');
                    }
                    combined.code.push_str(&candidate.code);
                    combined.end_line = candidate.end_line;
                    next_idx += 1;
                } else {
                    break;
                }
            }

            merged.push(combined);
            idx = next_idx;
        } else {
            merged.push(current);
            idx += 1;
        }
    }

    *matches = merged;
}

fn extract_symbol_from_items(
    items: &[Item],
    target: &str,
    content: &str,
    line_starts: &[usize],
    file_path: &Path,
    results: &mut Vec<SymbolMatch>,
    project_root: Option<&Path>,
) {
    for item in items {
        match item {
            Item::Fn(func) if func.sig.ident == target => {
                record_match(
                    results,
                    &func.sig.ident.to_string(),
                    "Function",
                    file_path,
                    content,
                    line_starts,
                    func.span(),
                    project_root,
                );
            }
            Item::Struct(struct_item) if struct_item.ident == target => {
                record_match(
                    results,
                    &struct_item.ident.to_string(),
                    "Struct",
                    file_path,
                    content,
                    line_starts,
                    struct_item.span(),
                    project_root,
                );
            }
            Item::Enum(enum_item) if enum_item.ident == target => {
                record_match(
                    results,
                    &enum_item.ident.to_string(),
                    "Enum",
                    file_path,
                    content,
                    line_starts,
                    enum_item.span(),
                    project_root,
                );
            }
            Item::Const(const_item) if const_item.ident == target => {
                record_match(
                    results,
                    &const_item.ident.to_string(),
                    "Const",
                    file_path,
                    content,
                    line_starts,
                    const_item.span(),
                    project_root,
                );
            }
            Item::Static(static_item) if static_item.ident == target => {
                record_match(
                    results,
                    &static_item.ident.to_string(),
                    "Static",
                    file_path,
                    content,
                    line_starts,
                    static_item.span(),
                    project_root,
                );
            }
            Item::Type(type_item) if type_item.ident == target => {
                record_match(
                    results,
                    &type_item.ident.to_string(),
                    "TypeAlias",
                    file_path,
                    content,
                    line_starts,
                    type_item.span(),
                    project_root,
                );
            }
            Item::Union(union_item) if union_item.ident == target => {
                record_match(
                    results,
                    &union_item.ident.to_string(),
                    "Union",
                    file_path,
                    content,
                    line_starts,
                    union_item.span(),
                    project_root,
                );
            }
            Item::Impl(impl_item) if type_matches_target(&impl_item.self_ty, target) => {
                record_match(
                    results,
                    target,
                    "Impl",
                    file_path,
                    content,
                    line_starts,
                    impl_item.span(),
                    project_root,
                );
            }
            Item::Macro(mac_item)
                if mac_item
                    .ident
                    .as_ref()
                    .map(|ident| ident == target)
                    .unwrap_or(false) =>
            {
                let macro_name = mac_item
                    .ident
                    .as_ref()
                    .map(|ident| ident.to_string())
                    .unwrap_or_else(|| target.to_string());

                record_match(
                    results,
                    &macro_name,
                    "Macro",
                    file_path,
                    content,
                    line_starts,
                    mac_item.span(),
                    project_root,
                );
            }
            Item::Mod(mod_item) => {
                if mod_item.ident == target {
                    record_match(
                        results,
                        &mod_item.ident.to_string(),
                        "Module",
                        file_path,
                        content,
                        line_starts,
                        mod_item.span(),
                        project_root,
                    );
                }

                if let Some((_, nested_items)) = &mod_item.content {
                    extract_symbol_from_items(
                        nested_items,
                        target,
                        content,
                        line_starts,
                        file_path,
                        results,
                        project_root,
                    );
                }
            }
            _ => {}
        }
    }
}

fn should_skip(entry: &DirEntry) -> bool {
    entry
        .path()
        .components()
        .any(|component| component.as_os_str() == "target")
}

fn extract_symbol_from_project(
    project_root: &Path,
    symbol: &str,
) -> Result<SymbolExtraction, Box<dyn std::error::Error>> {
    if !project_root.exists() {
        return Err(format!("Project root does not exist: {}", project_root.display()).into());
    }

    let mut matches = Vec::new();

    for entry in WalkDir::new(project_root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.file_type().is_file())
    {
        if should_skip(&entry) {
            continue;
        }

        let path = entry.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("rs") {
            continue;
        }

        let content = fs::read_to_string(path)?;
        let parsed = match parse_file(&content) {
            Ok(file) => file,
            Err(_) => continue,
        };
        let line_starts = compute_line_starts(&content);

        extract_symbol_from_items(
            &parsed.items,
            symbol,
            &content,
            &line_starts,
            path,
            &mut matches,
            Some(project_root),
        );
    }

    merge_adjacent_impls(&mut matches);

    Ok(SymbolExtraction {
        symbol: symbol.to_string(),
        matches,
    })
}

fn extract_definitions_per_file(
    source: &Path,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(source)?;
    let file = parse_file(&content)?;

    let mut definitions = Vec::new();
    for item in file.items {
        if let Item::Fn(func) = item {
            let span = func.span();
            let start = span.start();
            let end = span.end();
            definitions.push(serde_json::json!({
                "type": "Function",
                "name": func.sig.ident.to_string(),
                "start_line": start.line,
                "end_line": end.line,
            }));
        }
    }

    Ok(serde_json::Value::Array(definitions))
}
