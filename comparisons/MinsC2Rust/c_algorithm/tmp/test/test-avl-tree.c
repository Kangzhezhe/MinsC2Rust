/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file alloc-testing.h
 *
 * @brief Memory allocation testing framework.
 *
 * This file uses the preprocessor to redefine the standard C dynamic memory
 * allocation functions for testing purposes.  This allows checking that
 * code under test correctly frees back all memory allocated, as well as
 * the ability to impose artificial limits on allocation, to test that
 * code correctly handles out-of-memory scenarios.
 */

#ifndef ALLOC_TESTING_H
#define ALLOC_TESTING_H

/* Don't redefine the functions in the alloc-testing.c, as we need the
 * standard malloc/free functions. */

#ifndef ALLOC_TESTING_C
#undef malloc
#define malloc   alloc_test_malloc
#undef free
#define free     alloc_test_free
#undef realloc
#define realloc  alloc_test_realloc
#undef calloc
#define calloc   alloc_test_calloc
#undef strdup
#define strdup   alloc_test_strdup
#endif

/**
 * Allocate a block of memory.
 *
 * @param bytes          Number of bytes to allocate.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_malloc(size_t bytes);

/**
 * Free a block of memory.
 *
 * @param ptr            Pointer to the block to free.
 */

void alloc_test_free(void *ptr);

/**
 * Reallocate a previously-allocated block to a new size, preserving
 * contents.
 *
 * @param ptr            Pointer to the existing block.
 * @param bytes          Size of the new block, in bytes.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_realloc(void *ptr, size_t bytes);

/**
 * Allocate a block of memory for an array of structures, initialising
 * the contents to zero.
 *
 * @param nmemb          Number of structures to allocate for.
 * @param bytes          Size of each structure, in bytes.
 * @return               Pointer to the new memory block for the array,
 *                       or NULL if it was not possible to allocate the
 *                       new block.
 */

void *alloc_test_calloc(size_t nmemb, size_t bytes);

/**
 * Allocate a block of memory containing a copy of a string.
 *
 * @param string         The string to copy.
 * @return               Pointer to the new memory block containing the
 *                       copied string, or NULL if it was not possible
 *                       to allocate the new block.
 */

char *alloc_test_strdup(const char *string);

/**
 * Set an artificial limit on the amount of memory that can be
 * allocated.
 *
 * @param alloc_count    Number of allocations that are possible after
 *                       this call.  For example, if this has a value
 *                       of 3, malloc() can be called successfully
 *                       three times, but all allocation attempts
 *                       after this will fail.  If this has a negative
 *                       value, the allocation limit is disabled.
 */

void alloc_test_set_limit(signed int alloc_count);

/**
 * Get a count of the number of bytes currently allocated.
 *
 * @return               The number of bytes currently allocated by
 *                       the allocation system.
 */

size_t alloc_test_get_allocated(void);

#endif /* #ifndef ALLOC_TESTING_H */

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file framework.h
 *
 * @brief Framework for running unit tests.
 */

/**
 * A unit test.
 */

typedef void (*UnitTestFunction)(void);

/**
 * Run a list of unit tests.  The provided array contains a list of
 * pointers to test functions to invoke; the last entry is denoted
 * by a NULL pointer.
 *
 * @param tests          List of tests to invoke.
 */

void run_tests(UnitTestFunction *tests);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef TEST_FRAMEWORK_H */


_Atomic size_t num_assert = 0;
#undef assert
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */                                                           \
     else                                                                      \
       __assert_fail(#expr, __FILE__, __LINE__, __ASSERT_FUNCTION);            \
   }))

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/** @file avl-tree.h
 *
 * @brief Balanced binary tree
 *
 * The AVL tree structure is a balanced binary tree which stores
 * a collection of nodes (see @ref AVLTreeNode).  Each node has
 * a key and a value associated with it.  The nodes are sorted
 * within the tree based on the order of their keys. Modifications
 * to the tree are constructed such that the tree remains
 * balanced at all times (there are always roughly equal numbers
 * of nodes on either side of the tree).
 *
 * Balanced binary trees have several uses.  They can be used
 * as a mapping (searching for a value based on its key), or
 * as a set of keys which is always ordered.
 *
 * To create a new AVL tree, use @ref avl_tree_new.  To destroy
 * an AVL tree, use @ref avl_tree_free.
 *
 * To insert a new key-value pair into an AVL tree, use
 * @ref avl_tree_insert.  To remove an entry from an
 * AVL tree, use @ref avl_tree_remove or @ref avl_tree_remove_node.
 *
 * To search an AVL tree, use @ref avl_tree_lookup or
 * @ref avl_tree_lookup_node.
 *
 * Tree nodes can be queried using the
 * @ref avl_tree_node_child,
 * @ref avl_tree_node_parent,
 * @ref avl_tree_node_key and
 * @ref avl_tree_node_value functions.
 */

#ifndef ALGORITHM_AVLTREE_H
#define ALGORITHM_AVLTREE_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * An AVL tree balanced binary tree.
 *
 * @see avl_tree_new
 */

typedef struct _AVLTree AVLTree;

/**
 * A key for an @ref AVLTree.
 */

typedef void *AVLTreeKey;

/**
 * A value stored in an @ref AVLTree.
 */

typedef void *AVLTreeValue;

/**
 * A null @ref AVLTreeValue.
 */

#define AVL_TREE_NULL ((void *) 0)

/**
 * A node in an AVL tree.
 *
 * @see avl_tree_node_left_child
 * @see avl_tree_node_right_child
 * @see avl_tree_node_parent
 * @see avl_tree_node_key
 * @see avl_tree_node_value
 */

typedef struct _AVLTreeNode AVLTreeNode;

/**
 * An @ref AVLTreeNode can have left and right children.
 */

typedef enum {
	AVL_TREE_NODE_LEFT = 0,
	AVL_TREE_NODE_RIGHT = 1
} AVLTreeNodeSide;

/**
 * Type of function used to compare keys in an AVL tree.
 *
 * @param value1           The first key.
 * @param value2           The second key.
 * @return                 A negative number if value1 should be sorted
 *                         before value2, a positive number if value2 should
 *                         be sorted before value1, zero if the two keys
 *                         are equal.
 */

typedef int (*AVLTreeCompareFunc)(AVLTreeValue value1, AVLTreeValue value2);

/**
 * Create a new AVL tree.
 *
 * @param compare_func    Function to use when comparing keys in the tree.
 * @return                A new AVL tree, or NULL if it was not possible
 *                        to allocate the memory.
 */

AVLTree *avl_tree_new(AVLTreeCompareFunc compare_func);

/**
 * Destroy an AVL tree.
 *
 * @param tree            The tree to destroy.
 */

void avl_tree_free(AVLTree *tree);

/**
 * Insert a new key-value pair into an AVL tree.
 *
 * @param tree            The tree.
 * @param key             The key to insert.
 * @param value           The value to insert.
 * @return                The newly created tree node containing the
 *                        key and value, or NULL if it was not possible
 *                        to allocate the new memory.
 */

AVLTreeNode *avl_tree_insert(AVLTree *tree, AVLTreeKey key,
                             AVLTreeValue value);

/**
 * Remove a node from a tree.
 *
 * @param tree            The tree.
 * @param node            The node to remove
 */

void avl_tree_remove_node(AVLTree *tree, AVLTreeNode *node);

/**
 * Remove an entry from a tree, specifying the key of the node to
 * remove.
 *
 * @param tree            The tree.
 * @param key             The key of the node to remove.
 * @return                Zero (false) if no node with the specified key was
 *                        found in the tree, non-zero (true) if a node with
 *                        the specified key was removed.
 */

int avl_tree_remove(AVLTree *tree, AVLTreeKey key);

/**
 * Search an AVL tree for a node with a particular key.  This uses
 * the tree as a mapping.
 *
 * @param tree            The AVL tree to search.
 * @param key             The key to search for.
 * @return                The tree node containing the given key, or NULL
 *                        if no entry with the given key is found.
 */

AVLTreeNode *avl_tree_lookup_node(AVLTree *tree, AVLTreeKey key);

/**
 * Search an AVL tree for a value corresponding to a particular key.
 * This uses the tree as a mapping.  Note that this performs
 * identically to @ref avl_tree_lookup_node, except that the value
 * at the node is returned rather than the node itself.
 *
 * @param tree            The AVL tree to search.
 * @param key             The key to search for.
 * @return                The value associated with the given key, or
 *                        @ref AVL_TREE_NULL if no entry with the given key is
 *                        found.
 */

AVLTreeValue avl_tree_lookup(AVLTree *tree, AVLTreeKey key);

/**
 * Find the root node of a tree.
 *
 * @param tree            The tree.
 * @return                The root node of the tree, or NULL if the tree is
 *                        empty.
 */

AVLTreeNode *avl_tree_root_node(AVLTree *tree);

/**
 * Retrieve the key for a given tree node.
 *
 * @param node            The tree node.
 * @return                The key to the given node.
 */

AVLTreeKey avl_tree_node_key(AVLTreeNode *node);

/**
 * Retrieve the value at a given tree node.
 *
 * @param node            The tree node.
 * @return                The value at the given node.
 */

AVLTreeValue avl_tree_node_value(AVLTreeNode *node);

/**
 * Find the child of a given tree node.
 *
 * @param node            The tree node.
 * @param side            Which child node to get (left or right)
 * @return                The child of the tree node, or NULL if the
 *                        node has no child on the given side.
 */

AVLTreeNode *avl_tree_node_child(AVLTreeNode *node, AVLTreeNodeSide side);

/**
 * Find the parent node of a given tree node.
 *
 * @param node            The tree node.
 * @return                The parent node of the tree node, or NULL if
 *                        this is the root node.
 */

AVLTreeNode *avl_tree_node_parent(AVLTreeNode *node);

/**
 * Find the height of a subtree.
 *
 * @param node            The root node of the subtree.
 * @return                The height of the subtree.
 */

int avl_tree_subtree_height(AVLTreeNode *node);

/**
 * Convert the keys in an AVL tree into a C array.  This allows
 * the tree to be used as an ordered set.
 *
 * @param tree            The tree.
 * @return                A newly allocated C array containing all the keys
 *                        in the tree, in order.  The length of the array
 *                        is equal to the number of entries in the tree
 *                        (see @ref avl_tree_num_entries).
 */

AVLTreeValue *avl_tree_to_array(AVLTree *tree);

/**
 * Retrieve the number of entries in the tree.
 *
 * @param tree            The tree.
 * @return                The number of key-value pairs stored in the tree.
 */

unsigned int avl_tree_num_entries(AVLTree *tree);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_AVLTREE_H */

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file compare-int.h
 *
 * Comparison functions for pointers to integers.
 *
 * To find the difference between two values pointed at, use
 * @ref int_compare.
 *
 * To find if two values pointed at are equal, use @ref int_equal.
 */

#ifndef ALGORITHM_COMPARE_INT_H
#define ALGORITHM_COMPARE_INT_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compare the integer values pointed at by two pointers to determine
 * if they are equal.
 *
 * @param location1       Pointer to the first value to compare.
 * @param location2       Pointer to the second value to compare.
 * @return                Non-zero if the two values are equal, zero if the
 *                        two values are not equal.
 */

int int_equal(void *location1, void *location2);

/**
 * Compare the integer values pointed at by two pointers.
 *
 * @param location1        Pointer to the first value to compare.
 * @param location2        Pointer to the second value to compare.
 * @return                 A negative value if the first value is less than
 *                         the second value, a positive value if the first
 *                         value is greater than the second value, zero if
 *                         they are equal.
 */

int int_compare(void *location1, void *location2);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_COMPARE_INT_H */


#define NUM_TEST_VALUES 1000

int test_array[NUM_TEST_VALUES];

#if 0
/* Tree print function - useful for debugging. */

static void print_tree(AVLTreeNode *node, int depth)
{
	int *value;
	int i;

	if (node == NULL) {
		return;
	}

	print_tree(avl_tree_node_child(node, AVL_TREE_NODE_LEFT), depth + 1);

	for (i=0; i<depth*6; ++i) {
		printf(" ");
	}

	value = avl_tree_node_key(node);
	printf("%i\n", *value);

	print_tree(avl_tree_node_child(node, AVL_TREE_NODE_RIGHT), depth + 1);
}
#endif

int find_subtree_height(AVLTreeNode *node)
{
	AVLTreeNode *left_subtree;
	AVLTreeNode *right_subtree;
	int left_height, right_height;

	if (node == NULL) {
		return 0;
	}

	left_subtree = avl_tree_node_child(node, AVL_TREE_NODE_LEFT);
	right_subtree = avl_tree_node_child(node, AVL_TREE_NODE_RIGHT);
	left_height = find_subtree_height(left_subtree);
	right_height = find_subtree_height(right_subtree);

	if (left_height > right_height) {
		return left_height + 1;
	} else {
		return right_height + 1;
	}
}

/* Validates a subtree, returning its height */

int counter;

int validate_subtree(AVLTreeNode *node)
{
	AVLTreeNode *left_node, *right_node;
	int left_height, right_height;
	int *key;

	if (node == NULL) {
		return 0;
	}

	left_node = avl_tree_node_child(node, AVL_TREE_NODE_LEFT);
	right_node = avl_tree_node_child(node, AVL_TREE_NODE_RIGHT);

	/* Check the parent references of the children */

	if (left_node != NULL) {
		assert(avl_tree_node_parent(left_node) == node);
	}
	if (right_node != NULL) {
		assert(avl_tree_node_parent(right_node) == node);
	}

	/* Recursively validate the left and right subtrees,
	 * obtaining the height at the same time. */

	left_height = validate_subtree(left_node);

	/* Check that the keys are in the correct order */

	key = (int *) avl_tree_node_key(node);

	assert(*key > counter);
	counter = *key;

	right_height = validate_subtree(right_node);

	/* Check that the returned height value matches the
	 * result of avl_tree_subtree_height(). */

	assert(avl_tree_subtree_height(left_node) == left_height);
	assert(avl_tree_subtree_height(right_node) == right_height);

	/* Check this node is balanced */

	assert(left_height - right_height < 2 &&
	       right_height - left_height < 2);

	/* Calculate the height of this node */

	if (left_height > right_height) {
		return left_height + 1;
	} else {
		return right_height + 1;
	}
}

void validate_tree(AVLTree *tree)
{
	AVLTreeNode *root_node;
	int height;

	root_node = avl_tree_root_node(tree);

	if (root_node != NULL) {
		height = find_subtree_height(root_node);
		assert(avl_tree_subtree_height(root_node) == height);
	}

	counter = -1;
	validate_subtree(root_node);
}

AVLTree *create_tree(void)
{
	AVLTree *tree;
	int i;

	/* Create a tree and fill with nodes */

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		avl_tree_insert(tree, &test_array[i], &test_array[i]);
	}

	return tree;
}

void test_avl_tree_new(void)
{
	AVLTree *tree;

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	assert(tree != NULL);
	assert(avl_tree_root_node(tree) == NULL);
	assert(avl_tree_num_entries(tree) == 0);

	avl_tree_free(tree);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	assert(tree == NULL);

}

void test_avl_tree_insert_lookup(void)
{
	AVLTree *tree;
	AVLTreeNode *node;
	unsigned int i;
	int *value;

	/* Create a tree containing some values. Validate the
	 * tree is consistent at all stages. */

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = (int) i;
		avl_tree_insert(tree, &test_array[i], &test_array[i]);

		assert(avl_tree_num_entries(tree) == i + 1);
		validate_tree(tree);
	}

	assert(avl_tree_root_node(tree) != NULL);

	/* Check that all values can be read back again */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		node = avl_tree_lookup_node(tree, &i);
		assert(node != NULL);
		value = avl_tree_node_key(node);
		assert(*value == (int) i);
		value = avl_tree_node_value(node);
		assert(*value == (int) i);
	}

	/* Check that invalid nodes are not found */

	i = NUM_TEST_VALUES + 100;
	assert(avl_tree_lookup_node(tree, &i) == NULL);

	avl_tree_free(tree);
}

void test_avl_tree_child(void)
{
	AVLTree *tree;
	AVLTreeNode *root;
	AVLTreeNode *left;
	AVLTreeNode *right;
	int values[] = { 1, 2, 3 };
	int *p;
	int i;

	/* Create a tree containing some values. Validate the
	 * tree is consistent at all stages. */

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	for (i=0; i<3; ++i) {
		avl_tree_insert(tree, &values[i], &values[i]);
	}

	/* Check the tree */

	root = avl_tree_root_node(tree);
	p = avl_tree_node_value(root);
	assert(*p == 2);

	left = avl_tree_node_child(root, AVL_TREE_NODE_LEFT);
	p = avl_tree_node_value(left);
	assert(*p == 1);

	right = avl_tree_node_child(root, AVL_TREE_NODE_RIGHT);
	p = avl_tree_node_value(right);
	assert(*p == 3);

	/* Check invalid values */

	assert(avl_tree_node_child(root, 10000) == NULL);
	assert(avl_tree_node_child(root, 2) == NULL);

	avl_tree_free(tree);
}

void test_out_of_memory(void)
{
	AVLTree *tree;
	AVLTreeNode *node;
	int i;

	/* Create a tree */

	tree = create_tree();

	/* Set a limit to stop any more entries from being added. */

	alloc_test_set_limit(0);

	/* Try to add some more nodes and verify that this fails. */

	for (i=10000; i<20000; ++i) {
		node = avl_tree_insert(tree, &i, &i);
		assert(node == NULL);
		validate_tree(tree);
	}

	avl_tree_free(tree);
}

void test_avl_tree_free(void)
{
	AVLTree *tree;

	/* Try freeing an empty tree */

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);
	avl_tree_free(tree);

	/* Create a big tree and free it */

	tree = create_tree();
	avl_tree_free(tree);
}

void test_avl_tree_lookup(void)
{
	AVLTree *tree;
	int i;
	int *value;

	/* Create a tree and look up all values */

	tree = create_tree();

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		value = avl_tree_lookup(tree, &i);

		assert(value != NULL);
		assert(*value == i);
	}

	/* Test invalid values */

	i = -1;
	assert(avl_tree_lookup(tree, &i) == NULL);
	i = NUM_TEST_VALUES + 1;
	assert(avl_tree_lookup(tree, &i) == NULL);
	i = 8724897;
	assert(avl_tree_lookup(tree, &i) == NULL);

	avl_tree_free(tree);
}

void test_avl_tree_remove(void)
{
	AVLTree *tree;
	int i;
	int x, y, z;
	int value;
	unsigned int expected_entries;

	tree = create_tree();

	/* Try removing invalid entries */

	i = NUM_TEST_VALUES + 100;
	assert(avl_tree_remove(tree, &i) == 0);
	i = -1;
	assert(avl_tree_remove(tree, &i) == 0);

	/* Delete the nodes from the tree */

	expected_entries = NUM_TEST_VALUES;

	/* This looping arrangement causes nodes to be removed in a
	 * randomish fashion from all over the tree. */

	for (x=0; x<10; ++x) {
		for (y=0; y<10; ++y) {
			for (z=0; z<10; ++z) {
				value = z * 100 + (9 - y) * 10 + x;
				assert(avl_tree_remove(tree, &value) != 0);
				validate_tree(tree);
				expected_entries -= 1;
				assert(avl_tree_num_entries(tree)
				       == expected_entries);
			}
		}
	}

	/* All entries removed, should be empty now */

	assert(avl_tree_root_node(tree) == NULL);

	avl_tree_free(tree);
}

void test_avl_tree_to_array(void)
{
	AVLTree *tree;
	int entries[] = { 89, 23, 42, 4, 16, 15, 8, 99, 50, 30 };
	int sorted[]  = { 4, 8, 15, 16, 23, 30, 42, 50, 89, 99 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	unsigned int i;
	int **array;

	/* Add all entries to the tree */

	tree = avl_tree_new((AVLTreeCompareFunc) int_compare);

	for (i=0; i<num_entries; ++i) {
		avl_tree_insert(tree, &entries[i], NULL);
	}

	assert(avl_tree_num_entries(tree) == num_entries);

	/* Convert to an array and check the contents */

	array = (int **) avl_tree_to_array(tree);

	for (i=0; i<num_entries; ++i) {
		assert(*array[i] == sorted[i]);
	}

	free(array);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	array = (int **) avl_tree_to_array(tree);
	assert(array == NULL);
	validate_tree(tree);

	avl_tree_free(tree);
}

static UnitTestFunction tests[] = {
	test_avl_tree_new,
	test_avl_tree_free,
	test_avl_tree_child,
	test_avl_tree_insert_lookup,
	test_avl_tree_lookup,
	test_avl_tree_remove,
	test_avl_tree_to_array,
	test_out_of_memory,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}


