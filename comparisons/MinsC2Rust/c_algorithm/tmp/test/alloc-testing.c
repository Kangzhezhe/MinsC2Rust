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

#define ALLOC_TESTING_C

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


/* All allocated blocks are given this magic number */

#define ALLOC_TEST_MAGIC 0x72ec82d2

/* This value is written to memory after it is freshly allocated, to ensure
 * that code under test does not rely on memory being initialised by
 * malloc(). */

#define MALLOC_PATTERN 0xBAADF00D

/* This value is written to memory after it is freed, to ensure that code
 * does not rely on memory that has been freed. */

#define FREE_PATTERN 0xDEADBEEF

/**
 * All blocks allocated by the testing framework are preceded by a structure
 * of this type.
 */

typedef struct _BlockHeader BlockHeader;

struct _BlockHeader {
	unsigned int magic_number;
	size_t bytes;
};

/* Count of the current number of allocated bytes. */

static size_t allocated_bytes = 0;

/* Limit on number of allocations that are possible.  Each time an allocation
 * is made, this is decremented.  When it reaches zero, no more allocations
 * are allowed.  If this has a negative value, the limit is disabled. */

signed int allocation_limit = -1;

/* Get the block header for an allocated pointer. */

static BlockHeader *alloc_test_get_header(void *ptr)
{
	BlockHeader *result;

	/* Go back from the start of the memory block to get the header. */

	result = ((BlockHeader *) ptr) - 1;

	assert(result->magic_number == ALLOC_TEST_MAGIC);

	return result;
}

/* Overwrite a block of memory with a repeated pattern. */

static void alloc_test_overwrite(void *ptr, size_t length,
                                 unsigned int pattern)
{
	unsigned char *byte_ptr;
	int pattern_seq;
	unsigned char b;
	size_t i;

	byte_ptr = ptr;

	for (i=0; i<length; ++i) {
		pattern_seq = (int) (i & 3);
		b = (unsigned char) ((pattern >> (8 * pattern_seq)) & 0xff);
		byte_ptr[i] = b;
	}
}

/* Base malloc function used by other functions. */

void *alloc_test_malloc(size_t bytes)
{
	BlockHeader *header;
	void *ptr;

	/* Check if we have reached the allocation limit. */

	if (allocation_limit == 0) {
		return NULL;
	}

	/* Allocate the requested block with enough room for the block header
	 * as well. */

	header = malloc(sizeof(BlockHeader) + bytes);

	if (header == NULL) {
		return NULL;
	}

	header->magic_number = ALLOC_TEST_MAGIC;
	header->bytes = bytes;

	/* Fill memory with MALLOC_PATTERN, to ensure that code under test
	 * does not rely on memory being initialised to zero. */

	ptr = header + 1;
	alloc_test_overwrite(ptr, bytes, MALLOC_PATTERN);

	/* Update counter */

	allocated_bytes += bytes;

	/* Decrease the allocation limit */

	if (allocation_limit > 0) {
		--allocation_limit;
	}

	/* Skip past the header and return the block itself */

	return header + 1;
}

/* Base free function */

void alloc_test_free(void *ptr)
{
	BlockHeader *header;
	size_t block_size;

	/* Must accept NULL as a valid pointer to free. */

	if (ptr == NULL) {
		return;
	}

	/* Get the block header and do a sanity check */

	header = alloc_test_get_header(ptr);
	block_size = header->bytes;
	assert(allocated_bytes >= block_size);

	/* Trash the allocated block to foil any code that relies on memory
	 * that has been freed. */

	alloc_test_overwrite(ptr, header->bytes, FREE_PATTERN);

	/* Trash the magic number in the block header to stop the same block
	 * from being freed again. */

	header->magic_number = 0;

	/* Free the allocated memory. */

	free(header);

	/* Update counter */

	allocated_bytes -= block_size;
}

void *alloc_test_realloc(void *ptr, size_t bytes)
{
	BlockHeader *header;
	void *new_ptr;
	size_t bytes_to_copy;

	/* Allocate the new block */

	new_ptr = alloc_test_malloc(bytes);

	if (new_ptr == NULL) {
		return NULL;
	}

	/* Copy over the old data and free the old block, if there was any. */

	if (ptr != NULL) {
		header = alloc_test_get_header(ptr);

		bytes_to_copy = header->bytes;

		if (bytes_to_copy > bytes) {
			bytes_to_copy = bytes;
		}

		memcpy(new_ptr, ptr, bytes_to_copy);

		alloc_test_free(ptr);
	}

	return new_ptr;
}

void *alloc_test_calloc(size_t nmemb, size_t bytes)
{
	void *result;
	size_t total_bytes = nmemb * bytes;

	/* Allocate the block. */

	result = alloc_test_malloc(total_bytes);

	if (result == NULL) {
		return NULL;
	}

	/* Initialise to zero. */

	memset(result, 0, total_bytes);

	return result;
}

char *alloc_test_strdup(const char *string)
{
	char *result;

	result = alloc_test_malloc(strlen(string) + 1);

	if (result == NULL) {
		return NULL;
	}

	strcpy(result, string);

	return result;
}

void alloc_test_set_limit(signed int alloc_count)
{
	allocation_limit = alloc_count;
}

size_t alloc_test_get_allocated(void)
{
	return allocated_bytes;
}

