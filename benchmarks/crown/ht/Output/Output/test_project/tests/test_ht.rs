use ntest::timeout;
use std::cell::RefCell;
use std::rc::Rc;
use test_project::ht::{
    hash_key, ht_create, ht_destroy, ht_expand, ht_get, ht_iterator, ht_length, ht_next, ht_set,
    ht_set_entry, Ht, HtEntry, HtIterator,
};
#[test]
#[timeout(60000)]
pub fn test_ht_update_value() {
    let mut table = ht_create::<i32>();

    // Insert a key-value pair
    let value1 = 42;
    let key = String::from("key");
    assert!(ht_set(&mut table, key.clone(), value1).is_some());

    // Update the value for the same key
    let value2 = 84;
    assert!(ht_set(&mut table, key.clone(), value2).is_some());

    // Retrieve the updated value
    let retrieved_value = ht_get(&table, key.clone());
    assert!(retrieved_value.is_some());
    assert_eq!(*retrieved_value.unwrap().borrow(), value2);

    // Check the length of the hash table (should still be 1)
    assert_eq!(ht_length(&table), 1);

    ht_destroy(table);
}

#[test]
#[timeout(60000)]
pub fn test_ht_memory_management() {
    let mut table = ht_create::<Rc<RefCell<i32>>>();

    let value1 = Rc::new(RefCell::new(42));
    let value2 = Rc::new(RefCell::new(84));

    assert!(ht_set(&mut table, "key1".to_string(), Rc::clone(&value1)).is_some());
    assert!(ht_set(&mut table, "key2".to_string(), Rc::clone(&value2)).is_some());

    let mut it = ht_iterator(Rc::new(RefCell::new(table)));
    loop {
        let (has_next, new_it) = ht_next(it);
        it = new_it;
        if !has_next {
            break;
        }
    }

    let table = Rc::try_unwrap(it._table).unwrap().into_inner();
    ht_destroy(table);
}

#[test]
#[timeout(60000)]
pub fn test_ht_set_and_get() {
    let mut table = ht_create::<i32>();

    // Insert a key-value pair
    let value1 = 42;
    let key1 = String::from("key1");
    assert!(ht_set(&mut table, key1.clone(), value1).is_some());

    // Retrieve the value
    let retrieved_value = ht_get(&table, key1.clone());
    assert!(retrieved_value.is_some());
    assert_eq!(*retrieved_value.unwrap().borrow(), value1);

    // Insert another key-value pair
    let value2 = 84;
    let key2 = String::from("key2");
    assert!(ht_set(&mut table, key2.clone(), value2).is_some());

    // Retrieve the second value
    let retrieved_value = ht_get(&table, key2.clone());
    assert!(retrieved_value.is_some());
    assert_eq!(*retrieved_value.unwrap().borrow(), value2);

    // Check the length of the hash table
    assert_eq!(ht_length(&table), 2);

    ht_destroy(table);
}

#[test]
#[timeout(60000)]
pub fn test_ht_create_and_destroy() {
    let mut table = ht_create::<i32>();
    assert_eq!(ht_length(&table), 0);
    ht_destroy(table);
}

#[test]
#[timeout(60000)]
pub fn test_ht_iterator() {
    let mut table = ht_create();
    let value1 = 1;
    let value2 = 2;
    let value3 = 3;
    assert!(ht_set(&mut table, "key1".to_string(), value1).is_some());
    assert!(ht_set(&mut table, "key2".to_string(), value2).is_some());
    assert!(ht_set(&mut table, "key3".to_string(), value3).is_some());

    let it = ht_iterator(Rc::new(RefCell::new(table)));
    let mut count = 0;
    let mut it = it;
    loop {
        let (has_next, new_it) = ht_next(it);
        it = new_it;
        if !has_next {
            break;
        }
        assert!(it.key.is_some());
        assert!(it.value.is_some());
        count += 1;
    }

    assert_eq!(count, 3);

    let table = it._table.borrow();
    let table_clone = Ht {
        entries: table.entries.clone(),
        capacity: table.capacity,
        length: table.length,
    };
    ht_destroy(table_clone);
}
