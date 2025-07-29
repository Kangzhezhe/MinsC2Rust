// 测试函数

// 测试函数

// 测试函数
pub fn int_hash<T: Clone + Into<u64>>(vlocation: &T) -> u32 {
    let location = vlocation.clone();
    location.into() as u32
}
