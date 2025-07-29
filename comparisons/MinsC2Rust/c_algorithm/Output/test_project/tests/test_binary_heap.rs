use test_project::binary_heap::{
    binary_heap_cmp, binary_heap_free, binary_heap_insert, binary_heap_new,
    binary_heap_num_entries, binary_heap_pop, BinaryHeap, BinaryHeapType, BinaryHeapValue,
};

pub const NUM_TEST_VALUES: usize = 10000;
#[test]
pub fn test_binary_heap_insert() {
    let mut heap = binary_heap_new(BinaryHeapType::Min, int_compare).unwrap();
    let mut test_array: Vec<i32> = (0..NUM_TEST_VALUES as i32).collect();

    for i in 0..NUM_TEST_VALUES {
        assert!(binary_heap_insert(&mut heap, test_array[i]));
    }

    assert_eq!(binary_heap_num_entries(&heap), NUM_TEST_VALUES);

    binary_heap_free(heap);
}

#[test]
pub fn test_binary_heap_new_free() {
    for _ in 0..NUM_TEST_VALUES {
        let heap = binary_heap_new::<i32>(BinaryHeapType::Min, int_compare);
        binary_heap_free(heap.unwrap());
    }
}

#[test]
pub fn test_out_of_memory() {
    let mut heap = binary_heap_new(BinaryHeapType::Min, int_compare).unwrap();
    let values = vec![15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0];

    for i in 0..16 {
        assert!(binary_heap_insert(&mut heap, values[i]));
    }

    assert_eq!(binary_heap_num_entries(&heap), 16);

    for i in 0..16 {
        assert!(!binary_heap_insert(&mut heap, values[i]));
        assert_eq!(binary_heap_num_entries(&heap), 16);
    }

    for i in 0..16 {
        let value = binary_heap_pop(&mut heap).unwrap();
        assert_eq!(value, i);
    }

    assert_eq!(binary_heap_num_entries(&heap), 0);

    binary_heap_free(heap);
}

#[test]
pub fn test_min_heap() {
    let mut heap = binary_heap_new(BinaryHeapType::Min, int_compare).unwrap();
    let mut test_array: Vec<i32> = (0..NUM_TEST_VALUES as i32).collect();

    for i in 0..NUM_TEST_VALUES {
        assert!(binary_heap_insert(&mut heap, test_array[i]));
    }

    let mut i = -1;
    while binary_heap_num_entries(&heap) > 0 {
        let val = binary_heap_pop(&mut heap).unwrap();
        assert!(val == i + 1);
        i = val;
    }

    assert_eq!(binary_heap_num_entries(&heap), 0);
    assert!(binary_heap_pop(&mut heap).is_none());

    binary_heap_free(heap);
}

#[test]
pub fn test_max_heap() {
    pub const NUM_TEST_VALUES: usize = 10000;
    let mut test_array: Vec<i32> = Vec::with_capacity(NUM_TEST_VALUES);

    let mut heap = binary_heap_new(BinaryHeapType::Max, |a: &i32, b: &i32| {
        if a < b {
            -1
        } else if a > b {
            1
        } else {
            0
        }
    })
    .unwrap();

    for i in 0..NUM_TEST_VALUES {
        test_array.push(i as i32);
        assert!(binary_heap_insert(&mut heap, test_array[i]));
    }

    let mut i = NUM_TEST_VALUES as i32;
    while binary_heap_num_entries(&heap) > 0 {
        let val = binary_heap_pop(&mut heap).unwrap();
        assert_eq!(val, i - 1);
        i = val;
    }

    binary_heap_free(heap);
}

pub fn int_compare(a: &i32, b: &i32) -> i32 {
    if a < b {
        -1
    } else if a > b {
        1
    } else {
        0
    }
}
