use test_project::bst::{
    _bst_node_create, _bst_subtree_insert, _bst_subtree_min_val, _bst_subtree_remove, bst_contains,
    bst_create, bst_free, bst_insert, bst_isempty, bst_remove,
};

use ntest::timeout;
#[test]
#[timeout(60000)]
pub fn test_bst() {
    let mut bst = bst_create();
    let good_nums = [32, 16, 8, 12, 4, 64, 48, 80];
    let bad_nums = [1, 3, 5, 7, 9, 11, 13, 15];

    // Initialize the tree.
    for i in 0..8 {
        bst_insert(good_nums[i], &mut bst);
    }

    // Test containment.
    for i in 0..8 {
        assert!(bst_contains(good_nums[i], &bst));
    }
    println!("== Verified that BST contains all the expected values.");

    for i in 0..8 {
        assert!(!bst_contains(bad_nums[i], &bst));
    }
    println!("== Verified that BST contains none of the unexpected values.");

    /*
     * Test removal by removing one good number at a time and making sure the
     * remaining good numbers are still in the tree.
     */
    for i in 0..8 {
        bst_remove(good_nums[i], &mut bst);
        assert!(!bst_contains(good_nums[i], &bst));
        for j in (i + 1)..8 {
            assert!(bst_contains(good_nums[j], &bst));
        }
    }
    println!("== Verified removal works as expected.");

    bst_free(bst);
}
