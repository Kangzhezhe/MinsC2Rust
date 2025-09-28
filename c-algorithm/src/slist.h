// 识别到的宏定义
#define ALGORITHM_SLIST_H

// 识别到的typedef定义
typedef struct _SListEntry SListEntry;
typedef struct _SListIterator SListIterator;
typedef void *SListValue;

// 识别到的结构体定义
struct _SListIterator {
	SListEntry **prev_next;
	SListEntry *current;
};

// 识别到的宏定义
#define SLIST_NULL ((void *) 0)

// 识别到的typedef定义
typedef int (*SListCompareFunc)(SListValue value1, SListValue value2);
typedef int (*SListEqualFunc)(SListValue value1, SListValue value2);

// 识别到的函数定义
// 函数: slist_free (line 136)
void slist_free(SListEntry *list);

// 函数: slist_prepend (line 147)
SListEntry *slist_prepend(SListEntry **list, SListValue data);

// 函数: slist_append (line 158)
SListEntry *slist_append(SListEntry **list, SListValue data);

// 函数: slist_next (line 167)
SListEntry *slist_next(SListEntry *listentry);

// 函数: slist_data (line 176)
SListValue slist_data(SListEntry *listentry);

// 函数: slist_set_data (line 185)
void slist_set_data(SListEntry *listentry, SListValue value);

// 函数: slist_nth_entry (line 195)
SListEntry *slist_nth_entry(SListEntry *list, unsigned int n);

// 函数: slist_nth_data (line 206)
SListValue slist_nth_data(SListEntry *list, unsigned int n);

// 函数: slist_length (line 215)
unsigned int slist_length(SListEntry *list);

// 函数: slist_to_array (line 227)
SListValue *slist_to_array(SListEntry *list);

// 函数: slist_remove_entry (line 238)
int slist_remove_entry(SListEntry **list, SListEntry *entry);

// 函数: slist_remove_data (line 250)
unsigned int slist_remove_data(SListEntry **list,
                               SListEqualFunc callback,
                               SListValue data);

// 函数: slist_sort (line 261)
void slist_sort(SListEntry **list, SListCompareFunc compare_func);

// 函数: slist_find_data (line 275)
SListEntry *slist_find_data(SListEntry *list,
                            SListEqualFunc callback,
                            SListValue data);

// 函数: slist_iterate (line 287)
void slist_iterate(SListEntry **list, SListIterator *iter);

// 函数: slist_iter_has_more (line 298)
int slist_iter_has_more(SListIterator *iterator);

// 函数: slist_iter_next (line 308)
SListValue slist_iter_next(SListIterator *iterator);

// 函数: slist_iter_remove (line 317)
void slist_iter_remove(SListIterator *iterator);
