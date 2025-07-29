#include <stdio.h>
#include <assert.h>

#include "bst.h"


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
