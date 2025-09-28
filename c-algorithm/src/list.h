// 识别到的宏定义
#define ALGORITHM_LIST_H

// 识别到的typedef定义
typedef struct _ListEntry ListEntry;
typedef struct _ListIterator ListIterator;
typedef void *ListValue;

// 识别到的结构体定义
struct _ListIterator {
	ListEntry **prev_next;
	ListEntry *current;
};

// 识别到的宏定义
#define LIST_NULL ((void *) 0)

// 识别到的typedef定义
typedef int (*ListCompareFunc)(ListValue value1, ListValue value2);
typedef int (*ListEqualFunc)(ListValue value1, ListValue value2);

// 识别到的函数定义
// 函数: list_free (line 128)
void list_free(ListEntry *list);

// 函数: list_prepend (line 139)
ListEntry *list_prepend(ListEntry **list, ListValue data);

// 函数: list_append (line 150)
ListEntry *list_append(ListEntry **list, ListValue data);

// 函数: list_prev (line 160)
ListEntry *list_prev(ListEntry *listentry);

// 函数: list_next (line 170)
ListEntry *list_next(ListEntry *listentry);

// 函数: list_data (line 179)
ListValue list_data(ListEntry *listentry);

// 函数: list_set_data (line 188)
void list_set_data(ListEntry *listentry, ListValue value);

// 函数: list_nth_entry (line 198)
ListEntry *list_nth_entry(ListEntry *list, unsigned int n);

// 函数: list_nth_data (line 209)
ListValue list_nth_data(ListEntry *list, unsigned int n);

// 函数: list_length (line 218)
unsigned int list_length(ListEntry *list);

// 函数: list_to_array (line 230)
ListValue *list_to_array(ListEntry *list);

// 函数: list_remove_entry (line 241)
int list_remove_entry(ListEntry **list, ListEntry *entry);

// 函数: list_remove_data (line 253)
unsigned int list_remove_data(ListEntry **list, ListEqualFunc callback,
                              ListValue data);

// 函数: list_sort (line 263)
void list_sort(ListEntry **list, ListCompareFunc compare_func);

// 函数: list_find_data (line 276)
ListEntry *list_find_data(ListEntry *list,
                          ListEqualFunc callback,
                          ListValue data);

// 函数: list_iterate (line 287)
void list_iterate(ListEntry **list, ListIterator *iter);

// 函数: list_iter_has_more (line 298)
int list_iter_has_more(ListIterator *iterator);

// 函数: list_iter_next (line 308)
ListValue list_iter_next(ListIterator *iterator);

// 函数: list_iter_remove (line 317)
void list_iter_remove(ListIterator *iterator);
