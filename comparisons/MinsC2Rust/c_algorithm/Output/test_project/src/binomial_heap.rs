use std::cell::RefCell;
use std::rc::Rc;

#[derive(Clone)]
pub enum BinomialHeapType {
    Min,
    Max,
}

pub struct BinomialTree<T> {
    pub value: T,
    pub order: u16,
    pub refcount: u16,
    pub subtrees: Vec<Rc<RefCell<BinomialTree<T>>>>,
}

pub struct BinomialHeap<T> {
    pub heap_type: BinomialHeapType,
    pub compare_func: fn(&T, &T) -> i32,
    pub trees: Vec<Rc<RefCell<BinomialTree<T>>>>,
}

pub const NUM_TEST_VALUES: usize = 10000;
pub const TEST_VALUE: usize = NUM_TEST_VALUES / 2;
pub fn binomial_tree_unref<T>(tree: Rc<RefCell<BinomialTree<T>>>) {
    let mut tree = tree.borrow_mut();

    if tree.refcount == 0 {
        return;
    }

    tree.refcount -= 1;

    if tree.refcount == 0 {
        for subtree in &tree.subtrees {
            binomial_tree_unref(Rc::clone(subtree));
        }

        tree.subtrees.clear();
    }
}

pub fn binomial_heap_cmp<T>(heap: &BinomialHeap<T>, data1: &T, data2: &T) -> i32 {
    match heap.heap_type {
        BinomialHeapType::Min => (heap.compare_func)(data1, data2),
        BinomialHeapType::Max => -((heap.compare_func)(data1, data2)),
    }
}

pub fn binomial_tree_ref<T>(tree: Option<Rc<RefCell<BinomialTree<T>>>>) {
    if let Some(tree) = tree {
        tree.borrow_mut().refcount += 1;
    }
}

pub fn binomial_heap_merge_undo<T>(new_roots: Vec<Rc<RefCell<BinomialTree<T>>>>, count: usize) {
    for i in 0..=count {
        binomial_tree_unref(Rc::clone(&new_roots[i]));
    }
}

pub fn binomial_tree_merge<T: Clone>(
    heap: &BinomialHeap<T>,
    tree1: Rc<RefCell<BinomialTree<T>>>,
    tree2: Rc<RefCell<BinomialTree<T>>>,
) -> Option<Rc<RefCell<BinomialTree<T>>>> {
    let mut tree1 = tree1;
    let mut tree2 = tree2;

    if binomial_heap_cmp(heap, &tree1.borrow().value, &tree2.borrow().value) > 0 {
        std::mem::swap(&mut tree1, &mut tree2);
    }

    let new_tree = Rc::new(RefCell::new(BinomialTree {
        value: tree1.borrow().value.clone(),
        order: tree1.borrow().order + 1,
        refcount: 0,
        subtrees: Vec::with_capacity((tree1.borrow().order + 1) as usize),
    }));

    let mut subtrees = Vec::with_capacity((tree1.borrow().order + 1) as usize);
    for subtree in &tree1.borrow().subtrees {
        subtrees.push(Rc::clone(subtree));
    }
    subtrees.push(Rc::clone(&tree2));

    new_tree.borrow_mut().subtrees = subtrees;

    for subtree in &new_tree.borrow().subtrees {
        binomial_tree_ref(Some(Rc::clone(subtree)));
    }

    Some(new_tree)
}

pub fn binomial_heap_merge<T: Clone>(heap: &mut BinomialHeap<T>, other: &BinomialHeap<T>) -> bool {
    let max = if heap.trees.len() > other.trees.len() {
        heap.trees.len() + 1
    } else {
        other.trees.len() + 1
    };

    let mut new_roots: Vec<Rc<RefCell<BinomialTree<T>>>> = Vec::with_capacity(max);
    let mut new_roots_length = 0;
    let mut carry: Option<Rc<RefCell<BinomialTree<T>>>> = None;

    for i in 0..max {
        let mut vals: Vec<Rc<RefCell<BinomialTree<T>>>> = Vec::new();

        if i < heap.trees.len() && heap.trees[i].borrow().refcount > 0 {
            vals.push(Rc::clone(&heap.trees[i]));
        }

        if i < other.trees.len() && other.trees[i].borrow().refcount > 0 {
            vals.push(Rc::clone(&other.trees[i]));
        }

        if carry.is_some() {
            vals.push(Rc::clone(carry.as_ref().unwrap()));
        }

        if (vals.len() & 1) != 0 {
            new_roots.push(Rc::clone(&vals[vals.len() - 1]));
            binomial_tree_ref(Some(Rc::clone(&new_roots[i])));
            new_roots_length = i + 1;
        } else {
            new_roots.push(Rc::new(RefCell::new(BinomialTree {
                value: unsafe { std::mem::zeroed() },
                order: 0,
                refcount: 0,
                subtrees: Vec::new(),
            })));
        }

        let new_carry = if (vals.len() & 2) != 0 {
            let merged = binomial_tree_merge(heap, Rc::clone(&vals[0]), Rc::clone(&vals[1]));
            if merged.is_none() {
                binomial_heap_merge_undo(new_roots, i);
                binomial_tree_unref(carry.unwrap());
                return false;
            }
            merged
        } else {
            None
        };

        if carry.is_some() {
            binomial_tree_unref(carry.unwrap());
        }

        carry = new_carry;
        if carry.is_some() {
            binomial_tree_ref(carry.clone());
        }
    }

    for i in 0..heap.trees.len() {
        if heap.trees[i].borrow().refcount > 0 {
            binomial_tree_unref(Rc::clone(&heap.trees[i]));
        }
    }

    heap.trees = new_roots.into_iter().collect();
    heap.trees.truncate(new_roots_length);

    true
}

pub fn binomial_heap_new<T>(
    heap_type: BinomialHeapType,
    compare_func: fn(&T, &T) -> i32,
) -> Option<BinomialHeap<T>> {
    let new_heap = BinomialHeap {
        heap_type,
        compare_func,
        trees: Vec::new(),
    };

    Some(new_heap)
}

pub fn binomial_heap_insert<T: Clone>(heap: &mut BinomialHeap<T>, value: T) -> bool {
    let new_tree = Rc::new(RefCell::new(BinomialTree {
        value: value.clone(),
        order: 0,
        refcount: 1,
        subtrees: Vec::new(),
    }));

    let mut fake_heap = BinomialHeap {
        heap_type: heap.heap_type.clone(),
        compare_func: heap.compare_func,
        trees: vec![Rc::clone(&new_tree)],
    };

    let result = binomial_heap_merge(heap, &fake_heap);

    if result {
        binomial_tree_unref(Rc::clone(&new_tree));
    }

    result
}

pub fn binomial_heap_num_entries<T>(heap: &BinomialHeap<T>) -> usize {
    heap.trees
        .iter()
        .map(|tree| tree.borrow().refcount as usize)
        .sum()
}

pub fn binomial_heap_pop<T: Clone>(heap: &mut BinomialHeap<T>) -> Option<T> {
    if heap.trees.is_empty() {
        return None;
    }

    let mut least_index = 0;
    let mut least_tree = Rc::clone(&heap.trees[least_index]);

    for i in 1..heap.trees.len() {
        if heap.trees[i].borrow().refcount == 0 {
            continue;
        }

        if binomial_heap_cmp(
            heap,
            &heap.trees[i].borrow().value,
            &least_tree.borrow().value,
        ) < 0
        {
            least_index = i;
            least_tree = Rc::clone(&heap.trees[i]);
        }
    }

    let mut fake_heap = BinomialHeap {
        heap_type: heap.heap_type.clone(),
        compare_func: heap.compare_func,
        trees: Vec::new(),
    };

    for subtree in &least_tree.borrow().subtrees {
        fake_heap.trees.push(Rc::clone(subtree));
    }

    if binomial_heap_merge(heap, &fake_heap) {
        let result = least_tree.borrow().value.clone();
        binomial_tree_unref(Rc::clone(&least_tree));
        Some(result)
    } else {
        heap.trees[least_index] = least_tree;
        None
    }
}

pub fn binomial_heap_free<T>(heap: BinomialHeap<T>) {
    let mut heap = heap;

    for tree in heap.trees.iter() {
        binomial_tree_unref(Rc::clone(tree));
    }
}
