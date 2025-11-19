// 测试函数

// 测试函数

// 测试函数
pub fn string_nocase_hash(string: &str) -> u32 {
    let mut result: u32 = 5381;
    let mut p = string.chars();

    while let Some(c) = p.next() {
        result = (result << 5) + result + c.to_ascii_lowercase() as u32;
    }

    result
}
