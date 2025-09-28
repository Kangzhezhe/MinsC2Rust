// 识别到的包含指令
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sortedarray.h"
#include "alloc-testing.h"

// 识别到的结构体定义
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

// 识别到的函数定义
// 函数: sortedarray_first_index (line 71)
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

// 函数: sortedarray_last_index (line 94)
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

// 函数: sortedarray_get (line 115)
SortedArrayValue *sortedarray_get(SortedArray *array, unsigned int i)
{
	//check if array is NULL
	if (array == NULL) {
		return NULL;
	}

	//otherwise just return the element
	return array->data[i];	
}

// 函数: sortedarray_length (line 126)
unsigned int sortedarray_length(SortedArray *array)
{
	return array->length;
}

// 函数: sortedarray_new (line 131)
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

// 函数: sortedarray_free (line 169)
void sortedarray_free(SortedArray *sortedarray)
{
	if (sortedarray != NULL) {
		free(sortedarray->data);
		free(sortedarray);
	}
}

// 函数: sortedarray_remove (line 177)
void sortedarray_remove(SortedArray *sortedarray, unsigned int index)
{
	/* same as remove range of length 1 */
	sortedarray_remove_range(sortedarray, index, 1);
}

// 函数: sortedarray_remove_range (line 183)
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

// 函数: sortedarray_insert (line 202)
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

// 函数: sortedarray_index_of (line 264)
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

// 函数: sortedarray_clear (line 312)
void sortedarray_clear(SortedArray *sortedarray)
{
	/* set length to 0 */
	sortedarray->length = 0;
}
