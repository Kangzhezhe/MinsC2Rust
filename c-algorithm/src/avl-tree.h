// 识别到的宏定义
#define ALGORITHM_AVLTREE_H

// 识别到的typedef定义
typedef struct _AVLTree AVLTree;
typedef void *AVLTreeKey;
typedef void *AVLTreeValue;

// 识别到的宏定义
#define AVL_TREE_NULL ((void *) 0)

// 识别到的typedef定义
typedef struct _AVLTreeNode AVLTreeNode;
typedef enum {
	AVL_TREE_NODE_LEFT = 0,
	AVL_TREE_NODE_RIGHT = 1
} AVLTreeNodeSide;
typedef int (*AVLTreeCompareFunc)(AVLTreeValue value1, AVLTreeValue value2);

// 识别到的函数定义
// 函数: avl_tree_new (line 129)
AVLTree *avl_tree_new(AVLTreeCompareFunc compare_func);

// 函数: avl_tree_free (line 137)
void avl_tree_free(AVLTree *tree);

// 函数: avl_tree_insert (line 150)
AVLTreeNode *avl_tree_insert(AVLTree *tree, AVLTreeKey key,
                             AVLTreeValue value);

// 函数: avl_tree_remove_node (line 160)
void avl_tree_remove_node(AVLTree *tree, AVLTreeNode *node);

// 函数: avl_tree_remove (line 173)
int avl_tree_remove(AVLTree *tree, AVLTreeKey key);

// 函数: avl_tree_lookup_node (line 185)
AVLTreeNode *avl_tree_lookup_node(AVLTree *tree, AVLTreeKey key);

// 函数: avl_tree_lookup (line 200)
AVLTreeValue avl_tree_lookup(AVLTree *tree, AVLTreeKey key);

// 函数: avl_tree_root_node (line 210)
AVLTreeNode *avl_tree_root_node(AVLTree *tree);

// 函数: avl_tree_node_key (line 219)
AVLTreeKey avl_tree_node_key(AVLTreeNode *node);

// 函数: avl_tree_node_value (line 228)
AVLTreeValue avl_tree_node_value(AVLTreeNode *node);

// 函数: avl_tree_node_child (line 239)
AVLTreeNode *avl_tree_node_child(AVLTreeNode *node, AVLTreeNodeSide side);

// 函数: avl_tree_node_parent (line 249)
AVLTreeNode *avl_tree_node_parent(AVLTreeNode *node);

// 函数: avl_tree_subtree_height (line 258)
int avl_tree_subtree_height(AVLTreeNode *node);

// 函数: avl_tree_to_array (line 271)
AVLTreeValue *avl_tree_to_array(AVLTree *tree);

// 函数: avl_tree_num_entries (line 280)
unsigned int avl_tree_num_entries(AVLTree *tree);
