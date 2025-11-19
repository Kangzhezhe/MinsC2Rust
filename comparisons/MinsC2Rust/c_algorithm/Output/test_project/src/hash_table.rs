pub struct HashTablePair<K, V> {
    pub key: K,
    pub value: V,
}

impl<K: Clone, V: Clone> Clone for HashTablePair<K, V> {
    fn clone(&self) -> Self {
        HashTablePair {
            key: self.key.clone(),
            value: self.value.clone(),
        }
    }
}

pub struct HashTableEntry<K, V> {
    pub pair: HashTablePair<K, V>,
    pub next: Option<Box<HashTableEntry<K, V>>>,
}

impl<K: Clone, V: Clone> Clone for HashTableEntry<K, V> {
    fn clone(&self) -> Self {
        HashTableEntry {
            pair: self.pair.clone(),
            next: self.next.clone(),
        }
    }
}

pub struct HashTable<K, V> {
    pub table: Vec<Option<Box<HashTableEntry<K, V>>>>,
    pub table_size: usize,
    pub hash_func: fn(&K) -> u32,
    pub equal_func: fn(&K, &K) -> bool,
    pub key_free_func: Option<fn(K)>,
    pub value_free_func: Option<fn(V)>,
    pub entries: usize,
    pub prime_index: usize,
}

impl<K: Clone, V: Clone> Clone for HashTable<K, V> {
    fn clone(&self) -> Self {
        HashTable {
            table: self.table.clone(),
            table_size: self.table_size,
            hash_func: self.hash_func,
            equal_func: self.equal_func,
            key_free_func: self.key_free_func,
            value_free_func: self.value_free_func,
            entries: self.entries,
            prime_index: self.prime_index,
        }
    }
}

pub const HASH_TABLE_NUM_PRIMES: usize = 24;
pub const HASH_TABLE_PRIMES: [usize; HASH_TABLE_NUM_PRIMES] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317, 196613, 393241, 786433, 1572869,
    3145739, 6291469, 12582917, 25165843, 50331653, 100663319, 201326611, 402653189, 805306457,
    1610612741,
];

pub struct HashTableIterator<K, V> {
    pub hash_table: Box<HashTable<K, V>>,
    pub next_entry: Option<Box<HashTableEntry<K, V>>>,
    pub next_chain: usize,
}
pub fn hash_table_allocate_table<K, V>(hash_table: &mut HashTable<K, V>) -> bool {
    let new_table_size = if hash_table.prime_index < HASH_TABLE_NUM_PRIMES {
        HASH_TABLE_PRIMES[hash_table.prime_index]
    } else {
        hash_table.entries * 10
    };

    hash_table.table_size = new_table_size;

    hash_table.table = Vec::with_capacity(hash_table.table_size);
    for _ in 0..hash_table.table_size {
        hash_table.table.push(None);
    }

    true
}

pub fn hash_table_enlarge<K, V>(hash_table: &mut HashTable<K, V>) -> bool {
    let mut old_table = std::mem::take(&mut hash_table.table);
    let old_table_size = hash_table.table_size;
    let old_prime_index = hash_table.prime_index;

    hash_table.prime_index += 1;

    if !hash_table_allocate_table(hash_table) {
        hash_table.table = old_table;
        hash_table.table_size = old_table_size;
        hash_table.prime_index = old_prime_index;
        return false;
    }

    for i in 0..old_table_size {
        let mut rover = old_table[i].take();

        while let Some(mut entry) = rover {
            let next = entry.next.take();

            let pair = &entry.pair;
            let index = ((hash_table.hash_func)(&pair.key) as usize) % hash_table.table_size;

            entry.next = hash_table.table[index].take();
            hash_table.table[index] = Some(entry);

            rover = next;
        }
    }

    true
}

pub fn hash_table_free_entry<K, V>(
    hash_table: &mut HashTable<K, V>,
    entry: Box<HashTableEntry<K, V>>,
) {
    let pair = entry.pair;

    if let Some(key_free_func) = hash_table.key_free_func {
        key_free_func(pair.key);
    }

    if let Some(value_free_func) = hash_table.value_free_func {
        value_free_func(pair.value);
    }
}

pub fn hash_table_new<K, V>(
    hash_func: fn(&K) -> u32,
    equal_func: fn(&K, &K) -> bool,
) -> Option<HashTable<K, V>> {
    let mut hash_table = HashTable {
        table: Vec::new(),
        table_size: 0,
        hash_func,
        equal_func,
        key_free_func: None,
        value_free_func: None,
        entries: 0,
        prime_index: 0,
    };

    if !hash_table_allocate_table(&mut hash_table) {
        return None;
    }

    Some(hash_table)
}

pub fn hash_table_register_free_functions<K, V>(
    hash_table: &mut HashTable<K, V>,
    key_free_func: Option<fn(K)>,
    value_free_func: Option<fn(V)>,
) {
    hash_table.key_free_func = key_free_func;
    hash_table.value_free_func = value_free_func;
}

pub fn hash_table_insert<K, V>(hash_table: &mut HashTable<K, V>, key: K, value: V) -> bool {
    if (hash_table.entries * 3) / hash_table.table_size > 0 {
        if !hash_table_enlarge(hash_table) {
            return false;
        }
    }

    let index = ((hash_table.hash_func)(&key) as usize) % hash_table.table_size;

    let mut rover = &mut hash_table.table[index];

    while let Some(entry) = rover {
        if (hash_table.equal_func)(&entry.pair.key, &key) {
            if let Some(value_free_func) = hash_table.value_free_func {
                let value = std::mem::replace(&mut entry.pair.value, value);
                value_free_func(value);
            }
            if let Some(key_free_func) = hash_table.key_free_func {
                let key = std::mem::replace(&mut entry.pair.key, key);
                key_free_func(key);
            }
            return true;
        }
        rover = &mut entry.next;
    }

    let new_entry = Box::new(HashTableEntry {
        pair: HashTablePair { key, value },
        next: hash_table.table[index].take(),
    });

    hash_table.table[index] = Some(new_entry);
    hash_table.entries += 1;

    true
}

pub fn hash_table_free<K, V>(mut hash_table: HashTable<K, V>) {
    for i in 0..hash_table.table_size {
        let mut rover = hash_table.table[i].take();
        while let Some(mut entry) = rover {
            let next = entry.next.take();
            hash_table_free_entry(&mut hash_table, entry);
            rover = next;
        }
    }
}

pub fn hash_table_num_entries<K, V>(hash_table: &HashTable<K, V>) -> usize {
    hash_table.entries
}

pub fn hash_table_lookup<K, V>(hash_table: &HashTable<K, V>, key: K) -> Option<V>
where
    K: Clone + PartialEq,
    V: Clone,
{
    let index = (hash_table.hash_func)(&key) as usize % hash_table.table_size;

    let mut rover = &hash_table.table[index];

    while let Some(entry) = rover {
        let pair = &entry.pair;

        if (hash_table.equal_func)(&key, &pair.key) {
            return Some(pair.value.clone());
        }

        rover = &entry.next;
    }

    None
}

pub fn hash_table_iter_next<K: Clone, V: Clone>(
    iterator: &mut HashTableIterator<K, V>,
) -> Option<HashTablePair<K, V>> {
    let mut current_entry: Option<Box<HashTableEntry<K, V>>> = iterator.next_entry.take();
    let hash_table: &HashTable<K, V> = &iterator.hash_table;

    if current_entry.is_none() {
        return None;
    }

    let pair: HashTablePair<K, V> = current_entry.as_ref().unwrap().pair.clone();

    if let Some(next_entry) = current_entry.as_ref().unwrap().next.clone() {
        iterator.next_entry = Some(next_entry);
    } else {
        let mut chain: usize = iterator.next_chain + 1;
        iterator.next_entry = None;

        while chain < hash_table.table_size {
            if let Some(entry) = hash_table.table[chain].clone() {
                iterator.next_entry = Some(entry);
                break;
            }
            chain += 1;
        }

        iterator.next_chain = chain;
    }

    Some(pair)
}

pub fn hash_table_iter_has_more<K, V>(iterator: &HashTableIterator<K, V>) -> bool {
    iterator.next_entry.is_some()
}

pub fn hash_table_iterate<K: Clone, V: Clone>(
    hash_table: Box<HashTable<K, V>>,
    iterator: &mut HashTableIterator<K, V>,
) {
    let mut chain: usize = 0;

    iterator.hash_table = hash_table;

    iterator.next_entry = None;

    while chain < iterator.hash_table.table_size {
        if let Some(entry) = &iterator.hash_table.table[chain] {
            iterator.next_entry = Some(Box::new((**entry).clone()));
            iterator.next_chain = chain;
            break;
        }
        chain += 1;
    }
}

pub fn hash_table_remove<K, V>(hash_table: &mut HashTable<K, V>, key: K) -> bool
where
    K: Clone + PartialEq,
    V: Clone,
{
    let index = (hash_table.hash_func)(&key) as usize % hash_table.table_size;

    let mut rover = &mut hash_table.table[index];
    let mut result = false;

    while let Some(entry) = rover {
        if (hash_table.equal_func)(&key, &entry.pair.key) {
            let mut entry_to_remove = rover.take().unwrap();
            *rover = entry_to_remove.next.take();

            hash_table_free_entry(hash_table, entry_to_remove);
            hash_table.entries -= 1;
            result = true;
            break;
        }
        rover = &mut rover.as_mut().unwrap().next;
    }

    result
}
