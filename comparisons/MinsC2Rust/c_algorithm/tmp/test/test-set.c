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
 * @file set.h
 *
 * @brief Set of values.
 *
 * A set stores a collection of values.  Each value can only exist once in
 * the set.
 *
 * To create a new set, use @ref set_new.  To destroy a set, use
 * @ref set_free.
 *
 * To add a value to a set, use @ref set_insert.  To remove a value
 * from a set, use @ref set_remove.
 *
 * To find the number of entries in a set, use @ref set_num_entries.
 *
 * To query if a particular value is in a set, use @ref set_query.
 *
 * To iterate over all values in a set, use @ref set_iterate to initialise
 * a @ref SetIterator structure, with @ref set_iter_next and
 * @ref set_iter_has_more to read each value in turn.
 *
 * Two sets can be combined (union) using @ref set_union, while the
 * intersection of two sets can be generated using @ref set_intersection.
 */

#ifndef ALGORITHM_SET_H
#define ALGORITHM_SET_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Represents a set of values.  Created using the @ref set_new function and
 * destroyed using the @ref set_free function.
 */

typedef struct _Set Set;

/**
 * An object used to iterate over a set.
 *
 * @see set_iterate
 */

typedef struct _SetIterator SetIterator;

/**
 * Internal structure representing an entry in the set.
 */

typedef struct _SetEntry SetEntry;

/**
 * A value stored in a @ref Set.
 */

typedef void *SetValue;

/**
 * Definition of a @ref SetIterator.
 */

struct _SetIterator {
	Set *set;
	SetEntry *next_entry;
	unsigned int next_chain;
};

/**
 * A null @ref SetValue.
 */

#define SET_NULL ((void *) 0)

/**
 * Hash function.  Generates a hash key for values to be stored in a set.
 */

typedef unsigned int (*SetHashFunc)(SetValue value);

/**
 * Equality function.  Compares two values to determine if they are
 * equivalent.
 */

typedef int (*SetEqualFunc)(SetValue value1, SetValue value2);

/**
 * Function used to free values stored in a set.  See
 * @ref set_register_free_function.
 */

typedef void (*SetFreeFunc)(SetValue value);

/**
 * Create a new set.
 *
 * @param hash_func     Hash function used on values in the set.
 * @param equal_func    Compares two values in the set to determine
 *                      if they are equal.
 * @return              A new set, or NULL if it was not possible to
 *                      allocate the memory for the set.
 */

Set *set_new(SetHashFunc hash_func, SetEqualFunc equal_func);

/**
 * Destroy a set.
 *
 * @param set           The set to destroy.
 */

void set_free(Set *set);

/**
 * Register a function to be called when values are removed from
 * the set.
 *
 * @param set           The set.
 * @param free_func     Function to call when values are removed from the
 *                      set.
 */

void set_register_free_function(Set *set, SetFreeFunc free_func);

/**
 * Add a value to a set.
 *
 * @param set           The set.
 * @param data          The value to add to the set.
 * @return              Non-zero (true) if the value was added to the set,
 *                      zero (false) if it already exists in the set, or
 *                      if it was not possible to allocate memory for the
 *                      new entry.
 */

int set_insert(Set *set, SetValue data);

/**
 * Remove a value from a set.
 *
 * @param set           The set.
 * @param data          The value to remove from the set.
 * @return              Non-zero (true) if the value was found and removed
 *                      from the set, zero (false) if the value was not
 *                      found in the set.
 */

int set_remove(Set *set, SetValue data);

/**
 * Query if a particular value is in a set.
 *
 * @param set           The set.
 * @param data          The value to query for.
 * @return              Zero if the value is not in the set, non-zero if the
 *                      value is in the set.
 */

int set_query(Set *set, SetValue data);

/**
 * Retrieve the number of entries in a set
 *
 * @param set           The set.
 * @return              A count of the number of entries in the set.
 */

unsigned int set_num_entries(Set *set);

/**
 * Create an array containing all entries in a set.
 *
 * @param set              The set.
 * @return                 An array containing all entries in the set,
 *                         or NULL if it was not possible to allocate
 *                         memory for the array.
 */

SetValue *set_to_array(Set *set);

/**
 * Perform a union of two sets.
 *
 * @param set1             The first set.
 * @param set2             The second set.
 * @return                 A new set containing all values which are in the
 *                         first or second sets, or NULL if it was not
 *                         possible to allocate memory for the new set.
 */

Set *set_union(Set *set1, Set *set2);

/**
 * Perform an intersection of two sets.
 *
 * @param set1             The first set.
 * @param set2             The second set.
 * @return                 A new set containing all values which are in both
 *                         set, or NULL if it was not possible to allocate
 *                         memory for the new set.
 */

Set *set_intersection(Set *set1, Set *set2);

/**
 * Initialise a @ref SetIterator structure to iterate over the values
 * in a set.
 *
 * @param set              The set to iterate over.
 * @param iter             Pointer to an iterator structure to initialise.
 */

void set_iterate(Set *set, SetIterator *iter);

/**
 * Determine if there are more values in the set to iterate over.
 *
 * @param iterator         The set iterator object.
 * @return                 Zero if there are no more values in the set
 *                         to iterate over, non-zero if there are more
 *                         values to be read.
 */

int set_iter_has_more(SetIterator *iterator);

/**
 * Using a set iterator, retrieve the next value from the set.
 *
 * @param iterator         The set iterator.
 * @return                 The next value from the set, or @ref SET_NULL if no
 *                         more values are available.
 */

SetValue set_iter_next(SetIterator *iterator);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef ALGORITHM_SET_H */

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


int allocated_values;

Set *generate_set(void)
{
	Set *set;
	char buf[10];
	unsigned int i;
	char *value;

	set = set_new(string_hash, string_equal);

	/* Add 10,000 items sequentially, checking that the counter
	 * works properly */

	for (i=0; i<10000; ++i) {
		sprintf(buf, "%i", i);
		value = strdup(buf);

		set_insert(set, value);

		assert(set_num_entries(set) == i + 1);
	}

	set_register_free_function(set, free);

	return set;
}

void test_set_new_free(void)
{
	Set *set;
	int i;
	int *value;

	set = set_new(int_hash, int_equal);

	set_register_free_function(set, free);

	assert(set != NULL);

	/* Fill the set with many values before freeing */

	for (i=0; i<10000; ++i) {
		value = (int *) malloc(sizeof(int));

		*value = i;

		set_insert(set, value);
	}

	/* Free the set */

	set_free(set);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	set = set_new(int_hash, int_equal);
	assert(set == NULL);

	alloc_test_set_limit(1);
	set = set_new(int_hash, int_equal);
	assert(set == NULL);
	assert(alloc_test_get_allocated() == 0);
}

void test_set_insert(void)
{
	Set *set;
	int numbers1[] = { 1, 2, 3, 4, 5, 6 };
	int numbers2[] = { 5, 6, 7, 8, 9, 10 };
	int i;

	/* Perform a union of numbers1 and numbers2.  Cannot add the same
	 * value twice. */

	set = set_new(int_hash, int_equal);

	for (i=0; i<6; ++i) {
		set_insert(set, &numbers1[i]);
	}
	for (i=0; i<6; ++i) {
		set_insert(set, &numbers2[i]);
	}

	assert(set_num_entries(set) == 10);

	set_free(set);
}

void test_set_query(void)
{
	Set *set;
	char buf[10];
	int i;

	set = generate_set();

	/* Test all values */

	for (i=0; i<10000; ++i) {
		sprintf(buf, "%i", i);
		assert(set_query(set, buf) != 0);
	}

	/* Test invalid values returning zero */

	assert(set_query(set, "-1") == 0);
	assert(set_query(set, "100001") == 0);

	set_free(set);
}

void test_set_remove(void)
{
	Set *set;
	char buf[10];
	int i;
	unsigned int num_entries;

	set = generate_set();

	num_entries = set_num_entries(set);
	assert(num_entries == 10000);

	/* Remove some entries */

	for (i=4000; i<6000; ++i) {

		sprintf(buf, "%i", i);

		/* Check this is in the set */

		assert(set_query(set, buf) != 0);

		/* Remove it */

		assert(set_remove(set, buf) != 0);

		/* Check the number of entries decreases */

		assert(set_num_entries(set) == num_entries - 1);

		/* Check it is no longer in the set */

		assert(set_query(set, buf) == 0);

		--num_entries;
	}

	/* Try to remove some invalid entries */

	for (i=-1000; i<-500; ++i) {
		sprintf(buf, "%i", i);

		assert(set_remove(set, buf) == 0);
		assert(set_num_entries(set) == num_entries);
	}

	for (i=50000; i<51000; ++i) {
		sprintf(buf, "%i", i);

		assert(set_remove(set, buf) == 0);
		assert(set_num_entries(set) == num_entries);
	}

	set_free(set);
}

void test_set_union(void)
{
	int numbers1[] = {1, 2, 3, 4, 5, 6, 7};
	int numbers2[] = {5, 6, 7, 8, 9, 10, 11};
	int result[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11};
	int i;
	Set *set1;
	Set *set2;
	Set *result_set;
	size_t allocated;

	/* Create the first set */

	set1 = set_new(int_hash, int_equal);

	for (i=0; i<7; ++i) {
		set_insert(set1, &numbers1[i]);
	}

	/* Create the second set */

	set2 = set_new(int_hash, int_equal);

	for (i=0; i<7; ++i) {
		set_insert(set2, &numbers2[i]);
	}

	/* Perform the union */

	result_set = set_union(set1, set2);

	assert(set_num_entries(result_set) == 11);

	for (i=0; i<11; ++i) {
		assert(set_query(result_set, &result[i]) != 0);
	}

	set_free(result_set);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(set_union(set1, set2) == NULL);

	/* Can allocate set, can't copy all set1 values */

	alloc_test_set_limit(2 + 2);
	allocated = alloc_test_get_allocated();
	assert(set_union(set1, set2) == NULL);
	assert(alloc_test_get_allocated() == allocated);

	/* Can allocate set, can copy set1 values,
	 * can't copy all set2 values */

	alloc_test_set_limit(2 + 7 + 2);
	allocated = alloc_test_get_allocated();
	assert(set_union(set1, set2) == NULL);
	assert(alloc_test_get_allocated() == allocated);

	set_free(set1);
	set_free(set2);
}

void test_set_intersection(void)
{
	int numbers1[] = {1, 2, 3, 4, 5, 6, 7};
	int numbers2[] = {5, 6, 7, 8, 9, 10, 11};
	int result[] = {5, 6, 7};
	int i;
	Set *set1;
	Set *set2;
	Set *result_set;
	size_t allocated;

	/* Create the first set */

	set1 = set_new(int_hash, int_equal);

	for (i=0; i<7; ++i) {
		set_insert(set1, &numbers1[i]);
	}

	/* Create the second set */

	set2 = set_new(int_hash, int_equal);

	for (i=0; i<7; ++i) {
		set_insert(set2, &numbers2[i]);
	}

	/* Perform the intersection */

	result_set = set_intersection(set1, set2);

	assert(set_num_entries(result_set) == 3);

	for (i=0; i<3; ++i) {
		assert(set_query(result_set, &result[i]) != 0);
	}

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(set_intersection(set1, set2) == NULL);

	/* Can allocate set, can't copy all values */

	alloc_test_set_limit(2 + 2);
	allocated = alloc_test_get_allocated();
	assert(set_intersection(set1, set2) == NULL);
	assert(alloc_test_get_allocated() == allocated);

	set_free(set1);
	set_free(set2);
	set_free(result_set);
}

void test_set_to_array(void)
{
	Set *set;
	int values[100];
	int **array;
	int i;

	/* Create a set containing pointers to all entries in the "values"
	 * array. */

	set = set_new(pointer_hash, pointer_equal);

	for (i=0; i<100; ++i) {
		values[i] = 1;
		set_insert(set, &values[i]);
	}

	array = (int **) set_to_array(set);

	/* Check the array */

	for (i=0; i<100; ++i) {
		assert(*array[i] == 1);
		*array[i] = 0;
	}

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	assert(set_to_array(set) == NULL);

	free(array);
	set_free(set);
}

void test_set_iterating(void)
{
	Set *set;
	SetIterator iterator;
	int count;

	set = generate_set();

	/* Iterate over all values in the set */

	count = 0;
	set_iterate(set, &iterator);

	while (set_iter_has_more(&iterator)) {

		set_iter_next(&iterator);

		++count;
	}

	/* Test iter_next after iteration has completed. */

	assert(set_iter_next(&iterator) == NULL);

	/* Check final count */

	assert(count == 10000);

	set_free(set);

	/* Test iterating over an empty set */

	set = set_new(int_hash, int_equal);

	set_iterate(set, &iterator);

	assert(set_iter_has_more(&iterator) == 0);

	set_free(set);
}

/* Test the ability to remove the current value while iterating over
 * a set.  ie. the act of removing the current value should not affect
 * the iterator. */

void test_set_iterating_remove(void)
{
	Set *set;
	SetIterator iterator;
	int count;
	unsigned int removed;
	char *value;

	set = generate_set();

	count = 0;
	removed = 0;

	/* Iterate over all values in the set */

	set_iterate(set, &iterator);

	while (set_iter_has_more(&iterator)) {

		value = set_iter_next(&iterator);

		if ((atoi(value) % 100) == 0) {

			/* Remove this value */

			set_remove(set, value);

			++removed;
		}

		++count;
	}

	/* Check final counts */

	assert(count == 10000);
	assert(removed == 100);
	assert(set_num_entries(set) == 10000 - removed);

	set_free(set);
}

int *new_value(int value)
{
	int *result;

	result = malloc(sizeof(int));
	*result = value;

	++allocated_values;

	return result;
}

void free_value(void *value)
{
	free(value);

	--allocated_values;
}

void test_set_free_function(void)
{
	Set *set;
	int i;
	int *value;

	/* Create a set and fill it with 1000 values */

	set = set_new(int_hash, int_equal);

	set_register_free_function(set, free_value);

	allocated_values = 0;

	for (i=0; i<1000; ++i) {
		value = new_value(i);

		set_insert(set, value);
	}

	assert(allocated_values == 1000);

	/* Test removing a value */

	i = 500;
	set_remove(set, &i);

	assert(allocated_values == 999);

	/* Test freeing the set */

	set_free(set);

	assert(allocated_values == 0);
}

/* Test for out of memory scenario */

void test_set_out_of_memory(void)
{
	Set *set;
	int values[66];
	unsigned int i;

	set = set_new(int_hash, int_equal);

	/* Test normal failure */

	alloc_test_set_limit(0);
	values[0] = 0;
	assert(set_insert(set, &values[0]) == 0);
	assert(set_num_entries(set) == 0);

	alloc_test_set_limit(-1);

	/* Test failure when increasing table size.
	 * The initial table size is 193 entries.  The table increases in
	 * size when 1/3 full, so the 66th entry should cause the insert
	 * to fail. */

	for (i=0; i<65; ++i) {
		values[i] = (int) i;

		assert(set_insert(set, &values[i]) != 0);
		assert(set_num_entries(set) == i + 1);
	}

	assert(set_num_entries(set) == 65);

	/* Test the 66th insert */

	alloc_test_set_limit(0);

	values[65] = 65;

	assert(set_insert(set, &values[65]) == 0);
	assert(set_num_entries(set) == 65);

	set_free(set);
}


static UnitTestFunction tests[] = {
	test_set_new_free,
	test_set_insert,
	test_set_query,
	test_set_remove,
	test_set_intersection,
	test_set_union,
	test_set_iterating,
	test_set_iterating_remove,
	test_set_to_array,
	test_set_free_function,
	test_set_out_of_memory,
	NULL
};

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}

