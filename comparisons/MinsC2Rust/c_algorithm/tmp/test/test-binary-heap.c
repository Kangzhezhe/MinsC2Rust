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
 * @file binary-heap.h
 *
 * @brief Binary heap.
 *
 * A binary heap is a heap data structure implemented using a
 * binary tree.  In a heap, values are ordered by priority.
 *
 * To create a binary heap, use @ref binary_heap_new.  To destroy a
 * binary heap, use @ref binary_heap_free.
 *
 * To insert a value into a binary heap, use @ref binary_heap_insert.
 *
 * To remove the first value from a binary heap, use @ref binary_heap_pop.
 *
 */

#ifndef ALGORITHM_BINARY_HEAP_H
#define ALGORITHM_BINARY_HEAP_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Heap type.  If a heap is a min heap (@ref BINARY_HEAP_TYPE_MIN), the
 * values with the lowest priority are stored at the top of the heap and
 * will be the first returned.  If a heap is a max heap
 * (@ref BINARY_HEAP_TYPE_MAX), the values with the greatest priority are
 * stored at the top of the heap.
 */

typedef enum {
	/** A minimum heap. */

	BINARY_HEAP_TYPE_MIN,

	/** A maximum heap. */

	BINARY_HEAP_TYPE_MAX
} BinaryHeapType;

/**
 * A value stored in a @ref BinaryHeap.
 */

typedef void *BinaryHeapValue;

/**
 * A null @ref BinaryHeapValue.
 */

#define BINARY_HEAP_NULL ((void *) 0)

/**
 * Type of function used to compare values in a binary heap.
 *
 * @param value1           The first value.
 * @param value2           The second value.
 * @return                 A negative number if value1 is less than value2,
 *                         a positive number if value1 is greater than value2,
 *                         zero if the two are equal.
 */

typedef int (*BinaryHeapCompareFunc)(BinaryHeapValue value1,
                                     BinaryHeapValue value2);

/**
 * A binary heap data structure.
 */

typedef struct _BinaryHeap BinaryHeap;

/**
 * Create a new @ref BinaryHeap.
 *
 * @param heap_type        The type of heap: min heap or max heap.
 * @param compare_func     Pointer to a function used to compare the priority
 *                         of values in the heap.
 * @return                 A new binary heap, or NULL if it was not possible
 *                         to allocate the memory.
 */

BinaryHeap *binary_heap_new(BinaryHeapType heap_type,
                            BinaryHeapCompareFunc compare_func);

/**
 * Destroy a binary heap.
 *
 * @param heap             The heap to destroy.
 */

void binary_heap_free(BinaryHeap *heap);

/**
 * Insert a value into a binary heap.
 *
 * @param heap             The heap to insert into.
 * @param value            The value to insert.
 * @return                 Non-zero if the entry was added, or zero if it
 *                         was not possible to allocate memory for the new
 *                         entry.
 */

int binary_heap_insert(BinaryHeap *heap, BinaryHeapValue value);

/**
 * Remove the first value from a binary heap.
 *
 * @param heap             The heap.
 * @return                 The first value in the heap, or
 *                         @ref BINARY_HEAP_NULL if the heap is empty.
 */

BinaryHeapValue binary_heap_pop(BinaryHeap *heap);

/**
 * Find the number of values stored in a binary heap.
 *
 * @param heap             The heap.
 * @return                 The number of values in the heap.
 */

unsigned int binary_heap_num_entries(BinaryHeap *heap);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_BINARY_HEAP_H */

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

/* Test out of memory scenario when adding items */

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

static UnitTestFunction tests[] = {
	test_binary_heap_new_free,
	test_binary_heap_insert,
	test_min_heap,
	test_max_heap,
	test_out_of_memory,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

