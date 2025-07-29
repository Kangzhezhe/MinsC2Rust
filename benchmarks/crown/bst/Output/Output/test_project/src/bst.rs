use std::rc::Rc;
use std::cell::RefCell;

pub struct BstNode<T> {
    pub val: T,
    pub left: Option<Rc<RefCell<BstNode<T>>>>,
    pub right: Option<Rc<RefCell<BstNode<T>>>>,
}

pub struct Bst<T> {
    pub root: Option<Rc<RefCell<BstNode<T>>>>,
}

pub fn _bst_subtree_min_val<T: Ord + Clone>(n: Option<Rc<RefCell<BstNode<T>>>>) -> Option<T> {
    // The minimum value in any subtree is just the leftmost value. Keep going 
    // left till we get there.
    let mut current = n;
    while let Some(node) = current {
        if node.borrow().left.is_none() {
            return Some(node.borrow().val.clone());
        }
        current = node.borrow().left.clone();
    }
    None
}

pub fn _bst_subtree_remove<T: Ord + Clone>(val: T, n: Option<Rc<RefCell<BstNode<T>>>>) -> Option<Rc<RefCell<BstNode<T>>>> {
    if n.is_none() {
        return None;
    }

    let node = n.unwrap();
    let mut node_borrow = node.borrow_mut();

    if val < node_borrow.val {
        let left = node_borrow.left.take();
        node_borrow.left = _bst_subtree_remove(val, left);
        drop(node_borrow);
        return Some(node);
    } else if val > node_borrow.val {
        let right = node_borrow.right.take();
        node_borrow.right = _bst_subtree_remove(val, right);
        drop(node_borrow);
        return Some(node);
    } else {
        if node_borrow.left.is_some() && node_borrow.right.is_some() {
            let min_val = _bst_subtree_min_val(node_borrow.right.clone()).unwrap();
            node_borrow.val = min_val.clone();
            let right = node_borrow.right.take();
            node_borrow.right = _bst_subtree_remove(min_val, right);
            drop(node_borrow);
            return Some(node);
        } else if node_borrow.left.is_some() {
            let left = node_borrow.left.take();
            drop(node_borrow);
            return left;
        } else if node_borrow.right.is_some() {
            let right = node_borrow.right.take();
            drop(node_borrow);
            return right;
        } else {
            drop(node_borrow);
            return None;
        }
    }
}

pub fn _bst_node_create<T>(val: T) -> Rc<RefCell<BstNode<T>>> {
    let node = Rc::new(RefCell::new(BstNode {
        val,
        left: None,
        right: None,
    }));
    node
}

pub fn bst_remove<T: Ord + Clone>(val: T, bst: &mut Bst<T>) {
    assert!(bst.root.is_some());

    // We remove val by using our subtree removal function starting with the
    // subtree rooted at bst->root (i.e. the whole tree).
    let root = bst.root.take();
    bst.root = _bst_subtree_remove(val, root);
}

pub fn bst_isempty<T>(bst: &Bst<T>) -> bool {
    bst.root.is_none()
}

pub fn _bst_subtree_insert<T: PartialOrd + Clone>(val: T, n: Option<Rc<RefCell<BstNode<T>>>>) -> Option<Rc<RefCell<BstNode<T>>>> {
    match n {
        None => {
            Some(_bst_node_create(val))
        },
        Some(node) => {
            let mut node_mut = node.borrow_mut();
            if val < node_mut.val {
                node_mut.left = _bst_subtree_insert(val, node_mut.left.clone());
            } else {
                node_mut.right = _bst_subtree_insert(val, node_mut.right.clone());
            }
            Some(node.clone())
        }
    }
}

pub fn bst_free<T: Ord + Clone>(mut bst: Bst<T>) {
    assert!(bst.root.is_some());

    // Assume that bst_remove() frees each node it removes and use it to free
    // all of the nodes in the tree.
    while !bst_isempty(&bst) {
        let root_val = bst.root.as_ref().unwrap().borrow().val.clone();
        bst_remove(root_val, &mut bst);
    }
}

pub fn bst_contains<T: PartialOrd>(val: T, bst: &Bst<T>) -> bool {
    assert!(bst.root.is_some());

    let mut cur = bst.root.clone();
    while let Some(node) = cur {
        let node_ref = node.borrow();
        if val == node_ref.val {
            return true;
        } else if val < node_ref.val {
            cur = node_ref.left.clone();
        } else {
            cur = node_ref.right.clone();
        }
    }

    false
}

pub fn bst_insert<T: PartialOrd + Clone>(val: T, bst: &mut Bst<T>) {
    assert!(bst.root.is_some());
    bst.root = _bst_subtree_insert(val, bst.root.clone());
}

pub fn bst_create<T>() -> Bst<T> {
    Bst { root: None }
}

