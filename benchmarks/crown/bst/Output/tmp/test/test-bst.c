#include <stdio.h>
#include <assert.h>

/*
 * A definition for a binary search tree implementation.
 */

#ifndef __BST_H
#define __BST_H

/*
 * Structure used to represent a binary search tree.
 */
struct bst;

/*
 * Creates a new, empty binary search tree and returns a pointer to it.
 */
struct bst* bst_create();

/*
 * Free the memory associated with a binary search tree.
 *
 * Params:
 *   bst - the binary search tree to be destroyed
 */
void bst_free(struct bst* bst);

/*
 * Returns 1 if the given binary search tree is empty or 0 otherwise.
 *
 * Params:
 *   bst - the binary search tree whose emptiness is to be checked
 */
int bst_isempty(struct bst* bst);

/*
 * Inserts a given value into an existing binary search tree.
 *
 * Params:
 *   val - the value to be inserted into the tree
 *   bst - the binary search tree into which to insert val
 */
void bst_insert(int val, struct bst* bst);

/*
 * Removes a given value from an existing binary search tree.  If the
 * specified value is not contained in the specified tree, the tree is not
 * modified.
 *
 * Params:
 *   val - the value to be removed from the tree
 *   bst - the binary search tree from which to remove val
 */
void bst_remove(int val, struct bst* bst);

/*
 * Determines whether a binary search tree contains a given value.
 *
 * Params:
 *   val - the value to be found in the tree
 *   bst - the binary search tree in which to search for val
 *
 * Return:
 *   Returns 1 if bst contains val or 0 otherwise.
 */
int bst_contains(int val, struct bst* bst);


#endif


void test_bst(){
    struct bst* bst = bst_create();
    int good_nums[8] = {32, 16, 8, 12, 4, 64, 48, 80};
    int bad_nums[8] = {1, 3, 5, 7, 9, 11, 13, 15};
  
    // Initialize the tree.
    for (int i = 0; i < 8; i++) {
      bst_insert(good_nums[i], bst);
    }
  
    // Test containment.
    for (int i = 0; i < 8; i++) {
      assert(bst_contains(good_nums[i], bst) == 1);
    }
    printf("== Verified that BST contains all the expected values.\n");
  
    for (int i = 0; i < 8; i++) {
      assert(bst_contains(bad_nums[i], bst) == 0);
    }
    printf("== Verified that BST contains none of the unexpected values.\n");
  
    /*
     * Test removal by removing one good number at a time and making sure the
     * remaining good numbers are still in the tree.
     */
    for (int i = 0; i < 8; i++) {
      bst_remove(good_nums[i], bst);
      assert(!bst_contains(good_nums[i], bst));
      for (int j = i + 1; j < 8; j++) {
        assert(bst_contains(good_nums[j], bst));
      }
    }
    printf("== Verified removal works as expected.\n");
  
    bst_free(bst);
}

int main(int argc, char** argv) {
    test_bst();
}
