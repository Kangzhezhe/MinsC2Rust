def get_rust_function_conversion_prompt(child_funs_c, child_funs, child_context, before_details, source_context):
    ask = """
        1. 使用纯Rust特性，不使用unsafe代码。
        2. 用mut关键字声明可变变量，对于需要赋值的变量全部声明为mut
        3. 不使用任何 `c_void、*mut`指针，使用Rust的特性如泛型<T>，智能指针替代，确保内存安全和所有权管理
        4. 返回最优结果，不做解释。
        5. 不使用Markdown格式返回，函数定义单独另起一行。
        7. 结构体所有成员使用pub关键字，将所有函数，结构体，枚举，全局变量，全局类型定义设置成pub
        8. 可以用一些rust的高级特性 
        9. 避免使用 Box<dyn Any>
        10. 对于需要clone的类，结构体，实现clone方法
        11. 确保实现的函数功能的正确性，逻辑上与对应的c函数一致，对于测试函数，确保测试用例覆盖的情况下，测试通过
        12. 把测试用例中测试低内存场景的代码全部去掉，比如：Test low memory scenarios (failed malloc)，去掉所有相关的代码，去掉alloc_test_set_limit定义及相关函数 
        13. 结构体内部数据类型尽量用泛型<T>或智能指针，避免使用具体类型
        14. 测试函数不能有非生命周期的泛型参数，测试函数的格式为：pub fn test_name() { ... }
    """
    

    return f"""
        将以下C语言库函数转换为Rust库函数，要求如下：
        1. 返回值必须包含{child_funs_c}的Rust函数定义，保留函数命名与接口，不需要给出测试函数，不要使用面向对象封装函数。
        2. 对于未定义的结构体、全局变量、宏，需要给出定义。
        3. {ask}
        返回格式：
        pub fn {child_funs_c}(args ...) ->(return type) {{...}}
        参考内容：
        1. 已经转换的Rust子函数{child_funs}的定义：{child_context}
        2. 所有c语言全局变量、结构体、宏：{before_details}
        注意：
        1. 从参考内容Rust子函数{child_funs}里用到的结构体、全局变量、宏可直接调用，不给出定义。
        给定内容：
        1. 待转换的函数源代码内容：{source_context}
    """

def get_error_fixing_prompt(template, compile_error):
    return f"""
        Prompt:
        帮我修改以下rust代码中出现的编译错误
        要求：
        1. 请不使用Markdown格式返回代码。
        2. 重复定义的错误直接删除报错的定义
        3. 直接返回所有修改后的代码，不要解释
        4. 不要改变报错的代码的功能
        5. 避免使用 Box<dyn Any>，而是使用泛型<T>和特征约束来确保类型安全和性能
        6. 请确保功能代码的正确性
        待改错内容：{template+'//编译器错误信息：'+compile_error}
    """

def get_rust_function_conversion_prompt_english(child_funs_c, child_funs, child_context, before_details, source_context):
    
    ask = f"""
    1. Use pure Rust features, no unsafe code.
    2. Declare mutable variables with the mut keyword, and declare all variables that need to be assigned as mut.
    3. Do not use any `std::ffi::c_void, *mut` pointers, use Rust features such as generic<T>, smart pointers instead, to ensure memory safety and ownership management.
    4. Return the optimal result, without explanation.
    5. Do not use Markdown format for return, define function separately on a new line.
    7. Use the pub keyword for all members of a struct, and set all functions, structs, enums, global variables, and global type definitions to pub.
    8. Use some advanced Rust features.
    9. Avoid using Box<dyn Any>.
    10. Ensure the correctness of the implemented function's functionality, both logically and in terms of the corresponding C function. For test functions, ensure that the test cases are covered, and the test passes.
    11. Avoid simultaneous borrowing of a variable both as mutable and non-mutable, and ensure that all non-mutable borrowing operations are completed before any mutable borrowing operation.
    12. Remove all code for testing low memory scenarios (failed malloc) from the test cases, such as Test low memory scenarios (failed malloc), remove all related code, and the definition and related functions of alloc_test_set_limit.
    13. Use generic<T> or smart pointers as much as possible within struct data types, and avoid using specific types.
    14. Test functions should not have non-lifetime generic parameters.
    """

    return f"""
            Convert the following C library functions to Rust library functions, with the following requirements:
             1. The Rust function definition must include {child_funs_c}, retaining the function name and interface, without providing test functions.
             2. For undefined structure, global variables, and macros, provide definitions. 
             3. {ask}
             Return Format: pub fn {child_funs_c}(args ...) ->(return type) {{... }}
             The following is a translation of the provided content into English:
             Reference:
             1. Definition of Rust child functions that have been converted: {child_funs} {child_context}
             2. All C global variables, structures, and macros: {before_details} Note:
             1. You can directly call the functions, structures, global variables, and macros used in the Rust child functions {child_funs} referenced in the conversion context, without providing their definitions.
             Given content:
             1. The source code content of the function to be converted:{source_context}
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
5. Avoid Box<dyn Any> and instead use generics <T> and feature constraints to ensure type safety and performance
6. Ensure that the function code is correct
7. Implement the clone method for classes and structures that need clone
8. Avoid type mismatch errors. Make sure the type matches when you assign it, for example by providing Box<T> where the Box<T> type is needed, rather than providing T directly.
Content to fix: {template+'// compiler error message: '+compile_error}
    """

def get_task_prompt(non_function_content, first_lines):
    return f"""
        任务 ： 
        1. 给定一个Rust的全局定义字符串：'{non_function_content}',
        2. 给定一个字典：{first_lines}
        3. 将该字符串按指定字典的key进行分割。
        4. 将分割后的内容放入字典的extra字段中。
        5. 确保extra字段的值与同级的其他key的value相关,且extra字段只包含全局变量，结构体定义、宏等，不包含任何函数或表达式。
        6. extra字段的值类型为字符串。
        7. 返回处理后的JSON格式字符串，第二级的key只保留extra。
        8. 返回结果必须是JSON格式的数据，不要包含其他格式的数据。
        9. 不要对返回结果做任何解释。
        10. 返回格式为：{{"key1":{{"extra":"value1(来自给定Rust全局定义的一部分，且与字典的同级其他value相关)"}}, "key2":{{"extra":"value2(给定Rust全局定义的一部分,且与字典的同级其他value相关)"}}...}}， value1与value2来自于给定的rust全局定义字符串。
    """

def get_json_fixing_prompt(task_prompt,response, compile_error2):
    return f"""
        {task_prompt}
        上一次返回的extra代码分割的内容有编译错误，请修复以下json字符串中的extra分割错误并返回正确的json格式：
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
返回格式为{source}的所有非函数部分代码，不要返回任何其他的代码，不要对结果做任何解释。extra字段的值是导入模块语句，全局变量，结构体定义、宏等，不包含任何如fn func(){{...}}的任何函数或表达式或函数声明。
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
    "{source}": {{"extra": "导入模块语句，原有的extra，注意：不包含任何函数定义或表达式，如果出现redefine的报错，删除这个字段中出现的定义"}},
    "file1": {{"extra": "导入模块语句，声明为pub的全局变量，结构体定义、宏等，注意：不包含任何函数定义或表达式，实现trait时不需要pub" }}
}}
{source}的extra不要出现其他文件file1中相同的任何定义，确保所有的定义都是唯一的，不要出现重复定义，只修改作用域与导入模块，不定义任何函数，结构体，全局变量。
"""