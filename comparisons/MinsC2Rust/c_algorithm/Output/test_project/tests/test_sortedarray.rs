use test_project::compare_int::{int_compare};
use test_project::sortedarray::{SortedArray,sortedarray_new, sortedarray_insert, sortedarray_free, sortedarray_first_index, sortedarray_remove, sortedarray_index_of, sortedarray_last_index, sortedarray_remove_range, sortedarray_length, sortedarray_get};
pub const TEST_SIZE: usize = 20;pub fn generate_sortedarray_equ<T>(equ_func: fn(&T, &T) -> bool) -> Option<SortedArray<T>> 
where
    T: Clone + Ord + From<i32>,
{
    const TEST_SIZE: usize = 20;
    const TEST_ARRAY: [i32; TEST_SIZE] = [10, 12, 12, 1, 2, 3, 6, 7, 2, 23, 13, 23, 23, 34, 31, 9, 0, 0, 0, 0];

    let mut sortedarray = sortedarray_new(0, equ_func, |a: &T, b: &T| a.cmp(b))?;

    for i in 0..TEST_SIZE {
        let value = T::from(TEST_ARRAY[i]);
        sortedarray_insert(&mut sortedarray, value);
    }

    Some(sortedarray)
}

pub fn free_sorted_ints<T>(sortedarray: Option<Box<SortedArray<T>>>) {
    if let Some(mut sortedarray) = sortedarray {
        for i in 0..sortedarray_length(&sortedarray) {
            if let Some(pi) = sortedarray_get(&sortedarray, i) {
                // In Rust, we don't need to manually free memory as it is managed by the ownership system.
                // The Vec<T> inside SortedArray will automatically deallocate its memory when it goes out of scope.
            }
        }
        sortedarray_free(Some(sortedarray));
    }
}

pub fn generate_sortedarray<T>() -> Option<SortedArray<T>>
where
    T: Clone + Ord + From<i32>,
{
    generate_sortedarray_equ(|a: &T, b: &T| a == b)
}

pub fn check_sorted_prop<T: PartialOrd>(sortedarray: &SortedArray<T>) {
    for i in 1..sortedarray_length(sortedarray) {
        let prev = sortedarray_get(sortedarray, i - 1).unwrap();
        let curr = sortedarray_get(sortedarray, i).unwrap();
        assert!(int_compare(prev, curr) <= 0);
    }
}

#[test]
pub fn test_sortedarray_index_of() {
    const TEST_SIZE: usize = 20;
    let sortedarray = generate_sortedarray::<i32>();

    if let Some(sortedarray) = sortedarray {
        for i in 0..TEST_SIZE {
            if let Some(value) = sortedarray_get(&sortedarray, i) {
                let r = sortedarray_index_of(&sortedarray, *value);
                assert!(r >= 0);
                assert_eq!(*sortedarray_get(&sortedarray, r as usize).unwrap(), *value);
            }
        }

        free_sorted_ints(Some(Box::new(sortedarray)));
    }
}

#[test]
pub fn test_sortedarray_index_of_equ_key() {
    // replace equal function by function which checks pointers
    let sortedarray = generate_sortedarray_equ(ptr_equal as fn(&i32, &i32) -> bool);
    let sortedarray = match sortedarray {
        Some(array) => array,
        None => return,
    };

    // check if all search value return the same index
    for i in 0..TEST_SIZE {
        let value = match sortedarray_get(&sortedarray, i) {
            Some(v) => v.clone(),
            None => continue,
        };
        let r = sortedarray_index_of(&sortedarray, value);
        assert!(r >= 0);
        assert_eq!(i, r as usize);
    }

    free_sorted_ints(Some(Box::new(sortedarray)));
}

pub fn ptr_equal<T>(a: &T, b: &T) -> bool {
    std::ptr::eq(a, b)
}

#[test]
pub fn test_sortedarray_remove_range() {
    const TEST_REMOVE_RANGE: usize = 7;
    const TEST_REMOVE_RANGE_LENGTH: usize = 4;

    let mut sortedarray = generate_sortedarray::<i32>().expect("Failed to generate sorted array");

    let mut new_values = Vec::with_capacity(TEST_REMOVE_RANGE_LENGTH);
    for i in 0..TEST_REMOVE_RANGE_LENGTH {
        let value = *sortedarray_get(&sortedarray, TEST_REMOVE_RANGE + TEST_REMOVE_RANGE_LENGTH + i).unwrap();
        new_values.push(value);
    }

    sortedarray_remove_range(&mut sortedarray, TEST_REMOVE_RANGE, TEST_REMOVE_RANGE_LENGTH);

    for i in 0..TEST_REMOVE_RANGE_LENGTH {
        let value = *sortedarray_get(&sortedarray, TEST_REMOVE_RANGE + i).unwrap();
        assert_eq!(value, new_values[i]);
    }

    check_sorted_prop(&sortedarray);
    free_sorted_ints(Some(Box::new(sortedarray)));
}

#[test]
pub fn test_sortedarray_remove() {
    let mut sortedarray = generate_sortedarray::<i32>().expect("Failed to generate sorted array");

    let test_remove_el = 15;

    let ip = sortedarray_get(&sortedarray, test_remove_el + 1).expect("Failed to get element at index");
    let i = *ip;

    sortedarray_remove(&mut sortedarray, test_remove_el);

    let new_element = sortedarray_get(&sortedarray, test_remove_el).expect("Failed to get element at index after removal");
    assert_eq!(*new_element, i);

    check_sorted_prop(&sortedarray);
    free_sorted_ints(Some(Box::new(sortedarray)));
}

#[test]
pub fn test_sortedarray_get() {
    let mut i: usize;

    let arr = generate_sortedarray::<i32>();

    if let Some(arr) = arr {
        for i in 0..sortedarray_length(&arr) {
            let value1 = sortedarray_get(&arr, i);
            let value2 = sortedarray_get(&arr, i);
            assert!(value1 == value2);
            assert!(value1.unwrap() == value2.unwrap());
        }

        free_sorted_ints(Some(Box::new(arr)));
    }
}

