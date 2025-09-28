// 识别到的宏定义
#define ALGORITHM_ARRAYLIST_H

// 识别到的typedef定义
typedef void *ArrayListValue;
typedef struct _ArrayList ArrayList;

// 识别到的结构体定义
struct _ArrayList {

	/** Entries in the array */

	ArrayListValue *data;

	/** Length of the array */

	unsigned int length;

	/** Private data and should not be accessed */

	unsigned int _alloced;
};

// 识别到的typedef定义
typedef int (*ArrayListEqualFunc)(ArrayListValue value1,
                                  ArrayListValue value2);
typedef int (*ArrayListCompareFunc)(ArrayListValue value1,
                                    ArrayListValue value2);

// 识别到的函数定义
// 函数: arraylist_new (line 116)
ArrayList *arraylist_new(unsigned int length);

// 函数: arraylist_free (line 124)
void arraylist_free(ArrayList *arraylist);

// 函数: arraylist_append (line 136)
int arraylist_append(ArrayList *arraylist, ArrayListValue data);

// 函数: arraylist_prepend (line 148)
int arraylist_prepend(ArrayList *arraylist, ArrayListValue data);

// 函数: arraylist_remove (line 157)
void arraylist_remove(ArrayList *arraylist, unsigned int index);

// 函数: arraylist_remove_range (line 167)
void arraylist_remove_range(ArrayList *arraylist, unsigned int index,
                            unsigned int length);

// 函数: arraylist_insert (line 183)
int arraylist_insert(ArrayList *arraylist, unsigned int index,
                     ArrayListValue data);

// 函数: arraylist_index_of (line 197)
int arraylist_index_of(ArrayList *arraylist,
                       ArrayListEqualFunc callback,
                       ArrayListValue data);

// 函数: arraylist_clear (line 207)
void arraylist_clear(ArrayList *arraylist);

// 函数: arraylist_sort (line 216)
void arraylist_sort(ArrayList *arraylist, ArrayListCompareFunc compare_func);
