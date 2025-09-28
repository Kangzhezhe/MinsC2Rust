// 识别到的包含指令
#include <stdlib.h>
#include <assert.h>
#include "alloc-testing.h"
#include "framework.h"

// 识别到的全局变量
_Atomic size_t num_assert = 0;

// 识别到的宏定义
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */

// 识别到的包含指令
#include "binary-heap.h"
#include "compare-int.h"

// 识别到的宏定义
#define NUM_TEST_VALUES 10000

// 识别到的全局变量
int test_array[NUM_TEST_VALUES];

// 识别到的函数定义
// 函数: test_binary_heap_new_free (line 45)
void test_binary_heap_new_free(void)
{
	BinaryHeap *heap;
	int i;

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);
		binary_heap_free(heap);
	}

	/* Test low memory scenario */

	alloc_test_set_limit(0);
	heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);
	assert(heap == NULL);

	alloc_test_set_limit(1);
	heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);
	assert(heap == NULL);
}

// 函数: test_binary_heap_insert (line 66)
void test_binary_heap_insert(void)
{
	BinaryHeap *heap;
	int i;

	heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binary_heap_insert(heap, &test_array[i]) != 0);
	}

	assert(binary_heap_num_entries(heap) == NUM_TEST_VALUES);

	binary_heap_free(heap);
}

// 函数: test_min_heap (line 83)
void test_min_heap(void)
{
	BinaryHeap *heap;
	int *val;
	int i;

	heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);

	/* Push a load of values onto the heap */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binary_heap_insert(heap, &test_array[i]) != 0);
	}

	/* Pop values off the heap and check they are in order */

	i = -1;
	while (binary_heap_num_entries(heap) > 0) {
		val = (int *) binary_heap_pop(heap);

		assert(*val == i + 1);
		i = *val;
	}

	/* Test popping from an empty heap */

	assert(binary_heap_num_entries(heap) == 0);
	assert(binary_heap_pop(heap) == BINARY_HEAP_NULL);

	binary_heap_free(heap);
}

// 函数: test_max_heap (line 116)
void test_max_heap(void)
{
	BinaryHeap *heap;
	int *val;
	int i;

	heap = binary_heap_new(BINARY_HEAP_TYPE_MAX, int_compare);

	/* Push a load of values onto the heap */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binary_heap_insert(heap, &test_array[i]) != 0);
	}

	/* Pop values off the heap and check they are in order */

	i = NUM_TEST_VALUES;
	while (binary_heap_num_entries(heap) > 0) {
		val = (int *) binary_heap_pop(heap);

		assert(*val == i - 1);
		i = *val;
	}

	binary_heap_free(heap);
}

// 函数: test_out_of_memory (line 146)
void test_out_of_memory(void)
{
	BinaryHeap *heap;
	int *value;
	int values[] = {
		15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0,
	};
	int i;

	/* Allocate a heap and fill to the default limit */

	heap = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_compare);

	alloc_test_set_limit(0);

	for (i=0; i<16; ++i) {
		assert(binary_heap_insert(heap, &values[i]) != 0);
	}

	assert(binary_heap_num_entries(heap) == 16);

	/* Check that we cannot add new values */

	for (i=0; i<16; ++i) {
		assert(binary_heap_insert(heap, &values[i]) == 0);
		assert(binary_heap_num_entries(heap) == 16);
	}

	/* Check that we can read the values back out again and they
	 * are in the right order. */

	for (i=0; i<16; ++i) {
		value = binary_heap_pop(heap);
		assert(*value == i);
	}

	assert(binary_heap_num_entries(heap) == 0);

	binary_heap_free(heap);
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_binary_heap_new_free,
	test_binary_heap_insert,
	test_min_heap,
	test_max_heap,
	test_out_of_memory,
	NULL
};

// 识别到的函数定义
// 函数: main (line 196)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
