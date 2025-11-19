
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

/* Tests for the allocation testing framework. */

#include <stdio.h>
#include <assert.h>
#include <string.h>

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

static void test_malloc_free(void)
{
	void *block, *block2, *block3, *block4;
	unsigned char *ptr;
	int i;

	/* Allocate a block and check that the counters increase */

	assert(alloc_test_get_allocated() == 0);

	block = malloc(1024);

	assert(block != NULL);
	assert(alloc_test_get_allocated() == 1024);

	/* Check that the block is initialised with garbage */

	ptr = block;

	for (i=0; i<1024; ++i) {
		assert(ptr[i] != 0);
	}

	/* Free the block back and check the counters decrease */

	free(block);

	assert(alloc_test_get_allocated() == 0);

	/* Try setting a limit */

	alloc_test_set_limit(3);

	block = malloc(1024);
	assert(block != NULL);
	block2 = malloc(1024);
	assert(block2 != NULL);
	block3 = malloc(1024);
	assert(block3 != NULL);
	block4 = malloc(1024);
	assert(block4 == NULL);
	free(block);
	free(block2);
	free(block3);
	free(block4);
}

static void test_realloc(void)
{
	void *block;
	void *block2;

	/* This block will be allocated while the other tests are run */

	block2 = malloc(1024);

	/* Allocate a block */

	block = malloc(1024);

	assert(block != NULL);
	assert(alloc_test_get_allocated() == 1024 + 1024);

	/* Reallocate the block larger */

	block = realloc(block, 2048);
	assert(block != NULL);

	assert(alloc_test_get_allocated() == 2048 + 1024);

	/* Reallocate the block smaller */

	block = realloc(block, 1500);
	assert(block != NULL);

	assert(alloc_test_get_allocated() == 1500 + 1024);

	free(block);

	assert(alloc_test_get_allocated() == 0 + 1024);

	/* Test passing a NULL pointer to make realloc behave as malloc() */

	block = realloc(NULL, 1024);

	assert(block != NULL);

	assert(alloc_test_get_allocated() == 1024 + 1024);

	free(block);
	free(block2);

	assert(alloc_test_get_allocated() == 0);

	/* Test realloc with a limit set */

	block = malloc(512);
	assert(block != NULL);
	assert(alloc_test_get_allocated() == 512);

	alloc_test_set_limit(1);

	block = realloc(block, 1024);
	assert(block != NULL);
	assert(alloc_test_get_allocated() == 1024);

	assert(realloc(block, 2048) == NULL);
	assert(alloc_test_get_allocated() == 1024);

	free(block);
	assert(alloc_test_get_allocated() == 0);

	/* Test NULL realloc with limit */

	alloc_test_set_limit(1);

	block = realloc(NULL, 1024);
	assert(block != NULL);
	assert(alloc_test_get_allocated() == 1024);

	assert(realloc(NULL, 1024) == NULL);
	assert(alloc_test_get_allocated() == 1024);

	free(block);
}

static void test_calloc(void)
{
	unsigned char *block;
	int i;

	assert(alloc_test_get_allocated() == 0);

	/* Allocate a block */

	block = calloc(16, 64);

	assert(alloc_test_get_allocated() == 1024);

	assert(block != NULL);

	/* Check the block contents are initialised to zero */

	for (i=0; i<1024; ++i) {
		assert(block[i] == 0);
	}

	free(block);

	assert(alloc_test_get_allocated() == 0);

	/* Test calloc with limit */

	alloc_test_set_limit(1);

	block = calloc(1024, 1);
	assert(block != NULL);
	assert(alloc_test_get_allocated() == 1024);

	assert(calloc(1024, 1) == NULL);
	assert(alloc_test_get_allocated() == 1024);

	free(block);
}

static void test_strdup(void)
{
	char *str;

	assert(alloc_test_get_allocated() == 0);

	/* Test strdup */

	str = strdup("hello world");

	assert(str != NULL);
	assert(strcmp(str, "hello world") == 0);

	assert(alloc_test_get_allocated() == 12);

	free(str);

	assert(alloc_test_get_allocated() == 0);

	/* Test strdup with limit */

	alloc_test_set_limit(1);

	str = strdup("hello world");
	assert(str != NULL);
	assert(alloc_test_get_allocated() == 12);

	assert(strdup("hello world") == NULL);
	assert(alloc_test_get_allocated() == 12);

	free(str);
}

static void test_limits(void)
{
	void *block;

	/* Test normal malloc */

	block = malloc(2048);
	assert(block != NULL);
	free(block);

	/* Test malloc with limit */

	alloc_test_set_limit(1);
	block = malloc(1024);
	assert(block != NULL);
	assert(malloc(1024) == NULL);
	free(block);

	/* Check that it is possible to remove the limit */

	alloc_test_set_limit(-1);
	block = malloc(1024);
	assert(block != NULL);
	free(block);
}

static UnitTestFunction tests[] = {
	test_malloc_free,
	test_realloc,
	test_calloc,
	test_strdup,
	test_limits,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

