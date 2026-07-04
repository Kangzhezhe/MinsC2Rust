import os
import sys
import shutil
from typing import List, Dict, Optional

# Add Tool_py directory to path so that 'models' package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from models.llm_model import generate_response

DIFF_TEST_PROMPT = """
You are an expert Rust programmer and Test Engineer.
Your task is to generate a **Rust Differential Test file** that rigorously verifies the equivalence between a C function and its reported Rust translation.

### Context
- **C Library**: A shared library named `{lib_name}` (dynamic link: `lib{lib_name}.so`) has been compiled from the C source.
- **Rust Crate**: The Rust translation is in a crate named `test_project`. The module path is `test_project::{module_name}`.

### Input Source Code
**Original C Code**:
```c
{c_source}
```

**Translated Rust Code**:
```rust
{rust_source}
```

### Requirements for the Test File
1.  **Imports**:
    -   Use `libc` types (`c_int`, `c_void`, etc.).
    -   Import the Rust functions from `test_project::{module_name}`.

2.  **FFI Declaration**:
    -   Define a `#[link(name = "{lib_name}", kind = "dylib")]` block.
    -   Inside it, declare `extern "C"` functions corresponding to the C source key functions.
    -   Ensure C function signatures use `libc` types correctly (e.g., `*mut c_void` for `void*`).

3.  **Test Logic (Function `test_{module_name}_diff`)**:
    -   Create a Rust `#[test]` function.
    -   **Step 1: Ground Truth (C)**
        -   Call the C functions via FFI.
        -   Construct valid inputs (using raw pointers if necessary).
        -   Store the return value/state as the "Ground Truth".
    -   **Step 2: Target (Rust)**
        -   Call the translated Rust functions with **semantically equivalent inputs**.
        -   *Crucial*: You must adapt inputs. For example, if C takes `void*`, Rust might take `Rc<RefCell<T>>`. You must construct the Rust objects to match the C intent.
    -   **Step 3: Assertion**
        -   Compare the results.
        -   Handle Type Mismatch: If C returns `int` (1=success) and Rust returns `bool`, cast or compare logic (e.g., `assert_eq!(c_res != 0, r_res)`).

### Output Format
-   Return **ONLY** the raw Rust code for the test file.
-   Do **NOT** use markdown blocks (```rust ... ```).
-   Do **NOT** add explanations text.
"""

def generate_diff_test_with_llm(
    output_dir: str,
    lib_name: str,
    module_name: str,
    c_source: str,
    rust_source: str,
    model_name: str = "gpt4o"
):
    """
    使用 LLM 生成差分测试用例
    """
    
    prompt = DIFF_TEST_PROMPT.format(
        lib_name=lib_name,
        module_name=module_name,
        c_source=c_source,
        rust_source=rust_source
    )

    print(f"[-] Requesting LLM to generate diff test for {module_name} using {model_name}...")
    
    # 真实调用 LLM
    try:
        # Note: generate_response is imported from models/llm_model.py
        # use model_name to avoid UnboundLocalError in generate_response if unknown model passed
        if model_name not in ["local", "qwen", "deepseek", "zhipu", "claude", "gpt4o", "openai"]:
             print(f"[!] Warning: Model '{model_name}' might not be supported by generate_response. Defaulting to 'gpt4o'.")
             model_name = "gpt4o"

        rust_test_code = generate_response(prompt, llm_model=model_name, temperature=0.1)
    except Exception as e:
        print(f"[!] LLM Generation failed: {e}")
        return

    # 清理 markdown 标记（如果 LLM 输出了）
    rust_test_code = rust_test_code.replace("```rust", "").replace("```", "").strip()
    
    # 简单的完整性检查
    if "#[test]" not in rust_test_code:
        print(f"[!] Warning: Generated code might be incomplete (missing #[test])")

    test_file_path = os.path.join(output_dir, f"tests/test_diff_{module_name}.rs")
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    
    with open(test_file_path, "w") as f:
        f.write(rust_test_code)
    
    print(f"[+] Generated Differential Test: {test_file_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gen_diff_tests.py <rust_project_path> <c_src_path> [model_name]")
        sys.exit(1)
        
    project_path = sys.argv[1]
    c_src_path = sys.argv[2]
    model_name = sys.argv[3] if len(sys.argv) > 3 else "gpt4o"
    
    # 示例：读取真实源代码并喂给 LLM
    # 这里我们只演示 arraylist 模块
    module = "arraylist"
    
    try:
        # Read C Code
        c_file = os.path.join(c_src_path, f"{module}.c")
        if os.path.exists(c_file):
            with open(c_file, "r") as f:
                c_code = f.read()
        else:
            print(f"[!] C source not found: {c_file}")
            return

        # Read Rust Code
        rust_file = os.path.join(project_path, f"src/{module}.rs")
        if os.path.exists(rust_file):
            with open(rust_file, "r") as f:
                rust_code = f.read()
        else:
            print(f"[!] Rust source not found: {rust_file}")
            return
            
        generate_diff_test_with_llm(
            output_dir=project_path,
            lib_name="calgo",
            module_name=module,
            c_source=c_code,
            rust_source=rust_code,
            model_name=model_name
        )
            
    except Exception as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    main()
