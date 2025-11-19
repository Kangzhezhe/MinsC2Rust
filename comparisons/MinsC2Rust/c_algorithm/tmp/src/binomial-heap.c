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
#include <string.h>
#include <limits.h>

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

typedef struct _BinomialTree BinomialTree;

struct _BinomialTree
{
	BinomialHeapValue value;
	unsigned short order;
	unsigned short refcount;
	BinomialTree **subtrees;
};

struct _BinomialHeap
{
	BinomialHeapType heap_type;
	BinomialHeapCompareFunc compare_func;
	unsigned int num_values;
	BinomialTree **roots;
	unsigned int roots_length;
};

static int binomial_heap_cmp(BinomialHeap *heap,
                             BinomialHeapValue data1,
                             BinomialHeapValue data2)
{
	if (heap->heap_type == BINOMIAL_HEAP_TYPE_MIN) {
		return heap->compare_func(data1, data2);
	} else {
		return -(heap->compare_func(data1, data2));
	}
}

static void binomial_tree_ref(BinomialTree *tree)
{
	if (tree != NULL) {
		++tree->refcount;
	}
}

static void binomial_tree_unref(BinomialTree *tree)
{
	int i;

	if (tree == NULL) {
		return;
	}

	/* Subtract a reference */

	--tree->refcount;

	/* If this removed the last reference, unreference all subtrees
	 * and free. */

	if (tree->refcount == 0) {

		for (i=0; i<tree->order; ++i) {
			binomial_tree_unref(tree->subtrees[i]);
		}

		free(tree->subtrees);
		free(tree);
	}
}

static BinomialTree *binomial_tree_merge(BinomialHeap *heap,
                                         BinomialTree *tree1,
                                         BinomialTree *tree2)
{
	BinomialTree *new_tree;
	BinomialTree *tmp;
	int i;

	/* Order tree1 and tree2 so that tree1 is the tree with the
	 * smallest root */

	if (binomial_heap_cmp(heap, tree1->value, tree2->value) > 0) {

		/* Swap tree1 and tree2 */

		tmp = tree1;
		tree1 = tree2;
		tree2 = tmp;
	}

	/* Allocate a new tree */

	new_tree = malloc(sizeof(BinomialTree));

	if (new_tree == NULL) {
		return NULL;
	}

	new_tree->refcount = 0;
	new_tree->order = (unsigned short) (tree1->order + 1);

	/* Take the smallest value of the two trees */

	new_tree->value = tree1->value;

	/* Copy subtrees of the smallest tree.  The last entry in the
	 * array is the larger tree */

	new_tree->subtrees = malloc(sizeof(BinomialTree *) * new_tree->order);

	if (new_tree->subtrees == NULL) {
		free(new_tree);
		return NULL;
	}

	memcpy(new_tree->subtrees, tree1->subtrees,
	       sizeof(BinomialTree *) * tree1->order);
	new_tree->subtrees[new_tree->order - 1] = tree2;

	/* Add a reference to each of the subtrees we have referenced */

	for (i=0; i<new_tree->order; ++i) {
		binomial_tree_ref(new_tree->subtrees[i]);
	}

	return new_tree;
}

/* Used to perform an "undo" when an error occurs during
 * binomial_heap_merge.  Go through the list of roots so far and remove
 * references that have been added. */

static void binomial_heap_merge_undo(BinomialTree **new_roots,
                                     unsigned int count)
{
	unsigned int i;

	for (i=0; i<=count; ++i) {
		binomial_tree_unref(new_roots[i]);
	}

	free(new_roots);
}

/* Merge the data in the 'other' heap into the 'heap' heap.
 * Returns non-zero if successful. */

static int binomial_heap_merge(BinomialHeap *heap, BinomialHeap *other)
{
	BinomialTree **new_roots;
	unsigned int new_roots_length;
	BinomialTree *vals[3];
	int num_vals;
	BinomialTree *carry;
	BinomialTree *new_carry;
	unsigned int max;
	unsigned int i;

	/* Find the maximum length of the two heaps.  Add one because
	 * after merging we may have one more value to carry over. */

	if (heap->roots_length > other->roots_length) {
		max = heap->roots_length + 1;
	} else {
		max = other->roots_length + 1;
	}

	/* Allocate an array for the new roots */

	new_roots = malloc(sizeof(BinomialTree *) * max);

	if (new_roots == NULL) {
		return 0;
	}

	/* Go through one entry at a time.  This works kind of like a
	 * ripple-carry adder. */

	new_roots_length = 0;
	carry = NULL;

	for (i=0; i<max; ++i) {

		/* Build up 'vals' as a list of all the values we must
		 * merge at this step. */

		num_vals = 0;

		/* If there is a value in 'heap', add it */

		if (i < heap->roots_length && heap->roots[i] != NULL) {
			vals[num_vals] = heap->roots[i];
			++num_vals;
		}

		/* If there is a value in 'other', add it */

		if (i < other->roots_length && other->roots[i] != NULL) {
			vals[num_vals] = other->roots[i];
			++num_vals;
		}

		/* If there is a carried value from the previous iteration,
		 * add it */

		if (carry != NULL) {
			vals[num_vals] = carry;
			++num_vals;
		}

		/* When num_vals == 1 or 3, we store a value. */

		if ((num_vals & 1) != 0) {

			/* Save the last value into new_roots. */

			new_roots[i] = vals[num_vals - 1];
			binomial_tree_ref(new_roots[i]);
			new_roots_length = i + 1;

		} else {

			/* No value to store at this iteration */

			new_roots[i] = NULL;
		}

		/* When num_vals == 2 or 3, we must carry over to the
		 * next iteration */

		if ((num_vals & 2) != 0) {

			/* Merge the first two values and carry to the
			 * next iteration */

			new_carry = binomial_tree_merge(heap,
			                                vals[0],
			                                vals[1]);

			if (new_carry == NULL) {

				/* Remove references that we have added
				 * (freeing any BinomialTree structures
				 * that were created in the process) */

				binomial_heap_merge_undo(new_roots, i);

				/* Unreference the carry variable */

				binomial_tree_unref(carry);

				return 0;
			}

		} else {

			/* Nothing to carry */

			new_carry = NULL;
		}

		/* Unreference previous carried value */

		binomial_tree_unref(carry);

		/* Assign the new value of carry, and add a reference */

		carry = new_carry;

		binomial_tree_ref(carry);
	}

	/* Unreference all values in the old 'roots' array, freeing unused
	 * BinomialTree structures as necessary. */

	for (i=0; i<heap->roots_length; ++i) {
		if (heap->roots[i] != NULL) {
			binomial_tree_unref(heap->roots[i]);
		}
	}

	/* Free the old roots array and use the new one */

	free(heap->roots);
	heap->roots = new_roots;
	heap->roots_length = new_roots_length;

	/* Merged successfully */

	return 1;
}

BinomialHeap *binomial_heap_new(BinomialHeapType heap_type,
                                BinomialHeapCompareFunc compare_func)
{
	BinomialHeap *new_heap;

	/* Allocate a new heap */

	new_heap = calloc(1, sizeof(BinomialHeap));

	if (new_heap == NULL) {
		return NULL;
	}

	/* Initialise and return */

	new_heap->heap_type = heap_type;
	new_heap->compare_func = compare_func;

	return new_heap;
}

void binomial_heap_free(BinomialHeap *heap)
{
	unsigned int i;

	/* Unreference all trees in the heap.  This should free
	 * back all subtrees. */

	for (i=0; i<heap->roots_length; ++i) {
		binomial_tree_unref(heap->roots[i]);
	}

	/* Free the heap itself */

	free(heap->roots);
	free(heap);
}

int binomial_heap_insert(BinomialHeap *heap, BinomialHeapValue value)
{
	BinomialHeap fake_heap;
	BinomialTree *new_tree;
	int result;

	/* Allocate an order 0 tree for storing the new value */

	new_tree = malloc(sizeof(BinomialTree));

	if (new_tree == NULL) {
		return 0;
	}

	/* Fill in values.  This has an initial reference count of 1 that
	 * the "fake" heap holds; this will be removed at the end of
	 * this function. */

	new_tree->value = value;
	new_tree->order = 0;
	new_tree->refcount = 1;
	new_tree->subtrees = NULL;

	/* Build a fake heap structure for merging */

	fake_heap.heap_type = heap->heap_type;
	fake_heap.compare_func = heap->compare_func;
	fake_heap.num_values = 1;
	fake_heap.roots = &new_tree;
	fake_heap.roots_length = 1;

	/* Perform the merge */

	result = binomial_heap_merge(heap, &fake_heap);

	if (result != 0) {
		++heap->num_values;
	}

	/* Remove reference to the new tree. */

	binomial_tree_unref(new_tree);

	return result;
}

BinomialHeapValue binomial_heap_pop(BinomialHeap *heap)
{
	BinomialTree *least_tree;
	BinomialHeap fake_heap;
	BinomialHeapValue result;
	unsigned int i;
	unsigned int least_index;

	if (heap->num_values == 0) {
		return BINOMIAL_HEAP_NULL;
	}

	/* Find the tree with the lowest root value */

	least_index = UINT_MAX;

	for (i=0; i<heap->roots_length; ++i) {

		if (heap->roots[i] == NULL) {
			continue;
		}

		if (least_index == UINT_MAX
		 || binomial_heap_cmp(heap,
		                      heap->roots[i]->value,
		                      heap->roots[least_index]->value) < 0) {
			least_index = i;
		}
	}

	/* Remove the least_tree from the heap. */

	least_tree = heap->roots[least_index];
	heap->roots[least_index] = NULL;

	/* Construct a fake heap containing the data in the least tree */

	fake_heap.heap_type = heap->heap_type;
	fake_heap.compare_func = heap->compare_func;
	fake_heap.roots = least_tree->subtrees;
	fake_heap.roots_length = least_tree->order;

	/* Merge subtrees of least tree back into the heap */

	if (binomial_heap_merge(heap, &fake_heap)) {

		/* Merge successful */

		/* Remove reference to least tree */

		result = least_tree->value;
		binomial_tree_unref(least_tree);

		/* Update the number of values */

		--heap->num_values;

		return result;

	} else {

		/* Add the least tree back */

		heap->roots[least_index] = least_tree;

		/* Pop failed */

		return BINOMIAL_HEAP_NULL;
	}
}

unsigned int binomial_heap_num_entries(BinomialHeap *heap)
{
	return heap->num_values;
}

