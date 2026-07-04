use quote::ToTokens;
use serde_json::json;
use std::env;
use std::fs;
use syn::{parse_file, spanned::Spanned, Item};

fn push_definition(
    definitions: &mut Vec<serde_json::Value>,
    item_type: &str,
    name: String,
    span: proc_macro2::Span,
) {
    let start = span.start();
    let end = span.end();
    definitions.push(json!({
        "type": item_type,
        "name": name,
        "start_line": start.line,
        "end_line": end.line,
    }));
}

fn extract_definitions(file_path: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(file_path)?;
    let file = parse_file(&content)?;

    let mut definitions = vec![];

    for item in file.items {
        match item {
            Item::Fn(func_item) => {
                let ident = &func_item.sig.ident;
                push_definition(&mut definitions, "Function", ident.to_string(), func_item.span());
            }
            Item::Struct(item_struct) => {
                push_definition(&mut definitions, "Struct", item_struct.ident.to_string(), item_struct.span());
            }
            Item::Enum(item_enum) => {
                push_definition(&mut definitions, "Enum", item_enum.ident.to_string(), item_enum.span());
            }
            Item::Trait(item_trait) => {
                push_definition(&mut definitions, "Trait", item_trait.ident.to_string(), item_trait.span());
            }
            Item::Union(item_union) => {
                push_definition(&mut definitions, "Union", item_union.ident.to_string(), item_union.span());
            }
            Item::Type(item_type) => {
                push_definition(&mut definitions, "Type", item_type.ident.to_string(), item_type.span());
            }
            Item::Const(item_const) => {
                push_definition(&mut definitions, "Const", item_const.ident.to_string(), item_const.span());
            }
            Item::Static(item_static) => {
                push_definition(&mut definitions, "Static", item_static.ident.to_string(), item_static.span());
            }
            Item::Use(item_use) => {
                push_definition(
                    &mut definitions,
                    "Use",
                    item_use.to_token_stream().to_string(),
                    item_use.span(),
                );
            }
            Item::ExternCrate(item_extern_crate) => {
                push_definition(
                    &mut definitions,
                    "ExternCrate",
                    item_extern_crate.ident.to_string(),
                    item_extern_crate.span(),
                );
            }
            Item::Mod(item_mod) => {
                push_definition(&mut definitions, "Mod", item_mod.ident.to_string(), item_mod.span());
            }
            Item::Macro(item_macro) => {
                let name = item_macro
                    .mac
                    .path
                    .segments
                    .last()
                    .map(|segment| segment.ident.to_string())
                    .unwrap_or_else(|| item_macro.mac.path.to_token_stream().to_string());
                push_definition(&mut definitions, "Macro", name, item_macro.span());
            }
            Item::Impl(item_impl) => {
                let self_ty = item_impl.self_ty.to_token_stream().to_string();
                let name = if let Some((_, path, _)) = &item_impl.trait_ {
                    format!("{} for {}", path.to_token_stream(), self_ty)
                } else {
                    self_ty
                };
                push_definition(&mut definitions, "Impl", name, item_impl.span());
            }
            _ => {}
        }
    }

    Ok(json!(definitions))
}

fn main() {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <path_to_rust_file> <output_json_file>", args[0]);
        std::process::exit(1);
    }
    let rs_file_path = &args[1];
    let output_file_path = &args[2];

    match extract_definitions(rs_file_path) {
        Ok(definitions) => {
            let json_str =
                serde_json::to_string_pretty(&definitions).expect("Unable to serialize to JSON");
            fs::write(output_file_path, json_str).expect("Unable to write file");
        }
        Err(e) => {
            eprintln!("Error: {}", e);
        }
    }
}