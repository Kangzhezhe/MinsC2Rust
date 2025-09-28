// 识别到的宏定义
#define ALGORITHM_BINOMIAL_HEAP_H

// 识别到的typedef定义
typedef enum {
	/** A minimum heap. */

	BINOMIAL_HEAP_TYPE_MIN,

	/** A maximum heap. */

	BINOMIAL_HEAP_TYPE_MAX
} BinomialHeapType;
typedef void *BinomialHeapValue;

// 识别到的宏定义
#define BINOMIAL_HEAP_NULL ((void *) 0)

// 识别到的typedef定义
typedef int (*BinomialHeapCompareFunc)(BinomialHeapValue value1,
                                       BinomialHeapValue value2);
typedef struct _BinomialHeap BinomialHeap;

// 识别到的函数定义
// 函数: binomial_heap_new (line 104)
BinomialHeap *binomial_heap_new(BinomialHeapType heap_type,
                                BinomialHeapCompareFunc compare_func);

// 函数: binomial_heap_free (line 113)
void binomial_heap_free(BinomialHeap *heap);

// 函数: binomial_heap_insert (line 125)
int binomial_heap_insert(BinomialHeap *heap, BinomialHeapValue value);

// 函数: binomial_heap_pop (line 135)
BinomialHeapValue binomial_heap_pop(BinomialHeap *heap);

// 函数: binomial_heap_num_entries (line 144)
unsigned int binomial_heap_num_entries(BinomialHeap *heap);
