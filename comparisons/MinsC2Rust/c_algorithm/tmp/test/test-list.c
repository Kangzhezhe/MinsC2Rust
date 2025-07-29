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
 * @file list.h
 *
 * @brief Doubly-linked list.
 *
 * A doubly-linked list stores a collection of values.  Each entry in
 * the list (represented by a pointer a @ref ListEntry structure)
 * contains a link to the next entry and the previous entry.
 * It is therefore possible to iterate over entries in the list in either
 * direction.
 *
 * To create an empty list, create a new variable which is a pointer to
 * a @ref ListEntry structure, and initialise it to NULL.
 * To destroy an entire list, use @ref list_free.
 *
 * To add a value to a list, use @ref list_append or @ref list_prepend.
 *
 * To remove a value from a list, use @ref list_remove_entry or
 * @ref list_remove_data.
 *
 * To iterate over entries in a list, use @ref list_iterate to initialise
 * a @ref ListIterator structure, with @ref list_iter_next and
 * @ref list_iter_has_more to retrieve each value in turn.
 * @ref list_iter_remove can be used to remove the current entry.
 *
 * To access an entry in the list by index, use @ref list_nth_entry or
 * @ref list_nth_data.
 *
 * To modify data in the list use @ref list_set_data.
 *
 * To sort a list, use @ref list_sort.
 *
 */

#ifndef ALGORITHM_LIST_H
#define ALGORITHM_LIST_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Represents an entry in a doubly-linked list.  The empty list is
 * represented by a NULL pointer. To initialise a new doubly linked
 * list, simply create a variable of this type
 * containing a pointer to NULL.
 */

typedef struct _ListEntry ListEntry;

/**
 * Structure used to iterate over a list.
 */

typedef struct _ListIterator ListIterator;

/**
 * A value stored in a list.
 */

typedef void *ListValue;

/**
 * Definition of a @ref ListIterator.
 */

struct _ListIterator {
	ListEntry **prev_next;
	ListEntry *current;
};

/**
 * A null @ref ListValue.
 */

#define LIST_NULL ((void *) 0)

/**
 * Callback function used to compare values in a list when sorting.
 *
 * @param value1      The first value to compare.
 * @param value2      The second value to compare.
 * @return            A negative value if value1 should be sorted before
 *                    value2, a positive value if value1 should be sorted
 *                    after value2, zero if value1 and value2 are equal.
 */

typedef int (*ListCompareFunc)(ListValue value1, ListValue value2);

/**
 * Callback function used to determine of two values in a list are
 * equal.
 *
 * @param value1      The first value to compare.
 * @param value2      The second value to compare.
 * @return            A non-zero value if value1 and value2 are equal, zero
 *                    if they are not equal.
 */

typedef int (*ListEqualFunc)(ListValue value1, ListValue value2);

/**
 * Free an entire list.
 *
 * @param list         The list to free.
 */

void list_free(ListEntry *list);

/**
 * Prepend a value to the start of a list.
 *
 * @param list         Pointer to the list to prepend to.
 * @param data         The value to prepend.
 * @return             The new entry in the list, or NULL if it was not
 *                     possible to allocate the memory for the new entry.
 */

ListEntry *list_prepend(ListEntry **list, ListValue data);

/**
 * Append a value to the end of a list.
 *
 * @param list         Pointer to the list to append to.
 * @param data         The value to append.
 * @return             The new entry in the list, or NULL if it was not
 *                     possible to allocate the memory for the new entry.
 */

ListEntry *list_append(ListEntry **list, ListValue data);

/**
 * Retrieve the previous entry in a list.
 *
 * @param listentry    Pointer to the list entry.
 * @return             The previous entry in the list, or NULL if this
 *                     was the first entry in the list.
 */

ListEntry *list_prev(ListEntry *listentry);

/**
 * Retrieve the next entry in a list.
 *
 * @param listentry    Pointer to the list entry.
 * @return             The next entry in the list, or NULL if this was the
 *                     last entry in the list.
 */

ListEntry *list_next(ListEntry *listentry);

/**
 * Retrieve the value at a list entry.
 *
 * @param listentry    Pointer to the list entry.
 * @return             The value stored at the list entry.
 */

ListValue list_data(ListEntry *listentry);

/**
 * Set the value at a list entry. The value provided will be written to the 
 * given listentry. If listentry is NULL nothing is done.
 *
 * @param listentry 	Pointer to the list entry.
 * @param value			The value to set.
 */
void list_set_data(ListEntry *listentry, ListValue value);

/**
 * Retrieve the entry at a specified index in a list.
 *
 * @param list       The list.
 * @param n          The index into the list .
 * @return           The entry at the specified index, or NULL if out of range.
 */

ListEntry *list_nth_entry(ListEntry *list, unsigned int n);

/**
 * Retrieve the value at a specified index in the list.
 *
 * @param list       The list.
 * @param n          The index into the list.
 * @return           The value at the specified index, or @ref LIST_NULL if
 *                   unsuccessful.
 */

ListValue list_nth_data(ListEntry *list, unsigned int n);

/**
 * Find the length of a list.
 *
 * @param list       The list.
 * @return           The number of entries in the list.
 */

unsigned int list_length(ListEntry *list);

/**
 * Create a C array containing the contents of a list.
 *
 * @param list       The list.
 * @return           A newly-allocated C array containing all values in the
 *                   list, or NULL if it was not possible to allocate the
 *                   memory.  The length of the array is equal to the length
 *                   of the list (see @ref list_length).
 */

ListValue *list_to_array(ListEntry *list);

/**
 * Remove an entry from a list.
 *
 * @param list       Pointer to the list.
 * @param entry      The list entry to remove .
 * @return           If the entry is not found in the list, returns zero,
 *                   else returns non-zero.
 */

int list_remove_entry(ListEntry **list, ListEntry *entry);

/**
 * Remove all occurrences of a particular value from a list.
 *
 * @param list       Pointer to the list.
 * @param callback   Function to invoke to compare values in the list
 *                   with the value to be removed.
 * @param data       The value to remove from the list.
 * @return           The number of entries removed from the list.
 */

unsigned int list_remove_data(ListEntry **list, ListEqualFunc callback,
                              ListValue data);

/**
 * Sort a list.
 *
 * @param list          Pointer to the list to sort.
 * @param compare_func  Function used to compare values in the list.
 */

void list_sort(ListEntry **list, ListCompareFunc compare_func);

/**
 * Find the entry for a particular value in a list.
 *
 * @param list           The list to search.
 * @param callback       Function to invoke to compare values in the list
 *                       with the value to be searched for.
 * @param data           The value to search for.
 * @return               The list entry of the item being searched for, or
 *                       NULL if not found.
 */

ListEntry *list_find_data(ListEntry *list,
                          ListEqualFunc callback,
                          ListValue data);

/**
 * Initialise a @ref ListIterator structure to iterate over a list.
 *
 * @param list           A pointer to the list to iterate over.
 * @param iter           A pointer to an iterator structure to initialise.
 */

void list_iterate(ListEntry **list, ListIterator *iter);

/**
 * Determine if there are more values in the list to iterate over.
 *
 * @param iterator       The list iterator.
 * @return               Zero if there are no more values in the list to
 *                       iterate over, non-zero if there are more values to
 *                       read.
 */

int list_iter_has_more(ListIterator *iterator);

/**
 * Using a list iterator, retrieve the next value from the list.
 *
 * @param iterator       The list iterator.
 * @return               The next value from the list, or @ref LIST_NULL if
 *                       there are no more values in the list.
 */

ListValue list_iter_next(ListIterator *iterator);

/**
 * Delete the current entry in the list (the value last returned from
 * list_iter_next)
 *
 * @param iterator       The list iterator.
 */

void list_iter_remove(ListIterator *iterator);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_LIST_H */

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

ListEntry *generate_list(void)
{
	ListEntry *list = NULL;

	assert(list_append(&list, &variable1) != NULL);
	assert(list_append(&list, &variable2) != NULL);
	assert(list_append(&list, &variable3) != NULL);
	assert(list_append(&list, &variable4) != NULL);

	return list;
}

void check_list_integrity(ListEntry *list)
{
	ListEntry *prev;
	ListEntry *rover;

	prev = NULL;
	rover = list;

	while (rover != NULL) {
		assert(list_prev(rover) == prev);
		prev = rover;
		rover = list_next(rover);
	}
}

void test_list_append(void)
{
	ListEntry *list = NULL;

	assert(list_append(&list, &variable1) != NULL);
	check_list_integrity(list);
	assert(list_append(&list, &variable2) != NULL);
	check_list_integrity(list);
	assert(list_append(&list, &variable3) != NULL);
	check_list_integrity(list);
	assert(list_append(&list, &variable4) != NULL);
	check_list_integrity(list);

	assert(list_length(list) == 4);

	assert(list_nth_data(list, 0) == &variable1);
	assert(list_nth_data(list, 1) == &variable2);
	assert(list_nth_data(list, 2) == &variable3);
	assert(list_nth_data(list, 3) == &variable4);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(list_length(list) == 4);
	assert(list_append(&list, &variable1) == NULL);
	assert(list_length(list) == 4);
	check_list_integrity(list);

	list_free(list);
}

void test_list_prepend(void)
{
	ListEntry *list = NULL;

	assert(list_prepend(&list, &variable1) != NULL);
	check_list_integrity(list);
	assert(list_prepend(&list, &variable2) != NULL);
	check_list_integrity(list);
	assert(list_prepend(&list, &variable3) != NULL);
	check_list_integrity(list);
	assert(list_prepend(&list, &variable4) != NULL);
	check_list_integrity(list);

	assert(list_nth_data(list, 0) == &variable4);
	assert(list_nth_data(list, 1) == &variable3);
	assert(list_nth_data(list, 2) == &variable2);
	assert(list_nth_data(list, 3) == &variable1);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(list_length(list) == 4);
	assert(list_prepend(&list, &variable1) == NULL);
	assert(list_length(list) == 4);
	check_list_integrity(list);

	list_free(list);
}

void test_list_free(void)
{
	ListEntry *list;

	/* Create a list and free it */

	list = generate_list();

	list_free(list);

	/* Check the empty list frees correctly */

	list_free(NULL);
}

void test_list_next(void)
{
	ListEntry *list;
	ListEntry *rover;

	list = generate_list();

	rover = list;
	assert(list_data(rover) == &variable1);
	rover = list_next(rover);
	assert(list_data(rover) == &variable2);
	rover = list_next(rover);
	assert(list_data(rover) == &variable3);
	rover = list_next(rover);
	assert(list_data(rover) == &variable4);
	rover = list_next(rover);
	assert(rover == NULL);

	list_free(list);
}

void test_list_nth_entry(void)
{
	ListEntry *list;
	ListEntry *entry;

	list = generate_list();

	/* Check all values in the list */

	entry = list_nth_entry(list, 0);
	assert(list_data(entry) == &variable1);
	entry = list_nth_entry(list, 1);
	assert(list_data(entry) == &variable2);
	entry = list_nth_entry(list, 2);
	assert(list_data(entry) == &variable3);
	entry = list_nth_entry(list, 3);
	assert(list_data(entry) == &variable4);

	/* Check out of range values */

	entry = list_nth_entry(list, 4);
	assert(entry == NULL);
	entry = list_nth_entry(list, 400);
	assert(entry == NULL);

	list_free(list);
}

void test_list_nth_data(void)
{
	ListEntry *list;

	list = generate_list();

	/* Check all values in the list */

	assert(list_nth_data(list, 0) == &variable1);
	assert(list_nth_data(list, 1) == &variable2);
	assert(list_nth_data(list, 2) == &variable3);
	assert(list_nth_data(list, 3) == &variable4);

	/* Check out of range values */

	assert(list_nth_data(list, 4) == NULL);
	assert(list_nth_data(list, 400) == NULL);

	list_free(list);
}

void test_list_length(void)
{
	ListEntry *list;

	/* Generate a list and check that it is four entries long */

	list = generate_list();

	assert(list_length(list) == 4);

	/* Add an entry and check that it still works properly */

	assert(list_prepend(&list, &variable1) != NULL);

	assert(list_length(list) == 5);

	list_free(list);

	/* Check the length of the empty list */

	assert(list_length(NULL) == 0);
}

void test_list_remove_entry(void)
{
	ListEntry *empty_list = NULL;
	ListEntry *list;
	ListEntry *entry;

	list = generate_list();

	/* Remove the third entry */

	entry = list_nth_entry(list, 2);
	assert(list_remove_entry(&list, entry) != 0);
	assert(list_length(list) == 3);
	check_list_integrity(list);

	/* Remove the first entry */

	entry = list_nth_entry(list, 0);
	assert(list_remove_entry(&list, entry) != 0);
	assert(list_length(list) == 2);
	check_list_integrity(list);

	/* Try some invalid removes */

	/* NULL */

	assert(list_remove_entry(&list, NULL) == 0);

	/* Removing NULL from an empty list */

	assert(list_remove_entry(&empty_list, NULL) == 0);

	list_free(list);

	/* Test removing an entry when it is the only entry. */

	list = NULL;
	assert(list_append(&list, &variable1) != NULL);
	assert(list != NULL);
	assert(list_remove_entry(&list, list) != 0);
	assert(list == NULL);

	/* Test removing the last entry */

	list = generate_list();
	entry = list_nth_entry(list, 3);
	assert(list_remove_entry(&list, entry) != 0);
	check_list_integrity(list);
	list_free(list);
}

void test_list_remove_data(void)
{
	int entries[] = { 89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	int val;
	ListEntry *list;
	unsigned int i;

	/* Generate a list containing all the entries in the array */

	list = NULL;

	for (i=0; i<num_entries; ++i) {
		assert(list_prepend(&list, &entries[i]) != NULL);
	}

	/* Test removing invalid data */

	val = 0;
	assert(list_remove_data(&list, int_equal, &val) == 0);
	val = 56;
	assert(list_remove_data(&list, int_equal, &val) == 0);
	check_list_integrity(list);

	/* Remove the number 8 from the list */

	val = 8;
	assert(list_remove_data(&list, int_equal, &val) == 1);
	assert(list_length(list) == num_entries - 1);
	check_list_integrity(list);

	/* Remove the number 4 from the list (occurs multiple times) */

	val = 4;
	assert(list_remove_data(&list, int_equal, &val) == 4);
	assert(list_length(list) == num_entries - 5);
	check_list_integrity(list);

	/* Remove the number 89 from the list (first entry) */

	val = 89;
	assert(list_remove_data(&list, int_equal, &val) == 1);
	assert(list_length(list) == num_entries - 6);
	check_list_integrity(list);

	list_free(list);
}

void test_list_sort(void)
{
	ListEntry *list;
	int entries[] = { 89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4 };
	int sorted[]  = { 4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99 };
	unsigned int num_entries = sizeof(entries) / sizeof(int);
	unsigned int i;

	list = NULL;

	for (i=0; i<num_entries; ++i) {
		assert(list_prepend(&list, &entries[i]) != NULL);
	}

	list_sort(&list, int_compare);

	/* List length is unchanged */

	assert(list_length(list) == num_entries);

	/* Check the list is sorted */

	for (i=0; i<num_entries; ++i) {
		int *value;

		value = (int *) list_nth_data(list, i);
		assert(*value == sorted[i]);
	}

	list_free(list);

	/* Check sorting an empty list */

	list = NULL;

	list_sort(&list, int_compare);

	assert(list == NULL);
}

void test_list_find_data(void)
{
	int entries[] = { 89, 23, 42, 16, 15, 4, 8, 99, 50, 30 };
	int num_entries = sizeof(entries) / sizeof(int);
	ListEntry *list;
	ListEntry *result;
	int i;
	int val;
	int *data;

	/* Generate a list containing the entries */

	list = NULL;
	for (i=0; i<num_entries; ++i) {
		assert(list_append(&list, &entries[i]) != NULL);
	}

	/* Check that each value can be searched for correctly */

	for (i=0; i<num_entries; ++i) {

		val = entries[i];

		result = list_find_data(list, int_equal, &val);

		assert(result != NULL);

		data = (int *) list_data(result);
		assert(*data == val);
	}

	/* Check some invalid values return NULL */

	val = 0;
	assert(list_find_data(list, int_equal, &val) == NULL);
	val = 56;
	assert(list_find_data(list, int_equal, &val) == NULL);

	list_free(list);
}

void test_list_to_array(void)
{
	ListEntry *list;
	void **array;

	list = generate_list();

	array = list_to_array(list);

	assert(array[0] == &variable1);
	assert(array[1] == &variable2);
	assert(array[2] == &variable3);
	assert(array[3] == &variable4);

	free(array);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	array = list_to_array(list);
	assert(array == NULL);

	list_free(list);
}

void test_list_iterate(void)
{
	ListEntry *list;
	ListIterator iter;
	int i;
	int a;
	int counter;
	int *data;

	/* Create a list with 50 entries */

	list = NULL;

	for (i=0; i<50; ++i) {
		assert(list_prepend(&list, &a) != NULL);
	}

	/* Iterate over the list and count the number of entries visited */

	counter = 0;

	list_iterate(&list, &iter);

	/* Test remove before list_iter_next has been called */

	list_iter_remove(&iter);

	/* Iterate over the list */

	while (list_iter_has_more(&iter)) {
		data = (int *) list_iter_next(&iter);
		++counter;

		if ((counter % 2) == 0) {
			/* Delete half the entries in the list.  */

			list_iter_remove(&iter);

			/* Test double remove */

			list_iter_remove(&iter);
		}
	}

	/* Test iter_next after iteration has completed. */

	assert(list_iter_next(&iter) == NULL);

	/* Test remove at the end of a list */

	list_iter_remove(&iter);

	assert(counter == 50);
	assert(list_length(list) == 25);

	list_free(list);

	/* Test iterating over an empty list */

	list = NULL;
	counter = 0;

	list_iterate(&list, &iter);

	while (list_iter_has_more(&iter)) {
		data = (int *) list_iter_next(&iter);
		++counter;
	}

	assert(counter == 0);
}

/* Test that the iterator functions can survive removal of the current
 * value using the normal remove functions. */

void test_list_iterate_bad_remove(void)
{
	ListEntry *list;
	ListIterator iter;
	int values[49];
	int i;
	int *val;

	/* Create a list with 49 entries */

	list = NULL;

	for (i=0; i<49; ++i) {
		values[i] = i;
		assert(list_prepend(&list, &values[i]) != NULL);
	}

	/* Iterate over the list, removing each element in turn.  We
	 * use an odd number of list elements so that the first and
	 * last entries are removed. */

	list_iterate(&list, &iter);

	while (list_iter_has_more(&iter)) {
		val = list_iter_next(&iter);

		/* Remove all the even numbers. Check that list_iter_remove
		 * can cope with the fact that the current element has
		 * already been removed. */

		if ((*val % 2) == 0) {
			assert(list_remove_data(&list, int_equal, val) != 0);
			list_iter_remove(&iter);
		}
	}

	list_free(list);
}

static UnitTestFunction tests[] = {
	test_list_append,
	test_list_prepend,
	test_list_free,
	test_list_next,
	test_list_nth_entry,
	test_list_nth_data,
	test_list_length,
	test_list_remove_entry,
	test_list_remove_data,
	test_list_sort,
	test_list_find_data,
	test_list_to_array,
	test_list_iterate,
	test_list_iterate_bad_remove,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

