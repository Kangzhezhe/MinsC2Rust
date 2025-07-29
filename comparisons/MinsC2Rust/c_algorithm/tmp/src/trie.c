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

/* Trie: fast mapping of strings to values */

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

typedef struct _TrieNode TrieNode;

struct _TrieNode {
	TrieValue data;
	unsigned int use_count;
	TrieNode *next[256];
};

struct _Trie {
	TrieNode *root_node;
};

Trie *trie_new(void)
{
	Trie *new_trie;

	new_trie = (Trie *) malloc(sizeof(Trie));

	if (new_trie == NULL) {
		return NULL;
	}

	new_trie->root_node = NULL;

	return new_trie;
}

static void trie_free_list_push(TrieNode **list, TrieNode *node)
{
	node->data = *list;
	*list = node;
}

static TrieNode *trie_free_list_pop(TrieNode **list)
{
	TrieNode *result;

	result = *list;
	*list = result->data;

	return result;
}

void trie_free(Trie *trie)
{
	TrieNode *free_list;
	TrieNode *node;
	int i;

	free_list = NULL;

	/* Start with the root node */

	if (trie->root_node != NULL) {
		trie_free_list_push(&free_list, trie->root_node);
	}

	/* Go through the free list, freeing nodes.  We add new nodes as
	 * we encounter them; in this way, all the nodes are freed
	 * non-recursively. */

	while (free_list != NULL) {
		node = trie_free_list_pop(&free_list);

		/* Add all children of this node to the free list */

		for (i=0; i<256; ++i) {
			if (node->next[i] != NULL) {
				trie_free_list_push(&free_list, node->next[i]);
			}
		}

		/* Free the node */

		free(node);
	}

	/* Free the trie */

	free(trie);
}

static TrieNode *trie_find_end(Trie *trie, char *key)
{
	TrieNode *node;
	char *p;

	/* Search down the trie until the end of string is reached */

	node = trie->root_node;

	for (p=key; *p != '\0'; ++p) {

		if (node == NULL) {
			/* Not found in the tree. Return. */

			return NULL;
		}

		/* Jump to the next node */

		node = node->next[(unsigned char) *p];
	}

	/* This key is present if the value at the last node is not NULL */

	return node;
}

static TrieNode *trie_find_end_binary(Trie *trie, unsigned char *key,
                                      int key_length)
{
	TrieNode *node;
	int j;
	int c;

	/* Search down the trie until the end of string is reached */

	node = trie->root_node;

	for (j=0; j<key_length; j++) {

		if (node == NULL) {
			/* Not found in the tree. Return. */
			return NULL;
		}

		c = (unsigned char) key[j];

		/* Jump to the next node */

		node = node->next[c];
	}

	/* This key is present if the value at the last node is not NULL */

	return node;
}

/* Roll back an insert operation after a failed malloc() call. */

static void trie_insert_rollback(Trie *trie, unsigned char *key)
{
	TrieNode *node;
	TrieNode **prev_ptr;
	TrieNode *next_node;
	TrieNode **next_prev_ptr;
	unsigned char *p;

	/* Follow the chain along.  We know that we will never reach the
	 * end of the string because trie_insert never got that far.  As a
	 * result, it is not necessary to check for the end of string
	 * delimiter (NUL) */

	node = trie->root_node;
	prev_ptr = &trie->root_node;
	p = key;

	while (node != NULL) {

		/* Find the next node now. We might free this node. */

		next_prev_ptr = &node->next[(unsigned char) *p];
		next_node = *next_prev_ptr;
		++p;

		/* Decrease the use count and free the node if it
		 * reaches zero. */

		--node->use_count;

		if (node->use_count == 0) {
			free(node);

			if (prev_ptr != NULL) {
				*prev_ptr = NULL;
			}

			next_prev_ptr = NULL;
		}

		/* Update pointers */

		node = next_node;
		prev_ptr = next_prev_ptr;
	}
}

int trie_insert(Trie *trie, char *key, TrieValue value)
{
	TrieNode **rover;
	TrieNode *node;
	char *p;
	int c;

	/* Cannot insert NULL values */

	if (value == TRIE_NULL) {
		return 0;
	}

	/* Search to see if this is already in the tree */

	node = trie_find_end(trie, key);

	/* Already in the tree? If so, replace the existing value and
	 * return success. */

	if (node != NULL && node->data != TRIE_NULL) {
		node->data = value;
		return 1;
	}

	/* Search down the trie until we reach the end of string,
	 * creating nodes as necessary */

	rover = &trie->root_node;
	p = key;

	for (;;) {

		node = *rover;

		if (node == NULL) {

			/* Node does not exist, so create it */

			node = (TrieNode *) calloc(1, sizeof(TrieNode));

			if (node == NULL) {

				/* Allocation failed.  Go back and undo
				 * what we have done so far. */

				trie_insert_rollback(trie,
				                     (unsigned char *) key);

				return 0;
			}

			node->data = TRIE_NULL;

			/* Link in to the trie */

			*rover = node;
		}

		/* Increase the node use count */

		++node->use_count;

		/* Current character */

		c = (unsigned char) *p;

		/* Reached the end of string?  If so, we're finished. */

		if (c == '\0') {

			/* Set the data at the node we have reached */

			node->data = value;

			break;
		}

		/* Advance to the next node in the chain */

		rover = &node->next[c];
		++p;
	}

	return 1;
}


int trie_insert_binary(Trie *trie, unsigned char *key, int key_length,
                       TrieValue value)
{
	TrieNode **rover;
	TrieNode *node;
	int p,c;

	/* Cannot insert NULL values */

	if (value == TRIE_NULL) {
		return 0;
	}

	/* Search to see if this is already in the tree */

	node = trie_find_end_binary(trie, key, key_length);

	/* Already in the tree? If so, replace the existing value and
	 * return success. */

	if (node != NULL && node->data != TRIE_NULL) {
		node->data = value;
		return 1;
	}

	/* Search down the trie until we reach the end of string,
	 * creating nodes as necessary */

	rover = &trie->root_node;
	p = 0;

	for (;;) {

		node = *rover;

		if (node == NULL) {

			/* Node does not exist, so create it */

			node = (TrieNode *) calloc(1, sizeof(TrieNode));

			if (node == NULL) {

				/* Allocation failed.  Go back and undo
				 * what we have done so far. */

				trie_insert_rollback(trie, key);

				return 0;
			}

			node->data = TRIE_NULL;

			/* Link in to the trie */

			*rover = node;
		}

		/* Increase the node use count */

		++node->use_count;

		/* Current character */

		c = (unsigned char) key[p];

		/* Reached the end of string?  If so, we're finished. */

		if (p == key_length) {

			/* Set the data at the node we have reached */

			node->data = value;

			break;
		}

		/* Advance to the next node in the chain */

		rover = &node->next[c];
		++p;
	}

	return 1;
}

int trie_remove_binary(Trie *trie, unsigned char *key, int key_length)
{
	TrieNode *node;
	TrieNode *next;
	TrieNode **last_next_ptr;
	int p, c;

	/* Find the end node and remove the value */

	node = trie_find_end_binary(trie, key, key_length);

	if (node != NULL && node->data != TRIE_NULL) {
		node->data = TRIE_NULL;
	} else {
		return 0;
	}

	/* Now traverse the tree again as before, decrementing the use
	 * count of each node.  Free back nodes as necessary. */

	node = trie->root_node;
	last_next_ptr = &trie->root_node;
	p = 0;

	for (;;) {

		/* Find the next node */
		c = (unsigned char) key[p];
		next = node->next[c];

		/* Free this node if necessary */

		--node->use_count;

		if (node->use_count <= 0) {
			free(node);

			/* Set the "next" pointer on the previous node to NULL,
			 * to unlink the freed node from the tree.  This only
			 * needs to be done once in a remove.  After the first
			 * unlink, all further nodes are also going to be
			 * free'd. */

			if (last_next_ptr != NULL) {
				*last_next_ptr = NULL;
				last_next_ptr = NULL;
			}
		}

		/* Go to the next character or finish */
		if (p == key_length) {
			break;
		} else {
			++p;
		}

		/* If necessary, save the location of the "next" pointer
		 * so that it may be set to NULL on the next iteration if
		 * the next node visited is freed. */

		if (last_next_ptr != NULL) {
			last_next_ptr = &node->next[c];
		}

		/* Jump to the next node */

		node = next;
	}

	/* Removed successfully */

	return 1;
}

int trie_remove(Trie *trie, char *key)
{
	TrieNode *node;
	TrieNode *next;
	TrieNode **last_next_ptr;
	char *p;
	int c;

	/* Find the end node and remove the value */

	node = trie_find_end(trie, key);

	if (node != NULL && node->data != TRIE_NULL) {
		node->data = TRIE_NULL;
	} else {
		return 0;
	}

	/* Now traverse the tree again as before, decrementing the use
	 * count of each node.  Free back nodes as necessary. */

	node = trie->root_node;
	last_next_ptr = &trie->root_node;
	p = key;

	for (;;) {

		/* Find the next node */

		c = (unsigned char) *p;
		next = node->next[c];

		/* Free this node if necessary */

		--node->use_count;

		if (node->use_count <= 0) {
			free(node);

			/* Set the "next" pointer on the previous node to NULL,
			 * to unlink the freed node from the tree.  This only
			 * needs to be done once in a remove.  After the first
			 * unlink, all further nodes are also going to be
			 * free'd. */

			if (last_next_ptr != NULL) {
				*last_next_ptr = NULL;
				last_next_ptr = NULL;
			}
		}

		/* Go to the next character or finish */

		if (c == '\0') {
			break;
		} else {
			++p;
		}

		/* If necessary, save the location of the "next" pointer
		 * so that it may be set to NULL on the next iteration if
		 * the next node visited is freed. */

		if (last_next_ptr != NULL) {
			last_next_ptr = &node->next[c];
		}

		/* Jump to the next node */

		node = next;
	}

	/* Removed successfully */

	return 1;
}

TrieValue trie_lookup(Trie *trie, char *key)
{
	TrieNode *node;

	node = trie_find_end(trie, key);

	if (node != NULL) {
		return node->data;
	} else {
		return TRIE_NULL;
	}
}

TrieValue trie_lookup_binary(Trie *trie, unsigned char *key, int key_length)
{
	TrieNode *node;

	node = trie_find_end_binary(trie, key, key_length);

	if (node != NULL) {
		return node->data;
	} else {
		return TRIE_NULL;
	}
}

unsigned int trie_num_entries(Trie *trie)
{
	/* To find the number of entries, simply look at the use count
	 * of the root node. */

	if (trie->root_node == NULL) {
		return 0;
	} else {
		return trie->root_node->use_count;
	}
}

