#!/usr/bin/env python3
"""
从Tree-sitter解析的JSON文件重构C工程
保持原有的文件结构、目录组织和所有代码内容
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

try:  # 兼容脚本直接执行与包内导入
    from config import get_project_root, get_output_dir, to_absolute_path
except ImportError:  # pragma: no cover
    from .config import get_project_root, get_output_dir, to_absolute_path

_ANALYZER_DIR = Path(__file__).resolve().parent

class CProjectReconstructor:
    def __init__(self, json_file_path, source_project_path=None, target_dir=None):
        """初始化重构器"""
        json_path = Path(json_file_path)
        if not json_path.is_absolute():
            json_path = (_ANALYZER_DIR / json_path).resolve()
        else:
            json_path = json_path.resolve()
        self.json_file_path = json_path

        if source_project_path is None:
            source_project = get_project_root()
        else:
            source_project = Path(source_project_path)
            if not source_project.is_absolute():
                source_project = (_ANALYZER_DIR / source_project).resolve()
        self.source_project_path = Path(source_project).resolve()

        if target_dir is None:
            target_dir = _ANALYZER_DIR.parent / "temp" / "reconstructed_c_project"
        self.target_dir = Path(target_dir).resolve()

        self.analysis_data = {}

        # 加载分析数据
        with self.json_file_path.open('r', encoding='utf-8') as f:
            self.analysis_data = json.load(f)
    
    def reconstruct_project(self):
        """重构整个C工程"""
        print(f"🔄 开始重构C工程...")
        print(f"   源工程: {self.source_project_path}")
        print(f"   目标目录: {self.target_dir}")
        print("=" * 60)
        
        # 创建目标目录
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制整个项目结构（包括非C文件）
        self.copy_project_structure()
        
        # 重构C和H文件
        self.reconstruct_c_files()
        
        print(f"\n✅ C工程重构完成!")
        print(f"📁 重构的工程位于: {self.target_dir}")
    
    def copy_project_structure(self):
        """复制整个项目结构"""
        print("📁 复制项目结构...")
        
        # 复制整个目录树
        for root, dirs, files in os.walk(str(self.source_project_path)):
            # 计算相对路径
            rel_path = os.path.relpath(root, str(self.source_project_path))
            target_root = self.target_dir if rel_path == '.' else (self.target_dir / rel_path)
            
            # 创建目录
            Path(target_root).mkdir(parents=True, exist_ok=True)
            
            # 复制所有非C/H文件
            for file in files:
                source_file = Path(root) / file
                target_file = Path(target_root) / file
                
                # 如果不是C/H文件，直接复制
                if not (file.endswith('.c') or file.endswith('.h')):
                    shutil.copy2(source_file, target_file)
                    print(f"   📄 复制: {os.path.relpath(source_file, str(self.source_project_path))}")
    
    def reconstruct_c_files(self):
        """重构C和H文件"""
        print("\n🔧 重构C和H文件...")
        
        reconstructed_count = 0
        failed_count = 0
        
        for file_path, file_data in self.analysis_data.items():
            if not file_data.get('parse_success', False):
                print(f"❌ 跳过解析失败的文件: {file_path}")
                failed_count += 1
                continue
            
            # 计算目标文件路径
            abs_file_path = to_absolute_path(file_path)
            rel_path = os.path.relpath(str(abs_file_path), str(self.source_project_path))
            target_file_path = self.target_dir / rel_path
            
            try:
                # 读取原始文件内容
                with abs_file_path.open('r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                
                # 重构文件内容
                reconstructed_content = self.reconstruct_file_content(
                    original_content, file_data
                )
                
                # 写入重构后的文件
                target_file_path.parent.mkdir(parents=True, exist_ok=True)
                with target_file_path.open('w', encoding='utf-8') as f:
                    f.write(reconstructed_content)
                
                print(f"   ✅ 重构: {rel_path}")
                reconstructed_count += 1
                
                # 验证重构结果
                self.verify_reconstruction(
                    original_content, reconstructed_content, file_data, rel_path
                )
                
            except Exception as e:
                print(f"   ❌ 重构失败: {rel_path} - {str(e)}")
                failed_count += 1
                
                # 如果重构失败，复制原文件
                try:
                    shutil.copy2(abs_file_path, target_file_path)
                    print(f"   📄 已复制原文件: {rel_path}")
                except:
                    pass
        
        print(f"\n📊 重构统计:")
        print(f"   • 成功重构: {reconstructed_count} 个文件")
        print(f"   • 重构失败: {failed_count} 个文件")
    
    def reconstruct_file_content(self, original_content, file_data):
        """重构单个文件的内容 - 只重构识别到的元素"""
        
        # 只重构JSON中识别到的元素，忽略未识别的内容
        return self.reconstruct_identified_elements_only(original_content, file_data)
    
    def reassemble_from_elements(self, original_content, file_data):
        """从解析的元素重新组装文件内容（用于验证）"""
        # 这是一个更复杂的重构方法，用于验证解析的完整性
        
        # 获取所有解析的元素
        functions = file_data.get('functions', [])
        structs = file_data.get('structs', [])
        includes = file_data.get('includes', [])
        variables = file_data.get('variables', [])
        
        # 创建元素位置映射
        elements = []
        
        # 添加函数
        for func in functions:
            if 'start_byte' in func and 'end_byte' in func:
                elements.append({
                    'type': 'function',
                    'start_byte': func['start_byte'],
                    'end_byte': func['end_byte'],
                    'content': func.get('full_definition', '') or func.get('full_declaration', ''),
                    'name': func['name']
                })
        
        # 添加结构体
        for struct in structs:
            if 'start_byte' in struct and 'end_byte' in struct:
                elements.append({
                    'type': 'struct',
                    'start_byte': struct['start_byte'],
                    'end_byte': struct['end_byte'],
                    'content': struct.get('full_definition', ''),
                    'name': struct['name']
                })
        
        # 添加全局变量
        for var in variables:
            if 'start_byte' in var and 'end_byte' in var:
                elements.append({
                    'type': 'variable',
                    'start_byte': var['start_byte'],
                    'end_byte': var['end_byte'],
                    'content': var.get('full_declaration', '')
                })
        
        # 按位置排序
        elements.sort(key=lambda x: x['start_byte'])
        
        # 重新组装内容
        result_content = ""
        last_end = 0
        
        for element in elements:
            start_byte = element['start_byte']
            end_byte = element['end_byte']
            
            # 添加元素之前的内容（注释、空行等）
            if start_byte > last_end:
                result_content += original_content[last_end:start_byte]
            
            # 添加元素内容
            if element['content']:
                result_content += element['content']
            else:
                # 如果没有解析到内容，使用原始内容
                result_content += original_content[start_byte:end_byte]
            
            last_end = end_byte
        
        # 添加最后剩余的内容
        if last_end < len(original_content):
            result_content += original_content[last_end:]
        
        return result_content
    
    def reconstruct_identified_elements_only(self, original_content, file_data):
        """只重构识别到的元素，按源文件中的位置顺序输出"""
        
        # 获取所有识别到的元素
        functions = file_data.get('functions', [])
        structs = file_data.get('structs', [])
        includes = file_data.get('includes', [])
        variables = file_data.get('variables', [])
        typedefs = file_data.get('typedefs', [])
        macros = file_data.get('macros', [])
        enums = file_data.get('enums', [])
        
        # 收集所有元素并按在源文件中的位置排序
        all_elements = []
        
        # 添加所有类型的元素到统一列表中
        def add_element(elem_type, symbol, content):
            line_no = symbol.get('start_line') or symbol.get('line')
            if not line_no or not content:
                return
            all_elements.append({
                'type': elem_type,
                'line': line_no,
                'content': content,
                'data': symbol
            })

        for include in includes:
            add_element('include', include, include.get('full_declaration', ''))

        for macro in macros:
            macro_text = macro.get('full_definition') or macro.get('full_declaration', '')
            add_element('macro', macro, macro_text)

        for enum in enums:
            enum_def = enum.get('full_definition') or enum.get('full_declaration', '')
            if enum_def and not enum_def.rstrip().endswith(';'):
                enum_def = enum_def.rstrip() + ';'
            add_element('enum', enum, enum_def)

        for typedef in typedefs:
            add_element('typedef', typedef, typedef.get('full_declaration', ''))

        for var in variables:
            add_element('variable', var, var.get('full_declaration', ''))

        for struct in structs:
            struct_def = struct.get('full_definition', '')
            if struct_def and not struct_def.strip().endswith(';'):
                struct_def = struct_def.rstrip() + ';'
            add_element('struct', struct, struct_def)

        # 处理函数声明和定义
        for func in functions:
            func_text = func.get('full_definition') or func.get('full_declaration', '')
            add_element('function', func, func_text)
        
        # 按行号排序，去除重复
        all_elements.sort(key=lambda x: x['line'])
        
        # 构建重构后的内容
        reconstructed_lines = []
        current_section = None
        
        for element in all_elements:
            # 如果切换到新的元素类型，添加注释分隔
            if current_section != element['type']:
                if reconstructed_lines and reconstructed_lines[-1] != "":
                    reconstructed_lines.append("")
                
                section_names = {
                    'include': '// 识别到的包含指令',
                    'macro': '// 识别到的宏定义', 
                    'enum': '// 识别到的枚举定义',
                    'typedef': '// 识别到的typedef定义',
                    'variable': '// 识别到的全局变量',
                    'struct': '// 识别到的结构体定义',
                    'function': '// 识别到的函数定义'
                }
                
                if element['type'] in section_names:
                    reconstructed_lines.append(section_names[element['type']])
                
                current_section = element['type']
            
            # 添加元素内容
            if element['content']:
                if element['type'] == 'function':
                    # 为函数添加注释
                    func_data = element['data']
                    func_type = func_data.get('type', 'unknown')
                    func_name = func_data.get('name', 'unknown')
                    line_info = func_data.get('start_line', 'unknown')
                    reconstructed_lines.append(f"// 函数: {func_name} (line {line_info})")
                
                reconstructed_lines.append(element['content'])
                
                # 在结构体和函数后添加空行
                if element['type'] in ['struct', 'function']:
                    reconstructed_lines.append("")
        
        # 组合所有内容
        return '\n'.join(reconstructed_lines)
    
    def verify_reconstruction(self, original, reconstructed, file_data, file_path):
        """验证重构结果"""
        # 基本验证
        if len(original) != len(reconstructed):
            print(f"   ⚠️  长度不匹配: {file_path} (原:{len(original)} vs 重构:{len(reconstructed)})")
        
        # 检查函数数量
        original_functions = file_data.get('functions', [])
        if original_functions:
            print(f"   📊 包含 {len(original_functions)} 个函数")
        
        # 检查结构体数量
        original_structs = file_data.get('structs', [])
        if original_structs:
            print(f"   📦 包含 {len(original_structs)} 个结构体")
        
        # 检查typedef数量
        original_typedefs = file_data.get('typedefs', [])
        if original_typedefs:
            print(f"   🏷️  包含 {len(original_typedefs)} 个typedef")
    
    def generate_reconstruction_report(self):
        """生成重构报告"""
        report_path = self.target_dir / "reconstruction_report.md"
        
        with report_path.open('w', encoding='utf-8') as f:
            f.write("# C工程重构报告\\n\\n")
            f.write(f"**源工程**: {self.source_project_path}\\n")
            f.write(f"**目标目录**: {self.target_dir}\\n")
            f.write(f"**重构时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            f.write("## 文件重构统计\\n\\n")
            
            total_files = len(self.analysis_data)
            successful_files = sum(1 for data in self.analysis_data.values() if data.get('parse_success', False))
            
            f.write(f"- 总文件数: {total_files}\\n")
            f.write(f"- 成功解析: {successful_files}\\n")
            f.write(f"- 解析失败: {total_files - successful_files}\\n\\n")
            
            # 统计函数、结构体和typedef
            total_functions = sum(len(data.get('functions', [])) for data in self.analysis_data.values())
            total_structs = sum(len(data.get('structs', [])) for data in self.analysis_data.values())
            total_typedefs = sum(len(data.get('typedefs', [])) for data in self.analysis_data.values())
            
            f.write(f"- 总函数数: {total_functions}\\n")
            f.write(f"- 总结构体: {total_structs}\\n")
            f.write(f"- 总typedef: {total_typedefs}\\n\\n")
            
            f.write("## 重构方法\\n\\n")
            f.write("本次重构采用**元素选择性重构**的方法：\\n")
            f.write("1. 复制整个项目结构\\n")
            f.write("2. 保持所有非C/H文件不变\\n")  
            f.write("3. 只重构JSON中识别到的C/H文件元素\\n")
            f.write("4. 忽略未识别到的代码部分\\n")
            f.write("5. 按类型组织重构内容：包含指令 -> typedef定义 -> 全局变量 -> 结构体 -> 函数声明 -> 函数定义\\n")
        
        print(f"📄 重构报告已生成: {report_path}")

def main():
    """主函数"""

    json_file = get_output_dir() / "c_project_analysis.json"
    source_project = get_project_root()
    target_directory = _ANALYZER_DIR.parent / "temp" / "reconstructed_c_project"

    if not json_file.exists():
        print(f"❌ JSON文件不存在: {json_file}")
        return

    if not source_project.exists():
        print(f"❌ 源工程不存在: {source_project}")
        return

    reconstructor = CProjectReconstructor(json_file, source_project, target_directory)
    reconstructor.reconstruct_project()
    reconstructor.generate_reconstruction_report()

if __name__ == "__main__":
    main()
