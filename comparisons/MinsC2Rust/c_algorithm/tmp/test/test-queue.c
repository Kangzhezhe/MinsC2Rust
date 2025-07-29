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


int variable1, variable2, variable3, variable4;

Queue *generate_queue(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
		queue_push_head(queue, &variable2);
		queue_push_head(queue, &variable3);
		queue_push_head(queue, &variable4);
	}

	return queue;
}

/* Test cases for the queue */

void test_queue_new_free(void)
{
	int i;
	Queue *queue;

	/* Create and destroy a queue */

	queue = queue_new();

	queue_free(queue);

	/* Add lots of values and then destroy */

	queue = queue_new();

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
	}

	queue_free(queue);

	/* Test allocation when there is no free memory */

	alloc_test_set_limit(0);
	queue = queue_new();
	assert(queue == NULL);
}

void test_queue_push_head(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
		queue_push_head(queue, &variable2);
		queue_push_head(queue, &variable3);
		queue_push_head(queue, &variable4);
	}

	assert(!queue_is_empty(queue));

	/* Check values come out of the tail properly */

	assert(queue_pop_tail(queue) == &variable1);
	assert(queue_pop_tail(queue) == &variable2);
	assert(queue_pop_tail(queue) == &variable3);
	assert(queue_pop_tail(queue) == &variable4);

	/* Check values come back out of the head properly */

	assert(queue_pop_head(queue) == &variable4);
	assert(queue_pop_head(queue) == &variable3);
	assert(queue_pop_head(queue) == &variable2);
	assert(queue_pop_head(queue) == &variable1);

	queue_free(queue);

	/* Test behavior when running out of memory. */

	queue = queue_new();

	alloc_test_set_limit(0);
	assert(!queue_push_head(queue, &variable1));

	queue_free(queue);
}

void test_queue_pop_head(void)
{
	Queue *queue;

	/* Check popping off an empty queue */

	queue = queue_new();

	assert(queue_pop_head(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_pop_head(queue) == &variable4);
		assert(queue_pop_head(queue) == &variable3);
		assert(queue_pop_head(queue) == &variable2);
		assert(queue_pop_head(queue) == &variable1);
	}

	assert(queue_pop_head(queue) == NULL);

	queue_free(queue);
}

void test_queue_peek_head(void)
{
	Queue *queue;

	/* Check peeking into an empty queue */

	queue = queue_new();

	assert(queue_peek_head(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue, making sure that peek
	 * has the correct value beforehand */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_peek_head(queue) == &variable4);
		assert(queue_pop_head(queue) == &variable4);
		assert(queue_peek_head(queue) == &variable3);
		assert(queue_pop_head(queue) == &variable3);
		assert(queue_peek_head(queue) == &variable2);
		assert(queue_pop_head(queue) == &variable2);
		assert(queue_peek_head(queue) == &variable1);
		assert(queue_pop_head(queue) == &variable1);
	}

	assert(queue_peek_head(queue) == NULL);

	queue_free(queue);
}

void test_queue_push_tail(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_tail(queue, &variable1);
		queue_push_tail(queue, &variable2);
		queue_push_tail(queue, &variable3);
		queue_push_tail(queue, &variable4);
	}

	assert(!queue_is_empty(queue));

	/* Check values come out of the head properly */

	assert(queue_pop_head(queue) == &variable1);
	assert(queue_pop_head(queue) == &variable2);
	assert(queue_pop_head(queue) == &variable3);
	assert(queue_pop_head(queue) == &variable4);

	/* Check values come back out of the tail properly */

	assert(queue_pop_tail(queue) == &variable4);
	assert(queue_pop_tail(queue) == &variable3);
	assert(queue_pop_tail(queue) == &variable2);
	assert(queue_pop_tail(queue) == &variable1);

	queue_free(queue);

	/* Test behavior when running out of memory. */

	queue = queue_new();

	alloc_test_set_limit(0);
	assert(!queue_push_tail(queue, &variable1));

	queue_free(queue);
}

void test_queue_pop_tail(void)
{
	Queue *queue;

	/* Check popping off an empty queue */

	queue = queue_new();

	assert(queue_pop_tail(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_pop_tail(queue) == &variable1);
		assert(queue_pop_tail(queue) == &variable2);
		assert(queue_pop_tail(queue) == &variable3);
		assert(queue_pop_tail(queue) == &variable4);
	}

	assert(queue_pop_tail(queue) == NULL);

	queue_free(queue);
}

void test_queue_peek_tail(void)
{
	Queue *queue;

	/* Check peeking into an empty queue */

	queue = queue_new();

	assert(queue_peek_tail(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue, making sure that peek
	 * has the correct value beforehand */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_peek_tail(queue) == &variable1);
		assert(queue_pop_tail(queue) == &variable1);
		assert(queue_peek_tail(queue) == &variable2);
		assert(queue_pop_tail(queue) == &variable2);
		assert(queue_peek_tail(queue) == &variable3);
		assert(queue_pop_tail(queue) == &variable3);
		assert(queue_peek_tail(queue) == &variable4);
		assert(queue_pop_tail(queue) == &variable4);
	}

	assert(queue_peek_tail(queue) == NULL);

	queue_free(queue);
}

void test_queue_is_empty(void)
{
	Queue *queue;

	queue = queue_new();

	assert(queue_is_empty(queue));

	queue_push_head(queue, &variable1);

	assert(!queue_is_empty(queue));

	queue_pop_head(queue);

	assert(queue_is_empty(queue));

	queue_push_tail(queue, &variable1);

	assert(!queue_is_empty(queue));

	queue_pop_tail(queue);

	assert(queue_is_empty(queue));

	queue_free(queue);
}

static UnitTestFunction tests[] = {
	test_queue_new_free,
	test_queue_push_head,
	test_queue_pop_head,
	test_queue_peek_head,
	test_queue_push_tail,
	test_queue_pop_tail,
	test_queue_peek_tail,
	test_queue_is_empty,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

