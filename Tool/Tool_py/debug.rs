#!/usr/bin/env rust-script
//! ```cargo
//! [dependencies]
//! verify_project = { path = "." }
//! ```
// 调试 alloc_test_strdup 函数
use std::sync::atomic::{AtomicI32, AtomicUsize, Ordering};
use std::collections::HashMap;
use std::sync::Mutex;

pub static allocation_limit: AtomicI32 = AtomicI32::new(-1);
pub static allocated_bytes: AtomicUsize = AtomicUsize::new(0);

lazy_static::lazy_static! {
    static ref ALLOC_MAP: Mutex<HashMap<usize, usize>> = Mutex::new(HashMap::new());
}

pub fn alloc_test_set_limit(alloc_count: i32) {
    allocation_limit.store(alloc_count, Ordering::Relaxed);
}

pub fn alloc_test_get_allocated() -> usize {
    allocated_bytes.load(Ordering::SeqCst)
}

pub fn alloc_test_overwrite(ptr: *mut u8, len: usize, value: u32) {
    for i in 0..len {
        unsafe {
            *ptr.add(i) = (value & 0xFF) as u8;
        }
    }
}

pub fn alloc_test_malloc(bytes: usize) -> Option<*mut u8> {
    if allocation_limit.load(Ordering::SeqCst) == 0 {
        return None;
    }
    
    if bytes == 0 {
        return Some(std::ptr::null_mut());
    }
    
    // 使用 std::alloc::alloc 分配内存
    let layout = std::alloc::Layout::from_size_align(bytes, std::mem::align_of::<u8>()).unwrap();
    let ptr = unsafe { std::alloc::alloc(layout) };
    
    if ptr.is_null() {
        return None;
    }
    
    // 填充数据
    alloc_test_overwrite(ptr, bytes, 0xBAADF00D);
    
    // 增加计数
    allocated_bytes.fetch_add(bytes, Ordering::SeqCst);
    
    // 减少限制
    let current_limit = allocation_limit.load(Ordering::SeqCst);
    if current_limit > 0 {
        allocation_limit.store(current_limit - 1, Ordering::SeqCst);
    }
    
    // 记录到全局 map
    let mut map = ALLOC_MAP.lock().unwrap();
    map.insert(ptr as usize, bytes);
    
    Some(ptr)
}

pub fn alloc_test_free(ptr: *mut u8) {
    if ptr.is_null() {
        return;
    }
    
    let data_ptr = ptr as usize;
    
    // 从全局 map 中查找该指针对应的分配大小
    let mut map = ALLOC_MAP.lock().unwrap();
    if let Some(&block_size) = map.get(&data_ptr) {
        let current_bytes = allocated_bytes.load(Ordering::SeqCst);
        assert!(current_bytes >= block_size, "allocated_bytes >= block_size");
        
        // 覆盖内存为垃圾值
        alloc_test_overwrite(ptr, block_size, 0xDEADBEEF);
        
        // 减少计数
        allocated_bytes.fetch_sub(block_size, Ordering::SeqCst);
        
        // 从 map 中移除
        map.remove(&data_ptr);
        
        // 使用 std::alloc::dealloc 释放内存
        let layout = std::alloc::Layout::from_size_align(block_size, std::mem::align_of::<u8>()).unwrap();
        unsafe {
            std::alloc::dealloc(ptr, layout);
        }
    }
}

pub fn alloc_test_strdup(string: &str) -> Option<String> {
    let bytes = string.as_bytes();
    println!("Input string: {:?}", string);
    println!("Bytes len: {}", bytes.len());
    
    let result = alloc_test_malloc(bytes.len() + 1);
    println!("Malloc result: {:?}", result);
    
    match result {
        Some(ptr) => {
            unsafe {
                std::ptr::copy_nonoverlapping(bytes.as_ptr(), ptr, bytes.len());
                *ptr.add(bytes.len()) = 0;
                // 问题在这里：String::from_raw_parts 需要 ptr 指向有效的 UTF-8
                // 但 ptr 是 *mut u8，而 String::from_raw_parts 期望的是 *mut u8
                // 问题在于 capacity 和 length 的使用
                let s = String::from_raw_parts(ptr, bytes.len(), bytes.len() + 1);
                println!("Created string: {:?}", s);
                Some(s)
            }
        },
        None => None
    }
}

fn main() {
    // 测试 strdup
    let str = alloc_test_strdup("hello world");
    println!("Result: {:?}", str);
    println!("Is some: {}", str.is_some());
    
    if let Some(s) = str {
        println!("String content: {:?}", s);
        println!("String == 'hello world': {}", s == "hello world");
    }
}
