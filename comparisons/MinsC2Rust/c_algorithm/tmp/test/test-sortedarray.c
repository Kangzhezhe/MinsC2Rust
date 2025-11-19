/*

Copyright (c) 2016, Stefan Cloudt

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
)
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <time.h>

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

/*

Copyright (c) 2016, Stefan Cloudt

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
 * @file sortedarray.h
 *
 * @brief Automatically sorted and resizing array
 *
 * An SortedArray is an automatically resizing sorted array. Most operations
 * run O(n) worst case running time. Some operations run in O(log n).
 *
 * To retrieve a value use the sortedarray structure by accessing the data
 * field.
 *
 * To create a SortedArray, use @ref sortedarray_new
 * To destroy a SortedArray, use @ref sortedarray_free
 *
 * To add a value to a SortedArray, use @ref sortedarray_prepend, 
 * @ref sortedarray_append, or @ref sortedarray_insert.
 *
 * To remove a value from a SortedArray, use @ref sortedarray_remove
 * or @ref sortedarray_remove_range.
 */

#ifndef ALGORITHM_SORTEDARRAY_H
#define ALGORITHM_SORTEDARRAY_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A value to store in @ref SortedArray.
 */
typedef void *SortedArrayValue;

/**
 * A SortedArray structure. Use @ref sortedarray_new to create one.
 *
 * The SortedArray is an automatically resizing array which stores its 
 * elements in sorted order. Userdefined functions determine the sorting order.
 * All operations on a SortedArray maintain the sorted property. Most 
 * operations are done in O(n) time, but searching can be done in O(log n)
 * worst case.
 *
 * @see sortedarray_new
 */
typedef struct _SortedArray SortedArray;

/**
 * Compare two values in a SortedArray to determine if they are equal.
 *
 * @param value1	The first value to compare.
 * @param value2	The second value to compare.
 * @return		Non-zero if value1 equals value2, zero if they do not
 *			equal.
 *
 */
typedef int (*SortedArrayEqualFunc)(SortedArrayValue value1,
                                    SortedArrayValue value2);

/**
 * Compare two values in a SortedArray to determine their order.
 *
 * @param value1	The first value to compare.
 * @param value2	The second value to compare.
 * @return		Less than zero if value1 is compared smaller than 
 * 			value2, zero if they compare equal, or greater than
 * 			zero if value1 compares greate than value2.
 */
typedef int (*SortedArrayCompareFunc)(SortedArrayValue value1,
                                      SortedArrayValue value2);

/**
 * @brief Function to retrieve element at index i from array
 *
 * @param array			The pointer to the sortedarray to retrieve the element from.
 * @param i				The index of the element to retrieve.
 * @return				The i-th element of the array, or NULL if array was NULL.
 */
SortedArrayValue *sortedarray_get(SortedArray *array, unsigned int i);

/**
 * @brief Function to retrieve the length of the SortedArray array.
 *
 * @param array			The array to retrieve the length from.
 * @return				The lenght of the SortedArray.
 */
unsigned int sortedarray_length(SortedArray *array);

/**
 * Allocate a new SortedArray for use.
 *
 * @param length        Indication to the amount of memory that should be 
 *                      allocated. If 0 is given, then a default is used.
 * @param equ_func      The function used to determine if two values in the
 *                      SortedArray equal. This may not be NULL.
 * @param cmp_func      The function used to determine the relative order of
 *                      two values in the SortedArray. This may not be NULL.
 *
 * @return              A new SortedArray or NULL if it was not possible to
 *                      allocate one.
 */
SortedArray *sortedarray_new(unsigned int length, 
                             SortedArrayEqualFunc equ_func, 
                             SortedArrayCompareFunc cmp_func);

/**
 * Frees a SortedArray from memory.
 *
 * @param sortedarray   The SortedArray to free.
 */
void sortedarray_free(SortedArray *sortedarray);

/**
 * Remove a value from a SortedArray at a specified index while maintaining the
 * sorted property.
 *
 * @param sortedarray   The SortedArray to remove a value from.
 * @param index         The index to remove from the array.
 */
void sortedarray_remove(SortedArray *sortedarray, unsigned int index);

/**
 * Remove a range of entities from a SortedArray while maintaining the sorted 
 * property.
 *
 * @param sortedarray   The SortedArray to remove the range of values from.
 * @param index         The starting index of the range to remove.
 * @param length        The length of the range to remove.
 */
void sortedarray_remove_range(SortedArray *sortedarray, unsigned int index,
                              unsigned int length);

/**
 * Insert a value into a SortedArray while maintaining the sorted property.
 *
 * @param sortedarray   The SortedArray to insert into.
 * @param data          The data to insert.
 *
 * @return              Zero on failure, or a non-zero value if successfull.
 */
int sortedarray_insert(SortedArray *sortedarray, SortedArrayValue data);

/**
 * Find the index of a value in a SortedArray.
 *
 * @param sortedarray   The SortedArray to find in.
 * @param data          The value to find.
 * @return              The index of the value or -1 if the value is not found.
 */
int sortedarray_index_of(SortedArray *sortedarray, SortedArrayValue data);

/**
 * Remove all values from a SortedArray.
 *
 * @param sortedarray   The SortedArray to clear.
 */
void sortedarray_clear(SortedArray *sortedarray);

#ifdef __cplusplus
}
#endif

#endif // #ifndef ALGORITHM_SORTEDARRAY_H

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

#define TEST_SIZE 20
#define TEST_ARRAY {10, 12, 12, 1, 2, 3, 6, 7, 2, 23, 13, 23, 23, 34, 31, 9,\
   	21, -2, -12, -4}
#define TEST_REMOVE_EL 15
#define TEST_REMOVE_RANGE 7
#define TEST_REMOVE_RANGE_LENGTH 4

void check_sorted_prop(SortedArray *sortedarray)
{
	unsigned int i;
	for (i = 1; i < sortedarray_length(sortedarray); i++) {
		assert(int_compare(
		                   sortedarray_get(sortedarray, i-1),
						   sortedarray_get(sortedarray, i)) <= 0);
	}
}

void free_sorted_ints(SortedArray *sortedarray)
{
	unsigned int i;
	for (i = 0; i < sortedarray_length(sortedarray); i++) {
		int *pi = (int*) sortedarray_get(sortedarray, i);
		free(pi);
	}

	sortedarray_free(sortedarray);
}

SortedArray *generate_sortedarray_equ(SortedArrayEqualFunc equ_func)
{
	/* generate a sorted array of length TEST_SIZE, filled with random 
	   numbers. */
	SortedArray *sortedarray;
	unsigned int i;

	int array[TEST_SIZE] = TEST_ARRAY;

	sortedarray = sortedarray_new(0, equ_func, int_compare);

	for (i = 0; i < TEST_SIZE; ++i) {
		int *pi = malloc(sizeof(int));
		*pi = array[i];
		sortedarray_insert(sortedarray, pi);
	}

	return sortedarray;
}

SortedArray *generate_sortedarray(void)
{
	return generate_sortedarray_equ(int_equal);
}

void test_sortedarray_new_free(void)
{
	SortedArray *sortedarray;

	/* test normal */
	sortedarray = sortedarray_new(0, int_equal, int_compare);
	assert(sortedarray != NULL);
	sortedarray_free(sortedarray);

	/* freeing null */
	sortedarray_free(NULL);

	/* low memory */
	alloc_test_set_limit(0);
	sortedarray = sortedarray_new(0, int_equal, int_compare);
	assert(sortedarray == NULL);

	alloc_test_set_limit(-1);
}

void test_sortedarray_insert(void)
{
	SortedArray *sortedarray = generate_sortedarray();
	unsigned int i;

	/* insert a few random numbers, then check if everything is sorted */
	for (i = 0; i < 20; i++) {
		int i = (int) (((float) rand())/((float) RAND_MAX) * 100);
		int *pi = malloc(sizeof(int));
		*pi = i;
		sortedarray_insert(sortedarray, pi);
	}

	check_sorted_prop(sortedarray);
	free_sorted_ints(sortedarray);
}

void test_sortedarray_remove(void)
{
	SortedArray *sortedarray = generate_sortedarray();

	/* remove index 24 */
	int *ip = (int*) sortedarray_get(sortedarray, TEST_REMOVE_EL + 1);
	int i = *ip;
	free((int*) sortedarray_get(sortedarray, TEST_REMOVE_EL));
	sortedarray_remove(sortedarray, TEST_REMOVE_EL);
	assert(*((int*) sortedarray_get(sortedarray, TEST_REMOVE_EL)) == i);

	check_sorted_prop(sortedarray);
	free_sorted_ints(sortedarray);
}

void test_sortedarray_remove_range(void)
{
	SortedArray *sortedarray = generate_sortedarray();

	/* get values in test range */
	int new[TEST_REMOVE_RANGE_LENGTH];
	unsigned int i;
	for (i = 0; i < TEST_REMOVE_RANGE_LENGTH; i++) {
		new[i] = *((int*) sortedarray_get(sortedarray, TEST_REMOVE_RANGE + 
		                                    TEST_REMOVE_RANGE_LENGTH + i));
	}
	
	/* free removed elements */
	for (i = 0; i < TEST_REMOVE_RANGE_LENGTH; i++) {
		free((int*) sortedarray_get(sortedarray, TEST_REMOVE_RANGE + i));
	}

	/* remove */
	sortedarray_remove_range(sortedarray, TEST_REMOVE_RANGE, 
			TEST_REMOVE_RANGE_LENGTH);
	
	/* assert */
	for (i = 0; i < TEST_REMOVE_RANGE_LENGTH; i++) {
		assert(*((int*) sortedarray_get(sortedarray, TEST_REMOVE_RANGE + i)) == 
		                                                                new[i]);
	}

	check_sorted_prop(sortedarray);
	free_sorted_ints(sortedarray);
}

void test_sortedarray_index_of(void) {
	SortedArray *sortedarray = generate_sortedarray();

	unsigned int i;
	for (i = 0; i < TEST_SIZE; i++) {
		int r = sortedarray_index_of(sortedarray, 
		                sortedarray_get(sortedarray, i));
		assert(r >= 0);
		assert(*((int*) sortedarray_get(sortedarray,(unsigned int) r)) == 
		        *((int*) sortedarray_get(sortedarray, i)));
	}
	
	free_sorted_ints(sortedarray);
}

static int ptr_equal(SortedArrayValue v1, SortedArrayValue v2) {
	return v1 == v2;
}

void test_sortedarray_index_of_equ_key(void)
{
	/* replace equal function by function which checks pointers */
	SortedArray *sortedarray = generate_sortedarray_equ(ptr_equal);
	unsigned int i;

	/* check if all search value return the same index */
	for (i = 0; i < TEST_SIZE; i++) {
		int r = sortedarray_index_of(sortedarray, 
		                             sortedarray_get(sortedarray, i));
		assert(r >= 0);
		assert(i == (unsigned int) r);
	}

	free_sorted_ints(sortedarray);
}

void test_sortedarray_get(void) {
	unsigned int i;

	SortedArray *arr = generate_sortedarray();

	for (i = 0; i < sortedarray_length(arr); i++) {
		assert(sortedarray_get(arr, i) == sortedarray_get(arr, i));
		assert(*((int*) sortedarray_get(arr, i)) == 
		       *((int*) sortedarray_get(arr, i)));
	}

	free_sorted_ints(arr);
}

static UnitTestFunction tests[] = {
	test_sortedarray_new_free,
	test_sortedarray_insert,
	test_sortedarray_remove,
	test_sortedarray_remove_range,
	test_sortedarray_index_of,
	test_sortedarray_index_of_equ_key,
	test_sortedarray_get,
	NULL   
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
