use test_project::hash_table::{
    hash_table_allocate_table, hash_table_enlarge, hash_table_free, hash_table_free_entry,
    hash_table_insert, hash_table_iter_has_more, hash_table_iter_next, hash_table_iterate,
    hash_table_lookup, hash_table_new, hash_table_num_entries, hash_table_register_free_functions,
    hash_table_remove, HashTable, HashTableEntry, HashTableIterator, HashTablePair,
    HASH_TABLE_NUM_PRIMES, HASH_TABLE_PRIMES,
};

pub static mut allocated_values: i32 = 0;

pub static mut allocated_keys: i32 = 0;
pub fn new_value(value: i32) -> Box<i32> {
    let mut result = Box::new(value);
    unsafe {
        allocated_values += 1;
    }
    result
}

pub fn new_key(value: i32) -> Box<i32> {
    let mut result = Box::new(value);
    unsafe {
        allocated_keys += 1;
    }
    result
}

pub fn generate_hash_table() -> Option<HashTable<String, String>> {
    let mut hash_table = hash_table_new(string_hash, string_equal)?;

    for i in 0..10000 {
        let key = i.to_string();
        let value = key.clone();

        hash_table_insert(&mut hash_table, key, value);
    }

    hash_table_register_free_functions(
        &mut hash_table,
        None,
        Some(|v: String| {
            drop(v);
        }),
    );

    Some(hash_table)
}

#[test]
pub fn test_hash_table_new_free() {
    let value1 = 1;
    let value2 = 2;
    let value3 = 3;
    let value4 = 4;

    let mut hash_table = hash_table_new(int_hash, int_equal);

    assert!(hash_table.is_some());

    let mut hash_table = hash_table.unwrap();

    assert!(hash_table_insert(&mut hash_table, value1, value1));
    assert!(hash_table_insert(&mut hash_table, value2, value2));
    assert!(hash_table_insert(&mut hash_table, value3, value3));
    assert!(hash_table_insert(&mut hash_table, value4, value4));

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_insert_lookup() {
    let mut hash_table = generate_hash_table().expect("Failed to generate hash table");

    assert_eq!(hash_table_num_entries(&hash_table), 10000);

    for i in 0..10000 {
        let key = i.to_string();
        let value = hash_table_lookup(&hash_table, key.clone()).expect("Value not found");

        assert_eq!(value, key);
    }

    let invalid_key1 = (-1).to_string();
    assert!(hash_table_lookup(&hash_table, invalid_key1).is_none());

    let invalid_key2 = 10000.to_string();
    assert!(hash_table_lookup(&hash_table, invalid_key2).is_none());

    let key = 12345.to_string();
    hash_table_insert(&mut hash_table, key.clone(), "hello world".to_string());
    let value = hash_table_lookup(&hash_table, key).expect("Value not found");

    assert_eq!(value, "hello world");

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_iterating() {
    let mut hash_table = generate_hash_table().unwrap();
    let mut iterator = HashTableIterator {
        hash_table: Box::new(hash_table.clone()),
        next_entry: None,
        next_chain: 0,
    };

    let mut count = 0;

    hash_table_iterate(Box::new(hash_table.clone()), &mut iterator);

    while hash_table_iter_has_more(&iterator) {
        hash_table_iter_next(&mut iterator);
        count += 1;
    }

    assert_eq!(count, 10000);

    let pair = hash_table_iter_next(&mut iterator);
    assert!(pair.is_none());

    hash_table_free(hash_table);

    let mut empty_hash_table: HashTable<i32, i32> = hash_table_new(int_hash, int_equal).unwrap();
    let mut empty_iterator = HashTableIterator {
        hash_table: Box::new(empty_hash_table.clone()),
        next_entry: None,
        next_chain: 0,
    };

    hash_table_iterate(Box::new(empty_hash_table.clone()), &mut empty_iterator);

    assert!(!hash_table_iter_has_more(&empty_iterator));

    hash_table_free(empty_hash_table);
}

#[test]
pub fn test_hash_table_remove() {
    let mut hash_table = generate_hash_table().unwrap();
    let mut buf = String::new();

    assert_eq!(hash_table_num_entries(&hash_table), 10000);
    buf = 5000.to_string();
    assert!(hash_table_lookup(&hash_table, buf.clone()).is_some());

    // Remove an entry
    hash_table_remove(&mut hash_table, buf.clone());

    // Check entry counter
    assert_eq!(hash_table_num_entries(&hash_table), 9999);

    // Check that None is returned now
    assert!(hash_table_lookup(&hash_table, buf.clone()).is_none());

    // Try removing a non-existent entry
    buf = (-1).to_string();
    hash_table_remove(&mut hash_table, buf.clone());

    assert_eq!(hash_table_num_entries(&hash_table), 9999);

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_iterating_remove() {
    let mut hash_table = generate_hash_table().expect("Failed to generate hash table");

    let mut iterator = HashTableIterator {
        hash_table: Box::new(hash_table.clone()),
        next_entry: None,
        next_chain: 0,
    };

    let mut count = 0;
    let mut removed = 0;

    hash_table_iterate(Box::new(hash_table.clone()), &mut iterator);

    while hash_table_iter_has_more(&iterator) {
        let pair = hash_table_iter_next(&mut iterator).expect("Failed to get next pair");
        let val = pair.value;

        if val.parse::<i32>().unwrap() % 100 == 0 {
            hash_table_remove(&mut hash_table, val.clone());
            removed += 1;
        }

        count += 1;
    }

    assert_eq!(removed, 100);
    assert_eq!(count, 10000);

    assert_eq!(hash_table_num_entries(&hash_table), 10000 - removed);

    for i in 0..10000 {
        let buf = i.to_string();

        if i % 100 == 0 {
            assert!(hash_table_lookup(&hash_table, buf.clone()).is_none());
        } else {
            assert!(hash_table_lookup(&hash_table, buf.clone()).is_some());
        }
    }

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_iterator_key_pair() {
    let mut hash_table = hash_table_new(int_hash, int_equal).unwrap();
    let mut iterator = HashTableIterator {
        hash_table: Box::new(hash_table.clone()),
        next_entry: None,
        next_chain: 0,
    };

    let value1 = 1;
    let value2 = 2;

    hash_table_insert(&mut hash_table, value1, value1);
    hash_table_insert(&mut hash_table, value2, value2);

    hash_table_iterate(Box::new(hash_table.clone()), &mut iterator);

    while hash_table_iter_has_more(&iterator) {
        let pair = hash_table_iter_next(&mut iterator).unwrap();
        let key = pair.key;
        let val = pair.value;

        assert_eq!(key, val);
    }

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_out_of_memory() {
    let mut hash_table = hash_table_new(int_hash, int_equal).unwrap();
    let mut values = [0; 66];

    // Test normal failure
    values[0] = 0;
    assert!(!hash_table_insert(&mut hash_table, values[0], values[0]));
    assert_eq!(hash_table_num_entries(&hash_table), 0);

    // Test failure when increasing table size.
    // The initial table size is 193 entries. The table increases in
    // size when 1/3 full, so the 66th entry should cause the insert
    // to fail.
    for i in 0..65 {
        values[i] = i as i32;
        assert!(hash_table_insert(&mut hash_table, values[i], values[i]));
        assert_eq!(hash_table_num_entries(&hash_table), i + 1);
    }

    assert_eq!(hash_table_num_entries(&hash_table), 65);

    // Test the 66th insert
    values[65] = 65;
    assert!(!hash_table_insert(&mut hash_table, values[65], values[65]));
    assert_eq!(hash_table_num_entries(&hash_table), 65);

    hash_table_free(hash_table);
}

pub fn string_hash(key: &String) -> u32 {
    key.len() as u32
}

pub fn string_equal(key1: &String, key2: &String) -> bool {
    key1 == key2
}

pub fn int_hash(key: &i32) -> u32 {
    *key as u32
}

pub fn int_equal(key1: &i32, key2: &i32) -> bool {
    key1 == key2
}
