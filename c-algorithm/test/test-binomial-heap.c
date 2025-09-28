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
#include "binomial-heap.h"
#include "compare-int.h"

// 识别到的宏定义
#define NUM_TEST_VALUES 10000

// 识别到的全局变量
int test_array[NUM_TEST_VALUES];

// 识别到的函数定义
// 函数: test_binomial_heap_new_free (line 45)
void test_binomial_heap_new_free(void)
{
	BinomialHeap *heap;
	int i;

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare);
		binomial_heap_free(heap);
	}

	/* Test for out of memory */

	alloc_test_set_limit(0);

	assert(binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare) == NULL);
}

// 函数: test_binomial_heap_insert (line 62)
void test_binomial_heap_insert(void)
{
	BinomialHeap *heap;
	int i;

	heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binomial_heap_insert(heap, &test_array[i]) != 0);
	}
	assert(binomial_heap_num_entries(heap) == NUM_TEST_VALUES);

	/* Test for out of memory */

	alloc_test_set_limit(0);
	assert(binomial_heap_insert(heap, &i) == 0);

	binomial_heap_free(heap);
}

// 函数: test_min_heap (line 83)
void test_min_heap(void)
{
	BinomialHeap *heap;
	int *val;
	int i;

	heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare);

	/* Push a load of values onto the heap */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binomial_heap_insert(heap, &test_array[i]) != 0);
	}

	/* Pop values off the heap and check they are in order */

	i = -1;
	while (binomial_heap_num_entries(heap) > 0) {
		val = (int *) binomial_heap_pop(heap);

		assert(*val == i + 1);
		i = *val;
	}

	/* Test pop on an empty heap */

	val = (int *) binomial_heap_pop(heap);
	assert(val == NULL);

	binomial_heap_free(heap);
}

// 函数: test_max_heap (line 116)
void test_max_heap(void)
{
	BinomialHeap *heap;
	int *val;
	int i;

	heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MAX, int_compare);

	/* Push a load of values onto the heap */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		assert(binomial_heap_insert(heap, &test_array[i]) != 0);
	}

	/* Pop values off the heap and check they are in order */

	i = NUM_TEST_VALUES;
	while (binomial_heap_num_entries(heap) > 0) {
		val = (int *) binomial_heap_pop(heap);

		assert(*val == i - 1);
		i = *val;
	}

	/* Test pop on an empty heap */

	val = (int *) binomial_heap_pop(heap);
	assert(val == NULL);

	binomial_heap_free(heap);
}

// 识别到的宏定义
#define TEST_VALUE (NUM_TEST_VALUES / 2)

// 识别到的函数定义
// 函数: generate_heap (line 151)
static BinomialHeap *generate_heap(void)
{
	BinomialHeap *heap;
	int i;

	heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare);

	/* Push a load of values onto the heap */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		test_array[i] = i;
		if (i != TEST_VALUE) {
			assert(binomial_heap_insert(heap,
			                            &test_array[i]) != 0);
		}
	}

	return heap;
}

// 函数: verify_heap (line 174)
static void verify_heap(BinomialHeap *heap)
{
	unsigned int num_vals;
	int *val;
	int i;

	num_vals = binomial_heap_num_entries(heap);
	assert(num_vals == NUM_TEST_VALUES - 1);

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		if (i == TEST_VALUE) {
			continue;
		}

		/* Pop off the next value and check it */

		val = binomial_heap_pop(heap);
		assert(*val == i);

		/* Decrement num values counter */

		--num_vals;
		assert(binomial_heap_num_entries(heap) == num_vals);
	}
}

// 函数: test_insert_out_of_memory (line 202)
static void test_insert_out_of_memory(void)
{
	BinomialHeap *heap;
	int i;

	/* There are various memory allocations performed during the insert;
	 * probe at different limit levels to catch them all. */

	for (i=0; i<6; ++i) {
		heap = generate_heap();

		/* Insert should fail */

		alloc_test_set_limit(i);
		test_array[TEST_VALUE] = TEST_VALUE;
		assert(binomial_heap_insert(heap,
		                            &test_array[TEST_VALUE]) == 0);
		alloc_test_set_limit(-1);

		/* Check that the heap is unharmed */

		verify_heap(heap);

		binomial_heap_free(heap);
	}
}

// 函数: test_pop_out_of_memory (line 231)
void test_pop_out_of_memory(void)
{
	BinomialHeap *heap;
	int i;

	/* There are various memory allocations performed as part of the merge
	 * done during the pop.  Probe at different limit levels to catch them
	 * all. */

	for (i=0; i<6; ++i) {
		heap = generate_heap();

		/* Pop should fail */

		alloc_test_set_limit(i);
		assert(binomial_heap_pop(heap) == NULL);
		alloc_test_set_limit(-1);

		/* Check the heap is unharmed */

		binomial_heap_free(heap);
	}
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_binomial_heap_new_free,
	test_binomial_heap_insert,
	test_min_heap,
	test_max_heap,
	test_insert_out_of_memory,
	test_pop_out_of_memory,
	NULL
};

// 识别到的函数定义
// 函数: main (line 265)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
