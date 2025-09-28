// 识别到的宏定义
#define ALGORITHM_BINARY_HEAP_H

// 识别到的typedef定义
typedef enum {
	/** A minimum heap. */

	BINARY_HEAP_TYPE_MIN,

	/** A maximum heap. */

	BINARY_HEAP_TYPE_MAX
} BinaryHeapType;
typedef void *BinaryHeapValue;

// 识别到的宏定义
#define BINARY_HEAP_NULL ((void *) 0)

// 识别到的typedef定义
typedef int (*BinaryHeapCompareFunc)(BinaryHeapValue value1,
                                     BinaryHeapValue value2);
typedef struct _BinaryHeap BinaryHeap;

// 识别到的函数定义
// 函数: binary_heap_new (line 104)
BinaryHeap *binary_heap_new(BinaryHeapType heap_type,
                            BinaryHeapCompareFunc compare_func);

// 函数: binary_heap_free (line 113)
void binary_heap_free(BinaryHeap *heap);

// 函数: binary_heap_insert (line 125)
int binary_heap_insert(BinaryHeap *heap, BinaryHeapValue value);

// 函数: binary_heap_pop (line 135)
BinaryHeapValue binary_heap_pop(BinaryHeap *heap);

// 函数: binary_heap_num_entries (line 144)
unsigned int binary_heap_num_entries(BinaryHeap *heap);
