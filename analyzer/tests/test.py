#!/usr/bin/env python3
"""
在 AST 中查找指定符号的节点并打印 node.type / 行 / snippet / sexp
用法:
  python3 test.py -p /home/mins/MinsC2Rust -f binn_value,binn_new
"""
from pathlib import Path
import argparse, re, sys
from tree_sitter import Language, Parser
import tree_sitter_c as ts_c

def iter_nodes(n):
    yield n
    for c in n.children:
        yield from iter_nodes(c)

# 创建并复用 C 语言对象
C_LANGUAGE = Language(ts_c.language())
import subprocess, shutil

def analyze_file(path, names):
    raw = path.read_text(errors='ignore')
    content = raw
    gcc = shutil.which('gcc') or shutil.which('clang')
    if gcc:
        try:
            p = subprocess.run([gcc, '-E', '-P', '-DAPIENTRY=', '-xc', '-'],
                               input=raw.encode('utf8'), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
            content = p.stdout.decode('utf8')
        except Exception:
            content = raw
    # 使用带 language 的 Parser 构造（不要调用不存在的 set_language）
    p = Parser(C_LANGUAGE)
    tree = p.parse(bytes(content, 'utf8'))
    root = tree.root_node
    found = []
    for n in iter_nodes(root):
        try:
            text = content[n.start_byte:n.end_byte]
        except Exception:
            text = ""
        for name in names:
            if n.type == 'identifier' and text == name:
                found.append((name, n, text))
            elif name in text:
                found.append((name, n, text))
    if found:
        print("="*80)
        print("FILE:", path)
        for name, node, text in found:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            snippet = text.replace("\n","\\n")
            print(f"\nNAME: {name}")
            print(f" node.type: {node.type}  lines: {start_line}-{end_line}  bytes:{node.start_byte}-{node.end_byte}")
            print(" snippet:", snippet[:300])
            ids = []
            for c in iter_nodes(node):
                if c.type == 'identifier':
                    ids.append((content[c.start_byte:c.end_byte], c.start_point[0]+1))
            if ids:
                print(" identifier nodes:", ids[:10])
            else:
                print(" identifier nodes: NONE")
            try:
                print(" sexp:", node.sexp())
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--project', default='/home/mins/MinsC2Rust/benchmarks/crown/Input', help='项目根目录')
    parser.add_argument('-f','--functions', default='binn_value', help='逗号分隔的名字列表')
    args = parser.parse_args()

    names = [n.strip() for n in args.functions.split(',') if n.strip()]
    project = Path(args.project)

    candidates = []
    for ext in ('**/*.c','**/*.h'):
        for p in project.glob(ext):
            try:
                s = p.read_text(errors='ignore')
            except Exception:
                continue
            if any(re.search(r'\b'+re.escape(n)+r'\b', s) for n in names):
                candidates.append(p)

    if not candidates:
        print("No files with target names found by text search.")
        sys.exit(0)

    print(f"Found {len(candidates)} candidate files, parsing with tree-sitter...\n")
    for p in candidates:
        analyze_file(p, names)

if __name__ == '__main__':
    main()