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

struct _BinaryHeap {
	BinaryHeapType heap_type;
	BinaryHeapValue *values;
	unsigned int num_values;
	unsigned int alloced_size;
	BinaryHeapCompareFunc compare_func;
};

static int binary_heap_cmp(BinaryHeap *heap, BinaryHeapValue data1,
                           BinaryHeapValue data2)
{
	if (heap->heap_type == BINARY_HEAP_TYPE_MIN) {
		return heap->compare_func(data1, data2);
	} else {
		return -heap->compare_func(data1, data2);
	}
}

BinaryHeap *binary_heap_new(BinaryHeapType heap_type,
                            BinaryHeapCompareFunc compare_func)
{
	BinaryHeap *heap;

	heap = malloc(sizeof(BinaryHeap));

	if (heap == NULL) {
		return NULL;
	}

	heap->heap_type = heap_type;
	heap->num_values = 0;
	heap->compare_func = compare_func;

	/* Initial size of 16 elements */

	heap->alloced_size = 16;
	heap->values = malloc(sizeof(BinaryHeapValue) * heap->alloced_size);

	if (heap->values == NULL) {
		free(heap);
		return NULL;
	}

	return heap;
}

void binary_heap_free(BinaryHeap *heap)
{
	free(heap->values);
	free(heap);
}

int binary_heap_insert(BinaryHeap *heap, BinaryHeapValue value)
{
	BinaryHeapValue *new_values;
	unsigned int index;
	unsigned int new_size;
	unsigned int parent;

	/* Possibly realloc the heap to a larger size */

	if (heap->num_values >= heap->alloced_size) {

		/* Double the table size */

		new_size = heap->alloced_size * 2;
		new_values = realloc(heap->values,
		                     sizeof(BinaryHeapValue) * new_size);

		if (new_values == NULL) {
			return 0;
		}

		heap->alloced_size = new_size;
		heap->values = new_values;
	}

	/* Add to the bottom of the heap and start from there */

	index = heap->num_values;
	++heap->num_values;

	/* Percolate the value up to the top of the heap */

	while (index > 0) {

		/* The parent index is found by halving the node index */

		parent = (index - 1) / 2;

		/* Compare the node with its parent */

		if (binary_heap_cmp(heap, heap->values[parent], value) < 0) {

			/* Ordered correctly - insertion is complete */

			break;

		} else {

			/* Need to swap this node with its parent */

			heap->values[index] = heap->values[parent];

			/* Advance up to the parent */

			index = parent;
		}
	}

	/* Save the new value in the final location */

	heap->values[index] = value;

	return 1;
}

BinaryHeapValue binary_heap_pop(BinaryHeap *heap)
{
	BinaryHeapValue result;
	BinaryHeapValue new_value;
	unsigned int index;
	unsigned int next_index;
	unsigned int child1, child2;

	/* Empty heap? */

	if (heap->num_values == 0) {
		return BINARY_HEAP_NULL;
	}

	/* Take the value from the top of the heap */

	result = heap->values[0];

	/* Remove the last value from the heap; we will percolate this down
	 * from the top. */

	new_value = heap->values[heap->num_values - 1];
	--heap->num_values;

	/* Percolate the new top value down */

	index = 0;

	for (;;) {

		/* Calculate the array indexes of the children of this node */

		child1 = index * 2 + 1;
		child2 = index * 2 + 2;

		if (child1 < heap->num_values
		 && binary_heap_cmp(heap,
		                    new_value,
		                    heap->values[child1]) > 0) {

			/* Left child is less than the node.  We need to swap
			 * with one of the children, whichever is less. */

			if (child2 < heap->num_values
			 && binary_heap_cmp(heap,
			                    heap->values[child1],
			                    heap->values[child2]) > 0) {
				next_index = child2;
			} else {
				next_index = child1;
			}

		} else if (child2 < heap->num_values
		        && binary_heap_cmp(heap,
		                           new_value,
		                           heap->values[child2]) > 0) {

			/* Right child is less than the node.  Swap with the
			 * right child. */

			next_index = child2;

		} else {
			/* Node is less than both its children. The heap
			 * condition is satisfied.  * We can stop percolating
			 * down. */

			heap->values[index] = new_value;
			break;
		}

		/* Swap the current node with the least of the child nodes. */

		heap->values[index] = heap->values[next_index];

		/* Advance to the child we chose */

		index = next_index;
	}

	return result;
}

unsigned int binary_heap_num_entries(BinaryHeap *heap)
{
	return heap->num_values;
}

