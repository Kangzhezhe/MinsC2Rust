import os
import re
import glob
import subprocess

def get_header_macros(header_name):
    """
    Extracts macros defined specifically by a system header, excluding compiler built-ins.
    """
    try:
        # 1. Get base macros (without header)
        base_cmd = ['gcc', '-E', '-dM', '-x', 'c', '/dev/null']
        base_res = subprocess.run(base_cmd, capture_output=True, text=True)
        base_macros = set(base_res.stdout.splitlines())

        # 2. Get macros with header included
        # logic: -include header_name
        # We need to make sure we don't fail if header doesn't exist
        header_cmd = ['gcc', '-E', '-dM', f'-include{header_name}', '-x', 'c', '/dev/null']
        header_res = subprocess.run(header_cmd, capture_output=True, text=True)
        
        if header_res.returncode != 0:
            return "" # Header likely doesn't exist or error

        header_total_macros = set(header_res.stdout.splitlines())
        
        # 3. Diff
        filtered_macros = []
        for macro_line in (header_total_macros - base_macros):
            # Parse macro name to check against blacklist
            parts = macro_line.split()
            if len(parts) >= 2:
                # Handle function-like macros: #define MACRO(x) ...
                name = parts[1].split('(')[0]
                
                # Filter out:
                # 1. Internal macros (starting with _), EXCEPT for endian-related double-underbar macros which are critical.
                # 2. Standard library functions that shouldn't be macros (strstr etc)
                blacklist = {'strstr', 'strchr', 'strrchr', 'memchr', 'strpbrk', 'index', 'rindex', 'strcasestr'}
                
                is_internal = name.startswith('_')
                # Whitelist specific internal macros needed for endianness or system types
                if is_internal:
                    if name in ('__BIG_ENDIAN', '__LITTLE_ENDIAN', '__PDP_ENDIAN', '__BYTE_ORDER'):
                        is_internal = False
                        
                if not is_internal and name not in blacklist:
                     filtered_macros.append(macro_line)

        # Sort for stability
        return "\n".join(sorted(filtered_macros))
    except Exception as e:
        print(f"Warning: Failed to extract macros for {header_name}: {e}")
        return ""

def setup_fake_headers(project_root, output_dir):
    """
    Scans the project for #include <...> directives and creates fake header files
    that contain a special restoration marker comment.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Scan all .c and .h files in project
    headers_found = set()
    include_pattern = re.compile(r'^\s*#\s*include\s*<([^>]+)>')

    # Walk recursively through likely source directories
    search_roots = [
        os.path.join(project_root, 'benchmarks'),
        os.path.join(project_root, 'comparisons')
    ]
    
    for search_root in search_roots:
        for root, dirs, files in os.walk(search_root):
             # Skip hidden directories and output/build directories to save time
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('build', 'Output', 'test')]
            
            headers_found.update(
                m.group(1) 
                for f_name in files if f_name.endswith(('.c', '.h'))
                for line in open(os.path.join(root, f_name), 'r', errors='ignore') 
                if (m := include_pattern.search(line))
            )

    print(f"Found {len(headers_found)} unique system headers.")

    # 2. Create fake headers
    for header in headers_found:
        fake_path = os.path.join(output_dir, header)
        os.makedirs(os.path.dirname(fake_path), exist_ok=True)
        
        # Get macros from the real system header
        # We assume the host system has these headers available via gcc
        macros_content = ""
        try:
             # Only extract macros for likely configuration headers to avoid bloat/time?
             # User asked for general solution. General solution = do it for all appropriate ones.
             # However, dumping for huge headers might slow down initial setup.
             # But it's done once.
             # Let's do it for all.
             extracted = get_header_macros(header)
             if extracted:
                 macros_content = f"/* Auto-extracted macros from system {header} */\n" + extracted + "\n"
        except Exception:
             pass

        with open(fake_path, 'w') as f:
            f.write(f"/* FAKE HEADER for {header} */\n")
            f.write(macros_content)
            # The restore marker is crucial for the post-processing step
            f.write(f"/* __RESTORE_SYSTEM_INCLUDE: {header} */\n")
            
    print(f"Created fake headers in {output_dir}")

if __name__ == "__main__":
    # Adjust paths as needed
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    # Use Output/tmp/fake_system_headers instead of Tool/fake_system_headers
    output_dir = os.path.join(project_root, 'Output', 'tmp', 'fake_system_headers')
    setup_fake_headers(project_root, output_dir)
