
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

#include <stdlib.h>

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


/* malloc() / free() testing */

#ifdef ALLOC_TESTING
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

#endif

struct _RBTreeNode {
	RBTreeNodeColor color;
	RBTreeKey key;
	RBTreeValue value;
	RBTreeNode *parent;
	RBTreeNode *children[2];
};

struct _RBTree {
	RBTreeNode *root_node;
	RBTreeCompareFunc compare_func;
	int num_nodes;
};

static RBTreeNodeSide rb_tree_node_side(RBTreeNode *node)
{
	if (node->parent->children[RB_TREE_NODE_LEFT] == node) {
		return RB_TREE_NODE_LEFT;
	} else {
		return RB_TREE_NODE_RIGHT;
	}
}

static RBTreeNode *rb_tree_node_sibling(RBTreeNode *node)
{
	RBTreeNodeSide side;

	side = rb_tree_node_side(node);

	return node->parent->children[1 - side];
}

RBTreeNode *rb_tree_node_uncle(RBTreeNode *node)
{
	return rb_tree_node_sibling(node->parent);
}

/* Replace node1 with node2 at its parent. */

static void rb_tree_node_replace(RBTree *tree, RBTreeNode *node1,
                                 RBTreeNode *node2)
{
	int side;

	/* Set the node's parent pointer. */

	if (node2 != NULL) {
		node2->parent = node1->parent;
	}

	/* The root node? */

	if (node1->parent == NULL) {
		tree->root_node = node2;
	} else {
		side = rb_tree_node_side(node1);
		node1->parent->children[side] = node2;
	}
}

/* Rotate a section of the tree.  'node' is the node at the top
 * of the section to be rotated.  'direction' is the direction in
 * which to rotate the tree: left or right, as shown in the following
 * diagram:
 *
 * Left rotation:              Right rotation:
 *
 *      B                             D
 *     / \                           / \
 *    A   D                         B   E
 *       / \                       / \
 *      C   E                     A   C

 * is rotated to:              is rotated to:
 *
 *        D                           B
 *       / \                         / \
 *      B   E                       A   D
 *     / \                             / \
 *    A   C                           C   E
 */

static RBTreeNode *rb_tree_rotate(RBTree *tree, RBTreeNode *node,
                                  RBTreeNodeSide direction)
{
	RBTreeNode *new_root;

	/* The child of this node will take its place:
	   for a left rotation, it is the right child, and vice versa. */

	new_root = node->children[1-direction];

	/* Make new_root the root, update parent pointers. */

	rb_tree_node_replace(tree, node, new_root);

	/* Rearrange pointers */

	node->children[1-direction] = new_root->children[direction];
	new_root->children[direction] = node;

	/* Update parent references */

	node->parent = new_root;

	if (node->children[1-direction] != NULL) {
		node->children[1-direction]->parent = node;
	}

	return new_root;
}


RBTree *rb_tree_new(RBTreeCompareFunc compare_func)
{
	RBTree *new_tree;

	new_tree = malloc(sizeof(RBTree));

	if (new_tree == NULL) {
		return NULL;
	}

	new_tree->root_node = NULL;
	new_tree->num_nodes = 0;
	new_tree->compare_func = compare_func;

	return new_tree;
}

static void rb_tree_free_subtree(RBTreeNode *node)
{
	if (node != NULL) {
		/* Recurse to subnodes */

		rb_tree_free_subtree(node->children[RB_TREE_NODE_LEFT]);
		rb_tree_free_subtree(node->children[RB_TREE_NODE_RIGHT]);

		/* Free this node */

		free(node);
	}
}

void rb_tree_free(RBTree *tree)
{
	/* Free all nodes in the tree */

	rb_tree_free_subtree(tree->root_node);

	/* Free back the main tree structure */

	free(tree);
}

static void rb_tree_insert_case1(RBTree *tree, RBTreeNode *node);
static void rb_tree_insert_case2(RBTree *tree, RBTreeNode *node);
static void rb_tree_insert_case3(RBTree *tree, RBTreeNode *node);
static void rb_tree_insert_case4(RBTree *tree, RBTreeNode *node);
static void rb_tree_insert_case5(RBTree *tree, RBTreeNode *node);

/* Insert case 1: If the new node is at the root of the tree, it must
 * be recolored black, as the root is always black. */

static void rb_tree_insert_case1(RBTree *tree, RBTreeNode *node)
{
	if (node->parent == NULL) {

		/* The root node is black */

		node->color = RB_TREE_NODE_BLACK;

	} else {

		/* Not root */

		rb_tree_insert_case2(tree, node);
	}
}

/* Insert case 2: If the parent of the new node is red, this
 * conflicts with the red-black tree conditions, as both children
 * of every red node are black. */

static void rb_tree_insert_case2(RBTree *tree, RBTreeNode *node)
{
	/* Note that if this function is being called, we already know
	 * the node has a parent, as it is not the root node. */

	if (node->parent->color != RB_TREE_NODE_BLACK) {
		rb_tree_insert_case3(tree, node);
	}
}

/* Insert case 3: If the parent and uncle are both red, repaint them
 * both black and repaint the grandparent red.  */

static void rb_tree_insert_case3(RBTree *tree, RBTreeNode *node)
{
	RBTreeNode *grandparent;
	RBTreeNode *uncle;

	/* Note that the node must have a grandparent, as the parent
	 * is red, and the root node is always black. */

	grandparent = node->parent->parent;
	uncle = rb_tree_node_uncle(node);

	if (uncle != NULL && uncle->color == RB_TREE_NODE_RED) {

		node->parent->color = RB_TREE_NODE_BLACK;
		uncle->color = RB_TREE_NODE_BLACK;
		grandparent->color = RB_TREE_NODE_RED;

		/* Recurse to grandparent */

		rb_tree_insert_case1(tree, grandparent);

	} else {
		rb_tree_insert_case4(tree, node);
	}
}

/* Case 4: If the parent is red, but the uncle is black, we need to do
 * some rotations to keep the tree balanced and complying with the tree
 * conditions.  If the node is on the opposite side relative to its parent
 * as the parent is relative to its grandparent, rotate around the
 * parent.  Either way, we will continue to case 5.
 *
 * eg.
 *
 *         B                              B
 *        / \                            / \
 *       R   B          ->     node ->  R   B
 *        \                            /
 *         R  <- node                 R
 *
 */

void rb_tree_insert_case4(RBTree *tree, RBTreeNode *node)
{
	RBTreeNode *next_node;
	RBTreeNodeSide side;

	/* Note that at this point, by implication from case 3, we know
	 * that the parent is red, but the uncle is black.  We therefore
	 * only need to examine what side the node is on relative
	 * to its parent, and the side the parent is on relative to
	 * the grandparent. */

	side = rb_tree_node_side(node);

	if (side != rb_tree_node_side(node->parent)) {

		/* After the rotation, we will continue to case 5, but
		 * the parent node will be at the bottom. */

		next_node = node->parent;

		/* Rotate around the parent in the opposite direction
		 * to side. */

		rb_tree_rotate(tree, node->parent, 1-side);
	} else {
		next_node = node;
	}

	rb_tree_insert_case5(tree, next_node);
}

/* Case 5: The node is on the same side relative to its parent as the
 * parent is relative to its grandparent.  The node and its parent are
 * red, but the uncle is black.
 *
 * Now, rotate at the grandparent and recolor the parent and grandparent
 * to black and red respectively.
 *
 *               G/B                 P/B
 *              /   \               /   \
 *           P/R     U/B    ->   N/R     G/R
 *          /   \                       /   \
 *       N/R      ?                   ?      U/B
 *
 */

void rb_tree_insert_case5(RBTree *tree, RBTreeNode *node)
{
	RBTreeNode *parent;
	RBTreeNode *grandparent;
	RBTreeNodeSide side;

	parent = node->parent;
	grandparent = parent->parent;

	/* What side are we, relative to the parent?  This will determine
	 * the direction that we rotate. */

	side = rb_tree_node_side(node);

	/* Rotate at the grandparent, in the opposite direction to side. */

	rb_tree_rotate(tree, grandparent, 1-side);

	/* Recolor the (old) parent and grandparent. */

	parent->color = RB_TREE_NODE_BLACK;
	grandparent->color = RB_TREE_NODE_RED;
}

RBTreeNode *rb_tree_insert(RBTree *tree, RBTreeKey key, RBTreeValue value)
{
	RBTreeNode *node;
	RBTreeNode **rover;
	RBTreeNode *parent;
	RBTreeNodeSide side;

	/* Allocate a new node */

	node = malloc(sizeof(RBTreeNode));

	if (node == NULL) {
		return NULL;
	}

	/* Set up structure.  Initially, the node is red. */

	node->key = key;
	node->value = value;
	node->color = RB_TREE_NODE_RED;
	node->children[RB_TREE_NODE_LEFT] = NULL;
	node->children[RB_TREE_NODE_RIGHT] = NULL;

	/* First, perform a normal binary tree-style insert. */

	parent = NULL;
	rover = &tree->root_node;

	while (*rover != NULL) {

		/* Update parent */

		parent = *rover;

		/* Choose which path to go down, left or right child */

		if (tree->compare_func(value, (*rover)->value) < 0) {
			side = RB_TREE_NODE_LEFT;
		} else {
			side = RB_TREE_NODE_RIGHT;
		}

		rover = &(*rover)->children[side];
	}

	/* Insert at the position we have reached */

	*rover = node;
	node->parent = parent;

	/* Possibly reorder the tree. */

	rb_tree_insert_case1(tree, node);

	/* Update the node count */

	++tree->num_nodes;

	return node;
}

RBTreeNode *rb_tree_lookup_node(RBTree *tree, RBTreeKey key)
{
	RBTreeNode *node;
	RBTreeNodeSide side;
	int diff;

	node = tree->root_node;

	/* Search down the tree. */

	while (node != NULL) {
		diff = tree->compare_func(key, node->key);

		if (diff == 0) {
			return node;
		} else if (diff < 0) {
			side = RB_TREE_NODE_LEFT;
		} else {
			side = RB_TREE_NODE_RIGHT;
		}

		node = node->children[side];
	}

	/* Not found. */

	return NULL;
}

RBTreeValue rb_tree_lookup(RBTree *tree, RBTreeKey key)
{
	RBTreeNode *node;

	/* Find the node for this key. */

	node = rb_tree_lookup_node(tree, key);

	if (node == NULL) {
		return RB_TREE_NULL;
	} else {
		return node->value;
	}
}

void rb_tree_remove_node(RBTree *tree, RBTreeNode *node)
{
	/* TODO */
}

int rb_tree_remove(RBTree *tree, RBTreeKey key)
{
	RBTreeNode *node;

	/* Find the node to remove. */

	node = rb_tree_lookup_node(tree, key);

	if (node == NULL) {
		return 0;
	}

	rb_tree_remove_node(tree, node);

	return 1;
}

RBTreeNode *rb_tree_root_node(RBTree *tree)
{
	return tree->root_node;
}

RBTreeKey rb_tree_node_key(RBTreeNode *node)
{
	return node->key;
}

RBTreeValue rb_tree_node_value(RBTreeNode *node)
{
	return node->value;
}

RBTreeNode *rb_tree_node_child(RBTreeNode *node, RBTreeNodeSide side)
{
	if (side == RB_TREE_NODE_LEFT || side == RB_TREE_NODE_RIGHT) {
		return node->children[side];
	} else {
		return NULL;
	}
}

RBTreeNode *rb_tree_node_parent(RBTreeNode *node)
{
	return node->parent;
}

RBTreeValue *rb_tree_to_array(RBTree *tree)
{
	/* TODO */
	return NULL;
}

int rb_tree_num_entries(RBTree *tree)
{
	return tree->num_nodes;
}

