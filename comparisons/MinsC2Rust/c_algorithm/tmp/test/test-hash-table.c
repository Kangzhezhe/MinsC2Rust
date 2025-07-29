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
 * @file hash-table.h
 *
 * @brief Hash table.
 *
 * A hash table stores a set of values which can be addressed by a
 * key.  Given the key, the corresponding value can be looked up
 * quickly.
 *
 * To create a hash table, use @ref hash_table_new.  To destroy a
 * hash table, use @ref hash_table_free.
 *
 * To insert a value into a hash table, use @ref hash_table_insert.
 *
 * To remove a value from a hash table, use @ref hash_table_remove.
 *
 * To look up a value by its key, use @ref hash_table_lookup.
 *
 * To iterate over all values in a hash table, use
 * @ref hash_table_iterate to initialise a @ref HashTableIterator
 * structure.  Each value can then be read in turn using
 * @ref hash_table_iter_next and @ref hash_table_iter_has_more.
 */

#ifndef ALGORITHM_HASH_TABLE_H
#define ALGORITHM_HASH_TABLE_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A hash table structure.
 */

typedef struct _HashTable HashTable;

/**
 * Structure used to iterate over a hash table.
 */

typedef struct _HashTableIterator HashTableIterator;

/**
 * Internal structure representing an entry in a hash table.
 */

typedef struct _HashTableEntry HashTableEntry;

/**
 * A key to look up a value in a @ref HashTable.
 */

typedef void *HashTableKey;

/**
 * A value stored in a @ref HashTable.
 */

typedef void *HashTableValue;

/**
 * Internal structure representing an entry in hash table
 * used as @ref HashTableIterator next result.
 */

typedef struct _HashTablePair{
	HashTableKey key;
	HashTableValue value;
} HashTablePair;

/**
 * Definition of a @ref HashTableIterator.
 */

struct _HashTableIterator {
	HashTable *hash_table;
	HashTableEntry *next_entry;
	unsigned int next_chain;
};

/**
 * A null @ref HashTableValue.
 */

#define HASH_TABLE_NULL ((void *) 0)

/**
 * Hash function used to generate hash values for keys used in a hash
 * table.
 *
 * @param value  The value to generate a hash value for.
 * @return       The hash value.
 */

typedef unsigned int (*HashTableHashFunc)(HashTableKey value);

/**
 * Function used to compare two keys for equality.
 *
 * @return   Non-zero if the two keys are equal, zero if the keys are
 *           not equal.
 */

typedef int (*HashTableEqualFunc)(HashTableKey value1, HashTableKey value2);

/**
 * Type of function used to free keys when entries are removed from a
 * hash table.
 */

typedef void (*HashTableKeyFreeFunc)(HashTableKey value);

/**
 * Type of function used to free values when entries are removed from a
 * hash table.
 */

typedef void (*HashTableValueFreeFunc)(HashTableValue value);

/**
 * Create a new hash table.
 *
 * @param hash_func            Function used to generate hash keys for the
 *                             keys used in the table.
 * @param equal_func           Function used to test keys used in the table
 *                             for equality.
 * @return                     A new hash table structure, or NULL if it
 *                             was not possible to allocate the new hash
 *                             table.
 */

HashTable *hash_table_new(HashTableHashFunc hash_func,
                          HashTableEqualFunc equal_func);

/**
 * Destroy a hash table.
 *
 * @param hash_table           The hash table to destroy.
 */

void hash_table_free(HashTable *hash_table);

/**
 * Register functions used to free the key and value when an entry is
 * removed from a hash table.
 *
 * @param hash_table           The hash table.
 * @param key_free_func        Function used to free keys.
 * @param value_free_func      Function used to free values.
 */

void hash_table_register_free_functions(HashTable *hash_table,
                                        HashTableKeyFreeFunc key_free_func,
                                        HashTableValueFreeFunc value_free_func);

/**
 * Insert a value into a hash table, overwriting any existing entry
 * using the same key.
 *
 * @param hash_table           The hash table.
 * @param key                  The key for the new value.
 * @param value                The value to insert.
 * @return                     Non-zero if the value was added successfully,
 *                             or zero if it was not possible to allocate
 *                             memory for the new entry.
 */

int hash_table_insert(HashTable *hash_table,
                      HashTableKey key,
                      HashTableValue value);

/**
 * Look up a value in a hash table by key.
 *
 * @param hash_table          The hash table.
 * @param key                 The key of the value to look up.
 * @return                    The value, or @ref HASH_TABLE_NULL if there
 *                            is no value with that key in the hash table.
 */

HashTableValue hash_table_lookup(HashTable *hash_table,
                                 HashTableKey key);

/**
 * Remove a value from a hash table.
 *
 * @param hash_table          The hash table.
 * @param key                 The key of the value to remove.
 * @return                    Non-zero if a key was removed, or zero if the
 *                            specified key was not found in the hash table.
 */

int hash_table_remove(HashTable *hash_table, HashTableKey key);

/**
 * Retrieve the number of entries in a hash table.
 *
 * @param hash_table          The hash table.
 * @return                    The number of entries in the hash table.
 */

unsigned int hash_table_num_entries(HashTable *hash_table);

/**
 * Initialise a @ref HashTableIterator to iterate over a hash table.
 *
 * @param hash_table          The hash table.
 * @param iter                Pointer to an iterator structure to
 *                            initialise.
 */

void hash_table_iterate(HashTable *hash_table, HashTableIterator *iter);

/**
 * Determine if there are more keys in the hash table to iterate
 * over.
 *
 * @param iterator            The hash table iterator.
 * @return                    Zero if there are no more values to iterate
 *                            over, non-zero if there are more values to
 *                            iterate over.
 */

int hash_table_iter_has_more(HashTableIterator *iterator);

/**
 * Using a hash table iterator, retrieve the next @ref HashTablePair.
 *
 * Note: To avoid @ref HashTableEntry internal @ref HashTablePair
 *       from being tampered with, and potentially messing with
 *       internal table structure, the function returns a copy
 *       of @ref HashTablePair stored internally.
 *
 * @param iterator            The hash table iterator.
 * @return                    The next @ref HashTablePair from the hash
 *                            table, or @ref HASH_TABLE_NULL of Key and
 *                            Value if there are no more keys to iterate
 *                            over.
 */

HashTablePair hash_table_iter_next(HashTableIterator *iterator);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_HASH_TABLE_H */

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

int value1 = 1, value2 = 2, value3 = 3, value4 = 4;
int allocated_keys = 0;
int allocated_values = 0;

/* Generates a hash table for use in tests containing 10,000 entries */

HashTable *generate_hash_table(void)
{
	HashTable *hash_table;
	char buf[10];
	char *value;
	int i;

	/* Allocate a new hash table.  We use a hash table with keys that are
	 * string versions of the integer values 0..9999 to ensure that there
	 * will be collisions within the hash table (using integer values
	 * with int_hash causes no collisions) */

	hash_table = hash_table_new(string_hash, string_equal);

	/* Insert lots of values */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		sprintf(buf, "%i", i);

		value = strdup(buf);

		hash_table_insert(hash_table, value, value);
	}

	/* Automatically free all the values with the hash table */

	hash_table_register_free_functions(hash_table, NULL, free);

	return hash_table;
}

/* Basic allocate and free */

void test_hash_table_new_free(void)
{
	HashTable *hash_table;

	hash_table = hash_table_new(int_hash, int_equal);

	assert(hash_table != NULL);

	/* Add some values */

	hash_table_insert(hash_table, &value1, &value1);
	hash_table_insert(hash_table, &value2, &value2);
	hash_table_insert(hash_table, &value3, &value3);
	hash_table_insert(hash_table, &value4, &value4);

	/* Free the hash table */

	hash_table_free(hash_table);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	hash_table = hash_table_new(int_hash, int_equal);
	assert(hash_table == NULL);
	assert(alloc_test_get_allocated() == 0);

	alloc_test_set_limit(1);
	hash_table = hash_table_new(int_hash, int_equal);
	assert(hash_table == NULL);
	assert(alloc_test_get_allocated() == 0);
}

/* Test insert and lookup functions */

void test_hash_table_insert_lookup(void)
{
	HashTable *hash_table;
	char buf[10];
	char *value;
	int i;

	/* Generate a hash table */

	hash_table = generate_hash_table();

	assert(hash_table_num_entries(hash_table) == NUM_TEST_VALUES);

	/* Check all values */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		sprintf(buf, "%i", i);
		value = hash_table_lookup(hash_table, buf);

		assert(strcmp(value, buf) == 0);
	}

	/* Lookup on invalid values returns NULL */

	sprintf(buf, "%i", -1);
	assert(hash_table_lookup(hash_table, buf) == NULL);
	sprintf(buf, "%i", NUM_TEST_VALUES);
	assert(hash_table_lookup(hash_table, buf) == NULL);

	/* Insert overwrites existing entries with the same key */

	sprintf(buf, "%i", 12345);
	hash_table_insert(hash_table, buf, strdup("hello world"));
	value = hash_table_lookup(hash_table, buf);
	assert(strcmp(value, "hello world") == 0);

	hash_table_free(hash_table);
}

void test_hash_table_remove(void)
{
	HashTable *hash_table;
	char buf[10];

	hash_table = generate_hash_table();

	assert(hash_table_num_entries(hash_table) == NUM_TEST_VALUES);
	sprintf(buf, "%i", 5000);
	assert(hash_table_lookup(hash_table, buf) != NULL);

	/* Remove an entry */

	hash_table_remove(hash_table, buf);

	/* Check entry counter */

	assert(hash_table_num_entries(hash_table) == 9999);

	/* Check that NULL is returned now */

	assert(hash_table_lookup(hash_table, buf) == NULL);

	/* Try removing a non-existent entry */

	sprintf(buf, "%i", -1);
	hash_table_remove(hash_table, buf);

	assert(hash_table_num_entries(hash_table) == 9999);

	hash_table_free(hash_table);
}

void test_hash_table_iterating(void)
{
	HashTable *hash_table;
	HashTableIterator iterator;
	int count;

	hash_table = generate_hash_table();

	/* Iterate over all values in the table */

	count = 0;

	hash_table_iterate(hash_table, &iterator);

	while (hash_table_iter_has_more(&iterator)) {
		hash_table_iter_next(&iterator);

		++count;
	}

	assert(count == NUM_TEST_VALUES);

	/* Test iter_next after iteration has completed. */

	HashTablePair pair = hash_table_iter_next(&iterator);
	assert(pair.value == HASH_TABLE_NULL);

	hash_table_free(hash_table);

	/* Test iterating over an empty table */

	hash_table = hash_table_new(int_hash, int_equal);

	hash_table_iterate(hash_table, &iterator);

	assert(hash_table_iter_has_more(&iterator) == 0);

	hash_table_free(hash_table);
}

/* Demonstrates the ability to iteratively remove objects from
 * a hash table: ie. removing the current key being iterated over
 * does not break the iterator. */

void test_hash_table_iterating_remove(void)
{
	HashTable *hash_table;
	HashTableIterator iterator;
	char buf[10];
	char *val;
	HashTablePair pair;
	int count;
	unsigned int removed;
	int i;

	hash_table = generate_hash_table();

	/* Iterate over all values in the table */

	count = 0;
	removed = 0;

	hash_table_iterate(hash_table, &iterator);

	while (hash_table_iter_has_more(&iterator)) {

		/* Read the next value */

		pair = hash_table_iter_next(&iterator);
		val = pair.value;

		/* Remove every hundredth entry */

		if ((atoi(val) % 100) == 0) {
			hash_table_remove(hash_table, val);
			++removed;
		}

		++count;
	}

	/* Check counts */

	assert(removed == 100);
	assert(count == NUM_TEST_VALUES);

	assert(hash_table_num_entries(hash_table)
	       == NUM_TEST_VALUES - removed);

	/* Check all entries divisible by 100 were really removed */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		sprintf(buf, "%i", i);

		if (i % 100 == 0) {
			assert(hash_table_lookup(hash_table, buf) == NULL);
		} else {
			assert(hash_table_lookup(hash_table, buf) != NULL);
		}
	}

	hash_table_free(hash_table);
}

/* Create a new key */

int *new_key(int value)
{
	int *result;

	result = malloc(sizeof(int));
	*result = value;

	++allocated_keys;

	return result;
}

/* Callback function invoked when a key is freed */

void free_key(void *key)
{
	free(key);

	--allocated_keys;
}

/* Create a new value */

int *new_value(int value)
{
	int *result;

	result = malloc(sizeof(int));
	*result = value;

	++allocated_values;

	return result;
}

/* Callback function invoked when a value is freed */

void free_value(void *value)
{
	free(value);

	--allocated_values;
}

/* Test the use of functions to free keys / values when they are removed. */

void test_hash_table_free_functions(void)
{
	HashTable *hash_table;
	int *key;
	int *value;
	int i;

	/* Create a hash table, fill it with values */

	hash_table = hash_table_new(int_hash, int_equal);

	hash_table_register_free_functions(hash_table, free_key, free_value);

	allocated_values = 0;

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		key = new_key(i);
		value = new_value(99);

		hash_table_insert(hash_table, key, value);
	}

	assert(allocated_keys == NUM_TEST_VALUES);
	assert(allocated_values == NUM_TEST_VALUES);

	/* Check that removing a key works */

	i = NUM_TEST_VALUES / 2;
	hash_table_remove(hash_table, &i);

	assert(allocated_keys == NUM_TEST_VALUES - 1);
	assert(allocated_values == NUM_TEST_VALUES - 1);

	/* Check that replacing an existing key works */

	key = new_key(NUM_TEST_VALUES / 3);
	value = new_value(999);

	assert(allocated_keys == NUM_TEST_VALUES);
	assert(allocated_values == NUM_TEST_VALUES);

	hash_table_insert(hash_table, key, value);

	assert(allocated_keys == NUM_TEST_VALUES - 1);
	assert(allocated_values == NUM_TEST_VALUES - 1);

	/* A free of the hash table should free all of the keys and values */

	hash_table_free(hash_table);

	assert(allocated_keys == 0);
	assert(allocated_values == 0);
}

/* Test for out of memory scenario */

void test_hash_table_out_of_memory(void)
{
	HashTable *hash_table;
	int values[66];
	unsigned int i;

	hash_table = hash_table_new(int_hash, int_equal);

	/* Test normal failure */

	alloc_test_set_limit(0);
	values[0] = 0;
	assert(hash_table_insert(hash_table, &values[0], &values[0]) == 0);
	assert(hash_table_num_entries(hash_table) == 0);

	alloc_test_set_limit(-1);

	/* Test failure when increasing table size.
	 * The initial table size is 193 entries.  The table increases in
	 * size when 1/3 full, so the 66th entry should cause the insert
	 * to fail.
	 */

	for (i=0; i<65; ++i) {
		values[i] = (int) i;

		assert(hash_table_insert(hash_table,
		                         &values[i], &values[i]) != 0);
		assert(hash_table_num_entries(hash_table) == i + 1);
	}

	assert(hash_table_num_entries(hash_table) == 65);

	/* Test the 66th insert */

	alloc_test_set_limit(0);

	values[65] = 65;

	assert(hash_table_insert(hash_table, &values[65], &values[65]) == 0);
	assert(hash_table_num_entries(hash_table) == 65);

	hash_table_free(hash_table);
}

void test_hash_iterator_key_pair()
{
	HashTable *hash_table;
	HashTableIterator iterator;
	HashTablePair pair;
	hash_table = hash_table_new(int_hash, int_equal);

	/* Add some values */

	hash_table_insert(hash_table, &value1, &value1);
	hash_table_insert(hash_table, &value2, &value2);

	hash_table_iterate(hash_table, &iterator);

	while (hash_table_iter_has_more(&iterator)) {

		/* Retrieve both Key and Value */

		pair = hash_table_iter_next(&iterator);

		int *key = (int*) pair.key;
		int *val = (int*) pair.value;

		assert(*key == *val);
	}

	hash_table_free(hash_table);
}

static UnitTestFunction tests[] = {
	test_hash_table_new_free,
	test_hash_table_insert_lookup,
	test_hash_table_remove,
	test_hash_table_iterating,
	test_hash_table_iterating_remove,
	test_hash_table_free_functions,
	test_hash_table_out_of_memory,
	test_hash_iterator_key_pair,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

