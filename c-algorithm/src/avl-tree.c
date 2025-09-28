// 识别到的包含指令
#include <stdlib.h>
#include "avl-tree.h"
#include "alloc-testing.h"

// 识别到的结构体定义
struct _AVLTreeNode {
	AVLTreeNode *children[2];
	AVLTreeNode *parent;
	AVLTreeKey key;
	AVLTreeValue value;
	int height;
};

struct _AVLTree {
	AVLTreeNode *root_node;
	AVLTreeCompareFunc compare_func;
	unsigned int num_nodes;
};

// 识别到的函数定义
// 函数: avl_tree_new (line 47)
AVLTree *avl_tree_new(AVLTreeCompareFunc compare_func)
{
	AVLTree *new_tree;

	new_tree = (AVLTree *) malloc(sizeof(AVLTree));

	if (new_tree == NULL) {
		return NULL;
	}

	new_tree->root_node = NULL;
	new_tree->compare_func = compare_func;
	new_tree->num_nodes = 0;

	return new_tree;
}

// 函数: avl_tree_free_subtree (line 64)
static void avl_tree_free_subtree(AVLTree *tree, AVLTreeNode *node)
{
	if (node == NULL) {
		return;
	}

	avl_tree_free_subtree(tree, node->children[AVL_TREE_NODE_LEFT]);
	avl_tree_free_subtree(tree, node->children[AVL_TREE_NODE_RIGHT]);

	free(node);
}

// 函数: avl_tree_free (line 76)
void avl_tree_free(AVLTree *tree)
{
	/* Destroy all nodes */

	avl_tree_free_subtree(tree, tree->root_node);

	/* Free back the main tree data structure */

	free(tree);
}

// 函数: avl_tree_subtree_height (line 87)
int avl_tree_subtree_height(AVLTreeNode *node)
{
	if (node == NULL) {
		return 0;
	} else {
		return node->height;
	}
}

// 函数: avl_tree_update_height (line 100)
static void avl_tree_update_height(AVLTreeNode *node)
{
	AVLTreeNode *left_subtree;
	AVLTreeNode *right_subtree;
	int left_height, right_height;

	left_subtree = node->children[AVL_TREE_NODE_LEFT];
	right_subtree = node->children[AVL_TREE_NODE_RIGHT];
	left_height = avl_tree_subtree_height(left_subtree);
	right_height = avl_tree_subtree_height(right_subtree);

	if (left_height > right_height) {
		node->height = left_height + 1;
	} else {
		node->height = right_height + 1;
	}
}

// 函数: avl_tree_node_parent_side (line 120)
static AVLTreeNodeSide avl_tree_node_parent_side(AVLTreeNode *node)
{
	if (node->parent->children[AVL_TREE_NODE_LEFT] == node) {
		return AVL_TREE_NODE_LEFT;
	} else {
		return AVL_TREE_NODE_RIGHT;
	}
}

// 函数: avl_tree_node_replace (line 131)
static void avl_tree_node_replace(AVLTree *tree, AVLTreeNode *node1,
                                  AVLTreeNode *node2)
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
		side = avl_tree_node_parent_side(node1);
		node1->parent->children[side] = node2;

		avl_tree_update_height(node1->parent);
	}
}

// 函数: avl_tree_rotate (line 176)
static AVLTreeNode *avl_tree_rotate(AVLTree *tree, AVLTreeNode *node,
                                    AVLTreeNodeSide direction)
{
	AVLTreeNode *new_root;

	/* The child of this node will take its place:
	   for a left rotation, it is the right child, and vice versa. */

	new_root = node->children[1-direction];

	/* Make new_root the root, update parent pointers. */

	avl_tree_node_replace(tree, node, new_root);

	/* Rearrange pointers */

	node->children[1-direction] = new_root->children[direction];
	new_root->children[direction] = node;

	/* Update parent references */

	node->parent = new_root;

	if (node->children[1-direction] != NULL) {
		node->children[1-direction]->parent = node;
	}

	/* Update heights of the affected nodes */

	avl_tree_update_height(new_root);
	avl_tree_update_height(node);

	return new_root;
}

// 函数: avl_tree_node_balance (line 217)
static AVLTreeNode *avl_tree_node_balance(AVLTree *tree, AVLTreeNode *node)
{
	AVLTreeNode *left_subtree;
	AVLTreeNode *right_subtree;
	AVLTreeNode *child;
	int diff;

	left_subtree = node->children[AVL_TREE_NODE_LEFT];
	right_subtree = node->children[AVL_TREE_NODE_RIGHT];

	/* Check the heights of the child trees.  If there is an unbalance
	 * (difference between left and right > 2), then rotate nodes
	 * around to fix it */

	diff = avl_tree_subtree_height(right_subtree)
	     - avl_tree_subtree_height(left_subtree);

	if (diff >= 2) {

		/* Biased toward the right side too much. */

		child = right_subtree;

		if (avl_tree_subtree_height(child->children[AVL_TREE_NODE_RIGHT])
		  < avl_tree_subtree_height(child->children[AVL_TREE_NODE_LEFT])) {

			/* If the right child is biased toward the left
			 * side, it must be rotated right first (double
			 * rotation) */

			avl_tree_rotate(tree, right_subtree,
			                AVL_TREE_NODE_RIGHT);
		}

		/* Perform a left rotation.  After this, the right child will
		 * take the place of this node.  Update the node pointer. */

		node = avl_tree_rotate(tree, node, AVL_TREE_NODE_LEFT);

	} else if (diff <= -2) {

		/* Biased toward the left side too much. */

		child = node->children[AVL_TREE_NODE_LEFT];

		if (avl_tree_subtree_height(child->children[AVL_TREE_NODE_LEFT])
		  < avl_tree_subtree_height(child->children[AVL_TREE_NODE_RIGHT])) {

			/* If the left child is biased toward the right
			 * side, it must be rotated right left (double
			 * rotation) */

			avl_tree_rotate(tree, left_subtree,
			                AVL_TREE_NODE_LEFT);
		}

		/* Perform a right rotation.  After this, the left child will
		 * take the place of this node.  Update the node pointer. */

		node = avl_tree_rotate(tree, node, AVL_TREE_NODE_RIGHT);
	}

	/* Update the height of this node */

	avl_tree_update_height(node);

	return node;
}

// 函数: avl_tree_balance_to_root (line 288)
static void avl_tree_balance_to_root(AVLTree *tree, AVLTreeNode *node)
{
	AVLTreeNode *rover;

	rover = node;

	while (rover != NULL) {

		/* Balance this node if necessary */

		rover = avl_tree_node_balance(tree, rover);

		/* Go to this node's parent */

		rover = rover->parent;
	}
}

// 函数: avl_tree_insert (line 306)
AVLTreeNode *avl_tree_insert(AVLTree *tree, AVLTreeKey key, AVLTreeValue value)
{
	AVLTreeNode **rover;
	AVLTreeNode *new_node;
	AVLTreeNode *previous_node;

	/* Walk down the tree until we reach a NULL pointer */

	rover = &tree->root_node;
	previous_node = NULL;

	while (*rover != NULL) {
		previous_node = *rover;
		if (tree->compare_func(key, (*rover)->key) < 0) {
			rover = &((*rover)->children[AVL_TREE_NODE_LEFT]);
		} else {
			rover = &((*rover)->children[AVL_TREE_NODE_RIGHT]);
		}
	}

	/* Create a new node.  Use the last node visited as the parent link. */

	new_node = (AVLTreeNode *) malloc(sizeof(AVLTreeNode));

	if (new_node == NULL) {
		return NULL;
	}

	new_node->children[AVL_TREE_NODE_LEFT] = NULL;
	new_node->children[AVL_TREE_NODE_RIGHT] = NULL;
	new_node->parent = previous_node;
	new_node->key = key;
	new_node->value = value;
	new_node->height = 1;

	/* Insert at the NULL pointer that was reached */

	*rover = new_node;

	/* Rebalance the tree, starting from the previous node. */

	avl_tree_balance_to_root(tree, previous_node);

	/* Keep track of the number of entries */

	++tree->num_nodes;

	return new_node;
}

// 函数: avl_tree_node_get_replacement (line 360)
static AVLTreeNode *avl_tree_node_get_replacement(AVLTree *tree,
                                                  AVLTreeNode *node)
{
	AVLTreeNode *left_subtree;
	AVLTreeNode *right_subtree;
	AVLTreeNode *result;
	AVLTreeNode *child;
	int left_height, right_height;
	int side;

	left_subtree = node->children[AVL_TREE_NODE_LEFT];
	right_subtree = node->children[AVL_TREE_NODE_RIGHT];

	/* No children? */

	if (left_subtree == NULL && right_subtree == NULL) {
		return NULL;
	}

	/* Pick a node from whichever subtree is taller.  This helps to
	 * keep the tree balanced. */

	left_height = avl_tree_subtree_height(left_subtree);
	right_height = avl_tree_subtree_height(right_subtree);

	if (left_height < right_height) {
		side = AVL_TREE_NODE_RIGHT;
	} else {
		side = AVL_TREE_NODE_LEFT;
	}

	/* Search down the tree, back towards the center. */

	result = node->children[side];

	while (result->children[1-side] != NULL) {
		result = result->children[1-side];
	}

	/* Unlink the result node, and hook in its remaining child
	 * (if it has one) to replace it. */

	child = result->children[side];
	avl_tree_node_replace(tree, result, child);

	/* Update the subtree height for the result node's old parent. */

	avl_tree_update_height(result->parent);

	return result;
}

// 函数: avl_tree_remove_node (line 414)
void avl_tree_remove_node(AVLTree *tree, AVLTreeNode *node)
{
	AVLTreeNode *swap_node;
	AVLTreeNode *balance_startpoint;
	int i;

	/* The node to be removed must be swapped with an "adjacent"
	 * node, ie. one which has the closest key to this one. Find
	 * a node to swap with. */

	swap_node = avl_tree_node_get_replacement(tree, node);

	if (swap_node == NULL) {

		/* This is a leaf node and has no children, therefore
		 * it can be immediately removed. */

		/* Unlink this node from its parent. */

		avl_tree_node_replace(tree, node, NULL);

		/* Start rebalancing from the parent of the original node */

		balance_startpoint = node->parent;

	} else {
		/* We will start rebalancing from the old parent of the
		 * swap node.  Sometimes, the old parent is the node we
		 * are removing, in which case we must start rebalancing
		 * from the swap node. */

		if (swap_node->parent == node) {
			balance_startpoint = swap_node;
		} else {
			balance_startpoint = swap_node->parent;
		}

		/* Copy references in the node into the swap node */

		for (i=0; i<2; ++i) {
			swap_node->children[i] = node->children[i];

			if (swap_node->children[i] != NULL) {
				swap_node->children[i]->parent = swap_node;
			}
		}

		swap_node->height = node->height;

		/* Link the parent's reference to this node */

		avl_tree_node_replace(tree, node, swap_node);
	}

	/* Destroy the node */

	free(node);

	/* Keep track of the number of nodes */

	--tree->num_nodes;

	/* Rebalance the tree */

	avl_tree_balance_to_root(tree, balance_startpoint);
}

// 函数: avl_tree_remove (line 483)
int avl_tree_remove(AVLTree *tree, AVLTreeKey key)
{
	AVLTreeNode *node;

	/* Find the node to remove */

	node = avl_tree_lookup_node(tree, key);

	if (node == NULL) {
		/* Not found in tree */

		return 0;
	}

	/* Remove the node */

	avl_tree_remove_node(tree, node);

	return 1;
}

// 函数: avl_tree_lookup_node (line 504)
AVLTreeNode *avl_tree_lookup_node(AVLTree *tree, AVLTreeKey key)
{
	AVLTreeNode *node;
	int diff;

	/* Search down the tree and attempt to find the node which
	 * has the specified key */

	node = tree->root_node;

	while (node != NULL) {

		diff = tree->compare_func(key, node->key);

		if (diff == 0) {

			/* Keys are equal: return this node */

			return node;

		} else if (diff < 0) {
			node = node->children[AVL_TREE_NODE_LEFT];
		} else {
			node = node->children[AVL_TREE_NODE_RIGHT];
		}
	}

	/* Not found */

	return NULL;
}

// 函数: avl_tree_lookup (line 536)
AVLTreeValue avl_tree_lookup(AVLTree *tree, AVLTreeKey key)
{
	AVLTreeNode *node;

	/* Find the node */

	node = avl_tree_lookup_node(tree, key);

	if (node == NULL) {
		return AVL_TREE_NULL;
	} else {
		return node->value;
	}
}

// 函数: avl_tree_root_node (line 551)
AVLTreeNode *avl_tree_root_node(AVLTree *tree)
{
	return tree->root_node;
}

// 函数: avl_tree_node_key (line 556)
AVLTreeKey avl_tree_node_key(AVLTreeNode *node)
{
	return node->key;
}

// 函数: avl_tree_node_value (line 561)
AVLTreeValue avl_tree_node_value(AVLTreeNode *node)
{
	return node->value;
}

// 函数: avl_tree_node_child (line 566)
AVLTreeNode *avl_tree_node_child(AVLTreeNode *node, AVLTreeNodeSide side)
{
	if (side == AVL_TREE_NODE_LEFT || side == AVL_TREE_NODE_RIGHT) {
		return node->children[side];
	} else {
		return NULL;
	}
}

// 函数: avl_tree_node_parent (line 575)
AVLTreeNode *avl_tree_node_parent(AVLTreeNode *node)
{
	return node->parent;
}

// 函数: avl_tree_num_entries (line 580)
unsigned int avl_tree_num_entries(AVLTree *tree)
{
	return tree->num_nodes;
}

// 函数: avl_tree_to_array_add_subtree (line 585)
static void avl_tree_to_array_add_subtree(AVLTreeNode *subtree,
                                         AVLTreeValue *array,
                                         int *index)
{
	if (subtree == NULL) {
		return;
	}

	/* Add left subtree first */

	avl_tree_to_array_add_subtree(subtree->children[AVL_TREE_NODE_LEFT],
	                              array, index);

	/* Add this node */

	array[*index] = subtree->key;
	++*index;

	/* Finally add right subtree */

	avl_tree_to_array_add_subtree(subtree->children[AVL_TREE_NODE_RIGHT],
	                              array, index);
}

// 函数: avl_tree_to_array (line 609)
AVLTreeValue *avl_tree_to_array(AVLTree *tree)
{
	AVLTreeValue *array;
	int index;

	/* Allocate the array */

	array = malloc(sizeof(AVLTreeValue) * tree->num_nodes);

	if (array == NULL) {
		return NULL;
	}

	index = 0;

	/* Add all keys */

	avl_tree_to_array_add_subtree(tree->root_node, array, &index);

	return array;
}
