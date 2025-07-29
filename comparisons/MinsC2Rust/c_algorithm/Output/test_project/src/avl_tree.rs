use std::cmp::Ordering;

pub struct AVLTree<T: Clone> {
    pub root_node: Option<Box<AVLTreeNode<T>>>,
    pub compare_func: fn(&T, &T) -> i32,
    pub num_nodes: u32,
}

#[derive(PartialEq, Clone)]
pub struct AVLTreeNode<T: Clone> {
    pub left: Option<Box<AVLTreeNode<T>>>,
    pub right: Option<Box<AVLTreeNode<T>>>,
    pub parent: Option<Box<AVLTreeNode<T>>>,
    pub key: T,
    pub value: T,
    pub height: i32,
}

#[derive(Clone, Copy)]
pub enum AVLTreeNodeSide {
    Left = 0,
    Right = 1,
}
pub fn avl_tree_subtree_height<T: Clone>(node: Option<&Box<AVLTreeNode<T>>>) -> i32 {
    match node {
        None => 0,
        Some(n) => n.height,
    }
}

pub fn avl_tree_update_height<T: Clone>(node: &mut AVLTreeNode<T>) {
    let left_subtree = node.left.as_ref();
    let right_subtree = node.right.as_ref();
    
    let left_height = avl_tree_subtree_height(left_subtree);
    let right_height = avl_tree_subtree_height(right_subtree);
    
    if left_height > right_height {
        node.height = left_height + 1;
    } else {
        node.height = right_height + 1;
    }
}

pub fn avl_tree_node_parent_side<T: Clone + PartialEq>(node: &Box<AVLTreeNode<T>>) -> AVLTreeNodeSide {
    let parent = node.parent.as_ref().unwrap();
    if parent.left.as_ref().unwrap().as_ref() == node.as_ref() {
        AVLTreeNodeSide::Left
    } else {
        AVLTreeNodeSide::Right
    }
}

pub fn avl_tree_node_replace<T: PartialEq + Clone>(tree: &mut AVLTree<T>, node1: &mut AVLTreeNode<T>, mut node2: Option<Box<AVLTreeNode<T>>>) {
    if let Some(ref mut node2) = node2 {
        node2.parent = node1.parent.clone();
    }

    if node1.parent.is_none() {
        tree.root_node = node2;
    } else {
        let mut parent = node1.parent.clone();
        let side = avl_tree_node_parent_side(&Box::new(AVLTreeNode {
            left: None,
            right: None,
            parent: parent.clone(),
            key: node1.key.clone(),
            value: node1.value.clone(),
            height: node1.height,
        }));
        match side {
            AVLTreeNodeSide::Left => parent.as_mut().unwrap().left = node2,
            AVLTreeNodeSide::Right => parent.as_mut().unwrap().right = node2,
        }

        avl_tree_update_height(parent.as_mut().unwrap());
    }
}

pub fn avl_tree_rotate<T: PartialEq + Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
    direction: AVLTreeNodeSide,
) -> Box<AVLTreeNode<T>> {
    let direction_clone = direction;
    let mut new_root = match direction_clone {
        AVLTreeNodeSide::Left => node.right.take().unwrap(),
        AVLTreeNodeSide::Right => node.left.take().unwrap(),
    };

    avl_tree_node_replace(tree, node, Some(new_root.clone()));

    match direction_clone {
        AVLTreeNodeSide::Left => {
            node.right = new_root.left.take();
            new_root.left = Some(Box::new(node.clone()));
        },
        AVLTreeNodeSide::Right => {
            node.left = new_root.right.take();
            new_root.right = Some(Box::new(node.clone()));
        },
    }

    node.parent = Some(new_root.clone());

    let node_clone = node.clone();
    if let Some(mut child) = match direction_clone {
        AVLTreeNodeSide::Left => node.right.as_mut(),
        AVLTreeNodeSide::Right => node.left.as_mut(),
    } {
        child.parent = Some(Box::new(node_clone));
    }

    avl_tree_update_height(&mut new_root);
    avl_tree_update_height(node);

    new_root
}

pub fn avl_tree_node_balance<T: PartialEq + Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
) -> Box<AVLTreeNode<T>> {
    let left_subtree = node.left.as_ref();
    let right_subtree = node.right.as_ref();

    let diff = avl_tree_subtree_height(right_subtree) - avl_tree_subtree_height(left_subtree);

    if diff >= 2 {
        let mut child = node.right.as_mut().unwrap();

        if avl_tree_subtree_height(child.right.as_ref())
            < avl_tree_subtree_height(child.left.as_ref())
        {
            avl_tree_rotate(tree, child, AVLTreeNodeSide::Right);
        }

        let mut node_clone = node.clone();
        let mut new_node = avl_tree_rotate(tree, &mut node_clone, AVLTreeNodeSide::Left);
        avl_tree_update_height(&mut new_node);
        return new_node;
    } else if diff <= -2 {
        let mut child = node.left.as_mut().unwrap();

        if avl_tree_subtree_height(child.left.as_ref())
            < avl_tree_subtree_height(child.right.as_ref())
        {
            avl_tree_rotate(tree, child, AVLTreeNodeSide::Left);
        }

        let mut node_clone = node.clone();
        let mut new_node = avl_tree_rotate(tree, &mut node_clone, AVLTreeNodeSide::Right);
        avl_tree_update_height(&mut new_node);
        return new_node;
    }

    avl_tree_update_height(node);
    Box::new(node.clone())
}

pub fn avl_tree_balance_to_root<T: PartialEq + Clone>(tree: &mut AVLTree<T>, node: &mut AVLTreeNode<T>) {
    let mut rover = Box::new(node.clone());

    while rover.parent.is_some() {
        let mut balanced_node = avl_tree_node_balance(tree, &mut rover);
        rover = balanced_node.parent.take().unwrap();
    }
}

pub fn avl_tree_node_get_replacement<T: PartialEq + Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
) -> Option<Box<AVLTreeNode<T>>> {
    let left_subtree = node.left.as_ref();
    let right_subtree = node.right.as_ref();

    if left_subtree.is_none() && right_subtree.is_none() {
        return None;
    }

    let left_height = avl_tree_subtree_height(left_subtree);
    let right_height = avl_tree_subtree_height(right_subtree);

    let side = if left_height < right_height {
        AVLTreeNodeSide::Right
    } else {
        AVLTreeNodeSide::Left
    };

    let mut result = match side {
        AVLTreeNodeSide::Left => node.left.clone(),
        AVLTreeNodeSide::Right => node.right.clone(),
    };

    while result.as_ref().unwrap().left.is_some() || result.as_ref().unwrap().right.is_some() {
        result = match side {
            AVLTreeNodeSide::Left => result.unwrap().left.clone(),
            AVLTreeNodeSide::Right => result.unwrap().right.clone(),
        };
    }

    let child = match side {
        AVLTreeNodeSide::Left => result.as_ref().unwrap().left.clone(),
        AVLTreeNodeSide::Right => result.as_ref().unwrap().right.clone(),
    };
    avl_tree_node_replace(tree, result.as_mut().unwrap(), child);

    avl_tree_update_height(result.as_mut().unwrap().parent.as_mut().unwrap());

    result
}

pub fn avl_tree_node_key<T>(node: &AVLTreeNode<T>) -> T 
where
    T: Clone,
{
    node.key.clone()
}

pub fn avl_tree_node_parent<T: Clone>(node: &Box<AVLTreeNode<T>>) -> Option<Box<AVLTreeNode<T>>> {
    node.parent.as_ref().map(|parent| Box::new((**parent).clone()))
}

pub fn avl_tree_node_child<T: Clone>(node: &AVLTreeNode<T>, side: AVLTreeNodeSide) -> Option<&Box<AVLTreeNode<T>>> {
    match side {
        AVLTreeNodeSide::Left => node.left.as_ref(),
        AVLTreeNodeSide::Right => node.right.as_ref(),
    }
}

pub fn avl_tree_free_subtree<T: Clone>(tree: &mut AVLTree<T>, node: Option<Box<AVLTreeNode<T>>>) {
    if let Some(mut node) = node {
        avl_tree_free_subtree(tree, node.left.take());
        avl_tree_free_subtree(tree, node.right.take());
    }
}

pub fn avl_tree_insert<T: PartialEq + Clone>(
    tree: &mut AVLTree<T>,
    key: T,
    value: T,
) -> Option<Box<AVLTreeNode<T>>> {
    let mut rover = &mut tree.root_node;
    let mut previous_node: Option<Box<AVLTreeNode<T>>> = None;

    while let Some(ref mut node) = rover {
        previous_node = Some(node.clone());
        if (tree.compare_func)(&key, &node.key) < 0 {
            rover = &mut node.left;
        } else {
            rover = &mut node.right;
        }
    }

    let mut new_node = Box::new(AVLTreeNode {
        left: None,
        right: None,
        parent: previous_node.clone(),
        key: key.clone(),
        value: value.clone(),
        height: 1,
    });

    *rover = Some(new_node.clone());

    if let Some(ref mut prev_node) = previous_node {
        avl_tree_balance_to_root(tree, prev_node);
    }

    tree.num_nodes += 1;

    Some(new_node)
}

pub fn avl_tree_new<T: Clone>(compare_func: fn(&T, &T) -> i32) -> Option<AVLTree<T>> {
    let new_tree = AVLTree {
        root_node: None,
        compare_func,
        num_nodes: 0,
    };

    Some(new_tree)
}

pub fn avl_tree_lookup_node<T: Clone>(tree: &AVLTree<T>, key: T) -> Option<Box<AVLTreeNode<T>>> {
    let mut node = tree.root_node.clone();

    while let Some(ref current_node) = node {
        let diff = (tree.compare_func)(&key, &current_node.key);

        match diff.cmp(&0) {
            Ordering::Equal => return node,
            Ordering::Less => node = current_node.left.clone(),
            Ordering::Greater => node = current_node.right.clone(),
        }
    }

    None
}

pub fn avl_tree_remove_node<T: PartialEq + Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
) {
    let mut swap_node = avl_tree_node_get_replacement(tree, node);

    let mut balance_startpoint: Option<Box<AVLTreeNode<T>>>;

    if swap_node.is_none() {
        avl_tree_node_replace(tree, node, None);
        balance_startpoint = node.parent.clone();
    } else {
        let mut swap_node = swap_node.unwrap();

        if swap_node.parent.as_ref().unwrap().as_ref() == node {
            balance_startpoint = Some(swap_node.clone());
        } else {
            balance_startpoint = swap_node.parent.clone();
        }

        let children = [
            node.left.clone(),
            node.right.clone(),
        ];

        for i in 0..2 {
            let mut child = children[i].clone();
            if let Some(ref mut child) = child {
                child.parent = Some(swap_node.clone());
            }
            match i {
                0 => swap_node.left = child,
                1 => swap_node.right = child,
                _ => (),
            }
        }

        swap_node.height = node.height;

        avl_tree_node_replace(tree, node, Some(swap_node));
    }

    tree.num_nodes -= 1;

    if let Some(ref mut balance_startpoint) = balance_startpoint {
        avl_tree_balance_to_root(tree, balance_startpoint.as_mut());
    }
}

pub fn avl_tree_root_node<T: Clone>(tree: &AVLTree<T>) -> Option<&Box<AVLTreeNode<T>>> {
    tree.root_node.as_ref()
}

pub fn avl_tree_to_array_add_subtree<T: Clone>(
    subtree: Option<Box<AVLTreeNode<T>>>,
    array: &mut Vec<T>,
    index: &mut usize,
) {
    if subtree.is_none() {
        return;
    }

    let subtree = subtree.unwrap();

    // Add left subtree first
    avl_tree_to_array_add_subtree(subtree.left, array, index);

    // Add this node
    array[*index] = subtree.key.clone();
    *index += 1;

    // Finally add right subtree
    avl_tree_to_array_add_subtree(subtree.right, array, index);
}

pub fn avl_tree_free<T: Clone>(tree: &mut AVLTree<T>) {
    let root_node = tree.root_node.take();
    avl_tree_free_subtree(tree, root_node);
}

pub fn avl_tree_num_entries<T: Clone>(tree: &AVLTree<T>) -> u32 {
    tree.num_nodes
}

pub fn avl_tree_remove<T: PartialEq + Clone>(tree: &mut AVLTree<T>, key: T) -> bool {
    let node = avl_tree_lookup_node(tree, key);

    if node.is_none() {
        return false;
    }

    let mut node = node.unwrap();
    avl_tree_remove_node(tree, &mut node);

    true
}

pub fn avl_tree_node_value<T: Clone>(node: &AVLTreeNode<T>) -> T {
    node.value.clone()
}

pub fn avl_tree_to_array<T: Clone>(tree: &AVLTree<T>) -> Option<Vec<T>> {
    let mut array = Vec::with_capacity(tree.num_nodes as usize);
    let mut index = 0;

    avl_tree_to_array_add_subtree(tree.root_node.clone(), &mut array, &mut index);

    Some(array)
}

pub fn avl_tree_lookup<T: Clone>(tree: &AVLTree<T>, key: T) -> Option<T> {
    let node = avl_tree_lookup_node(tree, key);

    match node {
        Some(n) => Some(n.value.clone()),
        None => None,
    }
}

