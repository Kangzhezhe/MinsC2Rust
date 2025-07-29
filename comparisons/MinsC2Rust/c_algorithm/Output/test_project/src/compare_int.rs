
pub fn int_compare<T: PartialOrd>(location1: &T, location2: &T) -> i32 {
    if location1 < location2 {
        -1
    } else if location1 > location2 {
        1
    } else {
        0
    }
}

pub fn int_equal<T: PartialEq>(vlocation1: &T, vlocation2: &T) -> bool {
    vlocation1 == vlocation2
}

