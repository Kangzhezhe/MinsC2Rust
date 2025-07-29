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

struct _BloomFilter {
	BloomFilterHashFunc hash_func;
	unsigned char *table;
	unsigned int table_size;
	unsigned int num_functions;
};

/* Salt values.  These salts are XORed with the output of the hash function to
 * give multiple unique hashes.
 *
 * These are "nothing up my sleeve" numbers: they are derived from the first
 * 256 numbers in the book "A Million Random Digits with 100,000 Normal
 * Deviates" published by the RAND corporation, ISBN 0-8330-3047-7.
 *
 * The numbers here were derived by taking each number from the book in turn,
 * then multiplying by 256 and dividing by 100,000 to give a byte range value.
 * Groups of four numbers were then combined to give 32-bit integers, most
 * significant byte first.
 */

static const unsigned int salts[] = {
	0x1953c322, 0x588ccf17, 0x64bf600c, 0xa6be3f3d,
	0x341a02ea, 0x15b03217, 0x3b062858, 0x5956fd06,
	0x18b5624f, 0xe3be0b46, 0x20ffcd5c, 0xa35dfd2b,
	0x1fc4a9bf, 0x57c45d5c, 0xa8661c4a, 0x4f1b74d2,
	0x5a6dde13, 0x3b18dac6, 0x05a8afbf, 0xbbda2fe2,
	0xa2520d78, 0xe7934849, 0xd541bc75, 0x09a55b57,
	0x9b345ae2, 0xfc2d26af, 0x38679cef, 0x81bd1e0d,
	0x654681ae, 0x4b3d87ad, 0xd5ff10fb, 0x23b32f67,
	0xafc7e366, 0xdd955ead, 0xe7c34b1c, 0xfeace0a6,
	0xeb16f09d, 0x3c57a72d, 0x2c8294c5, 0xba92662a,
	0xcd5b2d14, 0x743936c8, 0x2489beff, 0xc6c56e00,
	0x74a4f606, 0xb244a94a, 0x5edfc423, 0xf1901934,
	0x24af7691, 0xf6c98b25, 0xea25af46, 0x76d5f2e6,
	0x5e33cdf2, 0x445eb357, 0x88556bd2, 0x70d1da7a,
	0x54449368, 0x381020bc, 0x1c0520bf, 0xf7e44942,
	0xa27e2a58, 0x66866fc5, 0x12519ce7, 0x437a8456,
};

BloomFilter *bloom_filter_new(unsigned int table_size,
                              BloomFilterHashFunc hash_func,
                              unsigned int num_functions)
{
	BloomFilter *filter;

	/* There is a limit on the number of functions which can be
	 * applied, due to the table size */

	if (num_functions > sizeof(salts) / sizeof(*salts)) {
		return NULL;
	}

	/* Allocate bloom filter structure */

	filter = malloc(sizeof(BloomFilter));

	if (filter == NULL) {
		return NULL;
	}

	/* Allocate table, each entry is one bit; these are packed into
	 * bytes.  When allocating we must round the length up to the nearest
	 * byte. */

	filter->table = calloc((table_size + 7) / 8, 1);

	if (filter->table == NULL) {
		free(filter);
		return NULL;
	}

	filter->hash_func = hash_func;
	filter->num_functions = num_functions;
	filter->table_size = table_size;

	return filter;
}

void bloom_filter_free(BloomFilter *bloomfilter)
{
	free(bloomfilter->table);
	free(bloomfilter);
}

void bloom_filter_insert(BloomFilter *bloomfilter, BloomFilterValue value)
{
	unsigned int hash;
	unsigned int subhash;
	unsigned int index;
	unsigned int i;
	unsigned char b;

	/* Generate hash of the value to insert */

	hash = bloomfilter->hash_func(value);

	/* Generate multiple unique hashes by XORing with values in the
	 * salt table. */

	for (i=0; i<bloomfilter->num_functions; ++i) {

		/* Generate a unique hash */

		subhash = hash ^ salts[i];

		/* Find the index into the table */

		index = subhash % bloomfilter->table_size;

		/* Insert into the table.
		 * index / 8 finds the byte index of the table,
		 * index % 8 gives the bit index within that byte to set. */

		b = (unsigned char) (1 << (index % 8));
		bloomfilter->table[index / 8] |= b;
	}
}

int bloom_filter_query(BloomFilter *bloomfilter, BloomFilterValue value)
{
	unsigned int hash;
	unsigned int subhash;
	unsigned int index;
	unsigned int i;
	unsigned char b;
	int bit;

	/* Generate hash of the value to lookup */

	hash = bloomfilter->hash_func(value);

	/* Generate multiple unique hashes by XORing with values in the
	 * salt table. */

	for (i=0; i<bloomfilter->num_functions; ++i) {

		/* Generate a unique hash */

		subhash = hash ^ salts[i];

		/* Find the index into the table to test */

		index = subhash % bloomfilter->table_size;

		/* The byte at index / 8 holds the value to test */

		b = bloomfilter->table[index / 8];
		bit = 1 << (index % 8);

		/* Test if the particular bit is set; if it is not set,
		 * this value can not have been inserted. */

		if ((b & bit) == 0) {
			return 0;
		}
	}

	/* All necessary bits were set.  This may indicate that the value
	 * was inserted, or the values could have been set through other
	 * insertions. */

	return 1;
}

void bloom_filter_read(BloomFilter *bloomfilter, unsigned char *array)
{
	unsigned int array_size;

	/* The table is an array of bits, packed into bytes.  Round up
	 * to the nearest byte. */

	array_size = (bloomfilter->table_size + 7) / 8;

	/* Copy into the buffer of the calling routine. */

	memcpy(array, bloomfilter->table, array_size);
}

void bloom_filter_load(BloomFilter *bloomfilter, unsigned char *array)
{
	unsigned int array_size;

	/* The table is an array of bits, packed into bytes.  Round up
	 * to the nearest byte. */

	array_size = (bloomfilter->table_size + 7) / 8;

	/* Copy from the buffer of the calling routine. */

	memcpy(bloomfilter->table, array, array_size);
}

BloomFilter *bloom_filter_union(BloomFilter *filter1, BloomFilter *filter2)
{
	BloomFilter *result;
	unsigned int i;
	unsigned int array_size;

	/* To perform this operation, both filters must be created with
	 * the same values. */

	if (filter1->table_size != filter2->table_size
	 || filter1->num_functions != filter2->num_functions
	 || filter1->hash_func != filter2->hash_func) {
		return NULL;
	}

	/* Create a new bloom filter for the result */

	result = bloom_filter_new(filter1->table_size,
	                          filter1->hash_func,
	                          filter1->num_functions);

	if (result == NULL) {
		return NULL;
	}

	/* The table is an array of bits, packed into bytes.  Round up
	 * to the nearest byte. */

	array_size = (filter1->table_size + 7) / 8;

	/* Populate the table of the new filter */

	for (i=0; i<array_size; ++i) {
		result->table[i] = filter1->table[i] | filter2->table[i];
	}

	return result;
}

BloomFilter *bloom_filter_intersection(BloomFilter *filter1,
                                       BloomFilter *filter2)
{
	BloomFilter *result;
	unsigned int i;
	unsigned int array_size;

	/* To perform this operation, both filters must be created with
	 * the same values. */

	if (filter1->table_size != filter2->table_size
	 || filter1->num_functions != filter2->num_functions
	 || filter1->hash_func != filter2->hash_func) {
		return NULL;
	}

	/* Create a new bloom filter for the result */

	result = bloom_filter_new(filter1->table_size,
	                          filter1->hash_func,
	                          filter1->num_functions);

	if (result == NULL) {
		return NULL;
	}

	/* The table is an array of bits, packed into bytes.  Round up
	 * to the nearest byte. */

	array_size = (filter1->table_size + 7) / 8;

	/* Populate the table of the new filter */

	for (i=0; i<array_size; ++i) {
		result->table[i] = filter1->table[i] & filter2->table[i];
	}

	return result;
}

