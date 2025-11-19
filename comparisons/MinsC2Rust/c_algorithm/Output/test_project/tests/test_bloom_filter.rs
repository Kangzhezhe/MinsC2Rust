use test_project::bloom_filter::{
    bloom_filter_free, bloom_filter_insert, bloom_filter_intersection, bloom_filter_load,
    bloom_filter_new, bloom_filter_query, bloom_filter_read, bloom_filter_union, BloomFilter,
    SALTS,
};
#[test]
pub fn test_bloom_filter_mismatch() {
    // Create one filter with both values set
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();

    // Different buffer size
    let mut filter2 = bloom_filter_new(64, string_hash, 4).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(Box::new(filter2));

    // Different hash function
    let mut filter2 = bloom_filter_new(128, string_nocase_hash, 4).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(Box::new(filter2));

    // Different number of salts
    let mut filter2 = bloom_filter_new(128, string_hash, 32).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(Box::new(filter2));

    bloom_filter_free(Box::new(filter1));
}

#[test]
pub fn test_bloom_filter_read_load() {
    let mut state: Vec<u8> = vec![0; 16];

    // Create a filter with some values set
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter1, "test 1");
    bloom_filter_insert(&mut filter1, "test 2");

    // Read the current state into an array
    bloom_filter_read(&filter1, &mut state);

    // Create a new filter and load the state
    let mut filter2 = bloom_filter_new(128, string_hash, 4).unwrap();
    bloom_filter_load(&mut filter2, &state);

    // Check the values are set in the new filter
    assert!(bloom_filter_query(&filter2, "test 1") != 0);
    assert!(bloom_filter_query(&filter2, "test 2") != 0);
}

#[test]
pub fn test_bloom_filter_insert_query() {
    // Create a filter
    let mut filter = bloom_filter_new(128, string_hash, 4).expect("Failed to create Bloom filter");

    // Check values are not present at the start
    assert_eq!(bloom_filter_query(&filter, "test 1"), 0);
    assert_eq!(bloom_filter_query(&filter, "test 2"), 0);

    // Insert some values
    bloom_filter_insert(&mut filter, "test 1");
    bloom_filter_insert(&mut filter, "test 2");

    // Check they are set
    assert_ne!(bloom_filter_query(&filter, "test 1"), 0);
    assert_ne!(bloom_filter_query(&filter, "test 2"), 0);

    // Free the filter
    bloom_filter_free(Box::new(filter));
}

#[test]
pub fn test_bloom_filter_intersection() {
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();
    let mut filter2 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter1, "test 1");
    bloom_filter_insert(&mut filter1, "test 2");

    bloom_filter_insert(&mut filter2, "test 1");

    assert_eq!(bloom_filter_query(&filter2, "test 2"), 0);

    let result = bloom_filter_intersection(&filter1, &filter2).unwrap();

    assert_ne!(bloom_filter_query(&result, "test 1"), 0);
    assert_eq!(bloom_filter_query(&result, "test 2"), 0);

    bloom_filter_free(Box::new(result));

    bloom_filter_free(Box::new(filter1));
    bloom_filter_free(Box::new(filter2));
}

#[test]
pub fn test_bloom_filter_new_free() {
    // One salt
    let filter = bloom_filter_new::<&str>(128, string_hash as fn(&str) -> u32, 1);
    assert!(filter.is_some());
    if let Some(filter) = filter {
        bloom_filter_free(Box::new(filter));
    }

    // Maximum number of salts
    let filter = bloom_filter_new::<&str>(128, string_hash as fn(&str) -> u32, 64);
    assert!(filter.is_some());
    if let Some(filter) = filter {
        bloom_filter_free(Box::new(filter));
    }

    // Test creation with too many salts
    let filter = bloom_filter_new::<&str>(128, string_hash as fn(&str) -> u32, 50000);
    assert!(filter.is_none());
}

#[test]
pub fn test_bloom_filter_union() {
    let mut filter1 =
        bloom_filter_new(128, string_hash as fn(&str) -> u32, 4).expect("Failed to create filter1");
    bloom_filter_insert(&mut filter1, "test 1");

    let mut filter2 =
        bloom_filter_new(128, string_hash as fn(&str) -> u32, 4).expect("Failed to create filter2");
    bloom_filter_insert(&mut filter2, "test 2");

    let result = bloom_filter_union(&filter1, &filter2).expect("Failed to create union filter");

    assert!(bloom_filter_query(&result, "test 1") != 0);
    assert!(bloom_filter_query(&result, "test 2") != 0);

    bloom_filter_free(Box::new(result));
    bloom_filter_free(Box::new(filter1));
    bloom_filter_free(Box::new(filter2));
}

pub fn string_nocase_hash(s: &str) -> u32 {
    let mut hash: u32 = 5381;
    for c in s.to_lowercase().bytes() {
        hash = ((hash << 5).wrapping_add(hash)) + c as u32;
    }
    hash
}

pub fn string_hash(s: &str) -> u32 {
    let mut hash: u32 = 5381;
    for c in s.bytes() {
        hash = ((hash << 5).wrapping_add(hash)) + c as u32;
    }
    hash
}
