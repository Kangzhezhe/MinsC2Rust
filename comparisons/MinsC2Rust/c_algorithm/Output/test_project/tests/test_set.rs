use test_project::set::{
    set_allocate_table, set_enlarge, set_free, set_free_entry, set_insert, set_intersection,
    set_iter_has_more, set_iter_next, set_iterate, set_new, set_num_entries, set_query,
    set_register_free_function, set_remove, set_to_array, set_union, Set, SetEntry, SetIterator,
    SetValue,
};

pub const SET_NUM_PRIMES: usize = 24;
pub const SET_PRIMES: [usize; 24] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317, 196613, 393241, 786433, 1572869,
    3145739, 6291469, 12582917, 25165843, 50331653, 100663319, 201326611, 402653189, 805306457,
    1610612741,
];

pub static mut ALLOCATED_VALUES: usize = 0;
pub fn generate_set() -> Option<Set<String>> {
    fn string_hash(s: &String) -> u32 {
        s.len() as u32
    }

    fn string_equal(s1: &String, s2: &String) -> bool {
        s1 == s2
    }

    let mut set = set_new(string_hash, string_equal)?;

    for i in 0..10000 {
        let value = i.to_string();
        set_insert(&mut set, value.clone());

        assert_eq!(set_num_entries(&set), i + 1);
    }

    set_register_free_function(
        &mut set,
        Some(|value| {
            // No need to explicitly free the value as Rust's ownership system handles it
        }),
    );

    Some(set)
}

pub fn new_value<T: Clone>(value: T) -> Box<SetValue<T>> {
    let result = Box::new(SetValue {
        value: value.clone(),
    });
    unsafe {
        ALLOCATED_VALUES += 1;
    }
    result
}

#[test]
pub fn test_set_query() {
    let mut set = generate_set().expect("Failed to generate set");

    // Test all values
    for i in 0..10000 {
        let buf = i.to_string();
        assert!(set_query(&set, buf.clone()));
    }

    // Test invalid values returning false
    assert!(!set_query(&set, "-1".to_string()));
    assert!(!set_query(&set, "100001".to_string()));

    set_free(Box::new(set));
}

#[test]
pub fn test_set_iterating() {
    let mut set = generate_set().expect("Failed to generate set");

    let mut count = 0;
    let mut iterator = SetIterator {
        set: &set,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&mut iterator);

    while set_iter_has_more(&iterator) {
        set_iter_next(&mut iterator);
        count += 1;
    }

    assert!(set_iter_next(&mut iterator).is_none());
    assert_eq!(count, 10000);

    set_free(Box::new(set));

    let mut empty_set = set_new(int_hash, int_equal).expect("Failed to create empty set");
    let mut empty_iterator = SetIterator {
        set: &empty_set,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&mut empty_iterator);
    assert!(!set_iter_has_more(&empty_iterator));

    set_free(Box::new(empty_set));
}

#[test]
pub fn test_set_out_of_memory() {
    let mut set = set_new(int_hash, int_equal).unwrap();
    let mut values = [0; 66];

    // Test normal failure
    values[0] = 0;
    assert!(!set_insert(&mut set, values[0]));
    assert_eq!(set_num_entries(&set), 0);

    // Test failure when increasing table size.
    // The initial table size is 193 entries. The table increases in
    // size when 1/3 full, so the 66th entry should cause the insert
    // to fail.
    for i in 0..65 {
        values[i] = i as i32;
        assert!(set_insert(&mut set, values[i]));
        assert_eq!(set_num_entries(&set), i + 1);
    }

    assert_eq!(set_num_entries(&set), 65);

    // Test the 66th insert
    values[65] = 65;
    assert!(!set_insert(&mut set, values[65]));
    assert_eq!(set_num_entries(&set), 65);

    set_free(Box::new(set));
}

#[test]
pub fn test_set_union() {
    let numbers1 = vec![1, 2, 3, 4, 5, 6, 7];
    let numbers2 = vec![5, 6, 7, 8, 9, 10, 11];
    let result = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];

    let mut set1 = set_new(int_hash, int_equal).unwrap();
    for num in &numbers1 {
        set_insert(&mut set1, *num);
    }

    let mut set2 = set_new(int_hash, int_equal).unwrap();
    for num in &numbers2 {
        set_insert(&mut set2, *num);
    }

    let result_set = set_union(&set1, &set2).unwrap();

    assert_eq!(set_num_entries(&result_set), 11);

    for num in &result {
        assert!(set_query(&result_set, *num));
    }

    set_free(Box::new(result_set));

    set_free(Box::new(set1));
    set_free(Box::new(set2));
}

#[test]
pub fn test_set_remove() {
    let mut set = generate_set().expect("Failed to generate set");

    let mut num_entries = set_num_entries(&set);
    assert_eq!(num_entries, 10000);

    for i in 4000..6000 {
        let buf = i.to_string();

        assert!(set_query(&set, buf.clone()));

        assert!(set_remove(&mut set, buf.clone()));

        assert_eq!(set_num_entries(&set), num_entries - 1);

        assert!(!set_query(&set, buf.clone()));

        num_entries -= 1;
    }

    for i in -1000..-500 {
        let buf = i.to_string();

        assert!(!set_remove(&mut set, buf.clone()));
        assert_eq!(set_num_entries(&set), num_entries);
    }

    for i in 50000..51000 {
        let buf = i.to_string();

        assert!(!set_remove(&mut set, buf.clone()));
        assert_eq!(set_num_entries(&set), num_entries);
    }

    set_free(Box::new(set));
}

#[test]
pub fn test_set_free_function() {
    let mut set = set_new(int_hash, int_equal).unwrap();
    set_register_free_function(&mut set, Some(free));

    unsafe {
        ALLOCATED_VALUES = 0;
    }

    for i in 0..1000 {
        let value = new_value(i);
        set_insert(&mut set, value.value);
    }

    unsafe {
        assert_eq!(ALLOCATED_VALUES, 1000);
    }

    let i = 500;
    set_remove(&mut set, i);

    unsafe {
        assert_eq!(ALLOCATED_VALUES, 999);
    }

    set_free(Box::new(set));

    unsafe {
        assert_eq!(ALLOCATED_VALUES, 0);
    }
}

pub fn free_value(value: Box<SetValue<i32>>) {
    unsafe {
        ALLOCATED_VALUES -= 1;
    }
}

#[test]
pub fn test_set_new_free() {
    let mut set = set_new(int_hash, int_equal).unwrap();

    set_register_free_function(&mut set, Some(free));

    for i in 0..10000 {
        set_insert(&mut set, i);
    }

    set_free(Box::new(set));
}

#[test]
pub fn test_set_intersection() {
    let numbers1 = vec![1, 2, 3, 4, 5, 6, 7];
    let numbers2 = vec![5, 6, 7, 8, 9, 10, 11];
    let result = vec![5, 6, 7];

    let mut set1 = set_new(int_hash, int_equal).unwrap();
    for num in &numbers1 {
        set_insert(&mut set1, *num);
    }

    let mut set2 = set_new(int_hash, int_equal).unwrap();
    for num in &numbers2 {
        set_insert(&mut set2, *num);
    }

    let result_set = set_intersection(&set1, &set2).unwrap();

    assert_eq!(set_num_entries(&result_set), 3);

    for num in &result {
        assert!(set_query(&result_set, *num));
    }

    set_free(Box::new(set1));
    set_free(Box::new(set2));
    set_free(Box::new(result_set));
}

#[test]
pub fn test_set_to_array() {
    let mut set = set_new(pointer_hash, pointer_equal).unwrap();
    let values = vec![1; 100];

    for i in 0..100 {
        set_insert(&mut set, &values[i]);
    }

    let array = set_to_array(&set);

    for i in 0..100 {
        assert_eq!(*array[i], 1);
    }

    set_free(Box::new(set));
}

pub fn string_hash(s: &String) -> u32 {
    s.bytes()
        .fold(0, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u32))
}

pub fn string_equal(s1: &String, s2: &String) -> bool {
    s1 == s2
}

pub fn int_hash(value: &i32) -> u32 {
    *value as u32
}

pub fn int_equal(value1: &i32, value2: &i32) -> bool {
    value1 == value2
}

pub fn free<T>(_value: Box<SetValue<T>>) {
    unsafe {
        ALLOCATED_VALUES -= 1;
    }
}

pub fn pointer_hash<T>(value: &T) -> u32 {
    // Placeholder for pointer hash function
    // In Rust, we typically don't use raw pointers, so this would need to be adapted
    // to the specific use case.
    0
}

pub fn pointer_equal<T: PartialEq>(value1: &T, value2: &T) -> bool {
    value1 == value2
}
