// 识别到的宏定义
#define ALGORITHM_SORTEDARRAY_H

// 识别到的typedef定义
typedef void *SortedArrayValue;
typedef struct _SortedArray SortedArray;
typedef int (*SortedArrayEqualFunc)(SortedArrayValue value1,
                                    SortedArrayValue value2);
typedef int (*SortedArrayCompareFunc)(SortedArrayValue value1,
                                      SortedArrayValue value2);

// 识别到的函数定义
// 函数: sortedarray_get (line 98)
SortedArrayValue *sortedarray_get(SortedArray *array, unsigned int i);

// 函数: sortedarray_length (line 106)
unsigned int sortedarray_length(SortedArray *array);

// 函数: sortedarray_new (line 121)
SortedArray *sortedarray_new(unsigned int length, 
                             SortedArrayEqualFunc equ_func, 
                             SortedArrayCompareFunc cmp_func);

// 函数: sortedarray_free (line 130)
void sortedarray_free(SortedArray *sortedarray);

// 函数: sortedarray_remove (line 139)
void sortedarray_remove(SortedArray *sortedarray, unsigned int index);

// 函数: sortedarray_remove_range (line 149)
void sortedarray_remove_range(SortedArray *sortedarray, unsigned int index,
                              unsigned int length);

// 函数: sortedarray_insert (line 160)
int sortedarray_insert(SortedArray *sortedarray, SortedArrayValue data);

// 函数: sortedarray_index_of (line 169)
int sortedarray_index_of(SortedArray *sortedarray, SortedArrayValue data);

// 函数: sortedarray_clear (line 176)
void sortedarray_clear(SortedArray *sortedarray);
