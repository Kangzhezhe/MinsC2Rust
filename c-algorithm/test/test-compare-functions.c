// 识别到的包含指令
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "alloc-testing.h"
#include "framework.h"

// 识别到的全局变量
_Atomic size_t num_assert = 0;

// 识别到的宏定义
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */

// 识别到的包含指令
#include "compare-int.h"
#include "compare-pointer.h"
#include "compare-string.h"

// 识别到的函数定义
// 函数: test_int_compare (line 45)
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

// 函数: test_int_equal (line 64)
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

// 函数: test_pointer_compare (line 79)
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

// 函数: test_pointer_equal (line 98)
void test_pointer_equal(void)
{
	int a, b;

	/* Non-zero (true) if the two pointers are equal */

	assert(pointer_equal(&a, &a) != 0);

	/* Zero (false) if the two pointers are not equal */

	assert(pointer_equal(&a, &b) == 0);
}

// 函数: test_string_compare (line 111)
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

// 函数: test_string_equal (line 130)
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

// 函数: test_string_nocase_compare (line 152)
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

// 函数: test_string_nocase_equal (line 179)
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

// 识别到的全局变量
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

// 识别到的函数定义
// 函数: main (line 213)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
