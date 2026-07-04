
from models.llm_model import generate_response
import difflib
from utils import debug, extract_related_items

def compare_strings(str1, str2):
    # 使用 difflib.ndiff 比较两个字符串
    diff = difflib.ndiff(str1.splitlines(), str2.splitlines())
    # 将差异结果转换为列表
    diff_list = list(diff)
    # 将差异结果转换为字符串
    diff_str = '\n'.join(diff_list)
    return diff_str

def get_trajectory(input_dict,response,test_error,llm_model):

    trajectory_prompt = f"""
    你是一个代码诊断专家，你之前有一个代码的改错任务，但是你改出来的代码仍然有错误存在，
    请你简单对比改错前后代码，描述这一次修改的过程，具体哪个地方的代码前后是怎么改的，报错信息是什么,以便你的之后的改错过程不再犯相同的错误：

    ## 使用 difflib库比较本次改错前后的代码的改动：
    {compare_strings(input_dict,response)}
    ## 本次改错的报错信息：
    {test_error}
    
    请按以下步骤思考：
    1. 提取这一轮改错前后的完整语句 （如：这一次我修改/插入/删除了XXX语句...）
    2. 提取这一次的报错信息的关键信息 （如：这一次报错内容是XXX语句，报错内容）

    只返回本次改错过程和报错信息的描述，不要给出下一次修改的建议和分析，避免影响下一次的判断
    用一段话描述但是不能缺少关键语句的详细信息
    返回格式为文本格式，不需要包含代码块，只需要包含文字描述即可。
    """

    trajectory_response = generate_response(trajectory_prompt, llm_model, temperature=0)
    return trajectory_response


def get_rust_function_conversion_prompt(child_funs_c, child_funs, child_context, before_details, source_context,pointer_functions):
    ask = f"""
        【输出与范围】
        1. 只返回 Rust 代码，不要解释，不要 Markdown，不要占位实现或省略号。
        2. 只转译并输出目标函数与最小必要 non-function 内容（必要 use/type/struct/enum/const/static），不要整模块重写。
        3. 保持函数名和语义与 C 一致；若 C 是全局函数，Rust 也必须保持全局函数，不要改成 impl 封装。

        【安全与类型（硬约束）】
        4. 使用纯 Rust 特性，禁止 `unsafe fn` 与 `unsafe {{}}`。
        5. 所有需要修改的变量必须用 mut 声明。
        6. 严禁使用 `c_void`、`void*`、`std::ffi`/`core::ffi`/`libc` 的 FFI 风格类型与别名。
                严禁在函数签名和函数体中出现 `*mut`、`*const` 裸指针，以及 `extern "C"` 风格接口。
                必须改写为安全 Rust 表达（引用/切片/Option/Result/Rc/RefCell/Vec/String 等）。
        7. 减少 Box<dyn Any> 的使用；存在共享或可变共享语义优先使用 Rc/RefCell/Weak（或并发场景 Arc/Mutex）/Box确保共享可变语义与所有权正确。
        8. 基本类型映射遵循：int/char/unsigned int/unsigned char/float/double -> i32/i8/u32/u8/f32/f64；
            char* 或字符串语义的 void* 优先映射为 String；其余“万能指针”语义的 void* 优先转换为泛型参数（如 T/Option<T>/Vec<T> 的安全表达）；忽略 typedef void* 的别名包装。
        9. 特别禁止生成 `type Xxx = *mut std::ffi::c_void` std::ffi::c_void`/`libc::c_void`/`void*` 或等价别名。
        10. 删除所有Test low memory scenario相关代码的逻辑，比如alloc_test_set_limit,alloc_test_get_allocated,alloc_test_malloc,alloc_test_free,alloc_test_overwrite,alloc_test_get_header,alloc_test_realloc等。

        【可见性与工程规范】
          10. 所有函数、结构体、枚举、全局变量、全局类型定义统一使用 pub；结构体字段也使用 pub。
          11. 允许使用 Rust 标准库，不允许使用第三方库。
          12. 对于可变全局状态，优先改为原子类型（如 AtomicUsize）并使用显式 Ordering。

        【一致性与可测试性】
          13. 确保逻辑与对应 C 函数一致，不要改变核心行为；不要使用 placeholder。
          14. 对需要 clone 的结构体/类型，补充 Clone 能力（derive 或等价实现）。
          15. 测试函数不能有非生命周期泛型参数，形如 `pub fn test_xxx() {{ ... }}`，并保持循环次数与断言数量语义一致。
    """
    

    return f"""
        将以下 C 代码转换为 Rust 代码，严格遵守规则并只返回代码。
        目标函数：{child_funs_c}
        规则：{ask}

        参考内容：
        1. 直接依赖函数：{child_funs}
        2. 直接依赖 Rust 上下文（按文件分块，已标注文件名）：
        {child_context}
        3. 相关 C 声明（结构体/全局变量/宏/枚举）：{before_details}

        待转换 C 源码（按文件分块，已标注文件名）：
        {source_context}
    """

def get_error_fixing_prompt(template, compile_error,before_details,pointer_functions,names_list):
    return f"""
        帮我修复以下 Rust 编译错误，只返回代码。
        约束：
        1. 只修改报错直接相关的函数体和必要的 non-function 内容；不要解释，不要使用 Markdown。
        2. 不要新增无关函数；若无 non-function 变更，就只返回修改后的函数。
        3. 优先复用现有定义或直接依赖导入；不要在当前模块臆造重复 struct/type/static/use。
        4. 保持原有功能与注释；重复定义直接删除新增重复项。
        5. 借用错误优先通过缩短 borrow 生命周期、引入局部中间值解决；类型/trait 错误优先做局部一致性修复。
                6. 不要新增任何 `unsafe fn` 或 `unsafe {{...}}`；若判断必须使用 unsafe 才能正确修复，请输出 `// handoff_to_swe: <根因摘要>`。
                7. 以下函数若作为函数指针使用，不允许改定义，只允许局部 xxx_wrap 适配：{pointer_functions}
                8. 若需要补类型声明，请遵守这些相关 C 声明，并将其转换为safe的Rust：{before_details}
                      9. 若涉及全局可变变量，优先改为 `AtomicUsize` 并使用原子读写；必要时补充
                  `use std::sync::atomic::{{AtomicUsize, Ordering}};`。
                      10. 所有权与共享可变场景优先采用 Rc/RefCell/Weak（并发场景可用 Arc/Mutex），
                  不要默认引入 Box。
                      11. Box 默认用于白名单场景：递归类型、明确单一拥有且不共享的堆数据、必须拥有所有权的 trait object；
                  非白名单若 Rc/RefCell 成本明显更高且语义仍为单一拥有，可保留 Box。
                  若涉及共享访问或共享可变，必须改为 Rc/RefCell/Weak。
                      12. 若报错涉及 `void*`/万能指针，优先改为泛型参数（T/Option<T>/Vec<T> 等安全表达），
                  不要回退到 `c_void`、FFI 别名或裸指针。

        待修代码与报错：{template+'//编译器错误信息：'+compile_error}
    """

def get_rust_function_conversion_prompt_english(child_funs_c, child_funs, child_context, before_details, source_context):
    ask = f"""
    1. Use native Rust features and forbid any `unsafe fn`/`unsafe {{ ... }}`.
    2. Declare mutable variables with the mut keyword, and declare all variables that need to be assigned as mut.
     3. Do not use FFI-style code: no `std::ffi/core::ffi/libc`, no `c_void`/`void*`, no raw pointers (`*mut`/`*const`), and no `extern "C"` APIs.
         Rewrite to safe Rust abstractions (references/slices/Option/Result/Rc/RefCell/Vec/String/generics) while preserving semantics.
         For wildcard `void*` semantics, prefer generic representations (e.g., T/Option<T>/Vec<T>) instead of FFI aliases or raw pointers.
         Prefer Rc/RefCell (or Arc/Mutex for concurrency) over Box.
         Prefer a whitelist-first policy for Box: recursive type layouts, clearly single-owner non-shared heap data, or owning trait objects.
         For non-whitelist cases, Box is still acceptable when Rc/RefCell would add clear complexity/runtime overhead and ownership remains single-owner.
         If sharing or shared mutability exists, switch to Rc/RefCell/Weak.
    4. Return the optimal result, without explanation.
    5. Do not use Markdown format for return, define function separately on a new line.
    7. Use the pub keyword for all members of a struct, and set all functions, structs, enums, global variables, and global type definitions to pub , add the pub keyword before all generated rust function definitions, do not include non-pub function definitions..
    8. Use some advanced Rust features.
    9. Avoid using Box<dyn Any>.
    10. Ensure the correctness of the implemented function's functionality, both logically and in terms of the corresponding C function. For test functions, ensure that the test cases are covered, and the test passes.
    11. Avoid simultaneous borrowing of a variable both as mutable and non-mutable, and ensure that all non-mutable borrowing operations are completed before any mutable borrowing operation.
    12. Do not remove low-memory test scenarios or alloc_test_* calls; if symbols are missing, prefer reusing dependency-module definitions/imports instead of guessing replacements in the current module.
    13. Use generic<T> or smart pointers as much as possible within struct data types.
        Prioritize Rc/RefCell/Weak patterns for shared mutable ownership, and avoid defaulting to Box outside whitelist-first scenarios.
    14. Test functions should not have non-lifetime generic parameters.
    15. For provided C declarations (typedef/struct/enum/union), keep definition fidelity:
        - Do not drop or invent fields.
        - Keep field names/count and fixed array lengths consistent with C declarations.
        - Rust type mapping is allowed only when semantics stay equivalent.
    16. For mutable global variables, prefer translating to thread-safe atomics:
        use `AtomicUsize` with explicit `Ordering` (`load/store/fetch_add` etc.), and include
        `use std::sync::atomic::{{AtomicUsize, Ordering}};` in non-function content when needed.
    """

    return f"""
            Convert the following C library functions to Rust library functions, with the following requirements:
             1. The Rust function definition must include {child_funs_c}, retaining the function name and interface, without providing test functions.
             2. For undefined structure, global variables, and macros, provide definitions. 
             3. {ask}
             Return Format: pub fn {child_funs_c}(args ...) ->(return type) {{... }}
             The following is a translation of the provided content into English:
             Reference:
                 1. Direct dependency functions: {child_funs}
                     Rust dependency context (file-split blocks with file names):
                     {child_context}
             2. All C global variables, structures, and macros: {before_details} Note:
             1. You can directly call the functions, structures, global variables, and macros used in the Rust child functions {child_funs} referenced in the conversion context, without providing their definitions.
             Given content:
                 1. C source content to convert (file-split blocks with file names):
                     {source_context}
    """

def get_error_fixing_prompt_english(template, compile_error):
    return f"""
        Prompt:
Help me fix a compilation error in the following rust code
Requirements:
1. Do not use Markdown format to return the code.
2. Redefined errors Delete the definitions that are reported
3. Directly return all the modified code without explanation
4. Do not change the function of the code that reports an error
5. Avoid Box<dyn Any>, avoid defaulting to Box, and instead use generics <T> with Rc/RefCell/Weak (or Arc/Mutex when needed) to ensure type safety and ownership correctness.
    For wildcard `void*` usage, prioritize generic forms (T/Option<T>/Vec<T>) over c_void/FFI aliases/raw pointers.
    Use a whitelist-first policy for Box (recursive layouts, clear single-owner non-shared heap data, owning trait objects),
    but allow Box in non-whitelist cases when Rc/RefCell would be clearly worse and ownership is still single-owner.
6. Ensure that the function code is correct
7. Implement the clone method for classes and structures that need clone
8. Avoid type mismatch errors. Make sure the type matches when you assign it, and prefer Rc<RefCell<T>> style adaptation for shared mutable ownership.
    Introduce Box<T> by whitelist-first policy; non-whitelist use is acceptable only with clear single-owner semantics and lower complexity.
9. Do not introduce any new unsafe fn/unsafe blocks; if a correct fix would require unsafe, return `// handoff_to_swe: <root cause summary>` instead of forcing a local unsafe patch.
Content to fix: {template+'// compiler error message: '+compile_error}
    """

def get_task_prompt(non_function_content, first_lines):
    return f"""
        任务 ： 
        1. 给定一个Rust的全局定义字符串：'{non_function_content}',
        2. 给定一个字典：{first_lines}
        3. 将该字符串按指定字典的 key 进行分割，并将分割后的内容分配放入字典的 extra 字段中。注意，只需分割并分配，不要复制多份插入，确保所有分割代码合并后与原全局定义字符串一致。
        4. 确保extra字段的值与同级的其他key的value相关,且extra字段只包含全局变量，结构体定义、宏等，不包含任何函数或表达式。
        5. extra字段的值类型为字符串。
        6. 返回处理后的JSON格式字符串，第二级的key只保留extra。
        7. 返回结果必须是JSON格式的数据，不要包含其他格式的数据。
        8. 不要对返回结果做任何解释。
        9. 返回格式为：{{"key1":{{"extra":"value1(来自给定Rust全局定义的一部分，且与字典的同级其他value相关)"}}, "key2":{{"extra":"value2(给定Rust全局定义的一部分,且与字典的同级其他value相关)"}}...}}， value1与value2来自于给定的rust全局定义字符串。
    """

def get_json_fixing_prompt(task_prompt,response, compile_error2):
    return f"""
        {task_prompt}
        上一次返回的extra代码分割的内容有编译错误，请修复以下json字符串中的extra分割错误并返回正确的json格式，删除rust代码中无关的中文符号：
        {response}。
        编译时出现以下错误，请重新插入extra，不要添加除了给定rust全局定义之外的其他代码，不要对返回结果做任何解释：
        {compile_error2}
    """

def get_json_parsing_fix_prompt(task_prompt,response, error_msg, error_position, error_content):
    return f"""
        {task_prompt}
        上一次返回的json格式有错误，无法被解析，请修复以下json字符串中的错误并返回正确的json格式：
        {response},返回处理好之后的json格式原字符串，不要对返回结果做任何解释，json解析报错内容：{error_msg}，报错位置：{error_position}，报错内容：{error_content}
    """


def generate_extra_prompt(first_lines, source, child_source, all_child_func_list):
    return f"""
{first_lines}
我有一个results.json，第一维的key是文件名，第二维的key是函数名，‘extra’的第二维key是文件内的全局非函数定义。
文件调用关系是{source}调用了{child_source}。
请补充{source}的extra部分，{source}用到的子函数有：{all_child_func_list}，使用use的外部导入方式use test_project::{child_source}.replace('-', '_')::{{用到的函数：{all_child_func_list}；其他用到的函数，其他用到的结构体，全局变量，宏定义}}。
导入{source}需要的所有元素，包括函数和全局定义，{source}文件不需要额外实现任何定义，只需要从外部导入。
返回格式为{source}的所有非函数部分代码，不要返回任何其他的代码，不要对结果做任何解释。extra字段的值是导入模块语句，全局变量，结构体定义、宏等，不包含任何如函数函数声明或定义。
"""

def generate_extra_prompt_fix(first_lines, source, child_source, all_child_func_list, test_error):
    filtered_first_lines = {}
    for file_key, functions_dict in first_lines.items():
        filtered_functions = {'extra': functions_dict.get('extra', '')}
        
        for func_name, func_def in functions_dict.items():
            if func_name == 'extra':
                continue
            # 直接判断函数名是否在错误信息中出现
            if func_name in test_error:
                filtered_functions[func_name] = func_def
        
        # 只有当有相关函数时才保留这个文件
        if len(filtered_functions) > 1 or filtered_functions.get('extra', '').strip():
            filtered_first_lines[file_key] = filtered_functions

    return f"""
{filtered_first_lines}
我有一个results.json，第一维的key是文件名，第二维的key是函数名，‘extra’的第二维key是文件内的全局非函数定义。
文件调用关系是{source}调用了{child_source}。
请补充{source}的extra部分，{source}用到的子函数有：{all_child_func_list}，使用use的外部导入方式use test_project::{child_source}.replace('-', '_')::{{用到的函数：{all_child_func_list}；其他用到的函数，其他用到的结构体，全局变量，宏定义}}。
导入{source}需要的所有元素，包括函数和全局定义，{source}文件不需要额外实现任何定义，只需要从外部导入。
返回格式为{source}的所有非函数部分代码，不要返回任何其他的代码，不要对结果做任何解释。extra字段的值是导入模块语句，全局变量，结构体定义、宏等，不包含任何如函数函数声明或定义。
"""

def fix_extra_prompt(prompt, response, source, child_source, test_error):
    return f"""
我的任务是：
{prompt}
上一次返回的结果：
{response}
上一次返回的结果存在以下问题：
{test_error}
请修复{source}的extra字段中的元素导入错误，包括导入{source}用到的模块，缺少导入的函数，结构体，全局变量，删除unresolved import；修复{child_source}的extra字段中的作用域问题，确保所有的元素都能被导入，不要改变extra全局定义中除了模块导入和调整作用域之外的任何代码。
如果文件中有私有的全局定义、结构体、宏的所有定义及所有子元素定义，都声明为pub，允许外部任意访问，并在json中返回。只允许改变里面的value，不要做任何解释。不要改变模块导入的路径。如果有代码重复定义的错误，删除{source}的extra中的定义。
返回格式为：file1:{{"extra":"value"}},file2:{{"extra":"value"}}，改正后的结果放入{source}的extra字段。
请确保返回的数据是有效的 JSON 格式，不修改原json的任何key如{child_source}，返回修改后完整的所有文件的extra字段。
extra字段不要出现任何函数如fn func(){{...}}，我的子文件中的所有函数已经存在完整的定义，不要帮我定义任何函数。
返回格式示例，请严格按照该格式返回：
{{
    "{source}": {{"extra": "导入模块语句，原有的extra，注意：不包含任何函数定义或表达式，如果出现redefine的报错，删除这个字段中出现的函数定义"}},
    "file1": {{"extra": "导入模块语句，声明为pub的全局变量，结构体定义、宏等，注意：不包含任何函数定义或表达式，实现trait时不需要pub,如果出现redefine的报错，删除这个字段中出现的函数定义" }}
}}
{source}的extra不要出现其他文件file1中相同的任何定义，确保所有的定义都是唯一的，不要出现重复定义，只修改作用域与导入模块，不定义任何函数，结构体，全局变量。
如果extra出现错误的特殊字符如中文符号，请删除这些特殊字符。
"""
