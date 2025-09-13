# 测试套件

这个目录包含了符号依赖分析器的完整测试套件，涵盖了各种C代码符号依赖关系的测试场景。所有测试使用assert断言进行自动化验证。

## 测试文件说明

### 基础测试
- `test_symbols.py` - 测试符号注册表的基本功能，使用assert验证符号存在性
- `test_binn_dependencies.py` - 测试binn_create_type函数的依赖提取（核心验证），严格断言期望依赖

### 专项测试
- `test_macro_dependencies.py` - 测试宏定义和宏使用的依赖关系识别
- `test_type_dependencies.py` - 测试结构体、类型定义、枚举的依赖关系，使用assert验证分析结果
- `test_function_dependencies.py` - 测试函数调用依赖，包括递归调用和跨文件调用，使用assert验证统计结果
- `test_scope_analysis.py` - 测试作用域分析和局部变量过滤功能（严格断言过滤正确性）

### 测试运行器
- `test_runner.py` - 统一的测试运行器，支持assert错误处理和测试结果统计

## 运行测试

### 运行所有测试
```bash
cd tests
python3 test_runner.py
```

### 运行快速测试
```bash
python3 test_runner.py --quick
```

### 运行特定测试
```bash
python3 test_runner.py --test test_binn_dependencies
```

### 单独运行测试文件
```bash
python3 test_macro_dependencies.py
python3 test_type_dependencies.py
python3 test_function_dependencies.py
python3 test_scope_analysis.py
```

## Assert断言验证

### 核心断言
- ✅ **符号存在性**: 验证期望的符号在注册表中存在
- ✅ **依赖关系**: 验证具体的依赖关系被正确识别
- ✅ **过滤正确性**: 严格验证局部变量和参数不被误识别为依赖
- ✅ **类型准确性**: 验证符号类型分类正确

### 失败处理
测试使用assert进行验证，失败时会：
- 显示具体的断言错误信息
- 继续运行其他测试
- 最终显示通过/失败统计

## 测试覆盖的场景

### 宏依赖测试
- ✅ 宏定义中引用其他宏
- ✅ 条件编译宏的识别
- ✅ 函数中宏的使用检测
- ✅ 宏命名模式的启发式识别

### 类型依赖测试
- ✅ 结构体定义中的类型引用
- ✅ typedef定义的依赖关系
- ✅ 函数中自定义类型的使用
- ✅ 枚举定义和使用

### 函数依赖测试
- ✅ 函数调用依赖识别
- ✅ 递归函数调用检测
- ✅ 跨文件函数调用分析
- ✅ 复杂函数的多类型依赖

### 作用域分析测试（严格断言）
- 🔒 **局部变量过滤**: assert确保局部变量不被误识别
- 🔒 **函数参数过滤**: assert确保参数不被误识别
- 🔒 **符号作用域准确性**: 严格验证作用域边界

## 基于的测试数据

测试用例基于以下C项目文件：
- `benchmarks/crown/Input/src/binn.c` - 主要的C实现文件
- `benchmarks/crown/Input/src/binn.h` - 头文件定义
- `benchmarks/crown/Input/test/test-binn.c` - 测试文件

这些文件包含了丰富的C语言特性：
- 宏定义和条件编译
- 结构体和类型定义
- 函数调用和递归
- 跨文件依赖关系
- 复杂的作用域结构

## 核心验证（Assert保证）

### binn_create_type函数依赖验证
```python
# 这些依赖必须被正确识别
assert 'APIENTRY' in found_dependencies
assert 'BINN_STORAGE_MIN' in found_dependencies  
assert 'BINN_STORAGE_MAX' in found_dependencies
assert 'BINN_STORAGE_HAS_MORE' in found_dependencies

# 这些局部符号不能被误识别
assert 'storage_type' not in found_dependencies    # 函数参数
assert 'data_type_index' not in found_dependencies # 函数参数
```

### 作用域过滤验证
```python
# 严格验证：局部变量不能被识别为依赖
assert len(false_positives) == 0, f"局部变量被误识别: {false_positives}"

# 严格验证：函数参数不能被识别为依赖  
assert len(param_false_positives) == 0, f"参数被误识别: {param_false_positives}"
```

## 测试结果示例

```
🧪 开始运行符号依赖分析器测试套件
============================================================
✅ 通过: 6
❌ 失败: 0  
📊 成功率: 100.0%
⏱️  总耗时: 2.45s
```
