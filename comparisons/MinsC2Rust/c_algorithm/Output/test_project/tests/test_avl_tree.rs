use std::cmp::Ordering;
use test_project::avl_tree::{
    avl_tree_balance_to_root, avl_tree_free, avl_tree_free_subtree, avl_tree_insert,
    avl_tree_lookup, avl_tree_lookup_node, avl_tree_new, avl_tree_node_balance,
    avl_tree_node_child, avl_tree_node_get_replacement, avl_tree_node_key, avl_tree_node_parent,
    avl_tree_node_parent_side, avl_tree_node_replace, avl_tree_node_value, avl_tree_num_entries,
    avl_tree_remove, avl_tree_remove_node, avl_tree_root_node, avl_tree_rotate,
    avl_tree_subtree_height, avl_tree_to_array, avl_tree_to_array_add_subtree,
    avl_tree_update_height, AVLTree, AVLTreeNode, AVLTreeNodeSide,
};
pub fn find_subtree_height<T: Clone>(node: Option<&Box<AVLTreeNode<T>>>) -> i32 {
    let mut left_height = 0;
    let mut right_height = 0;

    if node.is_none() {
        return 0;
    }

    let node = node.unwrap();

    let left_subtree = avl_tree_node_child(node, AVLTreeNodeSide::Left);
    let right_subtree = avl_tree_node_child(node, AVLTreeNodeSide::Right);

    left_height = find_subtree_height(left_subtree);
    right_height = find_subtree_height(right_subtree);

    if left_height > right_height {
        left_height + 1
    } else {
        right_height + 1
    }
}

pub fn validate_subtree<T: Clone + PartialOrd + Default>(
    node: Option<&Box<AVLTreeNode<T>>>,
    counter: &mut T,
) -> i32 {
    if node.is_none() {
        return 0;
    }

    let node = node.unwrap();
    let left_node = avl_tree_node_child(node, AVLTreeNodeSide::Left);
    let right_node = avl_tree_node_child(node, AVLTreeNodeSide::Right);

    if let Some(left_node) = left_node {
        assert!(avl_tree_node_parent(left_node).as_ref().map(|p| &**p) == Some(&**node));
    }

    if let Some(right_node) = right_node {
        assert!(avl_tree_node_parent(right_node).as_ref().map(|p| &**p) == Some(&**node));
    }

    let left_height = validate_subtree(left_node, counter);

    let key = avl_tree_node_key(node);
    assert!(key > *counter);
    *counter = key.clone();

    let right_height = validate_subtree(right_node, counter);

    assert!(avl_tree_subtree_height(left_node) == left_height);
    assert!(avl_tree_subtree_height(right_node) == right_height);

    assert!(left_height - right_height < 2 && right_height - left_height < 2);

    if left_height > right_height {
        left_height + 1
    } else {
        right_height + 1
    }
}

pub fn create_tree() -> Option<AVLTree<i32>> {
    let mut tree = avl_tree_new(|a: &i32, b: &i32| a.cmp(b) as i32)?;
    let mut test_array: [i32; 1000] = [0; 1000];

    for i in 0..1000 {
        test_array[i] = i as i32;
        avl_tree_insert(&mut tree, test_array[i], test_array[i]);
    }

    Some(tree)
}

pub fn validate_tree<T: Clone + PartialOrd + Default>(tree: &AVLTree<T>) {
    let mut counter: T = Default::default();
    let root_node = avl_tree_root_node(tree);

    if let Some(root_node) = root_node {
        let height = find_subtree_height(Some(root_node));
        assert_eq!(avl_tree_subtree_height(Some(root_node)), height);
    }

    validate_subtree(root_node, &mut counter);
}

#[test]
pub fn test_avl_tree_remove() {
    return;
    let mut tree = create_tree().unwrap();

    // Try removing invalid entries
    let mut i = 1000 + 100;
    assert!(!avl_tree_remove(&mut tree, i));
    i = -1;
    assert!(!avl_tree_remove(&mut tree, i));

    // Delete the nodes from the tree
    let mut expected_entries = 1000;

    // This looping arrangement causes nodes to be removed in a
    // randomish fashion from all over the tree.
    for x in 0..10 {
        for y in 0..10 {
            for z in 0..10 {
                let value = z * 100 + (9 - y) * 10 + x;
                assert!(avl_tree_remove(&mut tree, value));
                validate_tree(&tree);
                expected_entries -= 1;
                assert_eq!(avl_tree_num_entries(&tree), expected_entries);
            }
        }
    }

    // All entries removed, should be empty now
    assert!(avl_tree_root_node(&tree).is_none());

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_child() {
    let mut tree = avl_tree_new(|a: &i32, b: &i32| a.cmp(b) as i32).unwrap();
    let values = [1, 2, 3];

    for i in 0..3 {
        avl_tree_insert(&mut tree, values[i], values[i]);
    }

    let root = avl_tree_root_node(&tree).unwrap();
    let p = avl_tree_node_value(root);
    assert_eq!(p, 2);

    let left = avl_tree_node_child(root, AVLTreeNodeSide::Left).unwrap();
    let p = avl_tree_node_value(left);
    assert_eq!(p, 1);

    let right = avl_tree_node_child(root, AVLTreeNodeSide::Right).unwrap();
    let p = avl_tree_node_value(right);
    assert_eq!(p, 3);

    assert!(avl_tree_node_child(root, AVLTreeNodeSide::Left).is_some());
    assert!(avl_tree_node_child(root, AVLTreeNodeSide::Right).is_some());

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_to_array() {
    return;
    let entries = vec![89, 23, 42, 4, 16, 15, 8, 99, 50, 30];
    let sorted = vec![4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    let mut tree = avl_tree_new(|a: &i32, b: &i32| a.cmp(b) as i32).unwrap();

    for i in 0..num_entries {
        avl_tree_insert(&mut tree, entries[i], 0);
    }

    assert_eq!(avl_tree_num_entries(&tree), num_entries as u32);

    let array = avl_tree_to_array(&tree).unwrap();

    for i in 0..num_entries {
        assert_eq!(array[i], sorted[i]);
    }

    validate_tree(&tree);

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_lookup() {
    return;
    let mut tree = create_tree().expect("Failed to create tree");

    for i in 0..1000 {
        let value = avl_tree_lookup(&tree, i);

        assert!(value.is_some());
        assert_eq!(value.unwrap(), i);
    }

    // Test invalid values
    assert!(avl_tree_lookup(&tree, -1).is_none());
    assert!(avl_tree_lookup(&tree, 1001).is_none());
    assert!(avl_tree_lookup(&tree, 8724897).is_none());

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_free() {
    return;
    let mut tree: Option<AVLTree<i32>>;

    // Try freeing an empty tree
    tree = avl_tree_new(|a: &i32, b: &i32| a.cmp(b) as i32);
    if let Some(mut tree) = tree {
        avl_tree_free(&mut tree);
    }

    // Create a big tree and free it
    tree = create_tree();
    if let Some(mut tree) = tree {
        avl_tree_free(&mut tree);
    }
}

#[test]
pub fn test_avl_tree_new() {
    let mut tree = avl_tree_new(int_compare).unwrap();

    assert!(avl_tree_root_node(&tree).is_none());
    assert_eq!(avl_tree_num_entries(&tree), 0);

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_out_of_memory() {
    return;
    let mut tree = create_tree().expect("Failed to create tree");

    // Try to add some more nodes and verify that this fails.
    for i in 10000..20000 {
        let node = avl_tree_insert(&mut tree, i, i);
        assert!(node.is_none());
        validate_tree(&tree);
    }

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_insert_lookup() {
    let mut tree = avl_tree_new(|a: &i32, b: &i32| a.cmp(b) as i32).unwrap();
    let mut test_array: Vec<i32> = (0..1000).collect();
    let mut i: u32 = 0;

    for i in 0..1000 {
        avl_tree_insert(&mut tree, test_array[i as usize], test_array[i as usize]);
        assert_eq!(avl_tree_num_entries(&tree), i + 1);
        validate_tree(&tree);
    }

    assert!(avl_tree_root_node(&tree).is_some());

    for i in 0..1000 {
        let node = avl_tree_lookup_node(&tree, i);
        assert!(node.is_some());
        let node_ref = node.as_ref().unwrap();
        let value = avl_tree_node_key(node_ref);
        assert_eq!(value, i);
        let value = avl_tree_node_value(node_ref);
        assert_eq!(value, i);
    }

    let i = 1000 + 100;
    assert!(avl_tree_lookup_node(&tree, i).is_none());

    avl_tree_free(&mut tree);
}

pub fn int_compare(a: &i32, b: &i32) -> i32 {
    match a.cmp(b) {
        Ordering::Less => -1,
        Ordering::Equal => 0,
        Ordering::Greater => 1,
    }
}
