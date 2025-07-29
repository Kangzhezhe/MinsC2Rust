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


/* malloc() / free() testing */

#ifdef ALLOC_TESTING
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

#endif

/* A doubly-linked list */

struct _ListEntry {
	ListValue data;
	ListEntry *prev;
	ListEntry *next;
};

void list_free(ListEntry *list)
{
	ListEntry *entry;

	/* Iterate over each entry, freeing each list entry, until the
	 * end is reached */

	entry = list;

	while (entry != NULL) {
		ListEntry *next;

		next = entry->next;

		free(entry);

		entry = next;
	}
}

ListEntry *list_prepend(ListEntry **list, ListValue data)
{
	ListEntry *newentry;

	if (list == NULL) {

		/* not a valid list */

		return NULL;
	}

	/* Create new entry */

	newentry = malloc(sizeof(ListEntry));

	if (newentry == NULL) {
		return NULL;
	}

	newentry->data = data;

	/* Hook into the list start */

	if (*list != NULL) {
		(*list)->prev = newentry;
	}
	newentry->prev = NULL;
	newentry->next = *list;
	*list = newentry;

	return newentry;
}

ListEntry *list_append(ListEntry **list, ListValue data)
{
	ListEntry *rover;
	ListEntry *newentry;

	if (list == NULL) {
		return NULL;
	}

	/* Create new list entry */

	newentry = malloc(sizeof(ListEntry));

	if (newentry == NULL) {
		return NULL;
	}

	newentry->data = data;
	newentry->next = NULL;

	/* Hooking into the list is different if the list is empty */

	if (*list == NULL) {

		/* Create the start of the list */

		*list = newentry;
		newentry->prev = NULL;

	} else {

		/* Find the end of list */

		for (rover=*list; rover->next != NULL; rover = rover->next);

		/* Add to the end of list */

		newentry->prev = rover;
		rover->next = newentry;
	}

	return newentry;
}

ListValue list_data(ListEntry *listentry)
{
	if (listentry == NULL) {
		return LIST_NULL;
	}

	return listentry->data;
}

void list_set_data(ListEntry *listentry, ListValue value)
{
	if (listentry != NULL) {
		listentry->data = value;
	}
}

ListEntry *list_prev(ListEntry *listentry)
{
	if (listentry == NULL) {
		return NULL;
	}

	return listentry->prev;
}

ListEntry *list_next(ListEntry *listentry)
{
	if (listentry == NULL) {
		return NULL;
	}

	return listentry->next;
}

ListEntry *list_nth_entry(ListEntry *list, unsigned int n)
{
	ListEntry *entry;
	unsigned int i;

	/* Iterate through n list entries to reach the desired entry.
	 * Make sure we do not reach the end of the list. */

	entry = list;

	for (i=0; i<n; ++i) {

		if (entry == NULL) {
			return NULL;
		}
		entry = entry->next;
	}

	return entry;
}

ListValue list_nth_data(ListEntry *list, unsigned int n)
{
	ListEntry *entry;

	/* Find the specified entry */

	entry = list_nth_entry(list, n);

	/* If out of range, return NULL, otherwise return the data */

	if (entry == NULL) {
		return LIST_NULL;
	} else {
		return entry->data;
	}
}

unsigned int list_length(ListEntry *list)
{
	ListEntry *entry;
	unsigned int length;

	length = 0;
	entry = list;

	while (entry != NULL) {

		/* Count the number of entries */

		++length;

		entry = entry->next;
	}

	return length;
}

ListValue *list_to_array(ListEntry *list)
{
	ListEntry *rover;
	ListValue *array;
	unsigned int length;
	unsigned int i;

	/* Allocate an array equal in size to the list length */

	length = list_length(list);

	array = malloc(sizeof(ListValue) * length);

	if (array == NULL) {
		return NULL;
	}

	/* Add all entries to the array */

	rover = list;

	for (i=0; i<length; ++i) {

		/* Add this node's data */

		array[i] = rover->data;

		/* Jump to the next list node */

		rover = rover->next;
	}

	return array;
}

int list_remove_entry(ListEntry **list, ListEntry *entry)
{
	/* If the list is empty, or entry is NULL, always fail */

	if (list == NULL || *list == NULL || entry == NULL) {
		return 0;
	}

	/* Action to take is different if the entry is the first in the list */

	if (entry->prev == NULL) {

		/* Unlink the first entry and update the starting pointer */

		*list = entry->next;

		/* Update the second entry's prev pointer, if there is a second
		 * entry */

		if (entry->next != NULL) {
			entry->next->prev = NULL;
		}

	} else {

		/* This is not the first in the list, so we must have a
		 * previous entry.  Update its 'next' pointer to the new
		 * value */

		entry->prev->next = entry->next;

		/* If there is an entry following this one, update its 'prev'
		 * pointer to the new value */

		if (entry->next != NULL) {
			entry->next->prev = entry->prev;
		}
	}

	/* Free the list entry */

	free(entry);

	/* Operation successful */

	return 1;
}

unsigned int list_remove_data(ListEntry **list, ListEqualFunc callback,
                              ListValue data)
{
	unsigned int entries_removed;
	ListEntry *rover;
	ListEntry *next;

	if (list == NULL || callback == NULL) {
		return 0;
	}

	entries_removed = 0;

	/* Iterate over the entries in the list */

	rover = *list;

	while (rover != NULL) {

		next = rover->next;

		if (callback(rover->data, data)) {

			/* This data needs to be removed.  Unlink this entry
			 * from the list. */

			if (rover->prev == NULL) {

				/* This is the first entry in the list */

				*list = rover->next;
			} else {

				/* Point the previous entry at its new
				 * location */

				rover->prev->next = rover->next;
			}

			if (rover->next != NULL) {
				rover->next->prev = rover->prev;
			}

			/* Free the entry */

			free(rover);

			++entries_removed;
		}

		/* Advance to the next list entry */

		rover = next;
	}

	return entries_removed;
}

/* Function used internally for sorting.  Returns the last entry in the
 * new sorted list */

static ListEntry *list_sort_internal(ListEntry **list,
                                     ListCompareFunc compare_func)
{
	ListEntry *pivot;
	ListEntry *rover;
	ListEntry *less_list, *more_list;
	ListEntry *less_list_end, *more_list_end;

	if (list == NULL || compare_func == NULL) {
		return NULL;
	}

	/* If there are less than two entries in this list, it is
	 * already sorted */

	if (*list == NULL || (*list)->next == NULL) {
		return *list;
	}

	/* The first entry is the pivot */

	pivot = *list;

	/* Iterate over the list, starting from the second entry.  Sort
	 * all entries into the less and more lists based on comparisons
	 * with the pivot */

	less_list = NULL;
	more_list = NULL;
	rover = (*list)->next;

	while (rover != NULL) {
		ListEntry *next = rover->next;

		if (compare_func(rover->data, pivot->data) < 0) {

			/* Place this in the less list */

			rover->prev = NULL;
			rover->next = less_list;
			if (less_list != NULL) {
				less_list->prev = rover;
			}
			less_list = rover;

		} else {

			/* Place this in the more list */

			rover->prev = NULL;
			rover->next = more_list;
			if (more_list != NULL) {
				more_list->prev = rover;
			}
			more_list = rover;
		}

		rover = next;
	}

	/* Sort the sublists recursively */

	less_list_end = list_sort_internal(&less_list, compare_func);
	more_list_end = list_sort_internal(&more_list, compare_func);

	/* Create the new list starting from the less list */

	*list = less_list;

	/* Append the pivot to the end of the less list.  If the less list
	 * was empty, start from the pivot */

	if (less_list == NULL) {
		pivot->prev = NULL;
		*list = pivot;
	} else {
		pivot->prev = less_list_end;
		less_list_end->next = pivot;
	}

	/* Append the more list after the pivot */

	pivot->next = more_list;
	if (more_list != NULL) {
		more_list->prev = pivot;
	}

	/* Work out what the last entry in the list is.  If the more list was
	 * empty, the pivot was the last entry.  Otherwise, the end of the
	 * more list is the end of the total list. */

	if (more_list == NULL) {
		return pivot;
	} else {
		return more_list_end;
	}
}

void list_sort(ListEntry **list, ListCompareFunc compare_func)
{
	list_sort_internal(list, compare_func);
}

ListEntry *list_find_data(ListEntry *list,
                          ListEqualFunc callback,
                          ListValue data)
{
	ListEntry *rover;

	/* Iterate over entries in the list until the data is found */

	for (rover=list; rover != NULL; rover=rover->next) {
		if (callback(rover->data, data) != 0) {
			return rover;
		}
	}

	/* Not found */

	return NULL;
}

void list_iterate(ListEntry **list, ListIterator *iter)
{
	/* Start iterating from the beginning of the list. */

	iter->prev_next = list;

	/* We have not yet read the first item. */

	iter->current = NULL;
}

int list_iter_has_more(ListIterator *iter)
{
	if (iter->current == NULL || iter->current != *iter->prev_next) {

		/* Either we have not read the first entry, the current
		 * item was removed or we have reached the end of the
		 * list.  Use prev_next to determine if we have a next
		 * value to iterate over. */

		return *iter->prev_next != NULL;

	} else {
		/* The current entry as not been deleted since the last
		 * call to list_iter_next: there is a next entry if
		 * current->next is not NULL */

		return iter->current->next != NULL;
	}
}

ListValue list_iter_next(ListIterator *iter)
{
	if (iter->current == NULL || iter->current != *iter->prev_next) {

		/* Either we are reading the first entry, we have reached
		 * the end of the list, or the previous entry was removed.
		 * Get the next entry with iter->prev_next. */

		iter->current = *iter->prev_next;

	} else {

		/* Last value returned from list_iter_next was not deleted.
		 * Advance to the next entry. */

		iter->prev_next = &iter->current->next;
		iter->current = iter->current->next;
	}

	/* Have we reached the end of the list? */

	if (iter->current == NULL) {
		return LIST_NULL;
	} else {
		return iter->current->data;
	}
}

void list_iter_remove(ListIterator *iter)
{
	if (iter->current == NULL || iter->current != *iter->prev_next) {

		/* Either we have not yet read the first item, we have
		 * reached the end of the list, or we have already removed
		 * the current value.  Either way, do nothing. */

	} else {

		/* Remove the current entry */

		*iter->prev_next = iter->current->next;

		if (iter->current->next != NULL) {
			iter->current->next->prev = iter->current->prev;
		}

		free(iter->current);
		iter->current = NULL;
	}
}

