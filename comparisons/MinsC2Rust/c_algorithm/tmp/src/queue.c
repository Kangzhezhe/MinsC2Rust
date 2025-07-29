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
 * @file queue.h
 *
 * @brief Double-ended queue.
 *
 * A double ended queue stores a list of values in order.  New values
 * can be added and removed from either end of the queue.
 *
 * To create a new queue, use @ref queue_new.  To destroy a queue, use
 * @ref queue_free.
 *
 * To add values to a queue, use @ref queue_push_head and
 * @ref queue_push_tail.
 *
 * To read values from the ends of a queue, use @ref queue_pop_head
 * and @ref queue_pop_tail.  To examine the ends without removing values
 * from the queue, use @ref queue_peek_head and @ref queue_peek_tail.
 *
 */

#ifndef ALGORITHM_QUEUE_H
#define ALGORITHM_QUEUE_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A double-ended queue.
 */

typedef struct _Queue Queue;

/**
 * A value stored in a @ref Queue.
 */

typedef void *QueueValue;

/**
 * A null @ref QueueValue.
 */

#define QUEUE_NULL ((void *) 0)

/**
 * Create a new double-ended queue.
 *
 * @return           A new queue, or NULL if it was not possible to allocate
 *                   the memory.
 */

Queue *queue_new(void);

/**
 * Destroy a queue.
 *
 * @param queue      The queue to destroy.
 */

void queue_free(Queue *queue);

/**
 * Add a value to the head of a queue.
 *
 * @param queue      The queue.
 * @param data       The value to add.
 * @return           Non-zero if the value was added successfully, or zero
 *                   if it was not possible to allocate the memory for the
 *                   new entry.
 */

int queue_push_head(Queue *queue, QueueValue data);

/**
 * Remove a value from the head of a queue.
 *
 * @param queue      The queue.
 * @return           Value that was at the head of the queue, or
 *                   @ref QUEUE_NULL if the queue is empty.
 */

QueueValue queue_pop_head(Queue *queue);

/**
 * Read value from the head of a queue, without removing it from
 * the queue.
 *
 * @param queue      The queue.
 * @return           Value at the head of the queue, or @ref QUEUE_NULL if the
 *                   queue is empty.
 */

QueueValue queue_peek_head(Queue *queue);

/**
 * Add a value to the tail of a queue.
 *
 * @param queue      The queue.
 * @param data       The value to add.
 * @return           Non-zero if the value was added successfully, or zero
 *                   if it was not possible to allocate the memory for the
 *                   new entry.
 */

int queue_push_tail(Queue *queue, QueueValue data);

/**
 * Remove a value from the tail of a queue.
 *
 * @param queue      The queue.
 * @return           Value that was at the head of the queue, or
 *                   @ref QUEUE_NULL if the queue is empty.
 */

QueueValue queue_pop_tail(Queue *queue);

/**
 * Read a value from the tail of a queue, without removing it from
 * the queue.
 *
 * @param queue      The queue.
 * @return           Value at the tail of the queue, or QUEUE_NULL if the
 *                   queue is empty.
 */

QueueValue queue_peek_tail(Queue *queue);

/**
 * Query if any values are currently in a queue.
 *
 * @param queue      The queue.
 * @return           Zero if the queue is not empty, non-zero if the queue
 *                   is empty.
 */

int queue_is_empty(Queue *queue);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_QUEUE_H */


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

/* A double-ended queue */

typedef struct _QueueEntry QueueEntry;

struct _QueueEntry {
	QueueValue data;
	QueueEntry *prev;
	QueueEntry *next;
};

struct _Queue {
	QueueEntry *head;
	QueueEntry *tail;
};

Queue *queue_new(void)
{
	Queue *queue;

	queue = (Queue *) malloc(sizeof(Queue));

	if (queue == NULL) {
		return NULL;
	}

	queue->head = NULL;
	queue->tail = NULL;

	return queue;
}

void queue_free(Queue *queue)
{
	/* Empty the queue */

	while (!queue_is_empty(queue)) {
		queue_pop_head(queue);
	}

	/* Free back the queue */

	free(queue);
}

int queue_push_head(Queue *queue, QueueValue data)
{
	QueueEntry *new_entry;

	/* Create the new entry and fill in the fields in the structure */

	new_entry = malloc(sizeof(QueueEntry));

	if (new_entry == NULL) {
		return 0;
	}

	new_entry->data = data;
	new_entry->prev = NULL;
	new_entry->next = queue->head;

	/* Insert into the queue */

	if (queue->head == NULL) {

		/* If the queue was previously empty, both the head and
		 * tail must be pointed at the new entry */

		queue->head = new_entry;
		queue->tail = new_entry;

	} else {

		/* First entry in the list must have prev pointed back to this
		 * new entry */

		queue->head->prev = new_entry;

		/* Only the head must be pointed at the new entry */

		queue->head = new_entry;
	}

	return 1;
}

QueueValue queue_pop_head(Queue *queue)
{
	QueueEntry *entry;
	QueueValue result;

	/* Check the queue is not empty */

	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	}

	/* Unlink the first entry from the head of the queue */

	entry = queue->head;
	queue->head = entry->next;
	result = entry->data;

	if (queue->head == NULL) {

		/* If doing this has unlinked the last entry in the queue, set
		 * tail to NULL as well. */

		queue->tail = NULL;
	} else {

		/* The new first in the queue has no previous entry */

		queue->head->prev = NULL;
	}

	/* Free back the queue entry structure */

	free(entry);

	return result;
}

QueueValue queue_peek_head(Queue *queue)
{
	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	} else {
		return queue->head->data;
	}
}

int queue_push_tail(Queue *queue, QueueValue data)
{
	QueueEntry *new_entry;

	/* Create the new entry and fill in the fields in the structure */

	new_entry = malloc(sizeof(QueueEntry));

	if (new_entry == NULL) {
		return 0;
	}

	new_entry->data = data;
	new_entry->prev = queue->tail;
	new_entry->next = NULL;

	/* Insert into the queue tail */

	if (queue->tail == NULL) {

		/* If the queue was previously empty, both the head and
		 * tail must be pointed at the new entry */

		queue->head = new_entry;
		queue->tail = new_entry;

	} else {

		/* The current entry at the tail must have next pointed to this
		 * new entry */

		queue->tail->next = new_entry;

		/* Only the tail must be pointed at the new entry */

		queue->tail = new_entry;
	}

	return 1;
}

QueueValue queue_pop_tail(Queue *queue)
{
	QueueEntry *entry;
	QueueValue result;

	/* Check the queue is not empty */

	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	}

	/* Unlink the first entry from the tail of the queue */

	entry = queue->tail;
	queue->tail = entry->prev;
	result = entry->data;

	if (queue->tail == NULL) {

		/* If doing this has unlinked the last entry in the queue, set
		 * head to NULL as well. */

		queue->head = NULL;

	} else {

		/* The new entry at the tail has no next entry. */

		queue->tail->next = NULL;
	}

	/* Free back the queue entry structure */

	free(entry);

	return result;
}

QueueValue queue_peek_tail(Queue *queue)
{
	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	} else {
		return queue->tail->data;
	}
}

int queue_is_empty(Queue *queue)
{
	return queue->head == NULL;
}

