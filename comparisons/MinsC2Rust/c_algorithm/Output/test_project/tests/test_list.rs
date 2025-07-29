use test_project::list::{
    list_append, list_data, list_find_data, list_free, list_iter_has_more, list_iter_next,
    list_iter_remove, list_iterate, list_length, list_next, list_nth_data, list_nth_entry,
    list_prepend, list_prev, list_remove_data, list_remove_entry, list_sort, list_sort_internal,
    list_to_array, variable1, variable2, variable3, variable4, ListEntry, ListIterator,
};
pub fn generate_list() -> Option<Box<ListEntry<i32>>> {
    let mut list: Option<Box<ListEntry<i32>>> = None;

    assert!(list_append(&mut list, variable1).is_some());
    assert!(list_append(&mut list, variable2).is_some());
    assert!(list_append(&mut list, variable3).is_some());
    assert!(list_append(&mut list, variable4).is_some());

    list
}

#[test]
pub fn test_list_free() {
    let mut list = generate_list();
    list_free(list);

    list_free::<i32>(None);
}

#[test]
pub fn test_list_iterate_bad_remove() {
    let mut list: Option<Box<ListEntry<i32>>> = None;
    let mut iter = ListIterator {
        prev_next: None,
        current: None,
    };
    let mut values = [0; 49];

    for i in 0..49 {
        values[i] = i as i32; // Convert usize to i32
        assert!(list_prepend(&mut list, values[i]).is_some());
    }

    list_iterate(&mut list, &mut iter);

    while list_iter_has_more(&iter) {
        let val = list_iter_next(&mut iter).unwrap();

        if val % 2 == 0 {
            assert_ne!(
                list_remove_data(&mut list, |a: &i32, b: &i32| a == b, val),
                0
            );
            list_iter_remove(&mut iter);
        }
    }

    list_free(list);
}

#[test]
pub fn test_list_nth_data() {
    let list = generate_list();

    // Check all values in the list
    assert_eq!(list_nth_data(list.clone(), 0), Some(50));
    assert_eq!(list_nth_data(list.clone(), 1), Some(0));
    assert_eq!(list_nth_data(list.clone(), 2), Some(0));
    assert_eq!(list_nth_data(list.clone(), 3), Some(0));

    // Check out of range values
    assert_eq!(list_nth_data(list.clone(), 4), None);
    assert_eq!(list_nth_data(list.clone(), 400), None);

    list_free(list);
}

#[test]
pub fn test_list_to_array() {
    let list = generate_list();
    let array = list_to_array(list.clone());

    assert_eq!(array[0], 50);
    assert_eq!(array[1], 0);
    assert_eq!(array[2], 0);
    assert_eq!(array[3], 0);

    list_free(list);
}

#[test]
pub fn test_list_next() {
    let mut list = generate_list();
    let mut rover = list.clone();

    assert_eq!(list_data(rover.clone()), Some(50));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(0));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(0));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(0));
    rover = list_next(rover);
    assert_eq!(rover, None);

    list_free(list);
}

#[test]
pub fn test_list_sort() {
    let mut list: Option<Box<ListEntry<i32>>> = None;
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let sorted = vec![4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    for i in 0..num_entries {
        assert!(list_prepend(&mut list, entries[i]).is_some());
    }

    list_sort(&mut list, |a, b| match a.cmp(b) {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Equal => 0,
        std::cmp::Ordering::Greater => 1,
    });

    assert_eq!(list_length(list.clone()), num_entries);

    for i in 0..num_entries {
        let value = list_nth_data(list.clone(), i);
        assert_eq!(value, Some(sorted[i]));
    }

    list_free(list);

    let mut list: Option<Box<ListEntry<i32>>> = None;
    list_sort(&mut list, |a, b| match a.cmp(b) {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Equal => 0,
        std::cmp::Ordering::Greater => 1,
    });
    assert!(list.is_none());
}

#[test]
pub fn test_list_iterate() {
    let mut list: Option<Box<ListEntry<i32>>> = None;
    let mut iter = ListIterator {
        prev_next: None,
        current: None,
    };
    let a = 0;
    let mut counter = 0;

    // Create a list with 50 entries
    for _ in 0..50 {
        assert!(list_prepend(&mut list, a).is_some());
    }

    // Iterate over the list and count the number of entries visited
    list_iterate(&mut list, &mut iter);

    // Test remove before list_iter_next has been called
    list_iter_remove(&mut iter);

    // Iterate over the list
    while list_iter_has_more(&iter) {
        let data = list_iter_next(&mut iter);
        assert!(data.is_some());
        counter += 1;

        if (counter % 2) == 0 {
            // Delete half the entries in the list
            list_iter_remove(&mut iter);

            // Test double remove
            list_iter_remove(&mut iter);
        }
    }

    // Test iter_next after iteration has completed
    assert!(list_iter_next(&mut iter).is_none());

    // Test remove at the end of a list
    list_iter_remove(&mut iter);

    assert_eq!(counter, 50);
    assert_eq!(list_length(list.clone()), 25);

    list_free(list);

    // Test iterating over an empty list
    list = None;
    counter = 0;

    list_iterate(&mut list, &mut iter);

    while list_iter_has_more(&iter) {
        let data = list_iter_next(&mut iter);
        assert!(data.is_some());
        counter += 1;
    }

    assert_eq!(counter, 0);
}

#[test]
pub fn test_list_find_data() {
    let entries = vec![89, 23, 42, 16, 15, 4, 8, 99, 50, 30];
    let num_entries = entries.len();
    let mut list: Option<Box<ListEntry<i32>>> = None;

    // Generate a list containing the entries
    for i in 0..num_entries {
        assert!(list_append(&mut list, entries[i]).is_some());
    }

    // Check that each value can be searched for correctly
    for i in 0..num_entries {
        let val = entries[i];

        let result = list_find_data(list.clone(), |a, b| a == b, val);

        assert!(result.is_some());

        let data = list_data(result);
        assert_eq!(data, Some(val));
    }

    // Check some invalid values return None
    let val = 0;
    assert!(list_find_data(list.clone(), |a, b| a == b, val).is_none());
    let val = 56;
    assert!(list_find_data(list.clone(), |a, b| a == b, val).is_none());

    list_free(list);
}

#[test]
pub fn test_list_nth_entry() {
    let mut list = generate_list();

    // Check all values in the list
    let mut entry = list_nth_entry(list.clone(), 0);
    assert_eq!(list_data(entry), Some(50));
    entry = list_nth_entry(list.clone(), 1);
    assert_eq!(list_data(entry), Some(0));
    entry = list_nth_entry(list.clone(), 2);
    assert_eq!(list_data(entry), Some(0));
    entry = list_nth_entry(list.clone(), 3);
    assert_eq!(list_data(entry), Some(0));

    // Check out of range values
    entry = list_nth_entry(list.clone(), 4);
    assert_eq!(entry, None);
    entry = list_nth_entry(list.clone(), 400);
    assert_eq!(entry, None);

    list_free(list);
}

#[test]
pub fn test_list_prepend() {
    let mut list: Option<Box<ListEntry<i32>>> = None;

    assert!(list_prepend(&mut list, unsafe { variable1 }).is_some());
    check_list_integrity(&list);
    assert!(list_prepend(&mut list, unsafe { variable2 }).is_some());
    check_list_integrity(&list);
    assert!(list_prepend(&mut list, unsafe { variable3 }).is_some());
    check_list_integrity(&list);
    assert!(list_prepend(&mut list, unsafe { variable4 }).is_some());
    check_list_integrity(&list);

    assert_eq!(list_nth_data(list.clone(), 0), Some(unsafe { variable4 }));
    assert_eq!(list_nth_data(list.clone(), 1), Some(unsafe { variable3 }));
    assert_eq!(list_nth_data(list.clone(), 2), Some(unsafe { variable2 }));
    assert_eq!(list_nth_data(list.clone(), 3), Some(unsafe { variable1 }));

    assert_eq!(list_length(list.clone()), 4);

    list_free(list);
}

pub fn check_list_integrity<T>(list: &Option<Box<ListEntry<T>>>)
where
    T: Clone + PartialEq + std::fmt::Debug,
{
    let mut prev: Option<Box<ListEntry<T>>> = None;
    let mut rover = list.clone();

    while let Some(ref node) = rover {
        assert_eq!(list_prev(rover.clone()), prev);
        prev = rover.clone();
        rover = list_next(rover.clone());
    }
}

#[test]
pub fn test_list_length() {
    let mut list = generate_list();

    // Generate a list and check that it is four entries long
    assert_eq!(list_length(list.clone()), 4);

    // Add an entry and check that it still works properly
    unsafe {
        assert!(list_prepend(&mut list, variable1).is_some());
    }
    assert_eq!(list_length(list.clone()), 5);

    list_free(list);

    // Check the length of the empty list
    assert_eq!(list_length::<i32>(None), 0);
}

#[test]
pub fn test_list_remove_entry() {
    let mut empty_list: Option<Box<ListEntry<i32>>> = None;
    let mut list: Option<Box<ListEntry<i32>>>;
    let mut entry: Option<Box<ListEntry<i32>>>;

    list = generate_list();

    /* Remove the third entry */
    entry = list_nth_entry(list.clone(), 2);
    assert!(list_remove_entry(&mut list, entry) != false);
    assert!(list_length(list.clone()) == 3);
    check_list_integrity(&list);

    /* Remove the first entry */
    entry = list_nth_entry(list.clone(), 0);
    assert!(list_remove_entry(&mut list, entry) != false);
    assert!(list_length(list.clone()) == 2);
    check_list_integrity(&list);

    /* Try some invalid removes */
    /* NULL */
    assert!(list_remove_entry(&mut list, None) == false);

    /* Removing NULL from an empty list */
    assert!(list_remove_entry(&mut empty_list, None) == false);

    list_free(list);

    /* Test removing an entry when it is the only entry. */
    list = None;
    let list_clone = list.clone();
    assert!(list_append(&mut list, variable1).is_some());
    assert!(list.is_some());
    assert!(list_remove_entry(&mut list, list_clone) != false);
    assert!(list.is_none());

    /* Test removing the last entry */
    list = generate_list();
    entry = list_nth_entry(list.clone(), 3);
    assert!(list_remove_entry(&mut list, entry) != false);
    check_list_integrity(&list);
    list_free(list);
}
