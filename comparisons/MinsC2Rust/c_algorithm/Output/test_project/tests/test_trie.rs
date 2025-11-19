use test_project::trie::{
    trie_find_end, trie_find_end_binary, trie_free, trie_free_list_pop, trie_free_list_push,
    trie_insert, trie_insert_binary, trie_insert_rollback, trie_lookup, trie_lookup_binary,
    trie_new, trie_num_entries, trie_remove, trie_remove_binary, Trie,
};

pub const NUM_TEST_VALUES: usize = 10000;
pub const LONG_STRING_LEN: usize = 4096;
pub fn generate_binary_trie() -> Option<Trie<String>> {
    let mut trie = trie_new()?;

    let bin_key2: [u8; 8] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff, 0];
    let bin_key: [u8; 7] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff];

    assert!(trie_insert_binary(
        &mut trie,
        &bin_key2,
        bin_key2.len(),
        "goodbye world".to_string()
    ));
    assert!(trie_insert_binary(
        &mut trie,
        &bin_key,
        bin_key.len(),
        "hello world".to_string()
    ));

    Some(trie)
}

pub fn generate_trie() -> Option<Trie<i32>> {
    let mut trie = Trie::new();
    let mut entries = 0;

    for i in 0..NUM_TEST_VALUES {
        let test_string = format!("{}", i);
        let test_array = i as i32;

        assert!(trie_insert(&mut trie, &test_string, test_array));
        entries += 1;

        assert_eq!(trie_num_entries(&trie), entries);
    }

    Some(trie)
}

#[test]
pub fn test_trie_remove_binary() {
    let trie = generate_binary_trie().expect("Failed to generate binary trie");

    // Test look up and remove of invalid values
    let bin_key3: [u8; 3] = ['a' as u8, 'b' as u8, 'c' as u8];
    let bin_key4: [u8; 4] = ['z' as u8, 0, 'z' as u8, 'z' as u8];

    let value = trie_lookup_binary(&trie, &bin_key3, bin_key3.len());
    assert!(value.is_none());

    assert!(!trie_remove_binary(&trie, &bin_key3, bin_key3.len()));

    assert!(trie_lookup_binary(&trie, &bin_key4, bin_key4.len()).is_none());
    assert!(!trie_remove_binary(&trie, &bin_key4, bin_key4.len()));

    // Remove the two values
    let bin_key2: [u8; 8] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff, 0];
    let bin_key: [u8; 7] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff];

    assert!(trie_remove_binary(&trie, &bin_key2, bin_key2.len()));
    assert!(trie_lookup_binary(&trie, &bin_key2, bin_key2.len()).is_none());
    assert!(trie_lookup_binary(&trie, &bin_key, bin_key.len()).is_some());

    assert!(trie_remove_binary(&trie, &bin_key, bin_key.len()));
    assert!(trie_lookup_binary(&trie, &bin_key, bin_key.len()).is_none());

    trie_free(trie);
}

#[test]
pub fn test_trie_new_free() {
    let mut trie: Option<Trie<String>>;

    // Allocate and free an empty trie
    trie = trie_new();
    assert!(trie.is_some());
    if let Some(trie) = trie {
        trie_free(trie);
    }

    // Add some values before freeing
    trie = trie_new();
    assert!(trie.is_some());
    if let Some(mut trie) = trie {
        assert!(trie_insert(&mut trie, "hello", "there".to_string()));
        assert!(trie_insert(&mut trie, "hell", "testing".to_string()));
        assert!(trie_insert(&mut trie, "testing", "testing".to_string()));
        assert!(trie_insert(&mut trie, "", "asfasf".to_string()));
        trie_free(trie);
    }

    // Add a value, remove it and then free
    trie = trie_new();
    assert!(trie.is_some());
    if let Some(mut trie) = trie {
        assert!(trie_insert(&mut trie, "hello", "there".to_string()));
        assert!(trie_remove(&trie, "hello"));
        trie_free(trie);
    }

    // Test out of memory scenario (removed as per requirements)
}

#[test]
pub fn test_trie_replace() {
    let mut trie = generate_trie().expect("Failed to generate trie");

    // Test replacing values
    let mut val = 999;
    assert!(trie_insert(&mut trie, "999", val));
    assert_eq!(trie_num_entries(&trie), NUM_TEST_VALUES);

    assert_eq!(trie_lookup(&trie, "999"), Some(val));
    trie_free(trie);
}

#[test]
pub fn test_trie_lookup() {
    let mut trie = generate_trie().expect("Failed to generate trie");

    // Test lookup for non-existent values
    assert!(trie_lookup(&trie, "000000000000000").is_none());
    assert!(trie_lookup(&trie, "").is_none());

    // Look up all values
    for i in 0..NUM_TEST_VALUES {
        let buf = format!("{}", i);
        let val = trie_lookup(&trie, &buf);

        assert!(val.is_some());
        assert_eq!(val.unwrap(), i as i32);
    }

    trie_free(trie);
}

#[test]
pub fn test_trie_free_long() {
    let mut long_string = vec![b'A'; LONG_STRING_LEN];
    long_string[LONG_STRING_LEN - 1] = b'\0';

    let mut trie = trie_new().expect("Failed to create trie");
    let key = String::from_utf8(long_string.clone()).expect("Invalid UTF-8 sequence");
    trie_insert(&mut trie, &key, key.clone());

    trie_free(trie);
}

#[test]
pub fn test_trie_negative_keys() {
    let my_key = vec![b'a', b'b', b'c', 206, 236, 0];
    let mut trie = trie_new().unwrap();
    let value = "hello world";

    assert!(trie_insert(
        &mut trie,
        std::str::from_utf8(&my_key).unwrap(),
        value
    ));

    let lookup_value = trie_lookup(&trie, std::str::from_utf8(&my_key).unwrap());
    assert_eq!(lookup_value, Some(value));

    assert!(trie_remove(&trie, std::str::from_utf8(&my_key).unwrap()));
    assert!(!trie_remove(&trie, std::str::from_utf8(&my_key).unwrap()));
    assert_eq!(
        trie_lookup(&trie, std::str::from_utf8(&my_key).unwrap()),
        None
    );

    trie_free(trie);
}

#[test]
pub fn test_trie_insert_empty() {
    let mut trie = trie_new().unwrap();
    let buf = String::from("test");

    // Test insert on empty string
    assert!(trie_insert(&mut trie, "", buf.clone()));
    assert_ne!(trie_num_entries(&trie), 0);
    assert_eq!(trie_lookup(&trie, ""), Some(buf.clone()));
    assert!(trie_remove(&trie, ""));

    assert_eq!(trie_num_entries(&trie), 0);

    trie_free(trie);
}

#[test]
pub fn test_trie_insert() {
    let mut trie = generate_trie().expect("Failed to generate trie");
    let mut entries = trie_num_entries(&trie);

    // Test insert of None value has no effect
    assert!(!trie_insert(&mut trie, "hello world", 0));
    assert_eq!(trie_num_entries(&trie), entries);

    // Test rollback
    assert!(!trie_insert(&mut trie, "hello world", 1));
    assert_eq!(trie_num_entries(&trie), entries);

    trie_free(trie);
}

#[test]
pub fn test_trie_remove() {
    let mut trie = generate_trie().expect("Failed to generate trie");

    // Test remove on non-existent values.
    assert!(!trie_remove(&trie, "000000000000000"));
    assert!(!trie_remove(&trie, ""));

    let mut entries = trie_num_entries(&trie);

    assert_eq!(entries, NUM_TEST_VALUES);

    // Remove all values
    for i in 0..NUM_TEST_VALUES {
        let buf = format!("{}", i);

        // Remove value and check counter
        assert!(trie_remove(&trie, &buf));
        entries -= 1;
        assert_eq!(trie_num_entries(&trie), entries);
    }

    trie_free(trie);
}

#[test]
pub fn test_trie_insert_out_of_memory() {
    let mut trie = generate_binary_trie().expect("Failed to generate binary trie");

    let bin_key4: [u8; 4] = ['z' as u8, 0, 'z' as u8, 'z' as u8];

    assert!(!trie_insert_binary(
        &mut trie,
        &bin_key4,
        bin_key4.len(),
        "test value".to_string()
    ));
    assert!(trie_lookup_binary(&trie, &bin_key4, bin_key4.len()).is_none());
    assert_eq!(trie_num_entries(&trie), 2);

    trie_free(trie);
}

#[test]
pub fn test_trie_insert_binary() {
    let mut trie = generate_binary_trie().expect("Failed to generate binary trie");

    // Overwrite a value
    let bin_key: [u8; 7] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff];
    assert!(trie_insert_binary(
        &mut trie,
        &bin_key,
        bin_key.len(),
        "hi world".to_string()
    ));

    // Insert NULL value doesn't work
    let bin_key3: [u8; 3] = ['a' as u8, 'b' as u8, 'c' as u8];
    assert!(!trie_insert_binary(
        &mut trie,
        &bin_key3,
        bin_key3.len(),
        "".to_string()
    ));

    // Read them back
    let value = trie_lookup_binary(&trie, &bin_key, bin_key.len());
    assert_eq!(value, Some("hi world".to_string()));

    let bin_key2: [u8; 8] = ['a' as u8, 'b' as u8, 'c' as u8, 0, 1, 2, 0xff, 0];
    let value = trie_lookup_binary(&trie, &bin_key2, bin_key2.len());
    assert_eq!(value, Some("goodbye world".to_string()));

    trie_free(trie);
}
