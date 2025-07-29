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
 * @file bloom-filter.h
 *
 * @brief Bloom filter
 *
 * A bloom filter is a space efficient data structure that can be
 * used to test whether a given element is part of a set.  Lookups
 * will occasionally generate false positives, but never false
 * negatives.
 *
 * To create a bloom filter, use @ref bloom_filter_new.  To destroy a
 * bloom filter, use @ref bloom_filter_free.
 *
 * To insert a value into a bloom filter, use @ref bloom_filter_insert.
 *
 * To query whether a value is part of the set, use
 * @ref bloom_filter_query.
 */

#ifndef ALGORITHM_BLOOM_FILTER_H
#define ALGORITHM_BLOOM_FILTER_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A bloom filter structure.
 */

typedef struct _BloomFilter BloomFilter;

/**
 * A value stored in a @ref BloomFilter.
 */

typedef void *BloomFilterValue;

/**
 * Hash function used to generate hash values for values inserted into a
 * bloom filter.
 *
 * @param data   The value to generate a hash value for.
 * @return       The hash value.
 */

typedef unsigned int (*BloomFilterHashFunc)(BloomFilterValue data);

/**
 * Create a new bloom filter.
 *
 * @param table_size       The size of the bloom filter.  The greater
 *                         the table size, the more elements can be
 *                         stored, and the lesser the chance of false
 *                         positives.
 * @param hash_func        Hash function to use on values stored in the
 *                         filter.
 * @param num_functions    Number of hash functions to apply to each
 *                         element on insertion.  This running time for
 *                         insertion and queries is proportional to this
 *                         value.  The more functions applied, the lesser
 *                         the chance of false positives.  The maximum
 *                         number of functions is 64.
 * @return                 A new hash table structure, or NULL if it
 *                         was not possible to allocate the new bloom
 *                         filter.
 */

BloomFilter *bloom_filter_new(unsigned int table_size,
                              BloomFilterHashFunc hash_func,
                              unsigned int num_functions);

/**
 * Destroy a bloom filter.
 *
 * @param bloomfilter      The bloom filter to destroy.
 */

void bloom_filter_free(BloomFilter *bloomfilter);

/**
 * Insert a value into a bloom filter.
 *
 * @param bloomfilter          The bloom filter.
 * @param value                The value to insert.
 */

void bloom_filter_insert(BloomFilter *bloomfilter, BloomFilterValue value);

/**
 * Query a bloom filter for a particular value.
 *
 * @param bloomfilter          The bloom filter.
 * @param value                The value to look up.
 * @return                     Zero if the value was definitely not
 *                             inserted into the filter.  Non-zero
 *                             indicates that it either may or may not
 *                             have been inserted.
 */

int bloom_filter_query(BloomFilter *bloomfilter, BloomFilterValue value);

/**
 * Read the contents of a bloom filter into an array.
 *
 * @param bloomfilter          The bloom filter.
 * @param array                Pointer to the array to read into.  This
 *                             should be (table_size + 7) / 8 bytes in
 *                             length.
 */

void bloom_filter_read(BloomFilter *bloomfilter, unsigned char *array);

/**
 * Load the contents of a bloom filter from an array.
 * The data loaded should be the output read from @ref bloom_filter_read,
 * from a bloom filter created using the same arguments used to create
 * the original filter.
 *
 * @param bloomfilter          The bloom filter.
 * @param array                Pointer to the array to load from.  This
 *                             should be (table_size + 7) / 8 bytes in
 *                             length.
 */

void bloom_filter_load(BloomFilter *bloomfilter, unsigned char *array);

/**
 * Find the union of two bloom filters.  Values are present in the
 * resulting filter if they are present in either of the original
 * filters.
 *
 * Both of the original filters must have been created using the
 * same parameters to @ref bloom_filter_new.
 *
 * @param filter1              The first filter.
 * @param filter2              The second filter.
 * @return                     A new filter which is an intersection of the
 *                             two filters, or NULL if it was not possible
 *                             to allocate memory for the new filter, or
 *                             if the two filters specified were created
 *                             with different parameters.
 */

BloomFilter *bloom_filter_union(BloomFilter *filter1,
                                BloomFilter *filter2);

/**
 * Find the intersection of two bloom filters.  Values are only ever
 * present in the resulting filter if they are present in both of the
 * original filters.
 *
 * Both of the original filters must have been created using the
 * same parameters to @ref bloom_filter_new.
 *
 * @param filter1              The first filter.
 * @param filter2              The second filter.
 * @return                     A new filter which is an intersection of the
 *                             two filters, or NULL if it was not possible
 *                             to allocate memory for the new filter, or
 *                             if the two filters specified were created
 *                             with different parameters.
 */

BloomFilter *bloom_filter_intersection(BloomFilter *filter1,
                                       BloomFilter *filter2);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_BLOOM_FILTER_H */

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


void test_bloom_filter_new_free(void)
{
	BloomFilter *filter;

	/* One salt */

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter != NULL);

	bloom_filter_free(filter);

	/* Maximum number of salts */

	filter = bloom_filter_new(128, string_hash, 64);

	assert(filter != NULL);

	bloom_filter_free(filter);

	/* Test creation with too many salts */

	filter = bloom_filter_new(128, string_hash, 50000);

	assert(filter == NULL);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter == NULL);

	alloc_test_set_limit(1);

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter == NULL);
}

void test_bloom_filter_insert_query(void)
{
	BloomFilter *filter;

	/* Create a filter */

	filter = bloom_filter_new(128, string_hash, 4);

	/* Check values are not present at the start */

	assert(bloom_filter_query(filter, "test 1") == 0);
	assert(bloom_filter_query(filter, "test 2") == 0);

	/* Insert some values */

	bloom_filter_insert(filter, "test 1");
	bloom_filter_insert(filter, "test 2");

	/* Check they are set */

	assert(bloom_filter_query(filter, "test 1") != 0);
	assert(bloom_filter_query(filter, "test 2") != 0);

	bloom_filter_free(filter);
}

void test_bloom_filter_read_load(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	unsigned char state[16];

	/* Create a filter with some values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");
	bloom_filter_insert(filter1, "test 2");

	/* Read the current state into an array */

	bloom_filter_read(filter1, state);

	bloom_filter_free(filter1);

	/* Create a new filter and load the state */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_load(filter2, state);

	/* Check the values are set in the new filter */

	assert(bloom_filter_query(filter2, "test 1") != 0);
	assert(bloom_filter_query(filter2, "test 2") != 0);

	bloom_filter_free(filter2);
}

void test_bloom_filter_intersection(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	BloomFilter *result;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");
	bloom_filter_insert(filter1, "test 2");

	/* Create second filter with only one value set */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter2, "test 1");

	/* For this test, we need this to be definitely not present.
	 * Note that this could theoretically return non-zero here,
	 * depending on the hash function. */

	assert(bloom_filter_query(filter2, "test 2") == 0);

	/* Intersection */

	result = bloom_filter_intersection(filter1, filter2);

	/* test 1 should be set, as it is in both
	 * test 2 should not be set, as it is not present in both */

	assert(bloom_filter_query(result, "test 1") != 0);
	assert(bloom_filter_query(result, "test 2") == 0);

	bloom_filter_free(result);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	result = bloom_filter_intersection(filter1, filter2);
	assert(result == NULL);

	bloom_filter_free(filter1);
	bloom_filter_free(filter2);
}

void test_bloom_filter_union(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	BloomFilter *result;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");

	/* Create second filter with only one value set */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter2, "test 2");

	/* Union */

	result = bloom_filter_union(filter1, filter2);

	/* Both should be present */

	assert(bloom_filter_query(result, "test 1") != 0);
	assert(bloom_filter_query(result, "test 2") != 0);

	bloom_filter_free(result);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	result = bloom_filter_union(filter1, filter2);
	assert(result == NULL);

	bloom_filter_free(filter1);
	bloom_filter_free(filter2);
}

/* Test attempts to do union/intersection of mismatched filters */

void test_bloom_filter_mismatch(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	/* Different buffer size. */

	filter2 = bloom_filter_new(64, string_hash, 4);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	/* Different hash function */

	filter2 = bloom_filter_new(128, string_nocase_hash, 4);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	/* Different number of salts */

	filter2 = bloom_filter_new(128, string_hash, 32);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	bloom_filter_free(filter1);
}

static UnitTestFunction tests[] = {
	test_bloom_filter_new_free,
	test_bloom_filter_insert_query,
	test_bloom_filter_read_load,
	test_bloom_filter_intersection,
	test_bloom_filter_union,
	test_bloom_filter_mismatch,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

