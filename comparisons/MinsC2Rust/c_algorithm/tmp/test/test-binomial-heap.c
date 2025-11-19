/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#include <stdlib.h>
#include <assert.h>

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file alloc-testing.h
 *
 * @brief Memory allocation testing framework.
 *
 * This file uses the preprocessor to redefine the standard C dynamic memory
 * allocation functions for testing purposes.  This allows checking that
 * code under test correctly frees back all memory allocated, as well as
 * the ability to impose artificial limits on allocation, to test that
 * code correctly handles out-of-memory scenarios.
 */

#ifndef ALLOC_TESTING_H
#define ALLOC_TESTING_H

/* Don't redefine the functions in the alloc-testing.c, as we need the
 * standard malloc/free functions. */

#ifndef ALLOC_TESTING_C
#undef malloc
#define malloc   alloc_test_malloc
#undef free
#define free     alloc_test_free
#undef realloc
#define realloc  alloc_test_realloc
#undef calloc
#define calloc   alloc_test_calloc
#undef strdup
#define strdup   alloc_test_strdup
#endif

/**
 * Allocate a block of memory.
 *
 * @param bytes          Number of bytes to allocate.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_malloc(size_t bytes);

/**
 * Free a block of memory.
 *
 * @param ptr            Pointer to the block to free.
 */

void alloc_test_free(void *ptr);

/**
 * Reallocate a previously-allocated block to a new size, preserving
 * contents.
 *
 * @param ptr            Pointer to the existing block.
 * @param bytes          Size of the new block, in bytes.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_realloc(void *ptr, size_t bytes);

/**
 * Allocate a block of memory for an array of structures, initialising
 * the contents to zero.
 *
 * @param nmemb          Number of structures to allocate for.
 * @param bytes          Size of each structure, in bytes.
 * @return               Pointer to the new memory block for the array,
 *                       or NULL if it was not possible to allocate the
 *                       new block.
 */

void *alloc_test_calloc(size_t nmemb, size_t bytes);

/**
 * Allocate a block of memory containing a copy of a string.
 *
 * @param string         The string to copy.
 * @return               Pointer to the new memory block containing the
 *                       copied string, or NULL if it was not possible
 *                       to allocate the new block.
 */

char *alloc_test_strdup(const char *string);

/**
 * Set an artificial limit on the amount of memory that can be
 * allocated.
 *
 * @param alloc_count    Number of allocations that are possible after
 *                       this call.  For example, if this has a value
 *                       of 3, malloc() can be called successfully
 *                       three times, but all allocation attempts
 *                       after this will fail.  If this has a negative
 *                       value, the allocation limit is disabled.
 */

void alloc_test_set_limit(signed int alloc_count);

/**
 * Get a count of the number of bytes currently allocated.
 *
 * @return               The number of bytes currently allocated by
 *                       the allocation system.
 */

size_t alloc_test_get_allocated(void);

#endif /* #ifndef ALLOC_TESTING_H */

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file framework.h
 *
 * @brief Framework for running unit tests.
 */

/**
 * A unit test.
 */

typedef void (*UnitTestFunction)(void);

/**
 * Run a list of unit tests.  The provided array contains a list of
 * pointers to test functions to invoke; the last entry is denoted
 * by a NULL pointer.
 *
 * @param tests          List of tests to invoke.
 */

void run_tests(UnitTestFunction *tests);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef TEST_FRAMEWORK_H */


_Atomic size_t num_assert = 0;
#undef assert
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */                                                           \
     else                                                                      \
       __assert_fail(#expr, __FILE__, __LINE__, __ASSERT_FUNCTION);            \
   }))

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file binomial-heap.h
 *
 * @brief Binomial heap.
 *
 * A binomial heap is a heap data structure implemented using a
 * binomial tree.  In a heap, values are ordered by priority.
 *
 * To create a binomial heap, use @ref binomial_heap_new.  To destroy a
 * binomial heap, use @ref binomial_heap_free.
 *
 * To insert a value into a binomial heap, use @ref binomial_heap_insert.
 *
 * To remove the first value from a binomial heap, use @ref binomial_heap_pop.
 *
 */

#ifndef ALGORITHM_BINOMIAL_HEAP_H
#define ALGORITHM_BINOMIAL_HEAP_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Heap type.  If a heap is a min heap (@ref BINOMIAL_HEAP_TYPE_MIN), the
 * values with the lowest priority are stored at the top of the heap and
 * will be the first returned.  If a heap is a max heap
 * (@ref BINOMIAL_HEAP_TYPE_MAX), the values with the greatest priority
 * are stored at the top of the heap.
 */

typedef enum {
	/** A minimum heap. */

	BINOMIAL_HEAP_TYPE_MIN,

	/** A maximum heap. */

	BINOMIAL_HEAP_TYPE_MAX
} BinomialHeapType;

/**
 * A value stored in a @ref BinomialHeap.
 */

typedef void *BinomialHeapValue;

/**
 * A null @ref BinomialHeapValue.
 */

#define BINOMIAL_HEAP_NULL ((void *) 0)

/**
 * Type of function used to compare values in a binomial heap.
 *
 * @param value1           The first value.
 * @param value2           The second value.
 * @return                 A negative number if value1 is less than value2,
 *                         a positive number if value1 is greater than value2,
 *                         zero if the two are equal.
 */

typedef int (*BinomialHeapCompareFunc)(BinomialHeapValue value1,
                                       BinomialHeapValue value2);

/**
 * A binomial heap data structure.
 */

typedef struct _BinomialHeap BinomialHeap;

/**
 * Create a new @ref BinomialHeap.
 *
 * @param heap_type        The type of heap: min heap or max heap.
 * @param compare_func     Pointer to a function used to compare the priority
 *                         of values in the heap.
 * @return                 A new binomial heap, or NULL if it was not possible
 *                         to allocate the memory.
 */

BinomialHeap *binomial_heap_new(BinomialHeapType heap_type,
                                BinomialHeapCompareFunc compare_func);

/**
 * Destroy a binomial heap.
 *
 * @param heap             The heap to destroy.
 */

void binomial_heap_free(BinomialHeap *heap);

/**
 * Insert a value into a binomial heap.
 *
 * @param heap             The heap to insert into.
 * @param value            The value to insert.
 * @return                 Non-zero if the entry was added, or zero if it
 *                         was not possible to allocate memory for the new
 *                         entry.
 */

int binomial_heap_insert(BinomialHeap *heap, BinomialHeapValue value);

/**
 * Remove the first value from a binomial heap.
 *
 * @param heap             The heap.
 * @return                 The first value in the heap, or
 *                         @ref BINOMIAL_HEAP_NULL if the heap is empty.
 */

BinomialHeapValue binomial_heap_pop(BinomialHeap *heap);

/**
 * Find the number of values stored in a binomial heap.
 *
 * @param heap             The heap.
 * @return                 The number of values in the heap.
 */

unsigned int binomial_heap_num_entries(BinomialHeap *heap);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_BINOMIAL_HEAP_H */

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file compare-int.h
 *
 * Comparison functions for pointers to integers.
 *
 * To find the difference between two values pointed at, use
 * @ref int_compare.
 *
 * To find if two values pointed at are equal, use @ref int_equal.
 */

#ifndef ALGORITHM_COMPARE_INT_H
#define ALGORITHM_COMPARE_INT_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compare the integer values pointed at by two pointers to determine
 * if they are equal.
 *
 * @param location1       Pointer to the first value to compare.
 * @param location2       Pointer to the second value to compare.
 * @return                Non-zero if the two values are equal, zero if the
 *                        two values are not equal.
 */

int int_equal(void *location1, void *location2);

/**
 * Compare the integer values pointed at by two pointers.
 *
 * @param location1        Pointer to the first value to compare.
 * @param location2        Pointer to the second value to compare.
 * @return                 A negative value if the first value is less than
 *                         the second value, a positive value if the first
 *                         value is greater than the second value, zero if
 *                         they are equal.
 */

int int_compare(void *location1, void *location2);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_COMPARE_INT_H */


#define NUM_TEST_VALUES 10000

int test_array[NUM_TEST_VALUES];

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

#define TEST_VALUE (NUM_TEST_VALUES / 2)

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

/* Verify that the values read out of the specified heap are the
 * same as those inserted in generate_heap. */

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

/* Test out of memory when doing an insert */

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

/* Test out of memory when doing a pop */

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

static UnitTestFunction tests[] = {
	test_binomial_heap_new_free,
	test_binomial_heap_insert,
	test_min_heap,
	test_max_heap,
	test_insert_out_of_memory,
	test_pop_out_of_memory,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

