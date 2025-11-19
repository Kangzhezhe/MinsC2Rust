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
 * @file hash-pointer.h
 *
 * Hash function for a generic (void) pointer.  See @ref pointer_hash.
 */

#ifndef ALGORITHM_HASH_POINTER_H
#define ALGORITHM_HASH_POINTER_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Generate a hash key for a pointer.  The value pointed at by the pointer
 * is not used, only the pointer itself.
 *
 * @param location        The pointer
 * @return                A hash key for the pointer.
 */

unsigned int pointer_hash(void *location);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_HASH_POINTER_H */

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
 * @file hash-int.h
 *
 * Hash function for a pointer to an integer.  See @ref int_hash.
 */

#ifndef ALGORITHM_HASH_INT_H
#define ALGORITHM_HASH_INT_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Generate a hash key for a pointer to an integer.  The value pointed
 * at is used to generate the key.
 *
 * @param location        The pointer.
 * @return                A hash key for the value at the location.
 */

unsigned int int_hash(void *location);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_HASH_INT_H */

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
 * @file hash-string.h
 *
 * Hash functions for text strings.  For more information
 * see @ref string_hash or @ref string_nocase_hash.
 */

#ifndef ALGORITHM_HASH_STRING_H
#define ALGORITHM_HASH_STRING_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Generate a hash key from a string.
 *
 * @param string           The string.
 * @return                 A hash key for the string.
 */

unsigned int string_hash(void *string);

/**
 * Generate a hash key from a string, ignoring the case of letters.
 *
 * @param string           The string.
 * @return                 A hash key for the string.
 */

unsigned int string_nocase_hash(void *string);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_HASH_STRING_H */


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


#define NUM_TEST_VALUES 200

void test_pointer_hash(void)
{
	int array[NUM_TEST_VALUES];
	int i, j;

	/* Initialise the array to all zeros */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		array[i] = 0;
	}

	/* Check hashes are never the same */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		for (j=i+1; j<NUM_TEST_VALUES; ++j) {
			assert(pointer_hash(&array[i])
			       != pointer_hash(&array[j]));
		}
	}
}

void test_int_hash(void)
{
	int array[NUM_TEST_VALUES];
	int i, j;

	/* Initialise all entries in the array */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		array[i] = i;
	}

	/* Check hashes are never the same */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		for (j=i+1; j<NUM_TEST_VALUES; ++j) {
			assert(int_hash(&array[i]) != int_hash(&array[j]));
		}
	}

	/* Hashes of two variables containing the same value are the same */

	i = 5000;
	j = 5000;

	assert(int_hash(&i) == int_hash(&j));
}

void test_string_hash(void)
{
	char test1[] = "this is a test";
	char test2[] = "this is a tesu";
	char test3[] = "this is a test ";
	char test4[] = "this is a test";
	char test5[] = "This is a test";

	/* Contents affect the hash */

	assert(string_hash(test1) != string_hash(test2));

	/* Length affects the hash */

	assert(string_hash(test1) != string_hash(test3));

	/* Case sensitive */

	assert(string_hash(test1) != string_hash(test5));

	/* The same strings give the same hash */

	assert(string_hash(test1) == string_hash(test4));
}

void test_string_nocase_hash(void)
{
	char test1[] = "this is a test";
	char test2[] = "this is a tesu";
	char test3[] = "this is a test ";
	char test4[] = "this is a test";
	char test5[] = "This is a test";

	/* Contents affect the hash */

	assert(string_nocase_hash(test1) != string_nocase_hash(test2));

	/* Length affects the hash */

	assert(string_nocase_hash(test1) != string_nocase_hash(test3));

	/* Case insensitive */

	assert(string_nocase_hash(test1) == string_nocase_hash(test5));

	/* The same strings give the same hash */

	assert(string_nocase_hash(test1) == string_nocase_hash(test4));
}

static UnitTestFunction tests[] = {
	test_pointer_hash,
	test_int_hash,
	test_string_hash,
	test_string_nocase_hash,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

