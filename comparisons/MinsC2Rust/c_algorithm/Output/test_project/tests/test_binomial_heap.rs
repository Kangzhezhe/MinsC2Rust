use test_project::binomial_heap::{
    binomial_heap_cmp, binomial_heap_free, binomial_heap_insert, binomial_heap_merge,
    binomial_heap_merge_undo, binomial_heap_new, binomial_heap_num_entries, binomial_heap_pop,
    binomial_tree_merge, binomial_tree_ref, binomial_tree_unref, BinomialHeap, BinomialHeapType,
    BinomialTree, NUM_TEST_VALUES, TEST_VALUE,
};
pub fn generate_heap() -> Option<BinomialHeap<i32>> {
    let mut heap = binomial_heap_new(BinomialHeapType::Min, |a: &i32, b: &i32| a.cmp(b) as i32)?;

    let mut test_array = vec![0; NUM_TEST_VALUES];

    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        if i != TEST_VALUE {
            assert!(binomial_heap_insert(&mut heap, test_array[i]));
        }
    }

    Some(heap)
}

pub fn verify_heap<T: Clone + PartialEq + std::fmt::Debug>(
    heap: &mut BinomialHeap<T>,
    test_values: &[T],
    test_value_index: usize,
) {
    let mut num_vals = binomial_heap_num_entries(heap);
    assert_eq!(num_vals, test_values.len() - 1);

    for i in 0..test_values.len() {
        if i == test_value_index {
            continue;
        }

        let val = binomial_heap_pop(heap);
        assert_eq!(val.as_ref(), Some(&test_values[i]));

        num_vals -= 1;
        assert_eq!(binomial_heap_num_entries(heap), num_vals);
    }
}

#[test]
pub fn test_min_heap() {
    let mut heap = binomial_heap_new(BinomialHeapType::Min, int_compare).unwrap();
    let mut test_array: Vec<i32> = (0..NUM_TEST_VALUES as i32).collect();

    for i in 0..NUM_TEST_VALUES {
        assert!(binomial_heap_insert(&mut heap, test_array[i]));
    }

    let mut i = -1;
    while binomial_heap_num_entries(&heap) > 0 {
        let val = binomial_heap_pop(&mut heap).unwrap();
        assert_eq!(val, i + 1);
        i = val;
    }

    let val = binomial_heap_pop(&mut heap);
    assert!(val.is_none());

    binomial_heap_free(heap);
}

#[test]
pub fn test_insert_out_of_memory() {
    let mut heap: Option<BinomialHeap<i32>>;

    for _ in 0..6 {
        heap = generate_heap();

        let mut test_array = vec![0; NUM_TEST_VALUES];
        for i in 0..NUM_TEST_VALUES {
            test_array[i] = i as i32;
        }

        test_array[TEST_VALUE] = TEST_VALUE as i32;
        assert!(!binomial_heap_insert(
            heap.as_mut().unwrap(),
            test_array[TEST_VALUE]
        ));

        verify_heap(heap.as_mut().unwrap(), &test_array, TEST_VALUE);

        binomial_heap_free(heap.unwrap());
    }
}

#[test]
pub fn test_pop_out_of_memory() {
    for _ in 0..6 {
        let mut heap = generate_heap().unwrap();

        // Pop should fail
        assert!(binomial_heap_pop(&mut heap).is_none());

        // Check the heap is unharmed
        binomial_heap_free(heap);
    }
}

#[test]
pub fn test_binomial_heap_new_free() {
    for _ in 0..NUM_TEST_VALUES {
        let heap = binomial_heap_new(BinomialHeapType::Min, |a: &i32, b: &i32| match a.cmp(b) {
            std::cmp::Ordering::Less => -1,
            std::cmp::Ordering::Equal => 0,
            std::cmp::Ordering::Greater => 1,
        });
        if let Some(heap) = heap {
            binomial_heap_free(heap);
        }
    }
}

#[test]
pub fn test_max_heap() {
    let mut heap =
        binomial_heap_new(BinomialHeapType::Max, |a: &i32, b: &i32| a.cmp(b) as i32).unwrap();
    let mut test_array: Vec<i32> = (0..NUM_TEST_VALUES as i32).collect();

    for i in 0..NUM_TEST_VALUES {
        assert!(binomial_heap_insert(&mut heap, test_array[i]));
    }

    let mut i = NUM_TEST_VALUES as i32;
    while binomial_heap_num_entries(&heap) > 0 {
        let val = binomial_heap_pop(&mut heap).unwrap();
        assert_eq!(val, i - 1);
        i = val;
    }

    let val = binomial_heap_pop(&mut heap);
    assert!(val.is_none());

    binomial_heap_free(heap);
}

#[test]
pub fn test_binomial_heap_insert() {
    let mut heap = binomial_heap_new(BinomialHeapType::Min, int_compare).unwrap();
    let test_array: Vec<i32> = (0..NUM_TEST_VALUES as i32).collect();

    for i in 0..NUM_TEST_VALUES {
        assert!(binomial_heap_insert(&mut heap, test_array[i]));
    }
    assert_eq!(binomial_heap_num_entries(&heap), NUM_TEST_VALUES);

    binomial_heap_free(heap);
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
