use test_project::arraylist::{
    arraylist_append, arraylist_clear, arraylist_enlarge, arraylist_free, arraylist_index_of,
    arraylist_insert, arraylist_new, arraylist_prepend, arraylist_remove, arraylist_remove_range,
    arraylist_sort, arraylist_sort_internal, ArrayList,
};
pub fn generate_arraylist<T: Clone + Default>() -> Option<Box<ArrayList<T>>> {
    let mut arraylist = arraylist_new(0)?;

    for _ in 0..4 {
        arraylist_append(&mut arraylist, T::default());
        arraylist_append(&mut arraylist, T::default());
        arraylist_append(&mut arraylist, T::default());
        arraylist_append(&mut arraylist, T::default());
    }

    Some(arraylist)
}

#[test]
pub fn test_arraylist_new_free() {
    // Use a default size when given zero
    let arraylist = arraylist_new::<i32>(0);
    assert!(arraylist.is_some());
    arraylist_free(arraylist);

    // Normal allocated
    let arraylist = arraylist_new::<i32>(10);
    assert!(arraylist.is_some());
    arraylist_free(arraylist);

    // Freeing a null arraylist works
    arraylist_free::<i32>(None);
}

#[test]
pub fn test_arraylist_sort() {
    let mut arraylist: Option<Box<ArrayList<i32>>>;
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let sorted = vec![4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    arraylist = arraylist_new(10);

    for i in 0..num_entries {
        arraylist_prepend(arraylist.as_mut().unwrap(), entries[i]);
    }

    arraylist_sort(arraylist.as_mut().unwrap(), int_compare);

    assert_eq!(arraylist.as_ref().unwrap().length, num_entries);

    for i in 0..num_entries {
        let value = arraylist.as_ref().unwrap().data[i];
        assert_eq!(value, sorted[i]);
    }

    arraylist_free(arraylist);

    arraylist = arraylist_new(5);

    arraylist_sort(arraylist.as_mut().unwrap(), int_compare);

    assert_eq!(arraylist.as_ref().unwrap().length, 0);

    arraylist_free(arraylist);

    arraylist = arraylist_new(5);

    arraylist_prepend(arraylist.as_mut().unwrap(), entries[0]);
    arraylist_sort(arraylist.as_mut().unwrap(), int_compare);

    assert_eq!(arraylist.as_ref().unwrap().length, 1);
    assert_eq!(arraylist.as_ref().unwrap().data[0], entries[0]);

    arraylist_free(arraylist);
}

#[test]
pub fn test_arraylist_insert() {
    let mut arraylist = generate_arraylist::<i32>().unwrap();

    // Check for out of range insert
    assert_eq!(arraylist.length, 16);
    assert!(!arraylist_insert(&mut arraylist, 17, 1));
    assert_eq!(arraylist.length, 16);

    // Insert a new entry at index 5
    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 0);
    assert_eq!(arraylist.data[6], 0);

    assert!(arraylist_insert(&mut arraylist, 5, 4));

    assert_eq!(arraylist.length, 17);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 4);
    assert_eq!(arraylist.data[6], 0);
    assert_eq!(arraylist.data[7], 0);

    // Inserting at the start
    assert_eq!(arraylist.data[0], 0);
    assert_eq!(arraylist.data[1], 0);
    assert_eq!(arraylist.data[2], 0);

    assert!(arraylist_insert(&mut arraylist, 0, 4));

    assert_eq!(arraylist.length, 18);
    assert_eq!(arraylist.data[0], 4);
    assert_eq!(arraylist.data[1], 0);
    assert_eq!(arraylist.data[2], 0);
    assert_eq!(arraylist.data[3], 0);

    // Inserting at the end
    assert_eq!(arraylist.data[15], 0);
    assert_eq!(arraylist.data[16], 0);
    assert_eq!(arraylist.data[17], 4);

    assert!(arraylist_insert(&mut arraylist, 18, 1));

    assert_eq!(arraylist.length, 19);
    assert_eq!(arraylist.data[15], 0);
    assert_eq!(arraylist.data[16], 0);
    assert_eq!(arraylist.data[17], 4);
    assert_eq!(arraylist.data[18], 1);

    // Test inserting many entries
    for _ in 0..10000 {
        arraylist_insert(&mut arraylist, 10, 1);
    }

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_prepend() {
    let mut arraylist = arraylist_new(0).unwrap();

    assert_eq!(arraylist.length, 0);

    let variable1 = 1;
    let variable2 = 2;
    let variable3 = 3;
    let variable4 = 4;

    assert!(arraylist_prepend(&mut arraylist, variable1));
    assert_eq!(arraylist.length, 1);

    assert!(arraylist_prepend(&mut arraylist, variable2));
    assert_eq!(arraylist.length, 2);

    assert!(arraylist_prepend(&mut arraylist, variable3));
    assert_eq!(arraylist.length, 3);

    assert!(arraylist_prepend(&mut arraylist, variable4));
    assert_eq!(arraylist.length, 4);

    assert_eq!(arraylist.data[0], variable4);
    assert_eq!(arraylist.data[1], variable3);
    assert_eq!(arraylist.data[2], variable2);
    assert_eq!(arraylist.data[3], variable1);

    for _ in 0..10000 {
        assert!(arraylist_prepend(&mut arraylist, 0));
    }

    arraylist_free(Some(arraylist));

    let mut arraylist = arraylist_new(100).unwrap();

    for _ in 0..100 {
        assert!(arraylist_prepend(&mut arraylist, 0));
    }

    assert_eq!(arraylist.length, 100);
    assert!(!arraylist_prepend(&mut arraylist, 0));
    assert_eq!(arraylist.length, 100);

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_index_of() {
    let entries = vec![89, 4, 23, 42, 16, 15, 8, 99, 50, 30];
    let num_entries = entries.len();
    let mut arraylist = arraylist_new::<i32>(0).unwrap();

    for i in 0..num_entries {
        arraylist_append(&mut arraylist, entries[i]);
    }

    for i in 0..num_entries {
        let val = entries[i];
        let index = arraylist_index_of(&arraylist, int_equal, &val);
        assert_eq!(index, i as i32);
    }

    let val = 0;
    assert!(arraylist_index_of(&arraylist, int_equal, &val) < 0);
    let val = 57;
    assert!(arraylist_index_of(&arraylist, int_equal, &val) < 0);

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_clear() {
    let mut arraylist = arraylist_new(0).unwrap();

    // Emptying an already-empty arraylist
    arraylist_clear(&mut arraylist);
    assert_eq!(arraylist.length, 0);

    // Add some items and then empty it
    let variable1 = 1;
    let variable2 = 2;
    let variable3 = 3;
    let variable4 = 4;

    arraylist_append(&mut arraylist, variable1);
    arraylist_append(&mut arraylist, variable2);
    arraylist_append(&mut arraylist, variable3);
    arraylist_append(&mut arraylist, variable4);

    arraylist_clear(&mut arraylist);

    assert_eq!(arraylist.length, 0);

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_remove() {
    let mut arraylist = generate_arraylist::<i32>().expect("Failed to generate arraylist");

    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[3], 0);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 0);
    assert_eq!(arraylist.data[6], 0);

    arraylist_remove(&mut arraylist, 4);

    assert_eq!(arraylist.length, 15);
    assert_eq!(arraylist.data[3], 0);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 0);
    assert_eq!(arraylist.data[6], 0);

    // Try some invalid removes
    arraylist_remove(&mut arraylist, 15);

    assert_eq!(arraylist.length, 15);

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_remove_range() {
    let mut arraylist = generate_arraylist::<i32>().expect("Failed to generate arraylist");

    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[3], 0);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 0);
    assert_eq!(arraylist.data[6], 0);

    arraylist_remove_range(&mut arraylist, 4, 3);

    assert_eq!(arraylist.length, 13);
    assert_eq!(arraylist.data[3], 0);
    assert_eq!(arraylist.data[4], 0);
    assert_eq!(arraylist.data[5], 0);
    assert_eq!(arraylist.data[6], 0);

    // Try some invalid ones and check they don't do anything
    arraylist_remove_range(&mut arraylist, 10, 10);
    arraylist_remove_range(&mut arraylist, 0, 16);

    assert_eq!(arraylist.length, 13);

    arraylist_free(Some(arraylist));
}

#[test]
pub fn test_arraylist_append() {
    let mut arraylist = arraylist_new(0).unwrap();

    assert_eq!(arraylist.length, 0);

    let variable1 = 1;
    let variable2 = 2;
    let variable3 = 3;
    let variable4 = 4;

    assert!(arraylist_append(&mut arraylist, variable1));
    assert_eq!(arraylist.length, 1);

    assert!(arraylist_append(&mut arraylist, variable2));
    assert_eq!(arraylist.length, 2);

    assert!(arraylist_append(&mut arraylist, variable3));
    assert_eq!(arraylist.length, 3);

    assert!(arraylist_append(&mut arraylist, variable4));
    assert_eq!(arraylist.length, 4);

    assert_eq!(arraylist.data[0], variable1);
    assert_eq!(arraylist.data[1], variable2);
    assert_eq!(arraylist.data[2], variable3);
    assert_eq!(arraylist.data[3], variable4);

    for _ in 0..10000 {
        assert!(arraylist_append(&mut arraylist, 0));
    }

    arraylist_free(Some(arraylist));

    let mut arraylist = arraylist_new(100).unwrap();

    for _ in 0..100 {
        assert!(arraylist_append(&mut arraylist, 0));
    }

    assert_eq!(arraylist.length, 100);
    assert!(arraylist_append(&mut arraylist, 0));
    assert_eq!(arraylist.length, 101);

    arraylist_free(Some(arraylist));
}

fn int_compare(value1: &i32, value2: &i32) -> i32 {
    if value1 < value2 {
        -1
    } else if value1 > value2 {
        1
    } else {
        0
    }
}

pub fn int_equal(value1: &i32, value2: &i32) -> i32 {
    if value1 == value2 {
        1
    } else {
        0
    }
}
