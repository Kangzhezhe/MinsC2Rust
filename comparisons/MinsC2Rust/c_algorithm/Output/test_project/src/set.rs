pub struct Set<T> {
    pub table: Vec<Option<Box<SetEntry<T>>>>,
    pub entries: usize,
    pub table_size: usize,
    pub prime_index: usize,
    pub hash_func: fn(&T) -> u32,
    pub equal_func: fn(&T, &T) -> bool,
    pub free_func: Option<fn(Box<SetValue<T>>)>,
}

#[derive(Clone)]
pub struct SetEntry<T> {
    pub value: T,
    pub next: Option<Box<SetEntry<T>>>,
}

pub const SET_NUM_PRIMES: usize = 24;
pub const SET_PRIMES: [usize; 24] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317,
    196613, 393241, 786433, 1572869, 3145739, 6291469,
    12582917, 25165843, 50331653, 100663319, 201326611,
    402653189, 805306457, 1610612741,
];

pub struct SetIterator<'a, T> {
    pub set: &'a Set<T>,
    pub next_entry: Option<Box<SetEntry<T>>>,
    pub next_chain: usize,
}

pub struct SetValue<T> {
    pub value: T,
}

pub static mut ALLOCATED_VALUES: usize = 0;
pub fn set_allocate_table<T>(set: &mut Set<T>) -> bool {
    if set.prime_index < SET_NUM_PRIMES {
        set.table_size = SET_PRIMES[set.prime_index];
    } else {
        set.table_size = set.entries * 10;
    }

    set.table = Vec::with_capacity(set.table_size);
    for _ in 0..set.table_size {
        set.table.push(None);
    }

    true
}

pub fn set_enlarge<T>(set: &mut Set<T>) -> bool {
    let mut old_table = std::mem::take(&mut set.table);
    let old_table_size = set.table_size;
    let old_prime_index = set.prime_index;

    set.prime_index += 1;

    if !set_allocate_table(set) {
        set.table = old_table;
        set.table_size = old_table_size;
        set.prime_index = old_prime_index;
        return false;
    }

    for i in 0..old_table_size {
        let mut rover = old_table[i].take();

        while let Some(mut entry) = rover {
            let next = entry.next.take();

            let hash_func = set.hash_func;
            let index = (hash_func(&entry.value) as usize) % set.table_size;
            entry.next = set.table[index].take();
            set.table[index] = Some(entry);

            rover = next;
        }
    }

    true
}

pub fn set_free_entry<T>(set: &mut Set<T>, entry: Box<SetEntry<T>>) {
    if let Some(free_func) = set.free_func {
        free_func(Box::new(SetValue { value: entry.value }));
    }
}

pub fn set_new<T>(hash_func: fn(&T) -> u32, equal_func: fn(&T, &T) -> bool) -> Option<Set<T>> {
    let mut new_set = Set {
        table: Vec::new(),
        entries: 0,
        table_size: 0,
        prime_index: 0,
        hash_func,
        equal_func,
        free_func: None,
    };

    if !set_allocate_table(&mut new_set) {
        return None;
    }

    Some(new_set)
}

pub fn set_num_entries<T>(set: &Set<T>) -> usize {
    set.entries
}

pub fn set_register_free_function<T>(set: &mut Set<T>, free_func: Option<fn(Box<SetValue<T>>)>) {
    set.free_func = free_func;
}

pub fn set_insert<T>(set: &mut Set<T>, data: T) -> bool {
    if (set.entries * 3) / set.table_size > 0 {
        if !set_enlarge(set) {
            return false;
        }
    }

    let hash_func = set.hash_func;
    let index = (hash_func(&data) as usize) % set.table_size;

    let mut rover = &mut set.table[index];

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.value) {
            return false;
        }
        rover = &mut entry.next;
    }

    let newentry = Box::new(SetEntry {
        value: data,
        next: set.table[index].take(),
    });

    set.table[index] = Some(newentry);

    set.entries += 1;

    true
}

pub fn set_query<T>(set: &Set<T>, data: T) -> bool 
where
    T: Clone + PartialEq,
{
    let index = (set.hash_func)(&data) % set.table_size as u32;

    let mut rover = &set.table[index as usize];

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.value) {
            return true;
        }
        rover = &entry.next;
    }

    false
}

pub fn set_free<T>(mut set: Box<Set<T>>) {
    for i in 0..set.table_size {
        let mut rover = set.table[i].take();

        while let Some(mut entry) = rover {
            let next = entry.next.take();
            set_free_entry(&mut set, entry);
            rover = next;
        }
    }
}

pub fn set_iter_next<T: Clone>(iterator: &mut SetIterator<T>) -> Option<T> {
    let set = &iterator.set;

    if iterator.next_entry.is_none() {
        return None;
    }

    let current_entry = iterator.next_entry.as_ref().unwrap();
    let result = current_entry.value.clone();

    if let Some(next) = &current_entry.next {
        iterator.next_entry = Some(Box::new(SetEntry {
            value: next.value.clone(),
            next: next.next.clone(),
        }));
    } else {
        iterator.next_entry = None;

        let mut chain = iterator.next_chain + 1;

        while chain < set.table_size {
            if let Some(entry) = &set.table[chain] {
                iterator.next_entry = Some(Box::new(SetEntry {
                    value: entry.value.clone(),
                    next: entry.next.clone(),
                }));
                break;
            }

            chain += 1;
        }

        iterator.next_chain = chain;
    }

    Some(result)
}

pub fn set_intersection<T: Clone + PartialEq>(
    set1: &Set<T>,
    set2: &Set<T>,
) -> Option<Set<T>> {
    let mut new_set = set_new(set1.hash_func, set2.equal_func)?;

    let mut iterator = SetIterator {
        set: set1,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&mut iterator);

    while set_iter_has_more(&iterator) {
        let value = set_iter_next(&mut iterator)?;

        if set_query(set2, value.clone()) {
            if !set_insert(&mut new_set, value) {
                set_free(Box::new(new_set));
                return None;
            }
        }
    }

    Some(new_set)
}

pub fn set_iterate<T: Clone>(iterator: &mut SetIterator<T>) {
    iterator.next_entry = None;

    for chain in 0..iterator.set.table_size {
        if let Some(entry) = &iterator.set.table[chain] {
            iterator.next_entry = Some(Box::new(SetEntry {
                value: entry.value.clone(),
                next: entry.next.clone(),
            }));
            break;
        }
    }

    iterator.next_chain = 0;
}

pub fn set_iter_has_more<T>(iterator: &SetIterator<T>) -> bool {
    iterator.next_entry.is_some()
}

pub fn set_to_array<T>(set: &Set<T>) -> Vec<T> where T: Clone {
    let mut array: Vec<T> = Vec::with_capacity(set.entries);

    for i in 0..set.table_size {
        let mut rover = set.table[i].as_ref();

        while let Some(entry) = rover {
            array.push(entry.value.clone());
            rover = entry.next.as_ref();
        }
    }

    array
}

pub fn set_union<T: Clone + PartialEq>(set1: &Set<T>, set2: &Set<T>) -> Option<Set<T>> {
    let mut new_set = set_new(set1.hash_func, set1.equal_func)?;

    let mut iterator = SetIterator {
        set: set1,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&mut iterator);

    while set_iter_has_more(&iterator) {
        let value = set_iter_next(&mut iterator).unwrap();

        if !set_insert(&mut new_set, value) {
            set_free(Box::new(new_set));
            return None;
        }
    }

    let mut iterator = SetIterator {
        set: set2,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&mut iterator);

    while set_iter_has_more(&iterator) {
        let value = set_iter_next(&mut iterator).unwrap();

        if !set_query(&new_set, value.clone()) {
            if !set_insert(&mut new_set, value) {
                set_free(Box::new(new_set));
                return None;
            }
        }
    }

    Some(new_set)
}

pub fn set_remove<T>(set: &mut Set<T>, data: T) -> bool 
where
    T: Clone + PartialEq,
{
    let index = (set.hash_func)(&data) % set.table_size as u32;

    let mut rover = &mut set.table[index as usize];

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.value) {
            let mut entry = rover.take().unwrap();
            *rover = entry.next.take();
            set.entries -= 1;
            set_free_entry(set, entry);
            return true;
        }
        rover = &mut rover.as_mut().unwrap().next;
    }

    false
}

