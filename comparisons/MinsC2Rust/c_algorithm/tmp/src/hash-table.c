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

/* Hash table implementation */

#include <stdlib.h>
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

struct _HashTableEntry {
	HashTablePair pair;
	HashTableEntry *next;
};

struct _HashTable {
	HashTableEntry **table;
	unsigned int table_size;
	HashTableHashFunc hash_func;
	HashTableEqualFunc equal_func;
	HashTableKeyFreeFunc key_free_func;
	HashTableValueFreeFunc value_free_func;
	unsigned int entries;
	unsigned int prime_index;
};

/* This is a set of good hash table prime numbers, from:
 *   http://planetmath.org/encyclopedia/GoodHashTablePrimes.html
 * Each prime is roughly double the previous value, and as far as
 * possible from the nearest powers of two. */

static const unsigned int hash_table_primes[] = {
	193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317,
	196613, 393241, 786433, 1572869, 3145739, 6291469,
	12582917, 25165843, 50331653, 100663319, 201326611,
	402653189, 805306457, 1610612741,
};

static const unsigned int hash_table_num_primes
	= sizeof(hash_table_primes) / sizeof(int);

/* Internal function used to allocate the table on hash table creation
 * and when enlarging the table */

static int hash_table_allocate_table(HashTable *hash_table)
{
	unsigned int new_table_size;

	/* Determine the table size based on the current prime index.
	 * An attempt is made here to ensure sensible behavior if the
	 * maximum prime is exceeded, but in practice other things are
	 * likely to break long before that happens. */

	if (hash_table->prime_index < hash_table_num_primes) {
		new_table_size = hash_table_primes[hash_table->prime_index];
	} else {
		new_table_size = hash_table->entries * 10;
	}

	hash_table->table_size = new_table_size;

	/* Allocate the table and initialise to NULL for all entries */

	hash_table->table = calloc(hash_table->table_size,
	                           sizeof(HashTableEntry *));

	return hash_table->table != NULL;
}

/* Free an entry, calling the free functions if there are any registered */

static void hash_table_free_entry(HashTable *hash_table, HashTableEntry *entry)
{
	HashTablePair *pair;

	pair = &(entry->pair);

	/* If there is a function registered for freeing keys, use it to free
	 * the key */

	if (hash_table->key_free_func != NULL) {
		hash_table->key_free_func(pair->key);
	}

	/* Likewise with the value */

	if (hash_table->value_free_func != NULL) {
		hash_table->value_free_func(pair->value);
	}

	/* Free the data structure */

	free(entry);
}

HashTable *hash_table_new(HashTableHashFunc hash_func,
                          HashTableEqualFunc equal_func)
{
	HashTable *hash_table;

	/* Allocate a new hash table structure */

	hash_table = (HashTable *) malloc(sizeof(HashTable));

	if (hash_table == NULL) {
		return NULL;
	}

	hash_table->hash_func = hash_func;
	hash_table->equal_func = equal_func;
	hash_table->key_free_func = NULL;
	hash_table->value_free_func = NULL;
	hash_table->entries = 0;
	hash_table->prime_index = 0;

	/* Allocate the table */

	if (!hash_table_allocate_table(hash_table)) {
		free(hash_table);

		return NULL;
	}

	return hash_table;
}

void hash_table_free(HashTable *hash_table)
{
	HashTableEntry *rover;
	HashTableEntry *next;
	unsigned int i;

	/* Free all entries in all chains */

	for (i=0; i<hash_table->table_size; ++i) {
		rover = hash_table->table[i];
		while (rover != NULL) {
			next = rover->next;
			hash_table_free_entry(hash_table, rover);
			rover = next;
		}
	}

	/* Free the table */

	free(hash_table->table);

	/* Free the hash table structure */

	free(hash_table);
}

void hash_table_register_free_functions(HashTable *hash_table,
                                        HashTableKeyFreeFunc key_free_func,
                                        HashTableValueFreeFunc value_free_func)
{
	hash_table->key_free_func = key_free_func;
	hash_table->value_free_func = value_free_func;
}


static int hash_table_enlarge(HashTable *hash_table)
{
	HashTableEntry **old_table;
	unsigned int old_table_size;
	unsigned int old_prime_index;
	HashTableEntry *rover;
	HashTablePair *pair;
	HashTableEntry *next;
	unsigned int index;
	unsigned int i;

	/* Store a copy of the old table */

	old_table = hash_table->table;
	old_table_size = hash_table->table_size;
	old_prime_index = hash_table->prime_index;

	/* Allocate a new, larger table */

	++hash_table->prime_index;

	if (!hash_table_allocate_table(hash_table)) {

		/* Failed to allocate the new table */

		hash_table->table = old_table;
		hash_table->table_size = old_table_size;
		hash_table->prime_index = old_prime_index;

		return 0;
	}

	/* Link all entries from all chains into the new table */

	for (i=0; i<old_table_size; ++i) {
		rover = old_table[i];

		while (rover != NULL) {
			next = rover->next;

			/* Fetch rover HashTablePair */

			pair = &(rover->pair);

			/* Find the index into the new table */

			index = hash_table->hash_func(pair->key) % hash_table->table_size;

			/* Link this entry into the chain */

			rover->next = hash_table->table[index];
			hash_table->table[index] = rover;

			/* Advance to next in the chain */

			rover = next;
		}
	}

	/* Free the old table */

	free(old_table);

	return 1;
}

int hash_table_insert(HashTable *hash_table, HashTableKey key,
                      HashTableValue value)
{
	HashTableEntry *rover;
	HashTablePair *pair;
	HashTableEntry *newentry;
	unsigned int index;

	/* If there are too many items in the table with respect to the table
	 * size, the number of hash collisions increases and performance
	 * decreases. Enlarge the table size to prevent this happening */

	if ((hash_table->entries * 3) / hash_table->table_size > 0) {

		/* Table is more than 1/3 full */

		if (!hash_table_enlarge(hash_table)) {

			/* Failed to enlarge the table */

			return 0;
		}
	}

	/* Generate the hash of the key and hence the index into the table */

	index = hash_table->hash_func(key) % hash_table->table_size;

	/* Traverse the chain at this location and look for an existing
	 * entry with the same key */

	rover = hash_table->table[index];

	while (rover != NULL) {

		/* Fetch rover's HashTablePair entry */

		pair = &(rover->pair);

		if (hash_table->equal_func(pair->key, key) != 0) {

			/* Same key: overwrite this entry with new data */

			/* If there is a value free function, free the old data
			 * before adding in the new data */

			if (hash_table->value_free_func != NULL) {
				hash_table->value_free_func(pair->value);
			}

			/* Same with the key: use the new key value and free
			 * the old one */

			if (hash_table->key_free_func != NULL) {
				hash_table->key_free_func(pair->key);
			}

			pair->key = key;
			pair->value = value;

			/* Finished */

			return 1;
		}

		rover = rover->next;
	}

	/* Not in the hash table yet.  Create a new entry */

	newentry = (HashTableEntry *) malloc(sizeof(HashTableEntry));

	if (newentry == NULL) {
		return 0;
	}

	newentry->pair.key = key;
	newentry->pair.value = value;

	/* Link into the list */

	newentry->next = hash_table->table[index];
	hash_table->table[index] = newentry;

	/* Maintain the count of the number of entries */

	++hash_table->entries;

	/* Added successfully */

	return 1;
}

HashTableValue hash_table_lookup(HashTable *hash_table, HashTableKey key)
{
	HashTableEntry *rover;
	HashTablePair *pair;
	unsigned int index;

	/* Generate the hash of the key and hence the index into the table */

	index = hash_table->hash_func(key) % hash_table->table_size;

	/* Walk the chain at this index until the corresponding entry is
	 * found */

	rover = hash_table->table[index];

	while (rover != NULL) {
		pair = &(rover->pair);

		if (hash_table->equal_func(key, pair->key) != 0) {

			/* Found the entry.  Return the data. */

			return pair->value;
		}

		rover = rover->next;
	}

	/* Not found */

	return HASH_TABLE_NULL;
}

int hash_table_remove(HashTable *hash_table, HashTableKey key)
{
	HashTableEntry **rover;
	HashTableEntry *entry;
	HashTablePair *pair;
	unsigned int index;
	int result;

	/* Generate the hash of the key and hence the index into the table */

	index = hash_table->hash_func(key) % hash_table->table_size;

	/* Rover points at the pointer which points at the current entry
	 * in the chain being inspected.  ie. the entry in the table, or
	 * the "next" pointer of the previous entry in the chain.  This
	 * allows us to unlink the entry when we find it. */

	result = 0;
	rover = &hash_table->table[index];

	while (*rover != NULL) {

		pair = &((*rover)->pair);

		if (hash_table->equal_func(key, pair->key) != 0) {

			/* This is the entry to remove */

			entry = *rover;

			/* Unlink from the list */

			*rover = entry->next;

			/* Destroy the entry structure */

			hash_table_free_entry(hash_table, entry);

			/* Track count of entries */

			--hash_table->entries;

			result = 1;

			break;
		}

		/* Advance to the next entry */

		rover = &((*rover)->next);
	}

	return result;
}

unsigned int hash_table_num_entries(HashTable *hash_table)
{
	return hash_table->entries;
}

void hash_table_iterate(HashTable *hash_table, HashTableIterator *iterator)
{
	unsigned int chain;

	iterator->hash_table = hash_table;

	/* Default value of next if no entries are found. */

	iterator->next_entry = NULL;

	/* Find the first entry */

	for (chain=0; chain<hash_table->table_size; ++chain) {

		if (hash_table->table[chain] != NULL) {
			iterator->next_entry = hash_table->table[chain];
			iterator->next_chain = chain;
			break;
		}
	}
}

int hash_table_iter_has_more(HashTableIterator *iterator)
{
	return iterator->next_entry != NULL;
}

HashTablePair hash_table_iter_next(HashTableIterator *iterator)
{
	HashTableEntry *current_entry;
	HashTable *hash_table;
	HashTablePair pair = {NULL, NULL};
	unsigned int chain;

	hash_table = iterator->hash_table;

	if (iterator->next_entry == NULL) {
		return pair;
	}

	/* Result is immediately available */

	current_entry = iterator->next_entry;
	pair = current_entry->pair;

	/* Find the next entry */

	if (current_entry->next != NULL) {

		/* Next entry in current chain */

		iterator->next_entry = current_entry->next;

	} else {

		/* None left in this chain, so advance to the next chain */

		chain = iterator->next_chain + 1;

		/* Default value if no next chain found */

		iterator->next_entry = NULL;

		while (chain < hash_table->table_size) {

			/* Is there anything in this chain? */

			if (hash_table->table[chain] != NULL) {
				iterator->next_entry = hash_table->table[chain];
				break;
			}

			/* Try the next chain */

			++chain;
		}

		iterator->next_chain = chain;
	}

	return pair;
}

