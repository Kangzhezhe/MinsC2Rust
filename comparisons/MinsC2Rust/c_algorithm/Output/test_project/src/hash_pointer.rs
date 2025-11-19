// 测试函数

// 测试函数

// 测试函数
pub fn pointer_hash<T>(location: &T) -> u32 {
    let ptr = location as *const T as usize;
    ptr as u32
}
