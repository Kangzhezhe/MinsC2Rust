use std::collections::HashMap;
use std::rc::Rc;
use std::cell::RefCell;

pub struct TrieNode<T> {
    pub data: Option<T>,
    pub use_count: usize,
    pub next: HashMap<u8, Rc<RefCell<TrieNode<T>>>>,
}

pub struct Trie<T> {
    pub root_node: Rc<RefCell<TrieNode<T>>>,
}

impl<T> Trie<T> {
    pub fn new() -> Self {
        Trie {
            root_node: Rc::new(RefCell::new(TrieNode {
                data: None,
                use_count: 0,
                next: HashMap::new(),
            })),
        }
    }
}

pub fn trie_insert_rollback<T>(trie: &mut Trie<T>, key: &[u8]) {
    let mut node = Rc::clone(&trie.root_node);
    let mut prev_ptr = Rc::clone(&trie.root_node);
    let mut p = 0;

    while !node.borrow().next.is_empty() {
        let next_prev_ptr = {
            let node_borrow = node.borrow();
            let next_node = node_borrow.next.get(&key[p]).map(Rc::clone);
            p += 1;
            next_node
        };

        if let Some(next_node) = next_prev_ptr {
            node.borrow_mut().use_count -= 1;

            if node.borrow().use_count == 0 {
                let key_to_remove = key[p - 1];
                let mut prev_node_borrow = prev_ptr.borrow_mut();
                if let Some(prev_node) = prev_node_borrow.next.get_mut(&key_to_remove) {
                    *prev_node = Rc::new(RefCell::new(TrieNode {
                        data: None,
                        use_count: 0,
                        next: HashMap::new(),
                    }));
                }
            }

            prev_ptr = Rc::clone(&node);
            node = next_node;
        } else {
            break;
        }
    }
}

pub fn trie_find_end_binary<T>(trie: &Trie<T>, key: &[u8], key_length: usize) -> Option<Rc<RefCell<TrieNode<T>>>> {
    let mut node = Some(trie.root_node.clone());

    for j in 0..key_length {
        if let Some(current_node) = node {
            let c = key[j];
            let next_node = current_node.borrow().next.get(&c).cloned();
            node = next_node;
        } else {
            return None;
        }
    }

    node
}

pub fn trie_find_end<T>(trie: &Trie<T>, key: &str) -> Option<Rc<RefCell<TrieNode<T>>>> {
    let mut node = Rc::clone(&trie.root_node);
    let mut p = key.as_bytes().iter();

    while let Some(&c) = p.next() {
        let next_node = {
            let node_ref = node.borrow();
            node_ref.next.get(&c).map(|n| Rc::clone(n))
        };

        if let Some(next) = next_node {
            node = next;
        } else {
            return None;
        }
    }

    Some(node)
}

pub fn trie_new<T>() -> Option<Trie<T>> {
    Some(Trie {
        root_node: Rc::new(RefCell::new(TrieNode {
            data: None,
            use_count: 0,
            next: HashMap::new(),
        })),
    })
}

pub fn trie_insert_binary<T: Clone + PartialEq>(trie: &mut Trie<T>, key: &[u8], key_length: usize, value: T) -> bool {
    if let None = Some(&value) {
        return false;
    }

    let node = trie_find_end_binary(trie, key, key_length);

    if let Some(node) = node {
        if node.borrow().data.is_some() {
            node.borrow_mut().data = Some(value);
            return true;
        }
    }

    let mut rover = Rc::clone(&trie.root_node);
    let mut p = 0;

    loop {
        let new_node = {
            let mut node = rover.borrow_mut();

            if node.next.is_empty() {
                let new_node = Rc::new(RefCell::new(TrieNode {
                    data: None,
                    use_count: 0,
                    next: HashMap::new(),
                }));

                node.next.insert(key[p], new_node.clone());
                new_node
            } else {
                node.next.get(&key[p]).unwrap().clone()
            }
        };

        new_node.borrow_mut().use_count += 1;

        if p == key_length {
            new_node.borrow_mut().data = Some(value);
            break;
        }

        rover = new_node;
        p += 1;
    }

    true
}

pub fn trie_free_list_push<T: Clone>(list: &mut Option<Rc<RefCell<TrieNode<T>>>>, node: Rc<RefCell<TrieNode<T>>>) {
    let data = list.take().and_then(|n| n.borrow().data.clone());
    {
        let mut node_borrow = node.borrow_mut();
        node_borrow.data = data;
    }
    *list = Some(node);
}

pub fn trie_free_list_pop<T>(list: &mut Option<Rc<RefCell<TrieNode<T>>>>) -> Option<Rc<RefCell<TrieNode<T>>>> {
    if let Some(node) = list.take() {
        let mut node_ref = node.borrow_mut();
        *list = node_ref.data.take().map(|data| Rc::new(RefCell::new(TrieNode {
            data: Some(data),
            use_count: 0,
            next: HashMap::new(),
        })));
        Some(node.clone())
    } else {
        None
    }
}

pub fn trie_insert<T: Clone + PartialEq>(trie: &mut Trie<T>, key: &str, value: T) -> bool {
    if let Some(node) = trie_find_end(trie, key) {
        if node.borrow().data.is_some() {
            node.borrow_mut().data = Some(value);
            return true;
        }
    }

    let mut node = Rc::clone(&trie.root_node);
    let mut p = key.as_bytes().iter();

    loop {
        let c = if let Some(&c) = p.next() {
            c
        } else {
            node.borrow_mut().data = Some(value);
            break;
        };

        let next_node = {
            let mut node_borrow = node.borrow_mut();
            node_borrow.next.entry(c).or_insert_with(|| {
                Rc::new(RefCell::new(TrieNode {
                    data: None,
                    use_count: 0,
                    next: HashMap::new(),
                }))
            }).clone()
        };

        node.borrow_mut().use_count += 1;
        node = next_node;
    }

    true
}

pub fn trie_num_entries<T>(trie: &Trie<T>) -> usize {
    if Rc::ptr_eq(&trie.root_node, &Rc::new(RefCell::new(TrieNode {
        data: None,
        use_count: 0,
        next: HashMap::new(),
    }))) {
        0
    } else {
        trie.root_node.borrow().use_count
    }
}

pub fn trie_remove_binary<T>(trie: &Trie<T>, key: &[u8], key_length: usize) -> bool {
    let mut node = trie_find_end_binary(trie, key, key_length);

    if let Some(end_node) = node {
        let mut end_node = end_node.borrow_mut();
        if end_node.data.is_some() {
            end_node.data = None;
        } else {
            return false;
        }
    } else {
        return false;
    }

    let mut node = Some(trie.root_node.clone());
    let mut last_next_ptr: Option<Rc<RefCell<TrieNode<T>>>> = None;
    let mut p = 0;

    loop {
        if let Some(current_node) = node {
            let c = key[p];
            let next_node = current_node.borrow().next.get(&c).cloned();

            {
                let mut current_node = current_node.borrow_mut();
                current_node.use_count -= 1;

                if current_node.use_count == 0 {
                    if let Some(ref last_next) = last_next_ptr {
                        let mut last_next = last_next.borrow_mut();
                        last_next.next.remove(&c);
                    }
                }
            }

            if p == key_length {
                break;
            } else {
                p += 1;
            }

            last_next_ptr = Some(current_node.clone());

            node = next_node;
        } else {
            break;
        }
    }

    true
}

pub fn trie_lookup_binary<T: Clone>(trie: &Trie<T>, key: &[u8], key_length: usize) -> Option<T> {
    let node = trie_find_end_binary(trie, key, key_length);

    if let Some(node) = node {
        let node_ref = node.borrow();
        node_ref.data.clone()
    } else {
        None
    }
}

pub fn trie_free<T: Clone>(trie: Trie<T>) {
    let mut free_list: Option<Rc<RefCell<TrieNode<T>>>> = None;

    // Start with the root node
    if trie.root_node.borrow().use_count > 0 {
        trie_free_list_push(&mut free_list, trie.root_node.clone());
    }

    // Go through the free list, freeing nodes. We add new nodes as
    // we encounter them; in this way, all the nodes are freed
    // non-recursively.
    while let Some(node) = trie_free_list_pop(&mut free_list) {
        let mut node_borrow = node.borrow_mut();

        // Add all children of this node to the free list
        for (_, child) in node_borrow.next.drain() {
            if child.borrow().use_count > 0 {
                trie_free_list_push(&mut free_list, child);
            }
        }

        // Free the node by dropping it
        node_borrow.use_count = 0;
    }

    // The trie itself is automatically dropped when it goes out of scope
}

pub fn trie_remove<T>(trie: &Trie<T>, key: &str) -> bool {
    let node = trie_find_end(trie, key);

    if let Some(node) = node {
        let mut node_ref = node.borrow_mut();
        if node_ref.data.is_some() {
            node_ref.data = None;
        } else {
            return false;
        }
    } else {
        return false;
    }

    let mut node = Rc::clone(&trie.root_node);
    let mut last_next_ptr: Option<Rc<RefCell<TrieNode<T>>>> = None;
    let mut p = key.as_bytes().iter();

    loop {
        let c = if let Some(&c) = p.next() { c } else { break };

        let next_node = {
            let node_ref = node.borrow();
            node_ref.next.get(&c).map(|n| Rc::clone(n))
        };

        if let Some(next) = next_node {
            {
                let mut node_ref = node.borrow_mut();
                node_ref.use_count -= 1;

                if node_ref.use_count == 0 {
                    if let Some(last_next) = &last_next_ptr {
                        let mut last_next_ref = last_next.borrow_mut();
                        last_next_ref.next.remove(&c);
                    }
                }
            }

            last_next_ptr = Some(Rc::clone(&node));
            node = next;
        } else {
            break;
        }
    }

    true
}

pub fn trie_lookup<T>(trie: &Trie<T>, key: &str) -> Option<T>
where
    T: Clone,
{
    let node = trie_find_end(trie, key);

    if let Some(node) = node {
        let node_ref = node.borrow();
        node_ref.data.clone()
    } else {
        None
    }
}

