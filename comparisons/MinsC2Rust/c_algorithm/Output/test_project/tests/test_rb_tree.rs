use test_project::rb_tree::{
    rb_tree_free, rb_tree_free_subtree, rb_tree_insert, rb_tree_insert_case1, rb_tree_insert_case2,
    rb_tree_insert_case3, rb_tree_insert_case4, rb_tree_insert_case5, rb_tree_lookup,
    rb_tree_lookup_node, rb_tree_new, rb_tree_node_child, rb_tree_node_key, rb_tree_node_replace,
    rb_tree_node_sibling, rb_tree_node_uncle, rb_tree_node_value, rb_tree_num_entries,
    rb_tree_remove, rb_tree_remove_node, rb_tree_root_node, rb_tree_rotate, rb_tree_to_array,
    RBTree, RBTreeNode, RBTreeNodeColor, RBTreeNodeSide, NUM_TEST_VALUES,
};
pub fn find_subtree_height<T: Clone + PartialEq>(node: Option<&Box<RBTreeNode<T>>>) -> i32 {
    let mut left_subtree: Option<&Box<RBTreeNode<T>>>;
    let mut right_subtree: Option<&Box<RBTreeNode<T>>>;
    let mut left_height: i32;
    let mut right_height: i32;

    if node.is_none() {
        return 0;
    }

    left_subtree = rb_tree_node_child(node.unwrap(), RBTreeNodeSide::Left);
    right_subtree = rb_tree_node_child(node.unwrap(), RBTreeNodeSide::Right);
    left_height = find_subtree_height(left_subtree);
    right_height = find_subtree_height(right_subtree);

    if left_height > right_height {
        left_height + 1
    } else {
        right_height + 1
    }
}

pub fn create_tree() -> Option<Box<RBTree<i32>>> {
    let compare_func = |a: i32, b: i32| a.cmp(&b) as i32;
    let mut tree = RBTree::new(compare_func);
    let mut test_array: [i32; 1000] = [0; 1000];

    for i in 0..1000 {
        test_array[i] = i as i32;
        rb_tree_insert(&mut tree, test_array[i], test_array[i]);
    }

    Some(Box::new(tree))
}

pub fn validate_tree<T: Clone + PartialEq>(tree: &RBTree<T>) -> bool {
    if let Some(root) = &tree.root_node {
        if root.color != RBTreeNodeColor::Black {
            return false;
        }
    } else {
        return true;
    }

    fn validate_red_black_property<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> bool {
        if node.color == RBTreeNodeColor::Red {
            for child in &node.children {
                if let Some(child_node) = child {
                    if child_node.color == RBTreeNodeColor::Red {
                        return false;
                    }
                }
            }
        }
        true
    }

    fn validate_black_height<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> (bool, i32) {
        if node.children[0].is_none() && node.children[1].is_none() {
            return (
                true,
                if node.color == RBTreeNodeColor::Black {
                    1
                } else {
                    0
                },
            );
        }

        let mut left_valid = true;
        let mut right_valid = true;
        let mut left_height = 0;
        let mut right_height = 0;

        if let Some(left_child) = &node.children[0] {
            let (valid, height) = validate_black_height(left_child);
            left_valid = valid;
            left_height = height;
        }

        if let Some(right_child) = &node.children[1] {
            let (valid, height) = validate_black_height(right_child);
            right_valid = valid;
            right_height = height;
        }

        if !left_valid || !right_valid || left_height != right_height {
            return (false, 0);
        }

        (
            true,
            left_height
                + if node.color == RBTreeNodeColor::Black {
                    1
                } else {
                    0
                },
        )
    }

    fn validate_height_balance<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> bool {
        let left_height = find_subtree_height(node.children[0].as_ref());
        let right_height = find_subtree_height(node.children[1].as_ref());
        (left_height - right_height).abs() <= 1
    }

    fn validate_tree_recursive<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> bool {
        if !validate_red_black_property(node) {
            return false;
        }

        if !validate_height_balance(node) {
            return false;
        }

        for child in &node.children {
            if let Some(child_node) = child {
                if !validate_tree_recursive(child_node) {
                    return false;
                }
            }
        }

        true
    }

    if let Some(root) = &tree.root_node {
        if !validate_tree_recursive(root) {
            return false;
        }

        let (valid, _) = validate_black_height(root);
        if !valid {
            return false;
        }
    }

    true
}

#[test]
pub fn test_rb_tree_free() {
    let mut tree = rb_tree_new(int_compare).unwrap();
    rb_tree_free(tree);

    let mut tree = create_tree().unwrap();
    rb_tree_free(tree);
}

#[test]
pub fn test_rb_tree_new() {
    let tree = rb_tree_new(int_compare);

    assert!(tree.is_some());
    let tree = tree.unwrap();
    assert!(rb_tree_root_node(&tree).is_none());
    assert_eq!(rb_tree_num_entries(&tree), 0);

    rb_tree_free(tree);
}

#[test]
pub fn test_rb_tree_remove() {
    let mut tree = create_tree().unwrap();

    let invalid_key1 = 1000 + 100;
    assert!(!rb_tree_remove(&mut tree, invalid_key1));
    let invalid_key2 = -1;
    assert!(!rb_tree_remove(&mut tree, invalid_key2));

    let mut expected_entries = 1000;

    for x in 0..10 {
        for y in 0..10 {
            for z in 0..10 {
                let value = z * 100 + (9 - y) * 10 + x;
                assert!(rb_tree_remove(&mut tree, value));
                assert!(validate_tree(&tree));
                expected_entries -= 1;
                assert_eq!(rb_tree_num_entries(&tree), expected_entries);
            }
        }
    }

    assert!(rb_tree_root_node(&tree).is_none());

    rb_tree_free(tree);
}

#[test]
pub fn test_rb_tree_to_array() {
    let entries = vec![89, 23, 42, 4, 16, 15, 8, 99, 50, 30];
    let sorted = vec![4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    let mut tree = RBTree::new(|a: i32, b: i32| a.cmp(&b) as i32);

    for i in 0..num_entries {
        rb_tree_insert(&mut tree, entries[i], entries[i]);
    }

    assert_eq!(rb_tree_num_entries(&tree), num_entries as i32);

    let array = rb_tree_to_array(&tree);

    for i in 0..num_entries {
        assert_eq!(array[i], sorted[i]);
    }

    validate_tree(&tree);

    rb_tree_free(Box::new(tree));
}

#[test]
pub fn test_rb_tree_lookup() {
    let tree = create_tree().unwrap();

    for i in 0..NUM_TEST_VALUES {
        let value = rb_tree_lookup(&tree, i);

        assert!(value.is_some());
        assert_eq!(value.unwrap(), i);
    }

    // Test invalid values
    assert!(rb_tree_lookup(&tree, -1).is_none());
    assert!(rb_tree_lookup(&tree, NUM_TEST_VALUES + 1).is_none());
    assert!(rb_tree_lookup(&tree, 8724897).is_none());

    rb_tree_free(tree);
}

#[test]
pub fn test_rb_tree_insert_lookup() {
    pub const NUM_TEST_VALUES: i32 = 1000;
    let mut test_array: Vec<i32> = Vec::with_capacity(NUM_TEST_VALUES as usize);

    let mut tree = RBTree::new(int_compare);

    for i in 0..NUM_TEST_VALUES {
        test_array.push(i);
        rb_tree_insert(&mut tree, test_array[i as usize], test_array[i as usize]);

        assert_eq!(rb_tree_num_entries(&tree), i + 1);
        assert!(validate_tree(&tree));
    }

    assert!(rb_tree_root_node(&tree).is_some());

    for i in 0..NUM_TEST_VALUES {
        let node = rb_tree_lookup_node(&tree, i);
        assert!(node.is_some());
        let value = rb_tree_node_key(node.as_ref().unwrap());
        assert_eq!(value, i);
        let value = rb_tree_node_value(node.as_ref().unwrap());
        assert_eq!(value, i);
    }

    let invalid_key1 = -1;
    assert!(rb_tree_lookup_node(&tree, invalid_key1).is_none());

    let invalid_key2 = NUM_TEST_VALUES + 100;
    assert!(rb_tree_lookup_node(&tree, invalid_key2).is_none());

    rb_tree_free(Box::new(tree));
}

#[test]
pub fn test_out_of_memory() {
    let mut tree = create_tree().unwrap();

    // Try to add some more nodes and verify that this fails.
    for i in 10000..20000 {
        let node = rb_tree_insert(&mut tree, i, i);
        assert!(node.is_none());
        assert!(validate_tree(&tree));
    }

    rb_tree_free(tree);
}

#[test]
pub fn test_rb_tree_child() {
    let mut tree = RBTree::new(int_compare);
    let values = [1, 2, 3];

    for i in 0..3 {
        rb_tree_insert(&mut tree, values[i], values[i]);
    }

    let root = rb_tree_root_node(&tree).unwrap();
    let p = rb_tree_node_value(root);
    assert_eq!(p, 2);

    let left = rb_tree_node_child(root, RBTreeNodeSide::Left).unwrap();
    let p = rb_tree_node_value(left);
    assert_eq!(p, 1);

    let right = rb_tree_node_child(root, RBTreeNodeSide::Right).unwrap();
    let p = rb_tree_node_value(right);
    assert_eq!(p, 3);

    assert!(rb_tree_node_child(root, RBTreeNodeSide::Left).is_some());
    assert!(rb_tree_node_child(root, RBTreeNodeSide::Right).is_some());

    rb_tree_free(Box::new(tree));
}

pub fn int_compare(a: i32, b: i32) -> i32 {
    if a < b {
        -1
    } else if a > b {
        1
    } else {
        0
    }
}
