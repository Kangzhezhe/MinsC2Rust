import sys
from pathlib import Path

# 确保可以导入项目根下的 analyzer 包
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pytest

from analyzer import Analyzer, SymbolRef, to_absolute_path


@pytest.fixture(scope="module")
def az() -> Analyzer:
    return Analyzer()


def pick_function_symbol(az: Analyzer) -> SymbolRef:
    # 选择一个带有字节范围的函数符号，便于测试精确提取
    for s in az._by_key.values():
        if s.type == "functions" and s.start_byte is not None and s.end_byte is not None:
            if to_absolute_path(s.file_path).exists():
                return s
    # 退一步，只要有函数就行
    for s in az._by_key.values():
        if s.type == "functions" and to_absolute_path(s.file_path).exists():
            return s
    pytest.skip("未找到可用于测试的函数符号")


def test_initialization_and_topology(az: Analyzer):
    # 基础加载
    assert isinstance(az.analysis_data, dict) and len(az.analysis_data) > 0
    assert len(az._by_key) > 0

    # 拓扑信息（如果存在文件，应当能加载到）
    assert isinstance(az.ordered_names, list)
    assert isinstance(az.depth_by_name, dict)
    assert isinstance(az.cycle_groups, list)


def test_find_symbols_by_name_and_filters(az: Analyzer):
    # 选一个已有名称
    any_sym = next(iter(az._by_key.values()))
    name = any_sym.name

    # 名称查找
    by_name = az.find_symbols_by_name(name)
    assert len(by_name) >= 1

    # 类型过滤
    filtered = az.find_symbols_by_name(name, symbol_type=any_sym.type)
    assert all(s.type == any_sym.type for s in filtered)

    # 文件过滤（可能使结果更少或为空，但语义正确）
    filtered_file = az.find_symbols_by_name(name, file_path=any_sym.file_path)
    assert all(s.file_path == any_sym.file_path for s in filtered_file)

    # 未知名称
    none = az.find_symbols_by_name("__MINSC2RUST_TEST_NON_EXISTENT__")
    assert none == []


def test_get_definition_location_and_extract_text(az: Analyzer):
    sym = pick_function_symbol(az)

    locs = az.get_definition_location(sym.name, symbol_type=sym.type, file_path=sym.file_path)
    assert len(locs) >= 1
    fp, sl, el, sb, eb = locs[0]
    assert fp == sym.file_path
    assert sl >= 0 and el >= sl

    # 字节精确提取（若有）
    text = az.extract_definition_text(sym)
    assert isinstance(text, str)
    assert len(text) > 0

    # 行号回退提取：构造一个没有字节信息的 SymbolRef
    sym_line_only = SymbolRef(
        name=sym.name,
        type=sym.type,
        file_path=sym.file_path,
        start_line=sym.start_line,
        end_line=sym.end_line,
        start_byte=None,
        end_byte=None,
    )
    text2 = az.extract_definition_text(sym_line_only)
    assert isinstance(text2, str)
    assert len(text2) > 0


def test_get_dependencies_out_in_both_with_depth(az: Analyzer):
    sym = pick_function_symbol(az)

    # 出边（依赖谁）深度1
    nodes_out_1, edges_out_1 = az.get_dependencies(sym, depth=1, direction="out")
    assert isinstance(nodes_out_1, list) and isinstance(edges_out_1, list)
    assert len(nodes_out_1) >= 1  # 至少包含起点
    assert nodes_out_1[0].key() == sym.key()

    # 双向，深度2（不强制断言数量，防止数据集变动导致不稳定）
    nodes_both_2, edges_both_2 = az.get_dependencies(sym, depth=2, direction="both")
    assert isinstance(nodes_both_2, list) and isinstance(edges_both_2, list)
    assert any(n.key() == sym.key() for n in nodes_both_2)

    # 入边（被谁依赖）深度1
    nodes_in_1, edges_in_1 = az.get_dependencies(sym, depth=1, direction="in")
    assert isinstance(nodes_in_1, list) and isinstance(edges_in_1, list)

    # key 取回
    s2 = az.get_symbol_by_key(sym.key())
    assert s2 is not None


def test_sort_by_topo_and_cycle_groups(az: Analyzer):
    # 取拓扑序前若干名称，在索引中找候选
    picked = []
    for n in az.ordered_names[:10]:
        cands = az.find_symbols_by_name(n)
        if cands:
            picked.append(cands[0])
        if len(picked) >= 3:
            break

    if picked:
        sorted_syms = az.sort_by_topo(picked)
        assert [s.name for s in sorted_syms] == sorted([s.name for s in picked], key=lambda x: az.ordered_names.index(x))

    # 环信息类型存在即可
    assert isinstance(az.cycle_groups, list)


def test_unknown_symbol_behaviors(az: Analyzer):
    # 不存在的 key 查找
    with pytest.raises(KeyError):
        az.get_dependencies("__NO_SUCH_NAME__:functions:/nowhere.c", depth=1, direction="out")

    # 未命中位置查询返回空
    locs = az.get_definition_location("__NO_SUCH_NAME__", symbol_type="functions")
    assert locs == []
