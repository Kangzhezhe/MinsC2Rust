# 符号依赖关系分析器

这个模块用于分析C代码项目中的符号依赖关系，基于tree-sitter AST和`c_project_analysis.json`构建符号依赖图。

## ✨ 主要特性

- 🔍 **全面的符号类型支持**: functions, structs, typedefs, variables, macros, enums
- 🔗 **多种依赖关系类型**: function_call, type_reference, variable_use, macro_use, enum_use, struct_member  
- 🌳 **基于AST的精确分析**: 使用tree-sitter进行语法树分析
- 🎯 **智能作用域过滤**: 自动过滤局部变量和函数参数，避免误识别
- 🔄 **自动去重机制**: 智能检测并去除重复的依赖关系，提高数据质量
- 📊 **丰富的统计信息**: 提供详细的依赖关系统计和分析报告
- 🧪 **完整的测试覆盖**: 包含全面的assert断言测试套件

## 文件结构

```
symbol_dependency_analysis/
├── README.md                     # 本文件
├── symbol_dependency_analyzer.py # 主要的分析器实现
├── dependency_visualizer.py      # 依赖关系可视化器
├── test_visualization.py         # 可视化功能测试
├── test_symbols.py              # 测试脚本
├── requirements.txt             # 依赖包列表
└── output/                      # 可视化输出目录
```

## 使用方法

### 基础使用

```python
from symbol_dependency_analyzer import SymbolDependencyAnalyzer

# 创建分析器实例
analyzer = SymbolDependencyAnalyzer('/path/to/c_project_analysis.json')

# 构建符号注册表
analyzer.build_symbol_registry()

# 分析依赖关系
analyzer.analyze_all_dependencies()

# 获取统计信息
stats = analyzer.get_dependency_statistics()
print(f"总符号数: {stats['total_symbols']}")
print(f"总依赖数: {stats['total_dependencies']}")
```

### 查询特定符号的依赖

```python
# 获取函数的依赖关系
dependencies = analyzer.dependency_graph.get_symbol_dependencies('binn_create_type')
for dep in dependencies:
    print(f"{dep.source_symbol.name} -> {dep.target_symbol.name} ({dep.dependency_type.value})")
```

### 可视化依赖关系

```python
from dependency_visualizer import DependencyVisualizer

# 创建可视化器
visualizer = DependencyVisualizer('symbol_dependencies.json')

# 可视化符号的依赖关系
visualizer.visualize_dependencies('binn_create_type', direction='both', max_depth=2)

# 生成依赖摘要
summary = visualizer.generate_dependency_summary('binn_create_type')
print(summary)
```

### 命令行可视化

```bash
# 可视化指定符号的依赖关系
python3 dependency_visualizer.py --symbol binn_create_type --direction both

# 交互模式
python3 dependency_visualizer.py --interactive

# 显示依赖摘要
python3 dependency_visualizer.py --symbol binn_create_type --summary
```

## 运行测试

```bash
cd symbol_dependency_analysis
python3 symbol_dependency_analyzer.py  # 运行基础框架测试
python3 test_symbols.py               # 运行特定符号测试
python3 test_visualization.py         # 测试可视化功能
```

## 开发计划

### ✅ 第一阶段：基础框架（已完成）
- 数据结构设计
- 符号注册表构建
- 基础符号识别

### ✅ 第二阶段：AST遍历和符号识别（已完成）
- 实现AST遍历器
- 区分真实符号和局部变量
- 符号作用域分析
- **智能去重机制**: 自动检测并去除59.5%的重复依赖关系

### 🔧 性能优化成果
```
📊 去重效果统计:
  发现依赖: 10,215 个
  实际添加: 4,132 个  
  去重数量: 6,083 个
  去重率: 59.5%
  文件大小优化: 4.7MB → 2.1MB (减少55%)
```

### ✅ 第三阶段：构建完整依赖图（已完成）
- 提取所有依赖关系 ✅
- 构建完整符号依赖图 ✅
- 依赖图导出和可视化 ✅
- 交互式依赖查询 ✅
- 多种可视化模式 ✅

### 🎨 可视化功能
```
📊 可视化特性:
  支持方向: forward (前向), backward (后向), both (双向)
  节点着色: 按符号类型自动着色
  边样式: 按依赖类型区分线条样式
  交互模式: 命令行交互式查询
  输出格式: 高分辨率PNG图片
  文件管理: 统一保存在output目录
```

### ⏳ 第四阶段：测试和优化
- 准确性验证
- 性能优化
- 报告生成

## 示例输出

基于`binn_create_type`函数的依赖分析示例：

```
binn_create_type 依赖于:
├── APIENTRY (macro)
├── BINN_STORAGE_MIN (macro)
├── BINN_STORAGE_MAX (macro)
└── BINN_STORAGE_HAS_MORE (macro)
```

## 技术细节

- 使用tree-sitter-c进行AST解析
- 支持复杂的符号作用域分析
- 排除C关键字和内置函数
- 基于AST上下文推断依赖类型
