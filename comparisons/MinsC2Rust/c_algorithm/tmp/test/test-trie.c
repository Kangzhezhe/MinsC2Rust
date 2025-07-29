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
#include <string.h>
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
 * @file trie.h
 *
 * @brief Fast string lookups
 *
 * A trie is a data structure which provides fast mappings from strings
 * to values.
 *
 * To create a new trie, use @ref trie_new.  To destroy a trie,
 * use @ref trie_free.
 *
 * To insert a value into a trie, use @ref trie_insert. To remove a value
 * from a trie, use @ref trie_remove.
 *
 * To look up a value from its key, use @ref trie_lookup.
 *
 * To find the number of entries in a trie, use @ref trie_num_entries.
 */

#ifndef ALGORITHM_TRIE_H
#define ALGORITHM_TRIE_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A trie structure.
 */

typedef struct _Trie Trie;

/**
 * Value stored in a @ref Trie.
 */

typedef void *TrieValue;

/**
 * A null @ref TrieValue.
 */

#define TRIE_NULL ((void *) 0)

/**
 * Create a new trie.
 *
 * @return                   Pointer to a new trie structure, or NULL if it
 *                           was not possible to allocate memory for the
 *                           new trie.
 */

Trie *trie_new(void);

/**
 * Destroy a trie.
 *
 * @param trie               The trie to destroy.
 */

void trie_free(Trie *trie);

/**
 * Insert a new key-value pair into a trie.  The key is a NUL-terminated
 * string.  For binary strings, use @ref trie_insert_binary.
 *
 * @param trie               The trie.
 * @param key                The key to access the new value.
 * @param value              The value.
 * @return                   Non-zero if the value was inserted successfully,
 *                           or zero if it was not possible to allocate
 *                           memory for the new entry.
 */

int trie_insert(Trie *trie, char *key, TrieValue value);

/**
 * Insert a new key-value pair into a trie. The key is a sequence of bytes.
 * For a key that is a NUL-terminated text string, use @ref trie_insert.
 *
 * @param trie               The trie.
 * @param key                The key to access the new value.
 * @param key_length         The key length in bytes.
 * @param value              The value.
 * @return                   Non-zero if the value was inserted successfully,
 *                           or zero if it was not possible to allocate
 *                           memory for the new entry.
 */

int trie_insert_binary(Trie *trie, unsigned char *key,
                       int key_length, TrieValue value);

/**
 * Look up a value from its key in a trie.
 * The key is a NUL-terminated string; for binary strings, use
 * @ref trie_lookup_binary.
 *
 * @param trie               The trie.
 * @param key                The key.
 * @return                   The value associated with the key, or
 *                           @ref TRIE_NULL if not found in the trie.
 */

TrieValue trie_lookup(Trie *trie, char *key);

/**
 * Look up a value from its key in a trie.
 * The key is a sequence of bytes; for a key that is a NUL-terminated
 * text string, use @ref trie_lookup.
 *
 * @param trie               The trie.
 * @param key                The key.
 * @param key_length         The key length in bytes.
 * @return                   The value associated with the key, or
 *                           @ref TRIE_NULL if not found in the trie.
 */

TrieValue trie_lookup_binary(Trie *trie, unsigned char *key, int key_length);

/**
 * Remove an entry from a trie.
 * The key is a NUL-terminated string; for binary strings, use
 * @ref trie_lookup_binary.
 *
 * @param trie               The trie.
 * @param key                The key of the entry to remove.
 * @return                   Non-zero if the key was removed successfully,
 *                           or zero if it is not present in the trie.
 */

int trie_remove(Trie *trie, char *key);

/**
 * Remove an entry from a trie.
 * The key is a sequence of bytes; for a key that is a NUL-terminated
 * text string, use @ref trie_lookup.
 *
 * @param trie               The trie.
 * @param key                The key of the entry to remove.
 * @param key_length         The key length in bytes.
 * @return                   Non-zero if the key was removed successfully,
 *                           or zero if it is not present in the trie.
 */

int trie_remove_binary(Trie *trie, unsigned char *key, int key_length);

/**
 * Find the number of entries in a trie.
 *
 * @param trie               The trie.
 * @return                   Count of the number of entries in the trie.
 */

unsigned int trie_num_entries(Trie *trie);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_TRIE_H */


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

#define NUM_TEST_VALUES 10000

int test_array[NUM_TEST_VALUES];
char test_strings[NUM_TEST_VALUES][10];
unsigned char bin_key[] = { 'a', 'b', 'c', 0, 1, 2, 0xff };
unsigned char bin_key2[] = { 'a', 'b', 'c', 0, 1, 2, 0xff, 0 };
unsigned char bin_key3[] = { 'a', 'b', 'c' };
unsigned char bin_key4[] = { 'z', 0, 'z', 'z' };

Trie *generate_trie(void)
{
	Trie *trie;
	int i;
	unsigned int entries;

	/* Create a trie and fill it with a large number of values */

	trie = trie_new();
	entries = 0;

	for (i=0; i<NUM_TEST_VALUES; ++i) {

		/* Create a string containing a text version of i, and use
		 * it as a key for the value */

		test_array[i] = i;
		sprintf(test_strings[i], "%i", i);

		assert(trie_insert(trie, test_strings[i],
		                   &test_array[i]) != 0);

		++entries;

		assert(trie_num_entries(trie) == entries);
	}

	return trie;
}

void test_trie_new_free(void)
{
	Trie *trie;

	/* Allocate and free an empty trie */

	trie = trie_new();

	assert(trie != NULL);

	trie_free(trie);

	/* Add some values before freeing */

	trie = trie_new();

	assert(trie_insert(trie, "hello", "there") != 0);
	assert(trie_insert(trie, "hell", "testing") != 0);
	assert(trie_insert(trie, "testing", "testing") != 0);
	assert(trie_insert(trie, "", "asfasf") != 0);

	trie_free(trie);

	/* Add a value, remove it and then free */

	trie = trie_new();

	assert(trie_insert(trie, "hello", "there") != 0);
	assert(trie_remove(trie, "hello") != 0);

	trie_free(trie);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	trie = trie_new();
	assert(trie == NULL);
}

void test_trie_insert(void)
{
	Trie *trie;
	unsigned int entries;
	size_t allocated;

	trie = generate_trie();

	/* Test insert of NULL value has no effect */

	entries = trie_num_entries(trie);
	assert(trie_insert(trie, "hello world", NULL) == 0);
	assert(trie_num_entries(trie) == entries);

	/* Test out of memory scenario */

	allocated = alloc_test_get_allocated();
	alloc_test_set_limit(0);
	assert(trie_insert(trie, "a", "test value") == 0);
	assert(trie_num_entries(trie) == entries);

	/* Test rollback */

	alloc_test_set_limit(5);
	assert(trie_insert(trie, "hello world", "test value") == 0);
	assert(alloc_test_get_allocated() == allocated);
	assert(trie_num_entries(trie) == entries);

	trie_free(trie);
}

void test_trie_lookup(void)
{
	Trie *trie;
	char buf[10];
	int *val;
	int i;

	trie = generate_trie();

	/* Test lookup for non-existent values */

	assert(trie_lookup(trie, "000000000000000") == TRIE_NULL);
	assert(trie_lookup(trie, "") == TRIE_NULL);

	/* Look up all values */

	for (i=0; i<NUM_TEST_VALUES; ++i) {

		sprintf(buf, "%i", i);

		val = (int *) trie_lookup(trie, buf);

		assert(*val == i);
	}

	trie_free(trie);
}

void test_trie_remove(void)
{
	Trie *trie;
	char buf[10];
	int i;
	unsigned int entries;

	trie = generate_trie();

	/* Test remove on non-existent values. */

	assert(trie_remove(trie, "000000000000000") == 0);
	assert(trie_remove(trie, "") == 0);

	entries = trie_num_entries(trie);

	assert(entries == NUM_TEST_VALUES);

	/* Remove all values */

	for (i=0; i<NUM_TEST_VALUES; ++i) {

		sprintf(buf, "%i", i);

		/* Remove value and check counter */

		assert(trie_remove(trie, buf) != 0);
		--entries;
		assert(trie_num_entries(trie) == entries);
	}

	trie_free(trie);
}

void test_trie_replace(void)
{
	Trie *trie;
	int *val;

	trie = generate_trie();

	/* Test replacing values */

	val = malloc(sizeof(int));
	*val = 999;
	assert(trie_insert(trie, "999", val) != 0);
	assert(trie_num_entries(trie) == NUM_TEST_VALUES);

	assert(trie_lookup(trie, "999") == val);
	free(val);
	trie_free(trie);
}

void test_trie_insert_empty(void)
{
	Trie *trie;
	char buf[10];

	trie = trie_new();

	/* Test insert on empty string */

	assert(trie_insert(trie, "", buf) != 0);
	assert(trie_num_entries(trie) != 0);
	assert(trie_lookup(trie, "") == buf);
	assert(trie_remove(trie, "") != 0);

	assert(trie_num_entries(trie) == 0);

	trie_free(trie);
}

#define LONG_STRING_LEN 4096
static void test_trie_free_long(void)
{
	char *long_string;
	Trie *trie;

	/* Generate a long string */

	long_string = malloc(LONG_STRING_LEN);
	memset(long_string, 'A', LONG_STRING_LEN);
	long_string[LONG_STRING_LEN - 1] = '\0';

	/* Create a trie and add the string */

	trie = trie_new();
	trie_insert(trie, long_string, long_string);

	trie_free(trie);

	free(long_string);
}

/* Test the use of the trie when characters in the keys used are negative
 * (top bit set in the character; alternative, c >= 128). */

static void test_trie_negative_keys(void)
{
	char my_key[] = { 'a', 'b', 'c', -50, -20, '\0' };
	Trie *trie;
	void *value;

	trie = trie_new();

	assert(trie_insert(trie, my_key, "hello world") != 0);

	value = trie_lookup(trie, my_key);

	assert(!strcmp(value, "hello world"));

	assert(trie_remove(trie, my_key) != 0);
	assert(trie_remove(trie, my_key) == 0);
	assert(trie_lookup(trie, my_key) == NULL);

	trie_free(trie);
}

Trie *generate_binary_trie(void)
{
	Trie *trie;

	trie = trie_new();

	/* Insert some values */

	assert(trie_insert_binary(trie,
	                          bin_key2, sizeof(bin_key2),
	                          "goodbye world") != 0);
	assert(trie_insert_binary(trie,
	                          bin_key, sizeof(bin_key),
	                          "hello world") != 0);

	return trie;
}

void test_trie_insert_binary(void)
{
	Trie *trie;
	char *value;

	trie = generate_binary_trie();

	/* Overwrite a value */

	assert(trie_insert_binary(trie,
	                          bin_key, sizeof(bin_key),
	                          "hi world") != 0);

	/* Insert NULL value doesn't work */

	assert(trie_insert_binary(trie, bin_key3,
	                          sizeof(bin_key3), NULL) == 0);

	/* Read them back */

	value = trie_lookup_binary(trie, bin_key, sizeof(bin_key));
	assert(!strcmp(value, "hi world"));

	value = trie_lookup_binary(trie, bin_key2, sizeof(bin_key2));
	assert(!strcmp(value, "goodbye world"));

	trie_free(trie);
}

void test_trie_insert_out_of_memory(void)
{
	Trie *trie;

	trie = generate_binary_trie();

	alloc_test_set_limit(3);

	assert(trie_insert_binary(trie,
	                          bin_key4, sizeof(bin_key4),
	                          "test value") == 0);

	assert(trie_lookup_binary(trie, bin_key4, sizeof(bin_key4)) == NULL);
	assert(trie_num_entries(trie) == 2);

	trie_free(trie);
}

void test_trie_remove_binary(void)
{
	Trie *trie;
	void *value;

	trie = generate_binary_trie();

	/* Test look up and remove of invalid values */

	value = trie_lookup_binary(trie, bin_key3, sizeof(bin_key3));
	assert(value == NULL);

	assert(trie_remove_binary(trie, bin_key3, sizeof(bin_key3)) == 0);

	assert(trie_lookup_binary(trie, bin_key4, sizeof(bin_key4)) == 0);
	assert(trie_remove_binary(trie, bin_key4, sizeof(bin_key4)) == 0);

	/* Remove the two values */

	assert(trie_remove_binary(trie, bin_key2, sizeof(bin_key2)) != 0);
	assert(trie_lookup_binary(trie, bin_key2, sizeof(bin_key2)) == NULL);
	assert(trie_lookup_binary(trie, bin_key, sizeof(bin_key)) != NULL);

	assert(trie_remove_binary(trie, bin_key, sizeof(bin_key)) != 0);
	assert(trie_lookup_binary(trie, bin_key, sizeof(bin_key)) == NULL);

	trie_free(trie);
}

static UnitTestFunction tests[] = {
	test_trie_new_free,
	test_trie_insert,
	test_trie_lookup,
	test_trie_remove,
	test_trie_replace,
	test_trie_insert_empty,
	test_trie_free_long,
	test_trie_negative_keys,
	test_trie_insert_binary,
	test_trie_insert_out_of_memory,
	test_trie_remove_binary,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

