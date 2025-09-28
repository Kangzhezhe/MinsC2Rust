// 识别到的宏定义
#define ALGORITHM_RB_TREE_H

// 识别到的typedef定义
typedef struct _RBTree RBTree;
typedef void *RBTreeKey;
typedef void *RBTreeValue;

// 识别到的宏定义
#define RB_TREE_NULL ((void *) 0)

// 识别到的typedef定义
typedef struct _RBTreeNode RBTreeNode;
typedef int (*RBTreeCompareFunc)(RBTreeValue data1, RBTreeValue data2);
typedef enum {
	RB_TREE_NODE_RED,
	RB_TREE_NODE_BLACK,
} RBTreeNodeColor;
typedef enum {
	RB_TREE_NODE_LEFT = 0,
	RB_TREE_NODE_RIGHT = 1
} RBTreeNodeSide;

// 识别到的函数定义
// 函数: rb_tree_new (line 139)
RBTree *rb_tree_new(RBTreeCompareFunc compare_func);

// 函数: rb_tree_free (line 147)
void rb_tree_free(RBTree *tree);

// 函数: rb_tree_insert (line 160)
RBTreeNode *rb_tree_insert(RBTree *tree, RBTreeKey key, RBTreeValue value);

// 函数: rb_tree_remove_node (line 169)
void rb_tree_remove_node(RBTree *tree, RBTreeNode *node);

// 函数: rb_tree_remove (line 182)
int rb_tree_remove(RBTree *tree, RBTreeKey key);

// 函数: rb_tree_lookup_node (line 194)
RBTreeNode *rb_tree_lookup_node(RBTree *tree, RBTreeKey key);

// 函数: rb_tree_lookup (line 209)
RBTreeValue rb_tree_lookup(RBTree *tree, RBTreeKey key);

// 函数: rb_tree_root_node (line 219)
RBTreeNode *rb_tree_root_node(RBTree *tree);

// 函数: rb_tree_node_key (line 228)
RBTreeKey rb_tree_node_key(RBTreeNode *node);

// 函数: rb_tree_node_value (line 237)
RBTreeValue rb_tree_node_value(RBTreeNode *node);

// 函数: rb_tree_node_child (line 248)
RBTreeNode *rb_tree_node_child(RBTreeNode *node, RBTreeNodeSide side);

// 函数: rb_tree_node_parent (line 258)
RBTreeNode *rb_tree_node_parent(RBTreeNode *node);

// 函数: rb_tree_subtree_height (line 267)
int rb_tree_subtree_height(RBTreeNode *node);

// 函数: rb_tree_to_array (line 280)
RBTreeValue *rb_tree_to_array(RBTree *tree);

// 函数: rb_tree_num_entries (line 289)
int rb_tree_num_entries(RBTree *tree);
