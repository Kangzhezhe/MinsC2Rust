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
 * @file slist.h
 *
 * Singly-linked list.
 *
 * A singly-linked list stores a collection of values.  Each
 * entry in the list (represented by a pointer to a @ref SListEntry
 * structure) contains a link to the next entry.  It is only
 * possible to iterate over entries in a singly linked list in one
 * direction.
 *
 * To create a new singly-linked list, create a variable which is
 * a pointer to a @ref SListEntry, and initialise it to NULL.
 *
 * To destroy a singly linked list, use @ref slist_free.
 *
 * To add a new value at the start of a list, use @ref slist_prepend.
 * To add a new value at the end of a list, use @ref slist_append.
 *
 * To find the length of a list, use @ref slist_length.
 *
 * To access a value in a list by its index in the list, use
 * @ref slist_nth_data.
 *
 * To search a list for a value, use @ref slist_find_data.
 *
 * To sort a list into an order, use @ref slist_sort.
 *
 * To find a particular entry in a list by its index, use
 * @ref slist_nth_entry.
 *
 * To iterate over each value in a list, use @ref slist_iterate to
 * initialise a @ref SListIterator structure, with @ref slist_iter_next
 * and @ref slist_iter_has_more to retrieve each value in turn.
 * @ref slist_iter_remove can be used to efficiently remove the
 * current entry from the list.
 *
 * Given a particular entry in a list (@ref SListEntry):
 *
 * @li To find the next entry, use @ref slist_next.
 * @li To access the value stored at the entry, use @ref slist_data.
 * @li To set the value stored at the entry, use @ref slist_set_data.
 * @li To remove the entry, use @ref slist_remove_entry.
 *
 */

#ifndef ALGORITHM_SLIST_H
#define ALGORITHM_SLIST_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Represents an entry in a singly-linked list.  The empty list is
 * represented by a NULL pointer. To initialise a new singly linked
 * list, simply create a variable of this type
 * containing a pointer to NULL.
 */

typedef struct _SListEntry SListEntry;

/**
 * Structure used to iterate over a list.
 */

typedef struct _SListIterator SListIterator;

/**
 * Value stored in a list.
 */

typedef void *SListValue;

/**
 * Definition of a @ref SListIterator.
 */

struct _SListIterator {
	SListEntry **prev_next;
	SListEntry *current;
};

/**
 * A null @ref SListValue.
 */

#define SLIST_NULL ((void *) 0)

/**
 * Callback function used to compare values in a list when sorting.
 *
 * @return   A negative value if value1 should be sorted before value2,
 *           a positive value if value1 should be sorted after value2,
 *           zero if value1 and value2 are equal.
 */

typedef int (*SListCompareFunc)(SListValue value1, SListValue value2);

/**
 * Callback function used to determine of two values in a list are
 * equal.
 *
 * @return   A non-zero value if value1 and value2 are equal, zero if they
 *           are not equal.
 */

typedef int (*SListEqualFunc)(SListValue value1, SListValue value2);

/**
 * Free an entire list.
 *
 * @param list           The list to free.
 */

void slist_free(SListEntry *list);

/**
 * Prepend a value to the start of a list.
 *
 * @param list      Pointer to the list to prepend to.
 * @param data      The value to prepend.
 * @return          The new entry in the list, or NULL if it was not possible
 *                  to allocate a new entry.
 */

SListEntry *slist_prepend(SListEntry **list, SListValue data);

/**
 * Append a value to the end of a list.
 *
 * @param list      Pointer to the list to append to.
 * @param data      The value to append.
 * @return          The new entry in the list, or NULL if it was not possible
 *                  to allocate a new entry.
 */

SListEntry *slist_append(SListEntry **list, SListValue data);

/**
 * Retrieve the next entry in a list.
 *
 * @param listentry    Pointer to the list entry.
 * @return             The next entry in the list.
 */

SListEntry *slist_next(SListEntry *listentry);

/**
 * Retrieve the value stored at a list entry.
 *
 * @param listentry    Pointer to the list entry.
 * @return             The value at the list entry.
 */

SListValue slist_data(SListEntry *listentry);

/**
 * Set the value at a list entry. The value provided will be written to the 
 * given listentry. If listentry is NULL nothing is done.
 *
 * @param listentry 	Pointer to the list entry.
 * @param value			The value to set.
 */
void slist_set_data(SListEntry *listentry, SListValue value);

/**
 * Retrieve the entry at a specified index in a list.
 *
 * @param list       The list.
 * @param n          The index into the list .
 * @return           The entry at the specified index, or NULL if out of range.
 */

SListEntry *slist_nth_entry(SListEntry *list, unsigned int n);

/**
 * Retrieve the value stored at a specified index in the list.
 *
 * @param list       The list.
 * @param n          The index into the list.
 * @return           The value stored at the specified index, or
 *                   @ref SLIST_NULL if unsuccessful.
 */

SListValue slist_nth_data(SListEntry *list, unsigned int n);

/**
 * Find the length of a list.
 *
 * @param list       The list.
 * @return           The number of entries in the list.
 */

unsigned int slist_length(SListEntry *list);

/**
 * Create a C array containing the contents of a list.
 *
 * @param list       The list.
 * @return           A newly-allocated C array containing all values in the
 *                   list, or NULL if it was not possible to allocate the
 *                   memory for the array.  The length of the array is
 *                   equal to the length of the list (see @ref slist_length).
 */

SListValue *slist_to_array(SListEntry *list);

/**
 * Remove an entry from a list.
 *
 * @param list       Pointer to the list.
 * @param entry      The list entry to remove.
 * @return           If the entry is not found in the list, returns zero,
 *                   else returns non-zero.
 */

int slist_remove_entry(SListEntry **list, SListEntry *entry);

/**
 * Remove all occurrences of a particular value from a list.
 *
 * @param list       Pointer to the list.
 * @param callback   Callback function to invoke to compare values in the
 *                   list with the value to remove.
 * @param data       The value to remove from the list.
 * @return           The number of entries removed from the list.
 */

unsigned int slist_remove_data(SListEntry **list,
                               SListEqualFunc callback,
                               SListValue data);

/**
 * Sort a list.
 *
 * @param list          Pointer to the list to sort.
 * @param compare_func  Function used to compare values in the list.
 */

void slist_sort(SListEntry **list, SListCompareFunc compare_func);

/**
 * Find the entry for a particular value in a list.
 *
 * @param list           The list to search.
 * @param callback       Callback function to be invoked to determine if
 *                       values in the list are equal to the value to be
 *                       searched for.
 * @param data           The value to search for.
 * @return               The list entry of the value being searched for, or
 *                       NULL if not found.
 */

SListEntry *slist_find_data(SListEntry *list,
                            SListEqualFunc callback,
                            SListValue data);

/**
 * Initialise a @ref SListIterator structure to iterate over a list.
 *
 * @param list           Pointer to the list to iterate over.
 * @param iter           Pointer to a @ref SListIterator structure to
 *                       initialise.
 */

void slist_iterate(SListEntry **list, SListIterator *iter);

/**
 * Determine if there are more values in the list to iterate over.
 *
 * @param iterator       The list iterator.
 * @return               Zero if there are no more values in the list to
 *                       iterate over, non-zero if there are more values to
 *                       read.
 */

int slist_iter_has_more(SListIterator *iterator);

/**
 * Using a list iterator, retrieve the next value from the list.
 *
 * @param iterator       The list iterator.
 * @return               The next value from the list, or SLIST_NULL if
 *                       there are no more values in the list.
 */

SListValue slist_iter_next(SListIterator *iterator);

/**
 * Delete the current entry in the list (the value last returned from
 * @ref slist_iter_next)
 *
 * @param iterator       The list iterator.
 */

void slist_iter_remove(SListIterator *iterator);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_SLIST_H */

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

int variable1 = 50, variable2, variable3, variable4;

/* Returns a list containing four entries */

SListEntry *generate_list(void)
{
	SListEntry *list = NULL;

	assert(slist_append(&list, &variable1) != NULL);
	assert(slist_append(&list, &variable2) != NULL);
	assert(slist_append(&list, &variable3) != NULL);
	assert(slist_append(&list, &variable4) != NULL);

	return list;
}

void test_slist_append(void)
{
	SListEntry *list = NULL;

	assert(slist_append(&list, &variable1) != NULL);
	assert(slist_append(&list, &variable2) != NULL);
	assert(slist_append(&list, &variable3) != NULL);
	assert(slist_append(&list, &variable4) != NULL);
	assert(slist_length(list) == 4);

	assert(slist_nth_data(list, 0) == &variable1);
	assert(slist_nth_data(list, 1) == &variable2);
	assert(slist_nth_data(list, 2) == &variable3);
	assert(slist_nth_data(list, 3) == &variable4);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(slist_length(list) == 4);
	assert(slist_append(&list, &variable1) == NULL);
	assert(slist_length(list) == 4);

	slist_free(list);
}

void test_slist_prepend(void)
{
	SListEntry *list = NULL;

	assert(slist_prepend(&list, &variable1) != NULL);
	assert(slist_prepend(&list, &variable2) != NULL);
	assert(slist_prepend(&list, &variable3) != NULL);
	assert(slist_prepend(&list, &variable4) != NULL);

	assert(slist_nth_data(list, 0) == &variable4);
	assert(slist_nth_data(list, 1) == &variable3);
	assert(slist_nth_data(list, 2) == &variable2);
	assert(slist_nth_data(list, 3) == &variable1);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(slist_length(list) == 4);
	assert(slist_prepend(&list, &variable1) == NULL);
	assert(slist_length(list) == 4);

	slist_free(list);
}

void test_slist_free(void)
{
	SListEntry *list;

	/* Create a list and free it */

	list = generate_list();

	slist_free(list);

	/* Check the empty list frees correctly */

	slist_free(NULL);
}

void test_slist_next(void)
{
	SListEntry *list;
	SListEntry *rover;

	list = generate_list();

	rover = list;
	assert(slist_data(rover) == &variable1);
	rover = slist_next(rover);
	assert(slist_data(rover) == &variable2);
	rover = slist_next(rover);
	assert(slist_data(rover) == &variable3);
	rover = slist_next(rover);
	assert(slist_data(rover) == &variable4);
	rover = slist_next(rover);
	assert(rover == NULL);

	slist_free(list);
}

void test_slist_nth_entry(void)
{
	SListEntry *list;
	SListEntry *entry;

	list = generate_list();

	/* Check all values in the list */

	entry = slist_nth_entry(list, 0);
	assert(slist_data(entry) == &variable1);
	entry = slist_nth_entry(list, 1);
	assert(slist_data(entry) == &variable2);
	entry = slist_nth_entry(list, 2);
	assert(slist_data(entry) == &variable3);
	entry = slist_nth_entry(list, 3);
	assert(slist_data(entry) == &variable4);

	/* Check out of range values */

	entry = slist_nth_entry(list, 4);
	assert(entry == NULL);
	entry = slist_nth_entry(list, 400);
	assert(entry == NULL);

	slist_free(list);
}

void test_slist_nth_data(void)
{
	SListEntry *list;

	list = generate_list();

	/* Check all values in the list */

	assert(slist_nth_data(list, 0) == &variable1);
	assert(slist_nth_data(list, 1) == &variable2);
	assert(slist_nth_data(list, 2) == &variable3);
	assert(slist_nth_data(list, 3) == &variable4);

	/* Check out of range values */

	assert(slist_nth_data(list, 4) == NULL);
	assert(slist_nth_data(list, 400) == NULL);

	slist_free(list);
}

void test_slist_length(void)
{
	SListEntry *list;

	/* Generate a list and check that it is four entries long */

	list = generate_list();

	assert(slist_length(list) == 4);

	/* Add an entry and check that it still works properly */

	slist_prepend(&list, &variable1);

	assert(slist_length(list) == 5);

	/* Check the length of the empty list */

	assert(slist_length(NULL) == 0);

	slist_free(list);
}

void test_slist_remove_entry(void)
{
	SListEntry *empty_list = NULL;
	SListEntry *list;
	SListEntry *entry;

	list = generate_list();

	/* Remove the third entry */

	entry = slist_nth_entry(list, 2);
	assert(slist_remove_entry(&list, entry) != 0);
	assert(slist_length(list) == 3);

	/* Remove the first entry */

	entry = slist_nth_entry(list, 0);
	assert(slist_remove_entry(&list, entry) != 0);
	assert(slist_length(list) == 2);

	/* Try some invalid removes */

	/* This was already removed: */

	assert(slist_remove_entry(&list, entry) == 0);

	/* NULL */

	assert(slist_remove_entry(&list, NULL) == 0);

	/* Removing NULL from an empty list */

	assert(slist_remove_entry(&empty_list, NULL) == 0);

	slist_free(list);
}

void test_slist_remove_data(void)
{
	int entries[] = { 89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	int val;
	SListEntry *list;
	unsigned int i;

	/* Generate a list containing all the entries in the array */

	list = NULL;

	for (i=0; i<num_entries; ++i) {
		slist_prepend(&list, &entries[i]);
	}

	/* Test removing invalid data */

	val = 0;
	assert(slist_remove_data(&list, int_equal, &val) == 0);
	val = 56;
	assert(slist_remove_data(&list, int_equal, &val) == 0);

	/* Remove the number 8 from the list */

	val = 8;
	assert(slist_remove_data(&list, int_equal, &val) == 1);
	assert(slist_length(list) == num_entries - 1);

	/* Remove the number 4 from the list (occurs multiple times) */

	val = 4;
	assert(slist_remove_data(&list, int_equal, &val) == 4);
	assert(slist_length(list) == num_entries - 5);

	/* Remove the number 89 from the list (first entry) */

	val = 89;
	assert(slist_remove_data(&list, int_equal, &val) == 1);
	assert(slist_length(list) == num_entries - 6);

	slist_free(list);
}

void test_slist_sort(void)
{
	SListEntry *list;
	int entries[] = { 89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4 };
	int sorted[]  = { 4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	unsigned int i;

	list = NULL;

	for (i=0; i<num_entries; ++i) {
		slist_prepend(&list, &entries[i]);
	}

	slist_sort(&list, int_compare);

	/* List length is unchanged */

	assert(slist_length(list) == num_entries);

	/* Check the list is sorted */

	for (i=0; i<num_entries; ++i) {
		int *value;

		value = (int *) slist_nth_data(list, i);
		assert(*value == sorted[i]);
	}

	slist_free(list);

	/* Check sorting an empty list */

	list = NULL;

	slist_sort(&list, int_compare);

	assert(list == NULL);
}

void test_slist_find_data(void)
{
	int entries[] = { 89, 23, 42, 16, 15, 4, 8, 99, 50, 30 };
	int num_entries = sizeof(entries) / sizeof(int);
	SListEntry *list;
	SListEntry *result;
	int i;
	int val;
	int *data;

	/* Generate a list containing the entries */

	list = NULL;
	for (i=0; i<num_entries; ++i) {
		slist_append(&list, &entries[i]);
	}

	/* Check that each value can be searched for correctly */

	for (i=0; i<num_entries; ++i) {

		val = entries[i];

		result = slist_find_data(list, int_equal, &val);

		assert(result != NULL);

		data = (int *) slist_data(result);
		assert(*data == val);
	}

	/* Check some invalid values return NULL */

	val = 0;
	assert(slist_find_data(list, int_equal, &val) == NULL);
	val = 56;
	assert(slist_find_data(list, int_equal, &val) == NULL);

	slist_free(list);
}

void test_slist_to_array(void)
{
	SListEntry *list;
	void **array;

	list = generate_list();

	array = slist_to_array(list);

	assert(array[0] == &variable1);
	assert(array[1] == &variable2);
	assert(array[2] == &variable3);
	assert(array[3] == &variable4);

	free(array);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	array = slist_to_array(list);
	assert(array == NULL);

	slist_free(list);
}

void test_slist_iterate(void)
{
	SListEntry *list;
	SListIterator iter;
	int *data;
	int a;
	int i;
	int counter;

	/* Create a list with 50 entries */

	list = NULL;

	for (i=0; i<50; ++i) {
		slist_prepend(&list, &a);
	}

	/* Iterate over the list and count the number of entries visited */

	counter = 0;

	slist_iterate(&list, &iter);

	/* Test remove before slist_iter_next has been called */

	slist_iter_remove(&iter);

	/* Iterate over the list */

	while (slist_iter_has_more(&iter)) {

		data = (int *) slist_iter_next(&iter);

		++counter;

		/* Remove half the entries from the list */

		if ((counter % 2) == 0) {
			slist_iter_remove(&iter);

			/* Test double remove */

			slist_iter_remove(&iter);
		}
	}

	/* Test iter_next after iteration has completed. */

	assert(slist_iter_next(&iter) == SLIST_NULL);

	/* Test remove at the end of a list */

	slist_iter_remove(&iter);

	assert(counter == 50);
	assert(slist_length(list) == 25);

	slist_free(list);

	/* Test iterating over an empty list */

	list = NULL;
	counter = 0;

	slist_iterate(&list, &iter);

	while (slist_iter_has_more(&iter)) {

		data = (int *) slist_iter_next(&iter);

		++counter;

		/* Remove half the entries from the list */

		if ((counter % 2) == 0) {
			slist_iter_remove(&iter);
		}
	}

	assert(counter == 0);
}

/* Test that the iterator functions can survive removal of the current
 * value using the normal remove functions. */

void test_slist_iterate_bad_remove(void)
{
	SListEntry *list;
	SListIterator iter;
	int values[49];
	int i;
	int *val;

	/* Create a list with 49 entries */

	list = NULL;

	for (i=0; i<49; ++i) {
		values[i] = i;
		slist_prepend(&list, &values[i]);
	}

	/* Iterate over the list, removing each element in turn.  We
	 * use an odd number of list elements so that the first and
	 * last entries are removed. */

	slist_iterate(&list, &iter);

	while (slist_iter_has_more(&iter)) {
		val = slist_iter_next(&iter);

		/* Remove all the even numbers. Check that slist_iter_remove
		 * can cope with the fact that the current element has
		 * already been removed. */

		if ((*val % 2) == 0) {
			assert(slist_remove_data(&list, int_equal, val) != 0);
			slist_iter_remove(&iter);
		}
	}

	slist_free(list);
}

static UnitTestFunction tests[] = {
	test_slist_append,
	test_slist_prepend,
	test_slist_free,
	test_slist_next,
	test_slist_nth_entry,
	test_slist_nth_data,
	test_slist_length,
	test_slist_remove_entry,
	test_slist_remove_data,
	test_slist_sort,
	test_slist_find_data,
	test_slist_to_array,
	test_slist_iterate,
	test_slist_iterate_bad_remove,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

