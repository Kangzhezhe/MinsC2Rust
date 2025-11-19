
pub fn pointer_equal<T>(location1: &T, location2: &T) -> bool {
    std::ptr::eq(location1, location2)
}

pub fn pointer_compare<T>(location1: &T, location2: &T) -> i32 {
    if location1 as *const _ < location2 as *const _ {
        -1
    } else if location1 as *const _ > location2 as *const _ {
        1
    } else {
        0
    }
}

