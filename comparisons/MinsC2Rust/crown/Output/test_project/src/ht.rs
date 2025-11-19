use std::rc::Rc;
use std::cell::RefCell;
use std::fmt;

const INITIAL_CAPACITY: usize = 16;

#[derive(Debug)]
pub struct HtEntry<T> {
    pub key: Option<String>,
    pub value: Option<T>,
}

#[derive(Debug)]
pub struct Ht<T> {
    pub entries: Vec<Rc<RefCell<HtEntry<T>>>>,
    pub capacity: usize,
    pub length: usize,
}

pub struct HtIterator<T> {
    pub key: Option<String>,
    pub value: Option<T>,
    pub _table: Rc<RefCell<Ht<T>>>,
    pub _index: usize,
}

pub fn hash_key(key: String) -> u64 {
    let mut hash: u64 = 14695981039346656037;
    for c in key.chars() {
        hash ^= c as u64;
        hash = hash.wrapping_mul(1099511628211);
    }
    hash
}

pub fn ht_set_entry<T>(entries: &mut Vec<Rc<RefCell<HtEntry<T>>>>, capacity: usize, key: String, value: T, plength: &mut usize) -> Option<String> {
    let hash = hash_key(key.clone());
    let mut index = (hash & (capacity as u64 - 1)) as usize;

    loop {
        let entry = entries[index].borrow();
        if let Some(existing_key) = &entry.key {
            if *existing_key == key {
                entries[index].borrow_mut().value = Some(value);
                return Some(existing_key.clone());
            }
            index += 1;
            if index >= capacity {
                index = 0;
            }
        } else {
            break;
        }
    }

    if *plength != 0 {
        *plength += 1;
    }
    entries[index].borrow_mut().key = Some(key.clone());
    entries[index].borrow_mut().value = Some(value);
    Some(key)
}

pub fn ht_expand<T: Clone>(entries: &mut Vec<Rc<RefCell<HtEntry<T>>>>, capacity: &mut usize, length: &mut usize) -> bool {
    let new_capacity = *capacity * 2;
    if new_capacity < *capacity {
        return false;  // overflow (capacity would be too big)
    }

    let mut new_entries = Vec::with_capacity(new_capacity);
    for _ in 0..new_capacity {
        new_entries.push(Rc::new(RefCell::new(HtEntry { key: None, value: None })));
    }

    for i in 0..*capacity {
        let entry = entries[i].borrow();
        if let Some(key) = &entry.key {
            let value = entry.value.as_ref().unwrap().clone();
            ht_set_entry(&mut new_entries, new_capacity, key.clone(), value, length);
        }
    }

    *entries = new_entries;
    *capacity = new_capacity;
    true
}

pub fn ht_destroy<T>(table: Ht<T>) {
    // First free allocated keys.
    for i in 0..table.capacity {
        let mut entry = table.entries[i].borrow_mut();
        entry.key = None;
    }

    // Then free entries array and table itself.
    // Rust's ownership system will automatically handle the cleanup of the Vec and Ht struct.
}

pub fn ht_create<T>() -> Ht<T> {
    let mut table = Ht {
        entries: Vec::with_capacity(INITIAL_CAPACITY),
        capacity: INITIAL_CAPACITY,
        length: 0,
    };
    for _ in 0..INITIAL_CAPACITY {
        table.entries.push(Rc::new(RefCell::new(HtEntry {
            key: None,
            value: None,
        })));
    }
    table
}

pub fn ht_set<T: Clone>(table: &mut Ht<T>, key: String, value: T) -> Option<String> {
    if table.length >= table.capacity / 2 {
        if !ht_expand(&mut table.entries, &mut table.capacity, &mut table.length) {
            return None;
        }
    }
    ht_set_entry(&mut table.entries, table.capacity, key, value, &mut table.length)
}

pub fn ht_length<T>(table: &Ht<T>) -> usize {
    table.length
}

pub fn ht_get<T: Clone>(table: &Ht<T>, key: String) -> Option<Rc<RefCell<T>>> {
    let hash = hash_key(key.clone());
    let mut index = (hash & (table.capacity as u64 - 1)) as usize;

    while table.entries[index].borrow().key.is_some() {
        if table.entries[index].borrow().key.as_ref().unwrap() == &key {
            let value = table.entries[index].borrow().value.as_ref().unwrap().clone();
            return Some(Rc::new(RefCell::new(value)));
        }
        index += 1;
        if index >= table.capacity {
            index = 0;
        }
    }
    None
}

pub fn ht_iterator<T>(table: Rc<RefCell<Ht<T>>>) -> HtIterator<T> {
    HtIterator {
        key: None,
        value: None,
        _table: table,
        _index: 0,
    }
}

pub fn ht_next<T: Clone>(mut it: HtIterator<T>) -> (bool, HtIterator<T>) {
    let table = Rc::clone(&it._table);
    let mut table_borrow = table.borrow_mut();
    while it._index < table_borrow.capacity {
        let i = it._index;
        it._index += 1;
        if let Some(entry) = &table_borrow.entries[i].borrow().key {
            let entry_borrow = table_borrow.entries[i].borrow();
            it.key = entry_borrow.key.clone();
            it.value = entry_borrow.value.as_ref().map(|v| v.clone());
            return (true, it);
        }
    }
    (false, it)
}

