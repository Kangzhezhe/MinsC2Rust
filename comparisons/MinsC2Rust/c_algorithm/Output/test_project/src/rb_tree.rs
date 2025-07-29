pub const NUM_TEST_VALUES: i32 = 1000;

#[derive(Clone, Copy, PartialEq)]
pub enum RBTreeNodeSide {
    Left = 0,
    Right = 1,
}

#[derive(Clone, PartialEq)]
pub enum RBTreeNodeColor {
    Red,
    Black,
}

#[derive(Clone)]
pub struct RBTreeNode<T: Clone + PartialEq> {
    pub color: RBTreeNodeColor,
    pub key: T,
    pub value: T,
    pub parent: Option<Box<RBTreeNode<T>>>,
    pub children: [Option<Box<RBTreeNode<T>>>; 2],
}

pub struct RBTree<T: Clone + PartialEq> {
    pub root_node: Option<Box<RBTreeNode<T>>>,
    pub compare_func: fn(T, T) -> i32,
    pub num_nodes: i32,
}

impl<T: Clone + PartialEq> RBTree<T> {
    pub fn new(compare_func: fn(T, T) -> i32) -> Self {
        RBTree {
            root_node: None,
            compare_func,
            num_nodes: 0,
        }
    }
}
pub fn rb_tree_node_side<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> RBTreeNodeSide {
    if let Some(parent) = &node.parent {
        if let Some(left_child) = &parent.children[RBTreeNodeSide::Left as usize] {
            if std::ptr::eq(left_child.as_ref(), node) {
                return RBTreeNodeSide::Left;
            }
        }
    }
    RBTreeNodeSide::Right
}

pub fn rb_tree_node_replace<T: Clone + PartialEq>(
    tree: &mut RBTree<T>,
    node1: &mut RBTreeNode<T>,
    mut node2: Option<Box<RBTreeNode<T>>>,
) {
    let side;

    if let Some(ref mut node2_inner) = node2 {
        node2_inner.parent = node1.parent.take();
    }

    if node1.parent.is_none() {
        tree.root_node = node2;
    } else {
        side = rb_tree_node_side(node1);
        if let Some(ref mut parent) = node1.parent {
            parent.children[side as usize] = node2;
        }
    }
}

pub fn rb_tree_insert_case5<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &mut RBTreeNode<T>) {
    let side = rb_tree_node_side(node);
    let parent = node.parent.as_mut().unwrap();
    let grandparent = parent.parent.as_mut().unwrap();

    rb_tree_rotate(tree, grandparent, 1 - side as usize);

    parent.color = RBTreeNodeColor::Black;
    grandparent.color = RBTreeNodeColor::Red;
}

pub fn rb_tree_rotate<T: Clone + PartialEq>(
    tree: &mut RBTree<T>,
    node: &mut RBTreeNode<T>,
    direction: usize,
) -> Box<RBTreeNode<T>> {
    let mut new_root = node.children[1 - direction].take().unwrap();

    rb_tree_node_replace(tree, node, Some(new_root.clone()));

    node.children[1 - direction] = new_root.children[direction].take();
    new_root.children[direction] = Some(Box::new(node.clone()));

    node.parent = Some(new_root.clone());

    let node_clone = node.clone();
    if let Some(ref mut child) = node.children[1 - direction] {
        child.parent = Some(Box::new(node_clone));
    }

    new_root
}

pub fn rb_tree_node_sibling<T: Clone + PartialEq>(
    node: &RBTreeNode<T>,
) -> Option<Box<RBTreeNode<T>>> {
    let side = rb_tree_node_side(node);
    if let Some(parent) = &node.parent {
        return parent.children[1 - side as usize].clone();
    }
    None
}

pub fn rb_tree_insert_case4<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &mut RBTreeNode<T>) {
    let mut next_node: Box<RBTreeNode<T>>;
    let side = rb_tree_node_side(node);

    if side != rb_tree_node_side(node.parent.as_ref().unwrap()) {
        next_node = node.parent.take().unwrap();
        rb_tree_rotate(tree, next_node.as_mut(), 1 - side as usize);
    } else {
        next_node = Box::new(node.clone());
    }

    rb_tree_insert_case5(tree, next_node.as_mut());
}

pub fn rb_tree_node_uncle<T: Clone + PartialEq>(
    node: &RBTreeNode<T>,
) -> Option<Box<RBTreeNode<T>>> {
    if let Some(parent) = &node.parent {
        return rb_tree_node_sibling(parent);
    }
    None
}

pub fn rb_tree_insert_case3<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &mut RBTreeNode<T>) {
    let parent = node.parent.as_ref().unwrap().clone();
    let grandparent = parent.parent.as_ref().unwrap().clone();
    let uncle = rb_tree_node_uncle(node);

    if let Some(mut uncle_node) = uncle {
        if uncle_node.color == RBTreeNodeColor::Red {
            node.parent.as_mut().unwrap().color = RBTreeNodeColor::Black;
            uncle_node.color = RBTreeNodeColor::Black;
            let mut grandparent_mut = grandparent.clone();
            grandparent_mut.color = RBTreeNodeColor::Red;
            rb_tree_insert_case1(tree, &mut grandparent_mut);
        } else {
            rb_tree_insert_case4(tree, node);
        }
    } else {
        rb_tree_insert_case4(tree, node);
    }
}

pub fn rb_tree_insert_case2<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &mut RBTreeNode<T>) {
    if node.parent.as_ref().unwrap().color != RBTreeNodeColor::Black {
        rb_tree_insert_case3(tree, node);
    }
}

pub fn rb_tree_insert_case1<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &mut RBTreeNode<T>) {
    if node.parent.is_none() {
        node.color = RBTreeNodeColor::Black;
    } else {
        rb_tree_insert_case2(tree, node);
    }
}

pub fn rb_tree_node_child<T: Clone + PartialEq>(
    node: &RBTreeNode<T>,
    side: RBTreeNodeSide,
) -> Option<&Box<RBTreeNode<T>>> {
    if side == RBTreeNodeSide::Left || side == RBTreeNodeSide::Right {
        node.children[side as usize].as_ref()
    } else {
        None
    }
}

pub fn rb_tree_new<T: Clone + PartialEq>(compare_func: fn(T, T) -> i32) -> Option<Box<RBTree<T>>> {
    let mut new_tree = Box::new(RBTree {
        root_node: None,
        compare_func,
        num_nodes: 0,
    });

    Some(new_tree)
}

pub fn rb_tree_insert<T: Clone + PartialEq>(
    tree: &mut RBTree<T>,
    key: T,
    value: T,
) -> Option<Box<RBTreeNode<T>>> {
    let mut node = RBTreeNode {
        color: RBTreeNodeColor::Red,
        key: key.clone(),
        value: value.clone(),
        parent: None,
        children: [None, None],
    };

    let mut parent: Option<Box<RBTreeNode<T>>> = None;
    let mut rover = &mut tree.root_node;

    while let Some(ref mut current_node) = rover {
        parent = Some(current_node.clone());
        if (tree.compare_func)(value.clone(), current_node.value.clone()) < 0 {
            rover = &mut current_node.children[RBTreeNodeSide::Left as usize];
        } else {
            rover = &mut current_node.children[RBTreeNodeSide::Right as usize];
        }
    }

    *rover = Some(Box::new(node.clone()));
    node.parent = parent;

    rb_tree_insert_case1(tree, &mut node);

    tree.num_nodes += 1;

    Some(Box::new(node))
}

pub fn rb_tree_free_subtree<T: Clone + PartialEq>(node: Option<Box<RBTreeNode<T>>>) {
    if let Some(mut node) = node {
        rb_tree_free_subtree(node.children[RBTreeNodeSide::Left as usize].take());
        rb_tree_free_subtree(node.children[RBTreeNodeSide::Right as usize].take());
    }
}

pub fn rb_tree_lookup_node<T: Clone + PartialOrd>(
    tree: &RBTree<T>,
    key: T,
) -> Option<Box<RBTreeNode<T>>> {
    let mut node = tree.root_node.clone();

    while let Some(ref current_node) = node {
        let diff = (tree.compare_func)(key.clone(), current_node.key.clone());

        if diff == 0 {
            return node;
        } else if diff < 0 {
            node = current_node.children[RBTreeNodeSide::Left as usize].clone();
        } else {
            node = current_node.children[RBTreeNodeSide::Right as usize].clone();
        }
    }

    None
}

pub fn rb_tree_remove_node<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Box<RBTreeNode<T>>) {
    let mut node_to_remove = node;
    let mut child_node: Option<Box<RBTreeNode<T>>> = None;
    let mut parent_node: Option<Box<RBTreeNode<T>>> = None;
    let mut color: RBTreeNodeColor;

    if node_to_remove.children[RBTreeNodeSide::Left as usize].is_none() {
        child_node = node_to_remove.children[RBTreeNodeSide::Right as usize].take();
    } else if node_to_remove.children[RBTreeNodeSide::Right as usize].is_none() {
        child_node = node_to_remove.children[RBTreeNodeSide::Left as usize].take();
    } else {
        let mut successor = node_to_remove.children[RBTreeNodeSide::Right as usize]
            .as_ref()
            .unwrap()
            .clone();
        while successor.children[RBTreeNodeSide::Left as usize].is_some() {
            successor = successor.children[RBTreeNodeSide::Left as usize]
                .as_ref()
                .unwrap()
                .clone();
        }
        color = successor.color.clone();
        child_node = successor.children[RBTreeNodeSide::Right as usize].take();
        parent_node = successor.parent.take();

        if parent_node.as_ref().unwrap().key == node_to_remove.key {
            parent_node = Some(successor.clone());
        } else {
            if child_node.is_some() {
                child_node.as_mut().unwrap().parent = parent_node.clone();
            }
            parent_node.as_mut().unwrap().children[RBTreeNodeSide::Left as usize] =
                child_node.clone();
            successor.children[RBTreeNodeSide::Right as usize] =
                node_to_remove.children[RBTreeNodeSide::Right as usize].take();
            node_to_remove.children[RBTreeNodeSide::Right as usize]
                .as_mut()
                .unwrap()
                .parent = Some(successor.clone());
        }

        let parent_key = node_to_remove.parent.as_ref().unwrap().key.clone();
        let node_key = node_to_remove.key.clone();
        let side = if node_to_remove.parent.as_ref().unwrap().children
            [RBTreeNodeSide::Left as usize]
            .as_ref()
            .unwrap()
            .key
            == node_key
        {
            RBTreeNodeSide::Left as usize
        } else {
            RBTreeNodeSide::Right as usize
        };

        if tree.root_node.as_ref().unwrap().key == node_to_remove.key {
            tree.root_node = Some(successor.clone());
        } else {
            node_to_remove.parent.as_mut().unwrap().children[side] = Some(successor.clone());
        }
        successor.parent = node_to_remove.parent.take();
        successor.color = node_to_remove.color.clone();
        successor.children[RBTreeNodeSide::Left as usize] =
            node_to_remove.children[RBTreeNodeSide::Left as usize].take();
        node_to_remove.children[RBTreeNodeSide::Left as usize]
            .as_mut()
            .unwrap()
            .parent = Some(successor.clone());
    }

    if node_to_remove.color == RBTreeNodeColor::Black {
        if child_node.is_some() {
            child_node.as_mut().unwrap().color = RBTreeNodeColor::Black;
        } else {
            if parent_node.is_some() {
                if parent_node.as_ref().unwrap().children[RBTreeNodeSide::Left as usize].is_some() {
                    parent_node.as_mut().unwrap().children[RBTreeNodeSide::Left as usize]
                        .as_mut()
                        .unwrap()
                        .color = RBTreeNodeColor::Black;
                } else {
                    parent_node.as_mut().unwrap().children[RBTreeNodeSide::Right as usize]
                        .as_mut()
                        .unwrap()
                        .color = RBTreeNodeColor::Black;
                }
            }
        }
    }

    tree.num_nodes -= 1;
}

pub fn rb_tree_free<T: Clone + PartialEq>(mut tree: Box<RBTree<T>>) {
    rb_tree_free_subtree(tree.root_node.take());
}

pub fn rb_tree_num_entries<T: Clone + PartialEq>(tree: &RBTree<T>) -> i32 {
    tree.num_nodes
}

pub fn rb_tree_root_node<T: Clone + PartialEq>(tree: &RBTree<T>) -> Option<&Box<RBTreeNode<T>>> {
    tree.root_node.as_ref()
}

pub fn rb_tree_remove<T: Clone + PartialEq + PartialOrd>(tree: &mut RBTree<T>, key: T) -> bool {
    let node = rb_tree_lookup_node(tree, key.clone());

    if node.is_none() {
        return false;
    }

    rb_tree_remove_node(tree, node.unwrap());

    true
}

pub fn rb_tree_lookup<T: Clone + PartialOrd>(tree: &RBTree<T>, key: T) -> Option<T> {
    let node = rb_tree_lookup_node(tree, key);

    match node {
        Some(ref current_node) => Some(current_node.value.clone()),
        None => None,
    }
}

pub fn rb_tree_to_array<T: Clone + PartialEq>(tree: &RBTree<T>) -> Vec<T> {
    let mut result = Vec::new();
    let mut stack = Vec::new();
    let mut current = tree.root_node.as_ref();

    while !stack.is_empty() || current.is_some() {
        while let Some(node) = current {
            stack.push(node);
            current = node.children[RBTreeNodeSide::Left as usize].as_ref();
        }

        if let Some(node) = stack.pop() {
            result.push(node.value.clone());
            current = node.children[RBTreeNodeSide::Right as usize].as_ref();
        }
    }

    result
}

pub fn rb_tree_node_value<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> T {
    node.value.clone()
}

pub fn rb_tree_node_key<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> T {
    node.key.clone()
}
