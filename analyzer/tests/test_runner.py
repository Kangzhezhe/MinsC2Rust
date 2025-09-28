#!/usr/bin/env python3
"""
测试运行器：运行所有测试用例
"""

import sys
import os
import time
import importlib.util
import subprocess

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def run_all_tests():
    """运行所有测试用例"""
    test_modules = [
        'test_symbols',
        'test_binn_dependencies', 
        'test_macro_dependencies',
        'test_type_dependencies',
        'test_function_dependencies',
        'test_scope_analysis'
    ]
    
    print("🧪 开始运行符号依赖分析器测试套件")
    print("=" * 60)
    
    total_start_time = time.time()
    passed_tests = 0
    failed_tests = 0
    
    for i, module_name in enumerate(test_modules, 1):
        print(f"\n[{i}/{len(test_modules)}] 运行 {module_name}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # 使用subprocess运行测试，这样更安全
            result = subprocess.run([sys.executable, f"{module_name}.py"], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                passed_tests += 1
                print("✅ 测试通过")
            else:
                failed_tests += 1
                print(f"❌ 测试失败")
                if result.stderr:
                    print(f"错误: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            failed_tests += 1
            print("❌ 测试超时")
                
        except Exception as e:
            failed_tests += 1
            print(f"❌ 断言失败: {e}")
            continue
        except Exception as e:
            failed_tests += 1
            print(f"❌ 测试 {module_name} 失败: {e}")
            continue
        
        end_time = time.time()
        print(f"⏱️  耗时: {end_time - start_time:.2f}s")
    
    total_end_time = time.time()
    
    print("\n" + "=" * 60)
    print(f"🎉 测试完成！")
    print(f"✅ 通过: {passed_tests}")
    print(f"❌ 失败: {failed_tests}")
    print(f"📊 成功率: {passed_tests/(passed_tests+failed_tests)*100:.1f}%")
    print(f"⏱️  总耗时: {total_end_time - total_start_time:.2f}s")
    
    return failed_tests == 0

def run_quick_tests():
    """运行快速测试（只测试基础功能）"""
    print("🚀 运行快速测试")
    print("=" * 40)
    
    # 只运行最重要的测试
    important_tests = ['test_symbols', 'test_binn_dependencies']
    
    passed = 0
    failed = 0
    
    for test_name in important_tests:
        print(f"\n▶️  运行 {test_name}")
        try:
            module = __import__(test_name)
            if hasattr(module, '__main__'):
                exec(open(f"{test_name}.py").read())
            print(f"✅ {test_name} 通过")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name} 断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            failed += 1
    
    print(f"\n📊 快速测试结果: {passed} 通过, {failed} 失败")
    return failed == 0

def run_specific_test(test_name):
    """运行特定的测试"""
    print(f"🎯 运行特定测试: {test_name}")
    print("=" * 40)
    
    try:
        exec(open(f"{test_name}.py").read())
        print(f"✅ {test_name} 完成")
        return True
    except AssertionError as e:
        print(f"❌ {test_name} 断言失败: {e}")
        return False
    except Exception as e:
        print(f"❌ {test_name} 失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='符号依赖分析器测试运行器')
    parser.add_argument('--quick', action='store_true', help='运行快速测试')
    parser.add_argument('--test', type=str, help='运行特定测试')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_tests()
    elif args.test:
        run_specific_test(args.test)
    else:
        run_all_tests()
