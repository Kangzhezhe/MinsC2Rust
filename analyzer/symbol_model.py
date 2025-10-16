from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


SYMBOL_TYPE_NORMALIZATION: Dict[str, str] = {
    "functions": "functions",
    "function": "functions",
    "function_declaration": "functions",
    "function_definition": "functions",
    "function_proto": "functions",
    "function_prototype": "functions",
    "typedef": "typedefs",
    "typedef_declaration": "typedefs",
    "typedef_definition": "typedefs",
    "macro": "macros",
    "macro_definition": "macros",
    "variable": "variables",
    "variable_declaration": "variables",
    "variable_definition": "variables",
    "global_variable": "variables",
    "struct": "structs",
    "struct_declaration": "structs",
    "struct_definition": "structs",
    "union": "structs",
    "union_declaration": "structs",
    "union_definition": "structs",
    "enum": "enums",
    "enum_declaration": "enums",
    "enum_definition": "enums",
}


def normalize_symbol_type(sym_type: Optional[str]) -> Optional[str]:
    """将来自分析产物的符号类型归一化为 Analyzer 约定的六大类。"""
    if not sym_type:
        return None
    normalized = sym_type.strip().strip("'\"")
    key = normalized.lower()
    return SYMBOL_TYPE_NORMALIZATION.get(key, normalized)


@dataclass(slots=True)
class SymbolModel:
    """统一的符号数据模型，确保输出字段一致。"""

    name: str
    type: str
    start_line: int = 0
    end_line: int = 0
    start_byte: int = 0
    end_byte: int = 0
    full_declaration: str = ""
    full_definition: str = ""
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """导出为仅包含约定字段的字典。"""
        return asdict(self)

    @property
    def primary_text(self) -> str:
        """获取符号的主体文本，优先返回完整定义，其次返回声明。"""
        return self.full_definition or self.full_declaration or ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolModel":
        """从原始字典构建模型，自动填充缺省值。"""
        return cls(
            name=str(data.get("name", "")),
            type=str(normalize_symbol_type(data.get("type")) or ""),
            start_line=int(data.get("start_line", 0) or 0),
            end_line=int(data.get("end_line", 0) or 0),
            start_byte=int(data.get("start_byte", 0) or 0),
            end_byte=int(data.get("end_byte", 0) or 0),
            full_declaration=str(data.get("full_declaration", "") or ""),
            full_definition=str(data.get("full_definition", "") or ""),
            comment=str(data.get("comment", "") or ""),
        )

    def replace(self, **updates: Any) -> "SymbolModel":
        """创建带更新字段的新实例（类似 dataclasses.replace）。"""
        payload = self.to_dict()
        payload.update(updates)
        return SymbolModel.from_dict(payload)
