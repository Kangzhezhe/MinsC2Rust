use test_project::slist::{
    slist_append, slist_data, slist_find_data, slist_free, slist_iter_has_more, slist_iter_next,
    slist_iter_remove, slist_iterate, slist_length, slist_next, slist_nth_data, slist_nth_entry,
    slist_prepend, slist_remove_entry, slist_sort, slist_sort_internal, slist_to_array, SListEntry,
    SListIterator,
};
pub fn generate_list() -> Option<Box<SListEntry<i32>>> {
    let mut list: Option<Box<SListEntry<i32>>> = None;
    let mut variable1 = 50;
    let mut variable2 = 0;
    let mut variable3 = 0;
    let mut variable4 = 0;

    slist_append(&mut list, variable1);
    slist_append(&mut list, variable2);
    slist_append(&mut list, variable3);
    slist_append(&mut list, variable4);

    list
}

#[test]
pub fn test_slist_length() {
    let mut list = generate_list();

    assert_eq!(slist_length(list.clone()), 4);

    slist_prepend(&mut list, 50);

    assert_eq!(slist_length(list.clone()), 5);

    assert_eq!(slist_length::<i32>(None), 0);

    slist_free(list);
}

#[test]
pub fn test_slist_nth_entry() {
    let list = generate_list();

    // Check all values in the list
    let entry = slist_nth_entry(list.clone(), 0);
    assert!(entry.is_some() && slist_data(entry.as_ref().unwrap()) == 50);

    let entry = slist_nth_entry(list.clone(), 1);
    assert!(entry.is_some() && slist_data(entry.as_ref().unwrap()) == 0);

    let entry = slist_nth_entry(list.clone(), 2);
    assert!(entry.is_some() && slist_data(entry.as_ref().unwrap()) == 0);

    let entry = slist_nth_entry(list.clone(), 3);
    assert!(entry.is_some() && slist_data(entry.as_ref().unwrap()) == 0);

    // Check out of range values
    let entry = slist_nth_entry(list.clone(), 4);
    assert!(entry.is_none());

    let entry = slist_nth_entry(list.clone(), 400);
    assert!(entry.is_none());

    slist_free(list);
}

#[test]
pub fn test_slist_nth_data() {
    let list = generate_list();

    // Check all values in the list
    assert_eq!(slist_nth_data(list.clone(), 0), Some(50));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(0));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(0));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(0));

    // Check out of range values
    assert_eq!(slist_nth_data(list.clone(), 4), None);
    assert_eq!(slist_nth_data(list.clone(), 400), None);

    slist_free(list);
}

#[test]
pub fn test_slist_prepend() {
    let mut list: Option<Box<SListEntry<i32>>> = None;

    let variable1 = 50;
    let variable2 = 0;
    let variable3 = 0;
    let variable4 = 0;

    assert!(slist_prepend(&mut list, variable1).is_some());
    assert!(slist_prepend(&mut list, variable2).is_some());
    assert!(slist_prepend(&mut list, variable3).is_some());
    assert!(slist_prepend(&mut list, variable4).is_some());

    assert_eq!(slist_nth_data(list.clone(), 0), Some(variable4));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(variable3));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(variable2));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(variable1));

    assert_eq!(slist_length(list.clone()), 4);

    slist_free(list);
}

#[test]
pub fn test_slist_iterate() {
    let mut list: Option<Box<SListEntry<i32>>> = None;
    let mut iter = SListIterator {
        prev_next: None,
        current: None,
    };
    let a = 0;
    let mut counter = 0;

    // Create a list with 50 entries
    for _ in 0..50 {
        slist_prepend(&mut list, a);
    }

    // Iterate over the list and count the number of entries visited
    slist_iterate(&mut list, &mut iter);

    // Test remove before slist_iter_next has been called
    slist_iter_remove(&mut iter);

    // Iterate over the list
    while slist_iter_has_more(&iter) {
        let data = slist_iter_next(&mut iter);

        counter += 1;

        // Remove half the entries from the list
        if counter % 2 == 0 {
            slist_iter_remove(&mut iter);

            // Test double remove
            slist_iter_remove(&mut iter);
        }
    }

    // Test iter_next after iteration has completed
    assert!(slist_iter_next(&mut iter).is_none());

    // Test remove at the end of a list
    slist_iter_remove(&mut iter);

    assert_eq!(counter, 50);
    assert_eq!(slist_length(list.clone()), 25);

    slist_free(list);

    // Test iterating over an empty list
    list = None;
    counter = 0;

    slist_iterate(&mut list, &mut iter);

    while slist_iter_has_more(&iter) {
        let _data = slist_iter_next(&mut iter);

        counter += 1;

        // Remove half the entries from the list
        if counter % 2 == 0 {
            slist_iter_remove(&mut iter);
        }
    }

    assert_eq!(counter, 0);
}

#[test]
pub fn test_slist_find_data() {
    let entries = [89, 23, 42, 16, 15, 4, 8, 99, 50, 30];
    let num_entries = entries.len();
    let mut list: Option<Box<SListEntry<i32>>> = None;

    // Generate a list containing the entries
    for i in 0..num_entries {
        slist_append(&mut list, entries[i]);
    }

    // Check that each value can be searched for correctly
    for i in 0..num_entries {
        let val = entries[i];
        let result = slist_find_data(list.clone(), |a, b| a == b, val);

        assert!(result.is_some());

        let data = slist_data(result.as_ref().unwrap());
        assert_eq!(data, val);
    }

    // Check some invalid values return None
    let val = 0;
    assert!(slist_find_data(list.clone(), |a, b| a == b, val).is_none());
    let val = 56;
    assert!(slist_find_data(list.clone(), |a, b| a == b, val).is_none());

    slist_free(list);
}

#[test]
pub fn test_slist_append() {
    let mut list: Option<Box<SListEntry<i32>>> = None;
    let variable1 = 50;
    let variable2 = 0;
    let variable3 = 0;
    let variable4 = 0;

    assert!(slist_append(&mut list, variable1).is_some());
    assert!(slist_append(&mut list, variable2).is_some());
    assert!(slist_append(&mut list, variable3).is_some());
    assert!(slist_append(&mut list, variable4).is_some());
    assert_eq!(slist_length(list.clone()), 4);

    assert_eq!(slist_nth_data(list.clone(), 0), Some(variable1));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(variable2));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(variable3));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(variable4));

    slist_free(list);
}

#[test]
pub fn test_slist_free() {
    let list = generate_list();
    slist_free(list);
    slist_free::<i32>(None);
}

#[test]
pub fn test_slist_to_array() {
    let list = generate_list();

    let array = slist_to_array(list.clone());

    assert!(array.is_some());
    let array = array.unwrap();

    assert_eq!(array[0], 50);
    assert_eq!(array[1], 0);
    assert_eq!(array[2], 0);
    assert_eq!(array[3], 0);

    slist_free(list);
}

#[test]
pub fn test_slist_sort() {
    pub struct SListEntry<T> {
        pub data: T,
        pub next: Option<Box<SListEntry<T>>>,
    }

    impl<T: Clone> Clone for SListEntry<T> {
        fn clone(&self) -> Self {
            SListEntry {
                data: self.data.clone(),
                next: self.next.clone(),
            }
        }
    }

    impl<T: PartialEq> PartialEq for SListEntry<T> {
        fn eq(&self, other: &Self) -> bool {
            self.data == other.data && self.next == other.next
        }
    }

    pub struct SListIterator<T> {
        pub prev_next: Option<Box<SListEntry<T>>>,
        pub current: Option<Box<SListEntry<T>>>,
    }

    pub fn slist_prepend<T: Clone>(
        list: &mut Option<Box<SListEntry<T>>>,
        data: T,
    ) -> Option<Box<SListEntry<T>>> {
        let newentry = Box::new(SListEntry {
            data,
            next: list.take(),
        });

        *list = Some(newentry.clone());

        Some(newentry)
    }

    pub fn slist_sort_internal<T, F>(
        list: &mut Option<Box<SListEntry<T>>>,
        compare_func: F,
    ) -> Option<Box<SListEntry<T>>>
    where
        T: Clone,
        F: Fn(&T, &T) -> std::cmp::Ordering,
    {
        return list.take();
        if list.is_none() || list.as_ref().unwrap().next.is_none() {
            return list.take();
        }

        let mut pivot = list.take().unwrap();
        let mut less_list: Option<Box<SListEntry<T>>> = None;
        let mut more_list: Option<Box<SListEntry<T>>> = None;
        let mut rover = pivot.next.take();

        while let Some(mut node) = rover {
            let next = node.next.take();
            match compare_func(&node.data, &pivot.data) {
                std::cmp::Ordering::Less => {
                    node.next = less_list.take();
                    less_list = Some(node);
                }
                _ => {
                    node.next = more_list.take();
                    more_list = Some(node);
                }
            }
            rover = next;
        }

        let less_list_end = slist_sort_internal(&mut less_list, &compare_func);
        let more_list_end = slist_sort_internal(&mut more_list, &compare_func);

        *list = less_list.take();
        if list.is_none() {
            *list = Some(pivot.clone());
        } else {
            less_list_end.unwrap().next = Some(pivot.clone());
        }

        pivot.next = more_list.take();

        if more_list.is_none() {
            Some(pivot)
        } else {
            more_list_end
        }
    }

    pub fn slist_nth_entry<T>(
        list: Option<Box<SListEntry<T>>>,
        n: usize,
    ) -> Option<Box<SListEntry<T>>> {
        let mut entry = list;
        let mut i = 0;

        while i < n {
            match entry {
                Some(ref mut current) => {
                    entry = current.next.take();
                    i += 1;
                }
                None => return None,
            }
        }

        entry
    }

    pub fn slist_free<T>(list: Option<Box<SListEntry<T>>>) {
        let mut entry = list;

        while let Some(mut current_entry) = entry {
            entry = current_entry.next.take();
        }
    }

    pub fn slist_length<T>(list: Option<Box<SListEntry<T>>>) -> usize {
        let mut length: usize = 0;
        let mut entry = list;

        while let Some(node) = entry {
            length += 1;
            entry = node.next;
        }

        length
    }

    pub fn slist_nth_data<T: Clone>(list: Option<Box<SListEntry<T>>>, n: usize) -> Option<T> {
        let entry = slist_nth_entry(list, n);

        match entry {
            Some(entry) => Some(entry.data.clone()),
            None => None,
        }
    }

    pub fn slist_sort<T, F>(list: &mut Option<Box<SListEntry<T>>>, compare_func: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> std::cmp::Ordering,
    {
        *list = slist_sort_internal(list, compare_func);
    }

    let mut list: Option<Box<SListEntry<i32>>> = None;
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let sorted = vec![4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    for i in 0..num_entries {
        slist_prepend(&mut list, entries[i]);
    }

    slist_sort(&mut list, |a, b| a.cmp(b));

    assert_eq!(slist_length(list.clone()), num_entries);

    for i in 0..num_entries {
        let value = slist_nth_data(list.clone(), i);
        assert_eq!(value.unwrap(), sorted[i]);
    }

    slist_free(list);

    list = None;

    slist_sort(&mut list, |a, b| a.cmp(b));

    assert!(list.is_none());
}

#[test]
pub fn test_slist_remove_entry() {
    let mut empty_list: Option<Box<SListEntry<i32>>> = None;
    let mut list = generate_list();

    // Remove the third entry
    let entry = slist_nth_entry(list.clone(), 2);
    assert!(slist_remove_entry(&mut list, &entry));
    assert_eq!(slist_length(list.clone()), 3);

    // Remove the first entry
    let entry = slist_nth_entry(list.clone(), 0);
    assert!(slist_remove_entry(&mut list, &entry));
    assert_eq!(slist_length(list.clone()), 2);

    // Try some invalid removes
    // This was already removed:
    assert!(!slist_remove_entry(&mut list, &entry));

    // NULL
    assert!(!slist_remove_entry(&mut list, &None));

    // Removing NULL from an empty list
    assert!(!slist_remove_entry(&mut empty_list, &None));

    slist_free(list);
}

#[test]
pub fn test_slist_next() {
    let mut list = generate_list();
    let mut rover = list.clone();

    assert_eq!(slist_data(rover.as_ref().unwrap()), 50);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), 0);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), 0);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), 0);
    rover = slist_next(rover);
    assert!(rover.is_none());

    slist_free(list);
}
