import configparser
import os
import re
import sys
import json
from parse_config import read_config

# 读取文件内容
def read_file(filename):
    with open(filename, 'r') as file:
        return file.readlines()

import subprocess
import re
import os  # Add os module back


def _dedupe_keep_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _iter_compiler_tokens(entry):
    """Return command tokens while preserving original argument order."""
    args = entry.get("arguments")
    if isinstance(args, list) and args:
        return args
    cmd = entry.get("command", "")
    return cmd.split()


def _extract_include_dirs(entry):
    include_dirs = []
    base_dir = entry.get("directory", "")
    for token in _iter_compiler_tokens(entry):
        if token.startswith("-I") and len(token) > 2:
            inc = token[2:]
            if inc and not os.path.isabs(inc) and base_dir:
                inc = os.path.normpath(os.path.join(base_dir, inc))
            include_dirs.append(inc)
    return _dedupe_keep_order(include_dirs)

def merge_files(c_filename, output_filename, include_dirs, preprocess_flags=None):
    """
    Use gcc -E -P -C with fake system headers to preserve #include <...> directives.
    Strategies:
    1. Scan project for used system headers and create dummy versions in Tool/fake_system_headers.
       These dummy headers contain `/* __RESTORE_SYSTEM_INCLUDE: <header> */`.
    2. Run gcc -E -P -C with -I Tool/fake_system_headers.
    3. Post-process output to replace the restore markers with real #include <...> directives.
    """
    
    # Determine project root and fake header dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '../../'))
    
    # Place global fake headers in Output/tmp/fake_system_headers
    # This keeps Tool/ clean
    fake_header_dir = os.path.join(project_root, 'Output', 'tmp', 'fake_system_headers')
    
    # Verify fake headers exist, if not run the preparation script
    if not os.path.exists(fake_header_dir) or not os.listdir(fake_header_dir):
        print("Generating fake system headers...")
        try:
             # Import dynamically to avoid top-level cyclical deps if any (unlikely)
             sys.path.append(script_dir)
             import prepare_fake_headers
             # Ensure the output directory exists
             os.makedirs(fake_header_dir, exist_ok=True)
             prepare_fake_headers.setup_fake_headers(project_root, fake_header_dir)
             
             # Also cleanup old location if it exists
             old_loc = os.path.join(project_root, 'Tool/fake_system_headers')
             if os.path.exists(old_loc):
                 import shutil
                 shutil.rmtree(old_loc, ignore_errors=True)
                 
        except Exception as e:
            print(f"Warning: Could not generate fake headers: {e}")

    # Prepare GCC command
    # -E: Preprocess only
    # -P: No linemarkers
    # -C: Preserve comments (essential for our restore markers)
    cmd = ['gcc', '-E', '-P', '-C', c_filename, '-o', output_filename]

    # Preserve original compile macro environment (e.g., -D/-U/-std) when available.
    for flag in _dedupe_keep_order(preprocess_flags or []):
        cmd.append(flag)
    
    # Add include directories from compile_commands
    # Convert to list to avoid set ordering issues if any (though usually order matters)
    # include_dirs is passed as a set/collection. We should probably sort or keep logic.
    # But wait, include order matters. 'include_dirs' argument here seems to be a set in process_files?
    # "{arg[2:] ...}" composes a set.
    # This loses order. But usually -I order matters for overrides.
    # For now, append them.
    for include_dir in _dedupe_keep_order(include_dirs):
        cmd.append(f'-I{include_dir}')
        
    # Add fake header dir at the END of user includes but BEFORE system includes (implicit)
    # Actually, to override system headers, we just need -I because GCC looks at -I before std output.
    cmd.append(f'-I{fake_header_dir}')
    
    # Add -nostdinc? No, because we might miss some weird compiler-specific headers we didn't fake?
    # But if we don't use -nostdinc, and we miss a header in our fake dir, it will expand the REAL system header.
    # This is actually GOOD default info: "If not masked, expand it".
    # So we simply prioritize our fakes.

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error preprocessing {c_filename}: {e}")
        return []

    # 3. Restore system includes in the output file
    try:
        with open(output_filename, 'r') as f:
            content = f.read()
        
        # Regex to find our markers
        # Format: /* __RESTORE_SYSTEM_INCLUDE: <stdio.h> */
        # We capture the header name.
        # Note: We need to handle potential variations in spacing if GCC touches it?
        # Usually comments are preserved as is.
        
        restore_pattern = re.compile(r'/\*\s*__RESTORE_SYSTEM_INCLUDE:\s*([^\s\*]+)\s*\*/')
        
        # Function to replace match with #include <header>
        def restore_replacer(match):
            header = match.group(1)
            # Ensure filtering of garbage
            if header.startswith('<') and header.endswith('>'):
                return f'#include {header}'
            elif header.startswith('"') and header.endswith('"'):
                return f'#include {header}'
            else:
                 # Fallback if just name
                 return f'#include <{header}>'

        new_content = restore_pattern.sub(restore_replacer, content)
        
        # Write back
        with open(output_filename, 'w') as f:
            f.write(new_content)
            
        print(f"Merged file saved to {output_filename} (System headers preserved)")

    except Exception as e:
         print(f"Error restoring headers for {output_filename}: {e}")

    included_files = []
    
    # 4. Extract dependencies using gcc -MM (user headers only)
    try:
        # Use simple -MM command on the original file
        # We need the same include flags
        dep_cmd = ['gcc', '-MM', c_filename]
        for flag in _dedupe_keep_order(preprocess_flags or []):
            dep_cmd.append(flag)
        for include_dir in _dedupe_keep_order(include_dirs):
            dep_cmd.append(f'-I{include_dir}')
            
        # Run process
        output = subprocess.check_output(dep_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        
        # Parse Makefile rule output: "target.o: source.c header1.h header2.h ..."
        # Extract all dependencies
        # Remove backslashes and newlines
        output = output.replace('\\\n', ' ').replace('\n', ' ')
        
        # Split by space
        parts = output.split()
        
        # Iterate parts, skip target and colon
        for part in parts:
            if part.endswith(':') or part == '\\':
                continue
            
            # Normalize path
            path = os.path.normpath(part)
            basename = os.path.basename(path)
            name_no_ext = os.path.splitext(basename)[0]
            
            # Add to list if it's not the source file itself (though logic handles it outside too)
            # And prevent duplicates
            if name_no_ext not in included_files:
                included_files.append(name_no_ext)
                
    except Exception as e:
        print(f"Warning: Could not determine dependencies for {c_filename}: {e}")

    return included_files

def read_compile_commands(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def process_compile_commands(compile_commands_path, write_back=False):
    compile_commands = read_compile_commands(compile_commands_path)
    
    # Locate project root: Tool/Tool_py/../../ -> project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    for entry in compile_commands:
        # 1. Fix directory
        if 'directory' in entry and entry['directory'].startswith('/app'):
            entry['directory'] = entry['directory'].replace('/app', project_root)

        # 2. Fix file
        if 'file' in entry and entry['file'].startswith('/app'):
            entry['file'] = entry['file'].replace('/app', project_root)

        # 2.1 Normalize relative file path (common in bear-generated compile_commands)
        if 'file' in entry and entry['file'] and not os.path.isabs(entry['file']):
            base_dir = entry.get('directory', '')
            if base_dir:
                entry['file'] = os.path.normpath(os.path.join(base_dir, entry['file']))

        # 3. Fix command string
        if 'command' in entry:
            entry['command'] = entry['command'].replace('/app', project_root)
        
        # 4. Fix arguments (if present)?
        # Usually 'command' is enough if present.
        # But if 'arguments' is present, we should fix it too just in case.
        if 'arguments' in entry:
            updated_arguments = []
            for arg in entry['arguments']:
                if arg.startswith('/app'):
                    updated_arguments.append(arg.replace('/app', project_root))
                elif arg.startswith('-I/app'):
                     updated_arguments.append(arg.replace('/app', project_root))
                else:
                    updated_arguments.append(arg)
            entry['arguments'] = updated_arguments

        # 5. Handle missing command but present arguments (original logic)
        if entry.get('command','') == '' and entry.get('arguments','') != '':
            directory = entry['directory']
            updated_arguments = []
            for arg in entry['arguments']:
                if arg.startswith('-I'):
                    include_path = arg[2:]  # 提取 -I 后的路径
                    if not os.path.isabs(include_path):  # 如果是相对路径
                        absolute_path = os.path.normpath(os.path.join(directory, include_path))
                        updated_arguments.append(f'-I{absolute_path}')
                    else:
                        updated_arguments.append(arg)
                else:
                    updated_arguments.append(arg)
            entry['arguments'] = updated_arguments
            entry['command'] = ' '.join(updated_arguments)

    if write_back:
        with open(compile_commands_path, 'w') as file:
            json.dump(compile_commands, file, indent=4)
    return compile_commands

def _extract_preprocess_flags(entry):
    flags = []
    for token in _iter_compiler_tokens(entry):
        if token.startswith('-D') or token.startswith('-U'):
            flags.append(token)
        elif token.startswith('-std='):
            flags.append(token)
    return _dedupe_keep_order(flags)


def process_files(compile_commands_path, output_dir, excluded_files = {"framework"}):
    # 读取 compile_commands.json 文件
    # Keep compile_commands immutable by default to avoid permission failures.
    compile_commands = process_compile_commands(compile_commands_path, write_back=False)

    # 存储每个 .c 文件及其包含的 .h 文件的字典
    include_dict = {}
    all_file_paths = []
    processed_c_files = set()  # 记录已处理的.c文件基础名称

    # 收集所有包含目录
    all_include_dirs = []
    for entry in compile_commands:
        all_include_dirs.extend(_extract_include_dirs(entry))
    all_include_dirs = _dedupe_keep_order(all_include_dirs)

    # 处理每个 .c 文件
    for entry in compile_commands:
        c_filename = entry['file']
        
        # 确定输出文件的子目录：只有以'test-'开头的文件才放入test目录
        if os.path.basename(c_filename).startswith('test-'):
            sub_dir = 'test'
        else:
            sub_dir = 'src'

        # 创建输出子目录（如果不存在）
        output_sub_dir = os.path.join(output_dir, sub_dir)
        os.makedirs(output_sub_dir, exist_ok=True)

        output_filename = os.path.join(output_sub_dir, os.path.basename(c_filename))

        include_dirs = _extract_include_dirs(entry)
        preprocess_flags = _extract_preprocess_flags(entry)

        # 合并文件内容并保存到输出文件
        included_files = merge_files(c_filename, output_filename, include_dirs, preprocess_flags)
        
        if output_filename not in all_file_paths:
            all_file_paths.append(output_filename)
        
        filtered_files = [f for f in included_files if f not in excluded_files]
        key = os.path.splitext(os.path.basename(c_filename))[0]
        
        if key not in excluded_files:
            include_dict[key] = [f for f in filtered_files if f != key]
            processed_c_files.add(key)  # 记录已处理的.c文件基础名称

    # 处理独立的.h文件（没有对应.c文件的头文件）
    standalone_h_files = []

    for include_dir in all_include_dirs:
        if os.path.exists(include_dir):
            for root, dirs, files in os.walk(include_dir):
                for filename in files:
                    if filename.endswith('.h'):
                        h_basename = os.path.splitext(filename)[0]
                        
                        # 检查是否有对应的.c文件已经被处理
                        if h_basename not in processed_c_files and h_basename not in excluded_files:
                            h_filepath = os.path.join(root, filename)
                            
                            # 避免重复处理同名的头文件
                            if h_basename not in [os.path.splitext(os.path.basename(f))[0] for f in standalone_h_files]:
                                standalone_h_files.append(h_filepath)

    # 处理独立的.h文件
    for h_filepath in standalone_h_files:
        try:
            filename = os.path.basename(h_filepath)
            h_basename = os.path.splitext(filename)[0]
            
            # 确定输出子目录：只有以'test-'开头的文件才放入test目录
            if filename.startswith('test-'):
                sub_dir = 'test'
            else:
                sub_dir = 'src'
            
            output_sub_dir = os.path.join(output_dir, sub_dir)
            os.makedirs(output_sub_dir, exist_ok=True)
            
            # 创建对应的输出文件名，将.h改为.c
            output_h_filename = os.path.join(output_sub_dir, h_basename + '.c')
            
            # 处理独立的.h文件
            included_files = merge_files(h_filepath, output_h_filename, all_include_dirs, ["-DHAVE_CONFIG_H=1"])
            
            if output_h_filename not in all_file_paths:
                all_file_paths.append(output_h_filename)
            
            filtered_files = [f for f in included_files if f not in excluded_files]
            include_dict[h_basename] = [f for f in filtered_files if f != h_basename]
            
            print(f"Processed standalone header: {h_filepath} -> {output_h_filename}")
            
        except Exception as e:
            print(f"Warning: Could not process {h_filepath}: {e}")

    return include_dict, all_file_paths

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python merge_c_h.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    cfg = read_config(config_path)
    compile_commands_path = cfg['Paths']['compile_commands_path']
    tmp_dir = cfg['Paths']['tmp_dir']

    # 处理文件并获取包含的 .h 文件字典
    include_dict = process_files(compile_commands_path, tmp_dir)
    # print(json.dumps(include_dict, indent=4))