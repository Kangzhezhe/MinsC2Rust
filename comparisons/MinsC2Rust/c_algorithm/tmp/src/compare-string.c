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

#include <ctype.h>
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


/* Comparison functions for strings */

int string_equal(void *string1, void *string2)
{
	return strcmp((char *) string1, (char *) string2) == 0;
}

int string_compare(void *string1, void *string2)
{
	int result;

	result = strcmp((char *) string1, (char *) string2);

	if (result < 0) {
		return -1;
	} else if (result > 0) {
		return 1;
	} else {
		return 0;
	}
}

/* Comparison functions for strings, which ignore the case of letters. */

int string_nocase_equal(void *string1, void *string2)
{
	return string_nocase_compare((char *) string1, (char *) string2) == 0;
}

/* On many systems, strcasecmp or stricmp will give the same functionality
 * as this function.  However, it is non-standard and cannot be relied
 * on to be present. */

int string_nocase_compare(void *string1, void *string2)
{
	char *p1;
	char *p2;
	int c1, c2;

	/* Iterate over each character in the strings */

	p1 = (char *) string1;
	p2 = (char *) string2;

	for (;;) {

		c1 = tolower(*p1);
		c2 = tolower(*p2);

		if (c1 != c2) {

			/* Strings are different */

			if (c1 < c2) {
				return -1;
			} else {
				return 1;
			}
		}

		/* End of string */

		if (c1 == '\0')
			break;

		/* Advance to the next character */

		++p1;
		++p2;
	}

	/* Reached the end of string and no difference found */

	return 0;
}


