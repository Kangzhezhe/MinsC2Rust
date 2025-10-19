import re
import os
import sys
import csv
import json
from pathlib import Path
from typing import Callable, Mapping, MutableMapping, Optional, Sequence, List, Dict

def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


SAFETY_FIELDNAMES = [
    "Source",
    "Safe Loc",
    "Safe Loc Count",
    "Unsafe Loc Count",
    "Total Loc",
    "Safe Ref",
    "Safe Ref Count",
    "Unsafe Ref Count",
    "Total Ref Count",
]


def export_compile_metrics(
    project_root: Path,
    file_stats: Mapping[str, Mapping[str, int]],
    successful_functions: int,
    total_functions: int,
    *,
    logger: Callable[[str], None] = print,
    filename: str = "function_compile_metrics.csv",
) -> Path:
    """Persist per-file compile metrics and log the overall pass rate."""

    metrics_dir = project_root / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / filename

    if total_functions:
        pass_rate = successful_functions / total_functions
        logger(
            f"函数编译通过率: {successful_functions}/{total_functions} ({format_percent(pass_rate)})"
        )
    else:
        logger("未检测到需要处理的函数。")

    with metrics_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file", "passed_functions", "total_functions", "pass_rate"])

        for file_key in sorted(file_stats):
            stats = file_stats[file_key]
            total_count = int(stats.get("total", 0) or 0)
            if total_count == 0:
                continue
            passed_count = int(stats.get("passed", 0) or 0)
            file_rate = (passed_count / total_count) if total_count else 0.0
            writer.writerow(
                [
                    file_key,
                    passed_count,
                    total_count,
                    format_percent(file_rate),
                ]
            )

        overall_rate = (successful_functions / total_functions) if total_functions else 0.0
        writer.writerow(
            [
                "Overall",
                int(successful_functions),
                int(total_functions),
                format_percent(overall_rate),
            ]
        )

    logger(f"函数编译指标 CSV 已保存: {metrics_path}")
    return metrics_path


def calculate_combined_metrics(file_path):
    """
    同时计算安全行比例和引用安全比例
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code_lines = f.readlines()

    # 预处理：移除注释和字符串内容
    cleaned_lines = []
    for line in code_lines:
        line = re.sub(r'//.*|/\*.*?\*/', '', line)  # 移除行内注释
        line = re.sub(r'"(?:\\"|.)*?"', '""', line)  # 替换双引号字符串
        line = re.sub(r"'(?:\\'|.)*?'", "''", line)  # 替换单引号字符
        cleaned_lines.append(line.strip())

    # 初始化统计变量
    total_lines = 0
    unsafe_line_count = 0
    pending_unsafe = False  # 检测到unsafe但尚未找到{
    unsafe_scope_depth = 0  # 当前unsafe作用域的嵌套深度
    safe_refs = 0
    unsafe_refs = 0

    # 正则表达式模式
    ref_patterns = {
        'safe': re.compile(r'''
            &(?!mut\b)\w+       # 不可变引用 (&T)
            |&\s*mut\s+\w+      # 可变引用 (&mut T)
            |\b(?:Cell|RefCell|String|str|Vec|Box)\b  # 智能指针类型
        ''', re.VERBOSE),
        'unsafe': re.compile(r'\b\*(?:const|mut)\b')
    }

    for line in cleaned_lines:
        if not line:
            continue

        total_lines += 1

        # ===== 安全行统计 =====
        # 检测新的unsafe关键字（仅在非作用域中触发）
        if re.search(r'\bunsafe\b', line) and not pending_unsafe and unsafe_scope_depth == 0:
            pending_unsafe = True

        # 逐字符分析作用域变化
        for char in line:
            if char == '{':
                if pending_unsafe:  # 触发unsafe作用域开始
                    unsafe_scope_depth = 1
                    pending_unsafe = False
                elif unsafe_scope_depth > 0:  # 嵌套作用域
                    unsafe_scope_depth += 1
            elif char == '}' and unsafe_scope_depth > 0:
                unsafe_scope_depth -= 1

        # 统计不安全行
        if unsafe_scope_depth > 0:
            unsafe_line_count += 1

        # ===== 引用统计 =====
        safe_refs += len(ref_patterns['safe'].findall(line))
        unsafe_refs += len(ref_patterns['unsafe'].findall(line))

    # 计算指标
    safe_line_ratio = 1 - (unsafe_line_count / total_lines) if total_lines else 0
    total_refs = safe_refs + unsafe_refs
    if total_refs:
        ref_ratio = safe_refs / total_refs
    else:
        ref_ratio = 1.0

    return {
        'safe_line_ratio': round(safe_line_ratio, 4),
        'ref_ratio': round(ref_ratio, 4),
        'total_lines': total_lines,
        'unsafe_lines': unsafe_line_count,
        'safe_refs': safe_refs,
        'unsafe_refs': unsafe_refs
    }


def _build_safety_row(source: str, metrics: Mapping[str, float]) -> MutableMapping[str, object]:
    total_lines = int(metrics.get('total_lines', 0) or 0)
    unsafe_lines = int(metrics.get('unsafe_lines', 0) or 0)
    safe_refs = int(metrics.get('safe_refs', 0) or 0)
    unsafe_refs = int(metrics.get('unsafe_refs', 0) or 0)

    safe_line_ratio = float(metrics.get('safe_line_ratio') or 0.0)
    ref_ratio = float(metrics.get('ref_ratio') or 0.0)

    safe_line_count = max(total_lines - unsafe_lines, 0)
    total_refs = safe_refs + unsafe_refs

    return {
        'Source': source,
        'Safe Loc': format_percent(safe_line_ratio),
        'Safe Loc Count': safe_line_count,
        'Unsafe Loc Count': unsafe_lines,
        'Total Loc': total_lines,
        'Safe Ref': format_percent(ref_ratio),
        'Safe Ref Count': safe_refs,
        'Unsafe Ref Count': unsafe_refs,
        'Total Ref Count': total_refs,
    }


def _sum_counts(rows, count_key: str) -> int:
    total = 0
    for row in rows:
        value = row.get(count_key, 0)
        try:
            total += int(value)
        except (TypeError, ValueError):
            try:
                total += int(float(str(value).strip() or 0))
            except (TypeError, ValueError):
                continue
    return total


def _count_file_lines(path: Path) -> int:
    try:
        with path.open('r', encoding='utf-8') as fh:
            return sum(1 for _ in fh)
    except (OSError, UnicodeDecodeError):
        return 0


def _resolve_candidate(path_str: str, bases: Sequence[Optional[Path]]) -> Path:
    candidate = Path(path_str)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    extensions = (Path(), Path("src"))

    for base in bases:
        if base is None:
            continue
        for extra in extensions:
            try:
                resolved = (base / extra / candidate).resolve()
            except TypeError:
                continue
            if resolved.exists():
                return resolved

    if candidate.is_absolute():
        return candidate

    first_base = next((base for base in bases if base is not None), None)
    if first_base is not None:
        return (first_base / candidate).resolve()

    return candidate.resolve()

def process_directory(directory):
    """
    处理目录下所有.rs文件并汇总统计，返回每个文件的结果列表
    """
    results = []
    total_metrics = {
        'total_lines': 0,
        'unsafe_lines': 0,
        'safe_refs': 0,
        'unsafe_refs': 0
    }

    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith('.rs'):
                continue

            filepath = os.path.join(root, filename)
            try:
                metrics = calculate_combined_metrics(filepath)
            except Exception as e:
                print(f"处理文件 {filepath} 出错: {str(e)}")
                continue

            source = os.path.splitext(os.path.basename(filepath))[0]
            row = _build_safety_row(source, metrics)
            results.append(row)

            total_metrics['total_lines'] += metrics['total_lines']
            total_metrics['unsafe_lines'] += metrics['unsafe_lines']
            total_metrics['safe_refs'] += metrics['safe_refs']
            total_metrics['unsafe_refs'] += metrics['unsafe_refs']

    # 汇总
    safe_line_ratio = 1 - (total_metrics['unsafe_lines'] / total_metrics['total_lines']) if total_metrics['total_lines'] else 0
    total_refs = total_metrics['safe_refs'] + total_metrics['unsafe_refs']
    ref_ratio = total_metrics['safe_refs'] / total_refs if total_refs else 1.0
    overall_metrics = {
        'safe_line_ratio': safe_line_ratio,
        'ref_ratio': ref_ratio,
        'total_lines': total_metrics['total_lines'],
        'unsafe_lines': total_metrics['unsafe_lines'],
        'safe_refs': total_metrics['safe_refs'],
        'unsafe_refs': total_metrics['unsafe_refs'],
    }
    results.append(_build_safety_row('Overall', overall_metrics))
    return results

def process_csv_rows(rows):
    """
    对 rows 进行 hash-functions 和 compare-functions 的合并与平均
    """
    hash_functions_rows = []
    compare_functions_rows = []
    filtered_rows = []

    for row in rows:
        filename = row['Source']
        if filename == 'lib':
            continue  # 删除 'lib' 行
        elif filename in ['hash_pointer', 'hash_int', 'hash_string']:
            hash_functions_rows.append(row)
        elif filename in ['compare_int', 'compare_string', 'compare_pointer']:
            compare_functions_rows.append(row)
        else:
            # 替换文件名中的 '_' 为 '-'
            row['Source'] = filename.replace('_', '-')
            filtered_rows.append(row)

    # 计算 hash-functions 的平均值
    if hash_functions_rows:
        safe_loc_count = _sum_counts(hash_functions_rows, 'Safe Loc Count')
        unsafe_loc_count = _sum_counts(hash_functions_rows, 'Unsafe Loc Count')
        total_loc = _sum_counts(hash_functions_rows, 'Total Loc')
        safe_ref_count = _sum_counts(hash_functions_rows, 'Safe Ref Count')
        unsafe_ref_count = _sum_counts(hash_functions_rows, 'Unsafe Ref Count')
        total_ref = _sum_counts(hash_functions_rows, 'Total Ref Count') or (safe_ref_count + unsafe_ref_count)

        safe_line_ratio = (safe_loc_count / total_loc) if total_loc else 0.0
        ref_ratio = (safe_ref_count / total_ref) if total_ref else 1.0

        filtered_rows.append({
            'Source': 'hash-functions',
            'Safe Loc': format_percent(safe_line_ratio),
            'Safe Loc Count': safe_loc_count,
            'Unsafe Loc Count': unsafe_loc_count,
            'Total Loc': total_loc,
            'Safe Ref': format_percent(ref_ratio),
            'Safe Ref Count': safe_ref_count,
            'Unsafe Ref Count': unsafe_ref_count,
            'Total Ref Count': total_ref,
        })

    # 计算 compare-functions 的平均值
    if compare_functions_rows:
        safe_loc_count = _sum_counts(compare_functions_rows, 'Safe Loc Count')
        unsafe_loc_count = _sum_counts(compare_functions_rows, 'Unsafe Loc Count')
        total_loc = _sum_counts(compare_functions_rows, 'Total Loc')
        safe_ref_count = _sum_counts(compare_functions_rows, 'Safe Ref Count')
        unsafe_ref_count = _sum_counts(compare_functions_rows, 'Unsafe Ref Count')
        total_ref = _sum_counts(compare_functions_rows, 'Total Ref Count') or (safe_ref_count + unsafe_ref_count)

        safe_line_ratio = (safe_loc_count / total_loc) if total_loc else 0.0
        ref_ratio = (safe_ref_count / total_ref) if total_ref else 1.0

        filtered_rows.append({
            'Source': 'compare-functions',
            'Safe Loc': format_percent(safe_line_ratio),
            'Safe Loc Count': safe_loc_count,
            'Unsafe Loc Count': unsafe_loc_count,
            'Total Loc': total_loc,
            'Safe Ref': format_percent(ref_ratio),
            'Safe Ref Count': safe_ref_count,
            'Unsafe Ref Count': unsafe_ref_count,
            'Total Ref Count': total_ref,
        })

    return filtered_rows

def write_csv(rows, output_csv, fieldnames=None):
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        if not rows:
            return
        fieldnames = list(rows[0].keys())

    with output_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)

def calculate_safety_metrics(input_path, output_csv):
    rows = []
    if os.path.isfile(input_path):
        metrics = calculate_combined_metrics(input_path)
        source = os.path.splitext(os.path.basename(input_path))[0]
        rows.append(_build_safety_row(source, metrics))
    elif os.path.isdir(input_path):
        rows = process_directory(input_path)
    elif input_path.endswith('.csv'):
        # 直接处理已有csv
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                rows.append(row)
    else:
        print(f"无效路径: {input_path}")
        sys.exit(1)

    # 合并 hash-functions 和 compare-functions
    rows = process_csv_rows(rows)
    write_csv(rows, output_csv, fieldnames=SAFETY_FIELDNAMES)
    print(f"安全指标 CSV 已保存: {output_csv}")
    return rows


def calculate_translation_line_ratio(
    mapping_path: Path,
    output_csv: Path,
    *,
    c_root: Optional[Path] = None,
    rust_root: Optional[Path] = None,
) -> Sequence[Mapping[str, object]]:
    mapping_path = Path(mapping_path)
    if not mapping_path.exists():
        raise FileNotFoundError(f"未找到映射文件: {mapping_path}")

    with mapping_path.open('r', encoding='utf-8') as fh:
        mapping_data = json.load(fh) or {}

    modules = mapping_data.get('modules') or []
    c_to_rust = mapping_data.get('c_to_rust') or {}

    if rust_root is None:
        try:
            from analyzer.config import load_rust_output_dir  # type: ignore

            rust_root = load_rust_output_dir()
        except Exception:
            rust_root = mapping_path.parent
    if c_root is None:
        try:
            from analyzer.config import get_project_root  # type: ignore

            c_root = get_project_root()
        except Exception:
            c_root = None

    rows: List[Dict[str, object]] = []
    total_c_loc = 0
    total_rust_loc = 0

    def _format_ratio(rust_loc: int, c_loc: int) -> str:
        if c_loc <= 0:
            return 'N/A'
        ratio = rust_loc / c_loc
        return format_percent(ratio)

    def _append_row(rust_file: str, c_sources: Sequence[str]) -> None:
        nonlocal total_c_loc, total_rust_loc

        resolved_rust = _resolve_candidate(rust_file, (rust_root, mapping_path.parent))
        rust_loc = _count_file_lines(resolved_rust)

        c_loc_total = 0
        for c_source in c_sources:
            resolved_c = _resolve_candidate(c_source, (c_root, mapping_path.parent))
            c_loc_total += _count_file_lines(resolved_c)

        if c_loc_total > 0:
            total_c_loc += c_loc_total
            total_rust_loc += rust_loc

        rows.append({
            'Rust File': rust_file,
            'Rust LOC': rust_loc,
            'C Sources': '; '.join(c_sources) if c_sources else '',
            'C LOC': c_loc_total,
            'Rust/C LOC': _format_ratio(rust_loc, c_loc_total),
        })

    if modules:
        for module in modules:
            rust_file = module.get('rust_file')
            sources = module.get('sources') or []
            if not isinstance(rust_file, str):
                continue
            c_sources: list[str] = [str(item) for item in sources if isinstance(item, str)]
            _append_row(rust_file, c_sources)
    else:
        for c_file, rust_file in sorted(c_to_rust.items()):
            if not isinstance(rust_file, str) or not isinstance(c_file, str):
                continue
            _append_row(rust_file, [c_file])

    overall_ratio = _format_ratio(total_rust_loc, total_c_loc) if total_c_loc else 'N/A'
    rows.append({
        'Rust File': 'Overall',
        'Rust LOC': total_rust_loc,
        'C Sources': '-',
        'C LOC': total_c_loc,
        'Rust/C LOC': overall_ratio,
    })

    fieldnames = ['Rust File', 'Rust LOC', 'C Sources', 'C LOC', 'Rust/C LOC']
    write_csv(rows, output_csv, fieldnames=fieldnames)
    print(f"行数比例指标 CSV 已保存: {output_csv}")
    return rows

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_unsafe.py <file_or_directory> <output_csv>")
        sys.exit(1)
    calculate_safety_metrics(sys.argv[1], sys.argv[2])