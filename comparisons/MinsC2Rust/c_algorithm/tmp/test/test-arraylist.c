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

/* ArrayList test cases */

#include <stdio.h>
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
 * @file arraylist.h
 *
 * @brief Automatically resizing array
 *
 * ArrayLists are arrays of pointers which automatically increase in
 * size.
 *
 * To create an ArrayList, use @ref arraylist_new.
 * To destroy an ArrayList, use @ref arraylist_free.
 *
 * To add a value to an ArrayList, use @ref arraylist_prepend,
 * @ref arraylist_append, or @ref arraylist_insert.
 *
 * To remove a value from an ArrayList, use @ref arraylist_remove
 * or @ref arraylist_remove_range.
 */

#ifndef ALGORITHM_ARRAYLIST_H
#define ALGORITHM_ARRAYLIST_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A value to be stored in an @ref ArrayList.
 */

typedef void *ArrayListValue;

/**
 * An ArrayList structure.  New ArrayLists can be created using the
 * arraylist_new function.
 *
 * @see arraylist_new
 */

typedef struct _ArrayList ArrayList;

/**
 * Definition of an @ref ArrayList.
 */

struct _ArrayList {

	/** Entries in the array */

	ArrayListValue *data;

	/** Length of the array */

	unsigned int length;

	/** Private data and should not be accessed */

	unsigned int _alloced;
};

/**
 * Compare two values in an arraylist to determine if they are equal.
 *
 * @return Non-zero if the values are equal, zero if they are not equal.
 */

typedef int (*ArrayListEqualFunc)(ArrayListValue value1,
                                  ArrayListValue value2);

/**
 * Compare two values in an arraylist.  Used by @ref arraylist_sort
 * when sorting values.
 *
 * @param value1              The first value.
 * @param value2              The second value.
 * @return                    A negative number if value1 should be sorted
 *                            before value2, a positive number if value2 should
 *                            be sorted before value1, zero if the two values
 *                            are equal.
 */

typedef int (*ArrayListCompareFunc)(ArrayListValue value1,
                                    ArrayListValue value2);

/**
 * Allocate a new ArrayList for use.
 *
 * @param length         Hint to the initialise function as to the amount
 *                       of memory to allocate initially to the ArrayList.
 *                       If a value of zero is given, a sensible default
 *                       size is used.
 * @return               A new arraylist, or NULL if it was not possible
 *                       to allocate the memory.
 * @see arraylist_free
 */

ArrayList *arraylist_new(unsigned int length);

/**
 * Destroy an ArrayList and free back the memory it uses.
 *
 * @param arraylist      The ArrayList to free.
 */

void arraylist_free(ArrayList *arraylist);

/**
 * Append a value to the end of an ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param data           The value to append.
 * @return               Non-zero if the request was successful, zero
 *                       if it was not possible to allocate more memory
 *                       for the new entry.
 */

int arraylist_append(ArrayList *arraylist, ArrayListValue data);

/**
 * Prepend a value to the beginning of an ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param data           The value to prepend.
 * @return               Non-zero if the request was successful, zero
 *                       if it was not possible to allocate more memory
 *                       for the new entry.
 */

int arraylist_prepend(ArrayList *arraylist, ArrayListValue data);

/**
 * Remove the entry at the specified location in an ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param index          The index of the entry to remove.
 */

void arraylist_remove(ArrayList *arraylist, unsigned int index);

/**
 * Remove a range of entries at the specified location in an ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param index          The index of the start of the range to remove.
 * @param length         The length of the range to remove.
 */

void arraylist_remove_range(ArrayList *arraylist, unsigned int index,
                            unsigned int length);

/**
 * Insert a value at the specified index in an ArrayList.
 * The index where the new value can be inserted is limited by the
 * size of the ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param index          The index at which to insert the value.
 * @param data           The value.
 * @return               Returns zero if unsuccessful, else non-zero
 *                       if successful (due to an invalid index or
 *                       if it was impossible to allocate more memory).
 */

int arraylist_insert(ArrayList *arraylist, unsigned int index,
                     ArrayListValue data);

/**
 * Find the index of a particular value in an ArrayList.
 *
 * @param arraylist      The ArrayList to search.
 * @param callback       Callback function to be invoked to compare
 *                       values in the list with the value to be
 *                       searched for.
 * @param data           The value to search for.
 * @return               The index of the value if found, or -1 if not found.
 */

int arraylist_index_of(ArrayList *arraylist,
                       ArrayListEqualFunc callback,
                       ArrayListValue data);

/**
 * Remove all entries from an ArrayList.
 *
 * @param arraylist      The ArrayList.
 */

void arraylist_clear(ArrayList *arraylist);

/**
 * Sort the values in an ArrayList.
 *
 * @param arraylist      The ArrayList.
 * @param compare_func   Function used to compare values in sorting.
 */

void arraylist_sort(ArrayList *arraylist, ArrayListCompareFunc compare_func);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_ARRAYLIST_H */

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


int variable1, variable2, variable3, variable4;

ArrayList *generate_arraylist(void)
{
	ArrayList *arraylist;
	int i;

	arraylist = arraylist_new(0);

	for (i=0; i<4; ++i) {
		arraylist_append(arraylist, &variable1);
		arraylist_append(arraylist, &variable2);
		arraylist_append(arraylist, &variable3);
		arraylist_append(arraylist, &variable4);
	}

	return arraylist;
}

void test_arraylist_new_free(void)
{
	ArrayList *arraylist;

	/* Use a default size when given zero */

	arraylist = arraylist_new(0);
	assert(arraylist != NULL);
	arraylist_free(arraylist);

	/* Normal allocated */

	arraylist = arraylist_new(10);
	assert(arraylist != NULL);
	arraylist_free(arraylist);

	/* Freeing a null arraylist works */

	arraylist_free(NULL);

	/* Test low memory scenarios (failed malloc) */

	alloc_test_set_limit(0);
	arraylist = arraylist_new(0);
	assert(arraylist == NULL);

	alloc_test_set_limit(1);
	arraylist = arraylist_new(100);
	assert(arraylist == NULL);
}

void test_arraylist_append(void)
{
	ArrayList *arraylist;
	int i;

	arraylist = arraylist_new(0);

	assert(arraylist->length == 0);

	/* Append some entries */

	assert(arraylist_append(arraylist, &variable1) != 0);
	assert(arraylist->length == 1);

	assert(arraylist_append(arraylist, &variable2) != 0);
	assert(arraylist->length == 2);

	assert(arraylist_append(arraylist, &variable3) != 0);
	assert(arraylist->length == 3);

	assert(arraylist_append(arraylist, &variable4) != 0);
	assert(arraylist->length == 4);

	assert(arraylist->data[0] == &variable1);
	assert(arraylist->data[1] == &variable2);
	assert(arraylist->data[2] == &variable3);
	assert(arraylist->data[3] == &variable4);

	/* Test appending many entries */

	for (i=0; i<10000; ++i) {
		assert(arraylist_append(arraylist, NULL) != 0);
	}

	arraylist_free(arraylist);

	/* Test low memory scenario */

	arraylist = arraylist_new(100);

	alloc_test_set_limit(0);

	for (i=0; i<100; ++i) {
		assert(arraylist_append(arraylist, NULL) != 0);
	}

	assert(arraylist->length == 100);
	assert(arraylist_append(arraylist, NULL) == 0);
	assert(arraylist->length == 100);

	arraylist_free(arraylist);
}


void test_arraylist_prepend(void)
{
	ArrayList *arraylist;
	int i;

	arraylist = arraylist_new(0);

	assert(arraylist->length == 0);

	/* Append some entries */

	assert(arraylist_prepend(arraylist, &variable1) != 0);
	assert(arraylist->length == 1);

	assert(arraylist_prepend(arraylist, &variable2) != 0);
	assert(arraylist->length == 2);

	assert(arraylist_prepend(arraylist, &variable3) != 0);
	assert(arraylist->length == 3);

	assert(arraylist_prepend(arraylist, &variable4) != 0);
	assert(arraylist->length == 4);

	assert(arraylist->data[0] == &variable4);
	assert(arraylist->data[1] == &variable3);
	assert(arraylist->data[2] == &variable2);
	assert(arraylist->data[3] == &variable1);

	/* Test prepending many entries */

	for (i=0; i<10000; ++i) {
		assert(arraylist_prepend(arraylist, NULL) != 0);
	}

	arraylist_free(arraylist);

	/* Test low memory scenario */

	arraylist = arraylist_new(100);

	alloc_test_set_limit(0);

	for (i=0; i<100; ++i) {
		assert(arraylist_prepend(arraylist, NULL) != 0);
	}

	assert(arraylist->length == 100);
	assert(arraylist_prepend(arraylist, NULL) == 0);
	assert(arraylist->length == 100);

	arraylist_free(arraylist);
}

void test_arraylist_insert(void)
{
	ArrayList *arraylist;
	int i;

	arraylist = generate_arraylist();

	/* Check for out of range insert */

	assert(arraylist->length == 16);
	assert(arraylist_insert(arraylist, 17, &variable1) == 0);
	assert(arraylist->length == 16);

	/* Insert a new entry at index 5 */

	assert(arraylist->length == 16);
	assert(arraylist->data[4] == &variable1);
	assert(arraylist->data[5] == &variable2);
	assert(arraylist->data[6] == &variable3);

	assert(arraylist_insert(arraylist, 5, &variable4) != 0);

	assert(arraylist->length == 17);
	assert(arraylist->data[4] == &variable1);
	assert(arraylist->data[5] == &variable4);
	assert(arraylist->data[6] == &variable2);
	assert(arraylist->data[7] == &variable3);

	/* Inserting at the start */

	assert(arraylist->data[0] == &variable1);
	assert(arraylist->data[1] == &variable2);
	assert(arraylist->data[2] == &variable3);

	assert(arraylist_insert(arraylist, 0, &variable4) != 0);

	assert(arraylist->length == 18);
	assert(arraylist->data[0] == &variable4);
	assert(arraylist->data[1] == &variable1);
	assert(arraylist->data[2] == &variable2);
	assert(arraylist->data[3] == &variable3);

	/* Inserting at the end */

	assert(arraylist->data[15] == &variable2);
	assert(arraylist->data[16] == &variable3);
	assert(arraylist->data[17] == &variable4);

	assert(arraylist_insert(arraylist, 18, &variable1) != 0);

	assert(arraylist->length == 19);
	assert(arraylist->data[15] == &variable2);
	assert(arraylist->data[16] == &variable3);
	assert(arraylist->data[17] == &variable4);
	assert(arraylist->data[18] == &variable1);

	/* Test inserting many entries */

	for (i=0; i<10000; ++i) {
		arraylist_insert(arraylist, 10, &variable1);
	}

	arraylist_free(arraylist);
}

void test_arraylist_remove_range(void)
{
	ArrayList *arraylist;

	arraylist = generate_arraylist();

	assert(arraylist->length == 16);
	assert(arraylist->data[3] == &variable4);
	assert(arraylist->data[4] == &variable1);
	assert(arraylist->data[5] == &variable2);
	assert(arraylist->data[6] == &variable3);

	arraylist_remove_range(arraylist, 4, 3);

	assert(arraylist->length == 13);
	assert(arraylist->data[3] == &variable4);
	assert(arraylist->data[4] == &variable4);
	assert(arraylist->data[5] == &variable1);
	assert(arraylist->data[6] == &variable2);

	/* Try some invalid ones and check they don't do anything */

	arraylist_remove_range(arraylist, 10, 10);
	arraylist_remove_range(arraylist, 0, 16);

	assert(arraylist->length == 13);

	arraylist_free(arraylist);
}

void test_arraylist_remove(void)
{
	ArrayList *arraylist;

	arraylist = generate_arraylist();

	assert(arraylist->length == 16);
	assert(arraylist->data[3] == &variable4);
	assert(arraylist->data[4] == &variable1);
	assert(arraylist->data[5] == &variable2);
	assert(arraylist->data[6] == &variable3);

	arraylist_remove(arraylist, 4);

	assert(arraylist->length == 15);
	assert(arraylist->data[3] == &variable4);
	assert(arraylist->data[4] == &variable2);
	assert(arraylist->data[5] == &variable3);
	assert(arraylist->data[6] == &variable4);

	/* Try some invalid removes */

	arraylist_remove(arraylist, 15);

	assert(arraylist->length == 15);

	arraylist_free(arraylist);
}

void test_arraylist_index_of(void)
{
	int entries[] = { 89, 4, 23, 42, 16, 15, 8, 99, 50, 30 };
	int num_entries;
	ArrayList *arraylist;
	int i;
	int index;
	int val;

	/* Generate an arraylist containing the entries in the array */

	num_entries = sizeof(entries) / sizeof(int);
	arraylist = arraylist_new(0);

	for (i=0; i<num_entries; ++i) {
		arraylist_append(arraylist, &entries[i]);
	}

	/* Check all values get found correctly */

	for (i=0; i<num_entries; ++i) {

		val = entries[i];

		index = arraylist_index_of(arraylist, int_equal, &val);

		assert(index == i);
	}

	/* Check invalid values */

	val = 0;
	assert(arraylist_index_of(arraylist, int_equal, &val) < 0);
	val = 57;
	assert(arraylist_index_of(arraylist, int_equal, &val) < 0);

	arraylist_free(arraylist);
}

void test_arraylist_clear(void)
{
	ArrayList *arraylist;

	arraylist = arraylist_new(0);

	/* Emptying an already-empty arraylist */

	arraylist_clear(arraylist);
	assert(arraylist->length == 0);

	/* Add some items and then empty it */

	arraylist_append(arraylist, &variable1);
	arraylist_append(arraylist, &variable2);
	arraylist_append(arraylist, &variable3);
	arraylist_append(arraylist, &variable4);

	arraylist_clear(arraylist);

	assert(arraylist->length == 0);

	arraylist_free(arraylist);
}

void test_arraylist_sort(void)
{
	ArrayList *arraylist;
	int entries[] = { 89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4 };
	int sorted[]  = { 4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	unsigned int i;

	arraylist = arraylist_new(10);

	for (i=0; i<num_entries; ++i) {
		arraylist_prepend(arraylist, &entries[i]);
	}

	arraylist_sort(arraylist, int_compare);

	/* List length is unchanged */

	assert(arraylist->length == num_entries);

	/* Check the list is sorted */

	for (i=0; i<num_entries; ++i) {
		int *value;

		value = (int *) arraylist->data[i];
		assert(*value == sorted[i]);
	}

	arraylist_free(arraylist);

	/* Check sorting an empty list */

	arraylist = arraylist_new(5);

	arraylist_sort(arraylist, int_compare);

	assert(arraylist->length == 0);

	arraylist_free(arraylist);

	/* Check sorting a list with 1 entry */

	arraylist = arraylist_new(5);

	arraylist_prepend(arraylist, &entries[0]);
	arraylist_sort(arraylist, int_compare);

	assert(arraylist->length == 1);
	assert(arraylist->data[0] == &entries[0]);

	arraylist_free(arraylist);
}

static UnitTestFunction tests[] = {
	test_arraylist_new_free,
	test_arraylist_append,
	test_arraylist_prepend,
	test_arraylist_insert,
	test_arraylist_remove,
	test_arraylist_remove_range,
	test_arraylist_index_of,
	test_arraylist_clear,
	test_arraylist_sort,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

