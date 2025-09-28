// 识别到的宏定义
#define ALGORITHM_SET_H

// 识别到的typedef定义
typedef struct _Set Set;
typedef struct _SetIterator SetIterator;
typedef struct _SetEntry SetEntry;
typedef void *SetValue;

// 识别到的结构体定义
struct _SetIterator {
	Set *set;
	SetEntry *next_entry;
	unsigned int next_chain;
};

// 识别到的宏定义
#define SET_NULL ((void *) 0)

// 识别到的typedef定义
typedef unsigned int (*SetHashFunc)(SetValue value);
typedef int (*SetEqualFunc)(SetValue value1, SetValue value2);
typedef void (*SetFreeFunc)(SetValue value);

// 识别到的函数定义
// 函数: set_new (line 127)
Set *set_new(SetHashFunc hash_func, SetEqualFunc equal_func);

// 函数: set_free (line 135)
void set_free(Set *set);

// 函数: set_register_free_function (line 146)
void set_register_free_function(Set *set, SetFreeFunc free_func);

// 函数: set_insert (line 159)
int set_insert(Set *set, SetValue data);

// 函数: set_remove (line 171)
int set_remove(Set *set, SetValue data);

// 函数: set_query (line 182)
int set_query(Set *set, SetValue data);

// 函数: set_num_entries (line 191)
unsigned int set_num_entries(Set *set);

// 函数: set_to_array (line 202)
SetValue *set_to_array(Set *set);

// 函数: set_union (line 214)
Set *set_union(Set *set1, Set *set2);

// 函数: set_intersection (line 226)
Set *set_intersection(Set *set1, Set *set2);

// 函数: set_iterate (line 236)
void set_iterate(Set *set, SetIterator *iter);

// 函数: set_iter_has_more (line 247)
int set_iter_has_more(SetIterator *iterator);

// 函数: set_iter_next (line 257)
SetValue set_iter_next(SetIterator *iterator);
