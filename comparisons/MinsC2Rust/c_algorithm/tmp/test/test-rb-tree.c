/*

Copyright (c) 2008, Simon Howard

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

Copyright (c) 2008, Simon Howard

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

/** @file rbtree.h
 *
 * @brief Balanced binary tree
 *
 * The red-black tree structure is a balanced binary tree which stores
 * a collection of nodes (see @ref RBTreeNode).  Each node has
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
 * To create a new red-black tree, use @ref rb_tree_new.  To destroy
 * a red-black tree, use @ref rb_tree_free.
 *
 * To insert a new key-value pair into a red-black tree, use
 * @ref rb_tree_insert.  To remove an entry from a
 * red-black tree, use @ref rb_tree_remove or @ref rb_tree_remove_node.
 *
 * To search a red-black tree, use @ref rb_tree_lookup or
 * @ref rb_tree_lookup_node.
 *
 * Tree nodes can be queried using the
 * @ref rb_tree_node_left_child,
 * @ref rb_tree_node_right_child,
 * @ref rb_tree_node_parent,
 * @ref rb_tree_node_key and
 * @ref rb_tree_node_value functions.
 */

#ifndef ALGORITHM_RB_TREE_H
#define ALGORITHM_RB_TREE_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A red-black tree balanced binary tree.
 *
 * @see rb_tree_new
 */

typedef struct _RBTree RBTree;

/**
 * A key for an @ref RBTree.
 */

typedef void *RBTreeKey;

/**
 * A value stored in an @ref RBTree.
 */

typedef void *RBTreeValue;

/**
 * A null @ref RBTreeValue.
 */

#define RB_TREE_NULL ((void *) 0)

/**
 * A node in a red-black tree.
 *
 * @see rb_tree_node_left_child
 * @see rb_tree_node_right_child
 * @see rb_tree_node_parent
 * @see rb_tree_node_key
 * @see rb_tree_node_value
 */

typedef struct _RBTreeNode RBTreeNode;

/**
 * Type of function used to compare keys in a red-black tree.
 *
 * @param data1            The first key.
 * @param data2            The second key.
 * @return                 A negative number if data1 should be sorted
 *                         before data2, a positive number if data2 should
 *                         be sorted before data1, zero if the two keys
 *                         are equal.
 */

typedef int (*RBTreeCompareFunc)(RBTreeValue data1, RBTreeValue data2);

/**
 * Each node in a red-black tree is either red or black.
 */

typedef enum {
	RB_TREE_NODE_RED,
	RB_TREE_NODE_BLACK,
} RBTreeNodeColor;

/**
 * A @ref RBTreeNode can have left and right children.
 */

typedef enum {
	RB_TREE_NODE_LEFT = 0,
	RB_TREE_NODE_RIGHT = 1
} RBTreeNodeSide;

/**
 * Create a new red-black tree.
 *
 * @param compare_func    Function to use when comparing keys in the tree.
 * @return                A new red-black tree, or NULL if it was not possible
 *                        to allocate the memory.
 */

RBTree *rb_tree_new(RBTreeCompareFunc compare_func);

/**
 * Destroy a red-black tree.
 *
 * @param tree            The tree to destroy.
 */

void rb_tree_free(RBTree *tree);

/**
 * Insert a new key-value pair into a red-black tree.
 *
 * @param tree            The tree.
 * @param key             The key to insert.
 * @param value           The value to insert.
 * @return                The newly created tree node containing the
 *                        key and value, or NULL if it was not possible
 *                        to allocate the new memory.
 */

RBTreeNode *rb_tree_insert(RBTree *tree, RBTreeKey key, RBTreeValue value);

/**
 * Remove a node from a tree.
 *
 * @param tree            The tree.
 * @param node            The node to remove
 */

void rb_tree_remove_node(RBTree *tree, RBTreeNode *node);

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

int rb_tree_remove(RBTree *tree, RBTreeKey key);

/**
 * Search a red-black tree for a node with a particular key.  This uses
 * the tree as a mapping.
 *
 * @param tree            The red-black tree to search.
 * @param key             The key to search for.
 * @return                The tree node containing the given key, or NULL
 *                        if no entry with the given key is found.
 */

RBTreeNode *rb_tree_lookup_node(RBTree *tree, RBTreeKey key);

/**
 * Search a red-black tree for a value corresponding to a particular key.
 * This uses the tree as a mapping.  Note that this performs
 * identically to @ref rb_tree_lookup_node, except that the value
 * at the node is returned rather than the node itself.
 *
 * @param tree            The red-black tree to search.
 * @param key             The key to search for.
 * @return                The value associated with the given key, or
 *                        RB_TREE_NULL if no entry with the given key is
 *                        found.
 */

RBTreeValue rb_tree_lookup(RBTree *tree, RBTreeKey key);

/**
 * Find the root node of a tree.
 *
 * @param tree            The tree.
 * @return                The root node of the tree, or NULL if the tree is
 *                        empty.
 */

RBTreeNode *rb_tree_root_node(RBTree *tree);

/**
 * Retrieve the key for a given tree node.
 *
 * @param node            The tree node.
 * @return                The key to the given node.
 */

RBTreeKey rb_tree_node_key(RBTreeNode *node);

/**
 * Retrieve the value at a given tree node.
 *
 * @param node            The tree node.
 * @return                The value at the given node.
 */

RBTreeValue rb_tree_node_value(RBTreeNode *node);

/**
 * Get a child of a given tree node.
 *
 * @param node            The tree node.
 * @param side            The side relative to the node.
 * @return                The child of the tree node, or NULL if the
 *                        node has no child on the specified side.
 */

RBTreeNode *rb_tree_node_child(RBTreeNode *node, RBTreeNodeSide side);

/**
 * Find the parent node of a given tree node.
 *
 * @param node            The tree node.
 * @return                The parent node of the tree node, or NULL if
 *                        this is the root node.
 */

RBTreeNode *rb_tree_node_parent(RBTreeNode *node);

/**
 * Find the height of a subtree.
 *
 * @param node            The root node of the subtree.
 * @return                The height of the subtree.
 */

int rb_tree_subtree_height(RBTreeNode *node);

/**
 * Convert the keys in a red-black tree into a C array.  This allows
 * the tree to be used as an ordered set.
 *
 * @param tree            The tree.
 * @return                A newly allocated C array containing all the keys
 *                        in the tree, in order.  The length of the array
 *                        is equal to the number of entries in the tree
 *                        (see @ref rb_tree_num_entries).
 */

RBTreeValue *rb_tree_to_array(RBTree *tree);

/**
 * Retrieve the number of entries in the tree.
 *
 * @param tree            The tree.
 * @return                The number of key-value pairs stored in the tree.
 */

int rb_tree_num_entries(RBTree *tree);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_RB_TREE_H */

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

static void print_tree(RBTreeNode *node, int depth)
{
	int *value;
	int i;

	if (node == NULL) {
		return;
	}

	print_tree(rb_tree_node_child(node, RB_TREE_NODE_LEFT), depth + 1);

	for (i=0; i<depth*6; ++i) {
		printf(" ");
	}

	value = rb_tree_node_key(node);
	printf("%i\n", *value);

	print_tree(rb_tree_node_child(node, RB_TREE_NODE_RIGHT), depth + 1);
}
#endif

int find_subtree_height(RBTreeNode *node)
{
	RBTreeNode *left_subtree;
	RBTreeNode *right_subtree;
	int left_height, right_height;

	if (node == NULL) {
		return 0;
	}

	left_subtree = rb_tree_node_child(node, RB_TREE_NODE_LEFT);
	right_subtree = rb_tree_node_child(node, RB_TREE_NODE_RIGHT);
	left_height = find_subtree_height(left_subtree);
	right_height = find_subtree_height(right_subtree);

	if (left_height > right_height) {
		return left_height + 1;
	} else {
		return right_height + 1;
	}
}

void validate_tree(RBTree *tree)
{
}

RBTree *create_tree(void)
{
	RBTree *tree;
	int i;

	/* Create a tree and fill with nodes */

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		rb_tree_insert(tree, &test_array[i], &test_array[i]);
	}

	return tree;
}

void test_rb_tree_new(void)
{
	RBTree *tree;

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	assert(tree != NULL);
	assert(rb_tree_root_node(tree) == NULL);
	assert(rb_tree_num_entries(tree) == 0);

	rb_tree_free(tree);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	assert(tree == NULL);

}

void test_rb_tree_insert_lookup(void)
{
	RBTree *tree;
	RBTreeNode *node;
	int i;
	int *value;

	/* Create a tree containing some values. Validate the
	 * tree is consistent at all stages. */

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		rb_tree_insert(tree, &test_array[i], &test_array[i]);

		assert(rb_tree_num_entries(tree) == i + 1);
		validate_tree(tree);
	}

	assert(rb_tree_root_node(tree) != NULL);

	/* Check that all values can be read back again */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		node = rb_tree_lookup_node(tree, &i);
		assert(node != NULL);
		value = rb_tree_node_key(node);
		assert(*value == i);
		value = rb_tree_node_value(node);
		assert(*value == i);
	}

	/* Check that invalid nodes are not found */

	i = -1;
	assert(rb_tree_lookup_node(tree, &i) == NULL);
	i = NUM_TEST_VALUES + 100;
	assert(rb_tree_lookup_node(tree, &i) == NULL);

	rb_tree_free(tree);
}

void test_rb_tree_child(void)
{
	RBTree *tree;
	RBTreeNode *root;
	RBTreeNode *left;
	RBTreeNode *right;
	int values[] = { 1, 2, 3 };
	int *p;
	int i;

	/* Create a tree containing some values. Validate the
	 * tree is consistent at all stages. */

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	for (i=0; i<3; ++i) {
		rb_tree_insert(tree, &values[i], &values[i]);
	}

	/* Check the tree */

	root = rb_tree_root_node(tree);
	p = rb_tree_node_value(root);
	assert(*p == 2);

	left = rb_tree_node_child(root, RB_TREE_NODE_LEFT);
	p = rb_tree_node_value(left);
	assert(*p == 1);

	right = rb_tree_node_child(root, RB_TREE_NODE_RIGHT);
	p = rb_tree_node_value(right);
	assert(*p == 3);

	/* Check invalid values */

	assert(rb_tree_node_child(root, 10000) == NULL);
	assert(rb_tree_node_child(root, 2) == NULL);

	rb_tree_free(tree);
}

void test_out_of_memory(void)
{
	RBTree *tree;
	RBTreeNode *node;
	int i;

	/* Create a tree */

	tree = create_tree();

	/* Set a limit to stop any more entries from being added. */

	alloc_test_set_limit(0);

	/* Try to add some more nodes and verify that this fails. */

	for (i=10000; i<20000; ++i) {
		node = rb_tree_insert(tree, &i, &i);
		assert(node == NULL);
		validate_tree(tree);
	}

	rb_tree_free(tree);
}

void test_rb_tree_free(void)
{
	RBTree *tree;

	/* Try freeing an empty tree */

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);
	rb_tree_free(tree);

	/* Create a big tree and free it */

	tree = create_tree();
	rb_tree_free(tree);
}

void test_rb_tree_lookup(void)
{
	RBTree *tree;
	int i;
	int *value;

	/* Create a tree and look up all values */

	tree = create_tree();

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		value = rb_tree_lookup(tree, &i);

		assert(value != NULL);
		assert(*value == i);
	}

	/* Test invalid values */

	i = -1;
	assert(rb_tree_lookup(tree, &i) == NULL);
	i = NUM_TEST_VALUES + 1;
	assert(rb_tree_lookup(tree, &i) == NULL);
	i = 8724897;
	assert(rb_tree_lookup(tree, &i) == NULL);

	rb_tree_free(tree);
}

void test_rb_tree_remove(void)
{
	RBTree *tree;
	int i;
	int x, y, z;
	int value;
	int expected_entries;

	tree = create_tree();

	/* Try removing invalid entries */

	i = NUM_TEST_VALUES + 100;
	assert(rb_tree_remove(tree, &i) == 0);
	i = -1;
	assert(rb_tree_remove(tree, &i) == 0);

	/* Delete the nodes from the tree */

	expected_entries = NUM_TEST_VALUES;

	/* This looping arrangement causes nodes to be removed in a
	 * randomish fashion from all over the tree. */

	for (x=0; x<10; ++x) {
		for (y=0; y<10; ++y) {
			for (z=0; z<10; ++z) {
				value = z * 100 + (9 - y) * 10 + x;
				assert(rb_tree_remove(tree, &value) != 0);
				validate_tree(tree);
				expected_entries -= 1;
				assert(rb_tree_num_entries(tree)
				       == expected_entries);
			}
		}
	}

	/* All entries removed, should be empty now */

	assert(rb_tree_root_node(tree) == NULL);

	rb_tree_free(tree);
}

void test_rb_tree_to_array(void)
{
	RBTree *tree;
	int entries[] = { 89, 23, 42, 4, 16, 15, 8, 99, 50, 30 };
	int sorted[]  = { 4, 8, 15, 16, 23, 30, 42, 50, 89, 99 };
	int num_entries = sizeof(entries) / sizeof(int);
	int i;
	int **array;

	/* Add all entries to the tree */

	tree = rb_tree_new((RBTreeCompareFunc) int_compare);

	for (i=0; i<num_entries; ++i) {
		rb_tree_insert(tree, &entries[i], NULL);
	}

	assert(rb_tree_num_entries(tree) == num_entries);

	/* Convert to an array and check the contents */

	array = (int **) rb_tree_to_array(tree);

	for (i=0; i<num_entries; ++i) {
		assert(*array[i] == sorted[i]);
	}

	free(array);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	array = (int **) rb_tree_to_array(tree);
	assert(array == NULL);
	validate_tree(tree);

	rb_tree_free(tree);
}

static UnitTestFunction tests[] = {
	test_rb_tree_new,
	test_rb_tree_free,
	test_rb_tree_child,
	test_rb_tree_insert_lookup,
	test_rb_tree_lookup,
	/*test_rb_tree_remove,*/
	/*test_rb_tree_to_array,*/
	test_out_of_memory,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}


