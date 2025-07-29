
pub fn string_nocase_compare(string1: &str, string2: &str) -> i32 {
    let mut p1 = string1.chars();
    let mut p2 = string2.chars();

    loop {
        let c1 = p1.next().map(|c| c.to_ascii_lowercase());
        let c2 = p2.next().map(|c| c.to_ascii_lowercase());

        match (c1, c2) {
            (Some(c1), Some(c2)) => {
                if c1 != c2 {
                    return if c1 < c2 { -1 } else { 1 };
                }
            }
            (Some(_), None) => return 1,
            (None, Some(_)) => return -1,
            (None, None) => return 0,
        }
    }
}

pub fn string_compare(string1: &str, string2: &str) -> i32 {
    let result = string1.cmp(string2);

    match result {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Greater => 1,
        std::cmp::Ordering::Equal => 0,
    }
}

pub fn string_nocase_equal(string1: &str, string2: &str) -> bool {
    string_nocase_compare(string1, string2) == 0
}

pub fn string_equal<T: AsRef<str>>(string1: T, string2: T) -> bool {
    string1.as_ref() == string2.as_ref()
}

