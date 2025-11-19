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

/* Test cases for compare functions */

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
 * @file compare-pointer.h
 *
 * Comparison functions for generic (void) pointers.
 *
 * To find the difference between two pointers, use @ref pointer_compare.
 *
 * To find if two pointers are equal, use @ref pointer_equal.
 */

#ifndef ALGORITHM_COMPARE_POINTER_H
#define ALGORITHM_COMPARE_POINTER_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compare two pointers to determine if they are equal.
 *
 * @param location1       The first pointer.
 * @param location2       The second pointer.
 * @return                Non-zero if the pointers are equal, zero if they
 *                        are not equal.
 */

int pointer_equal(void *location1, void *location2);

/**
 * Compare two pointers.
 *
 * @param location1       The first pointer.
 * @param location2       The second pointer.
 * @return                A negative value if the first pointer is in a lower
 *                        memory address than the second, a positive value if
 *                        the first pointer is in a higher memory address than
 *                        the second, zero if they point to the same location.
 */

int pointer_compare(void *location1, void *location2);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_COMPARE_POINTER_H */

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
 * @file compare-string.h
 *
 * Comparison functions for strings.
 *
 * To find the difference between two strings, use @ref string_compare.
 *
 * To find if two strings are equal, use @ref string_equal.
 *
 * For case insensitive versions, see @ref string_nocase_compare and
 * @ref string_nocase_equal.
 */

#ifndef ALGORITHM_COMPARE_STRING_H
#define ALGORITHM_COMPARE_STRING_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compare two strings to determine if they are equal.
 *
 * @param string1         The first string.
 * @param string2         The second string.
 * @return                Non-zero if the strings are equal, zero if they are
 *                        not equal.
 */

int string_equal(void *string1, void *string2);

/**
 * Compare two strings.
 *
 * @param string1         The first string.
 * @param string2         The second string.
 * @return                A negative value if the first string should be
 *                        sorted before the second, a positive value if the
 *                        first string should be sorted after the second,
 *                        zero if the two strings are equal.
 */

int string_compare(void *string1, void *string2);

/**
 * Compare two strings to determine if they are equal, ignoring the
 * case of letters.
 *
 * @param string1         The first string.
 * @param string2         The second string.
 * @return                Non-zero if the strings are equal, zero if they are
 *                        not equal.
 */

int string_nocase_equal(void *string1, void *string2);

/**
 * Compare two strings, ignoring the case of letters.
 *
 * @param string1         The first string.
 * @param string2         The second string.
 * @return                A negative value if the first string should be
 *                        sorted before the second, a positive value if the
 *                        first string should be sorted after the second,
 *                        zero if the two strings are equal.
 */

int string_nocase_compare(void *string1, void *string2);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_COMPARE_STRING_H */


void test_int_compare(void)
{
	int a = 4;
	int b = 8;
	int c = 4;

	/* If first is less than second, result is negative) */

	assert(int_compare(&a, &b) < 0);

	/* If first is more than second, result is positive) */

	assert(int_compare(&b, &a) > 0);

	/* If both are equal, result is zero */

	assert(int_compare(&a, &c) == 0);
}

void test_int_equal(void)
{
	int a = 4;
	int b = 8;
	int c = 4;

	/* Returns non-zero (true) if both are equal */

	assert(int_equal(&a, &c) != 0);

	/* Returns zero (false) if not equal) */

	assert(int_equal(&a, &b) == 0);
}

void test_pointer_compare(void)
{
	int array[5];

	/* Negative if first argument is a lower memory address than
	 * the second */

	assert(pointer_compare(&array[0], &array[4]) < 0);

	/* Positive if the first argument is a higher memory address
	 * than the second */

	assert(pointer_compare(&array[3], &array[2]) > 0);

	/* Zero if the two arguments are equal */

	assert(pointer_compare(&array[4], &array[4]) == 0);
}

void test_pointer_equal(void)
{
	int a, b;

	/* Non-zero (true) if the two pointers are equal */

	assert(pointer_equal(&a, &a) != 0);

	/* Zero (false) if the two pointers are not equal */

	assert(pointer_equal(&a, &b) == 0);
}

void test_string_compare(void)
{
	char test1[] = "Apple";
	char test2[] = "Orange";
	char test3[] = "Apple";

	/* Negative if first argument should be sorted before the second */

	assert(string_compare(test1, test2) < 0);

	/* Positive if the second argument should be sorted before the first */

	assert(string_compare(test2, test1) > 0);

	/* Zero if the two arguments are equal */

	assert(string_compare(test1, test3) == 0);
}

void test_string_equal(void)
{
	char test1[] = "this is a test string";
	char test2[] = "this is a test string ";
	char test3[] = "this is a test strin";
	char test4[] = "this is a test strinG";
	char test5[] = "this is a test string";

	/* Non-zero (true) if the two strings are equal */

	assert(string_equal(test1, test5) != 0);

	/* Zero (false) if the two strings are different */

	/* Check that length affects the result */
	assert(string_equal(test1, test2) == 0);
	assert(string_equal(test1, test3) == 0);

	/* Case sensitive */
	assert(string_equal(test1, test4) == 0);
}

void test_string_nocase_compare(void)
{
	char test1[] = "Apple";
	char test2[] = "Orange";
	char test3[] = "Apple";
	char test4[] = "Alpha";
	char test5[] = "bravo";
	char test6[] = "Charlie";

	/* Negative if first argument should be sorted before the second */

	assert(string_nocase_compare(test1, test2) < 0);

	/* Positive if the second argument should be sorted before the first */

	assert(string_nocase_compare(test2, test1) > 0);

	/* Zero if the two arguments are equal */

	assert(string_nocase_compare(test1, test3) == 0);

	/* Check ordering is independent of case */

	assert(string_nocase_compare(test4, test5) < 0);
	assert(string_nocase_compare(test5, test6) < 0);
}

void test_string_nocase_equal(void)
{
	char test1[] = "this is a test string";
	char test2[] = "this is a test string ";
	char test3[] = "this is a test strin";
	char test4[] = "this is a test strinG";
	char test5[] = "this is a test string";

	/* Non-zero (true) if the two strings are equal */

	assert(string_nocase_equal(test1, test5) != 0);

	/* Zero (false) if the two strings are different */

	/* Check that length affects the result */
	assert(string_nocase_equal(test1, test2) == 0);
	assert(string_nocase_equal(test1, test3) == 0);

	/* Case insensitive */
	assert(string_nocase_equal(test1, test4) != 0);
}

static UnitTestFunction tests[] = {
	test_int_compare,
	test_int_equal,
	test_pointer_compare,
	test_pointer_equal,
	test_string_compare,
	test_string_equal,
	test_string_nocase_compare,
	test_string_nocase_equal,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

