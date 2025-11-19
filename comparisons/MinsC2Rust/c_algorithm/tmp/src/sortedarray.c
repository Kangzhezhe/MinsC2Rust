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
 * @file sortedarray.c
 * 
 * @brief File containing the implementation of sortedarray.h
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

/**
 * Definition of a @ref SortedArray
 */
struct _SortedArray {
	/**
	 * This field contains the actual array. The array always has a length
	 * of value of field length.
	 */
	SortedArrayValue *data;

	/**
	 * The length of the sorted array.
	 */
	unsigned int length;

	/**
	 * Field for internal usage only indicating how much memory already has
	 * been allocated for *data.
	 */
	unsigned int _alloced;

	/**
	 * The callback used to determine if two values equal.
	 */
	SortedArrayEqualFunc equ_func;

	/**
	 * The callback use to determine the order of two values.
	 */
	SortedArrayCompareFunc cmp_func;
};

/* Function for finding first index of range which equals data. An equal value
   must be present. */
static unsigned int sortedarray_first_index(SortedArray *sortedarray,
                                   SortedArrayValue data, unsigned int left,
                                   unsigned int right)
{
	unsigned int index = left;

	while (left < right) {
		index = (left + right) / 2;

		int order = sortedarray->cmp_func(data, 
		                                  sortedarray->data[index]);
		if (order > 0) {
			left = index + 1;
		} else {
			right = index;
		}
	}

	return index;
}

/* Function for finding last index of range which equals data. An equal value
   must be present. */
static unsigned int sortedarray_last_index(SortedArray *sortedarray, 
                                  SortedArrayValue data, unsigned int left, 
                                  unsigned int right)
{
	unsigned int index = right;

	while (left < right) {
		index = (left + right) / 2;

		int order = sortedarray->cmp_func(data, 
		                                  sortedarray->data[index]);
		if (order <= 0) {
			left = index + 1;
		} else {
			right = index;
		}
	}

	return index;
}

SortedArrayValue *sortedarray_get(SortedArray *array, unsigned int i)
{
	//check if array is NULL
	if (array == NULL) {
		return NULL;
	}

	//otherwise just return the element
	return array->data[i];	
}

unsigned int sortedarray_length(SortedArray *array)
{
	return array->length;
}

SortedArray *sortedarray_new(unsigned int length,
                             SortedArrayEqualFunc equ_func,
                             SortedArrayCompareFunc cmp_func)
{
	/* check input requirements */
	if (equ_func == NULL || cmp_func == NULL) {
		return NULL;
	}

	/* If length is 0, set it to a default. */
	if (length == 0) {
		length = 16;
	}

	SortedArrayValue *array = malloc(sizeof(SortedArrayValue) * length);

	/* on failure, return null */
	if (array == NULL) {
		return NULL;
	}

	SortedArray *sortedarray = malloc(sizeof(SortedArray));    

	/* check for failure */
	if (sortedarray == NULL) {
		free(array);
		return NULL;
	}
    
	/* init */
	sortedarray->data = array;
	sortedarray->length = 0;
	sortedarray->_alloced = length;
	sortedarray->equ_func = equ_func;
	sortedarray->cmp_func = cmp_func;
	return sortedarray;
}

void sortedarray_free(SortedArray *sortedarray)
{
	if (sortedarray != NULL) {
		free(sortedarray->data);
		free(sortedarray);
	}
}

void sortedarray_remove(SortedArray *sortedarray, unsigned int index)
{
	/* same as remove range of length 1 */
	sortedarray_remove_range(sortedarray, index, 1);
}

void sortedarray_remove_range(SortedArray *sortedarray, unsigned int index,
                              unsigned int length)
{
	/* removal does not violate sorted property */

	/* check if valid range */
	if (index > sortedarray->length || index + length > sortedarray->length) {
		return;
	}

	/* move entries back */
	memmove(&sortedarray->data[index],
	        &sortedarray->data[index + length],
	        (sortedarray->length - (index + length)) 
	              * sizeof(SortedArrayValue));

	sortedarray->length -= length;
}

int sortedarray_insert(SortedArray *sortedarray, SortedArrayValue data)
{
	/* do a binary search like loop to find right position */
	unsigned int left  = 0;
	unsigned int right = sortedarray->length;
	unsigned int index = 0;

	/* When length is 1 set right to 0 so that the loop is not entered */	
	right = (right > 1) ? right : 0;

	while (left != right) {
		index = (left + right) / 2;

		int order = sortedarray->cmp_func(data, 
		                                  sortedarray->data[index]);
		if (order < 0) {
			/* value should be left of index */
			right = index;
		} else if (order > 0) {
			/* value should be right of index */
			left = index + 1;
		} else {
			/* value should be at index */
			break;
		}
	}

	/* look whether the item should be put before or after the index */
	if (sortedarray->length > 0 && sortedarray->cmp_func(data, 
	                       sortedarray->data[index]) > 0) {
		index++;
	}

	/* insert element at index */
	if (sortedarray->length + 1 > sortedarray->_alloced) {
		/* enlarge the array */
		unsigned int newsize;
		SortedArrayValue *data;

		newsize = sortedarray->_alloced * 2;
		data = realloc(sortedarray->data, sizeof(SortedArrayValue) * newsize);

		if (data == NULL) {
			return 0;
		} else {
			sortedarray->data = data;
			sortedarray->_alloced = newsize;
		}
	}

	/* move all other elements */
	memmove(&sortedarray->data[index + 1],
	        &sortedarray->data[index],
	        (sortedarray->length - index) * sizeof(SortedArrayValue));

	/* insert entry */
	sortedarray->data[index] = data;
	++(sortedarray->length);

	return 1;
}

int sortedarray_index_of(SortedArray *sortedarray, SortedArrayValue data)
{
	if (sortedarray == NULL) {
		return -1;
	}
	
	/* do a binary search */
	unsigned int left = 0;
	unsigned int right = sortedarray->length;
	unsigned int index = 0;

	/* safe subtract 1 of right without going negative */
	right = (right > 1) ? right : 0;

	while (left != right) {
		index = (left + right) / 2;

		int order = sortedarray->cmp_func(data, 
		                                  sortedarray->data[index]);
		if (order < 0) {
			/* value should be left */
			right = index;
		} else if (order > 0) {
			/* value should be right */
			left = index + 1;
		} else {
			/* no binary search can be done anymore, 
			   search linear now */
			left = sortedarray_first_index(sortedarray, data, left,
			                               index);
			right = sortedarray_last_index(sortedarray, data, 
			                               index, right);

			for (index = left; index <= right; index++) {
				if (sortedarray->equ_func(data, 
				                sortedarray->data[index])) {
					return (int) index;
				}
			}

			/* nothing is found */
			return -1;
		}
	}

	return -1;
}

void sortedarray_clear(SortedArray *sortedarray)
{
	/* set length to 0 */
	sortedarray->length = 0;
}
