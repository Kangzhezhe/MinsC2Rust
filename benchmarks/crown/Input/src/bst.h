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
