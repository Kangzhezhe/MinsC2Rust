# 符号依赖可视化使用示例

## 📚 快速开始

### 安装依赖
```bash
pip3 install matplotlib networkx numpy
```

### 基本用法

#### 1. 命令行模式

```bash
# 可视化符号的所有依赖关系
python3 dependency_visualizer.py --symbol binn_create_type --direction both

# 只看符号依赖的其他符号
python3 dependency_visualizer.py --symbol main --direction forward --depth 2

# 只看依赖该符号的其他符号  
python3 dependency_visualizer.py --symbol BOOL --direction backward --depth 1

# 显示依赖摘要
python3 dependency_visualizer.py --symbol binn_create_type --summary
```

#### 2. 交互模式

```bash
python3 dependency_visualizer.py --interactive
```

交互命令：
- `list` - 列出可用符号
- `search <关键词>` - 搜索符号
- `vis <符号> [方向] [深度]` - 可视化依赖关系
- `summary <符号>` - 显示依赖摘要
- `help` - 显示帮助
- `quit` - 退出

#### 3. Python编程接口

```python
from dependency_visualizer import DependencyVisualizer

# 创建可视化器
visualizer = DependencyVisualizer('symbol_dependencies.json')

# 可视化符号依赖
filepath = visualizer.visualize_dependencies(
    'binn_create_type', 
    direction='both',    # 'forward', 'backward', 'both'
    max_depth=2,         # 搜索深度
    max_nodes=50         # 最大节点数
)

# 生成依赖摘要
summary = visualizer.generate_dependency_summary('binn_create_type')
print(summary)

# 查找可用符号
symbols = visualizer.list_available_symbols(20)
```

## 🎨 可视化特性

### 节点颜色
- 🔵 **蓝色** - 函数 (functions)
- 🔴 **红色** - 宏 (macros)  
- 🟢 **绿色** - 结构体 (structs)
- 🟠 **橙色** - 类型定义 (typedefs)
- 🟣 **紫色** - 变量 (variables)
- 🟡 **黄色** - 目标符号（高亮显示）

### 边样式
- **实线** - 函数调用、结构体成员访问
- **虚线** - 类型引用、枚举使用
- **点划线** - 宏使用
- **点线** - 变量使用

### 图例信息
- 节点数量、边数量
- 搜索深度
- 符号类型分布
- 依赖关系类型

## 📁 输出文件

所有可视化图片保存在 `output/` 目录下，文件命名格式：
```
deps_<符号名>_<方向>_<深度>d.png
```

示例：
- `deps_main_forward_2d.png` - main符号的前向依赖（深度2）
- `deps_BOOL_backward_1d.png` - BOOL符号的后向依赖（深度1）
- `deps_binn_create_type_both_2d.png` - binn_create_type的双向依赖（深度2）

## 🎯 实用技巧

### 1. 控制图复杂度
```bash
# 限制节点数量避免图过于复杂
python3 dependency_visualizer.py --symbol main --max-nodes 20

# 降低搜索深度
python3 dependency_visualizer.py --symbol main --depth 1
```

### 2. 分析核心符号
```bash
# 查看被依赖最多的符号
python3 dependency_visualizer.py --symbol BOOL --direction backward

# 查看依赖最多的符号
python3 dependency_visualizer.py --symbol main --direction forward
```

### 3. 理解模块关系
```bash
# 查看特定函数的依赖
python3 dependency_visualizer.py --symbol binn_create_type --summary
```

## 🔧 常见问题

### Q: 图片中文字无法显示？
A: 这是字体问题，不影响功能使用。符号名称都是英文，核心信息完整。

### Q: 图太复杂看不清？
A: 可以降低深度（--depth 1）或限制节点数（--max-nodes 20）

### Q: 找不到某个符号？
A: 使用 `search` 命令或 `list` 命令确认符号是否存在

### Q: 想要不同的可视化效果？
A: 可以修改 `dependency_visualizer.py` 中的颜色和样式设置
