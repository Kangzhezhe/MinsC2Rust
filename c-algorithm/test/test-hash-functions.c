// 识别到的包含指令
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "alloc-testing.h"
#include "framework.h"
#include "hash-pointer.h"
#include "hash-int.h"
#include "hash-string.h"

// 识别到的全局变量
_Atomic size_t num_assert = 0;

// 识别到的宏定义
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */
#define NUM_TEST_VALUES 200

// 识别到的函数定义
// 函数: test_pointer_hash (line 46)
void test_pointer_hash(void)
{
	int array[NUM_TEST_VALUES];
	int i, j;

	/* Initialise the array to all zeros */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		array[i] = 0;
	}

	/* Check hashes are never the same */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		for (j=i+1; j<NUM_TEST_VALUES; ++j) {
			assert(pointer_hash(&array[i])
			       != pointer_hash(&array[j]));
		}
	}
}

// 函数: test_int_hash (line 67)
void test_int_hash(void)
{
	int array[NUM_TEST_VALUES];
	int i, j;

	/* Initialise all entries in the array */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		array[i] = i;
	}

	/* Check hashes are never the same */

	for (i=0; i<NUM_TEST_VALUES; ++i) {
		for (j=i+1; j<NUM_TEST_VALUES; ++j) {
			assert(int_hash(&array[i]) != int_hash(&array[j]));
		}
	}

	/* Hashes of two variables containing the same value are the same */

	i = 5000;
	j = 5000;

	assert(int_hash(&i) == int_hash(&j));
}

// 函数: test_string_hash (line 94)
void test_string_hash(void)
{
	char test1[] = "this is a test";
	char test2[] = "this is a tesu";
	char test3[] = "this is a test ";
	char test4[] = "this is a test";
	char test5[] = "This is a test";

	/* Contents affect the hash */

	assert(string_hash(test1) != string_hash(test2));

	/* Length affects the hash */

	assert(string_hash(test1) != string_hash(test3));

	/* Case sensitive */

	assert(string_hash(test1) != string_hash(test5));

	/* The same strings give the same hash */

	assert(string_hash(test1) == string_hash(test4));
}

// 函数: test_string_nocase_hash (line 119)
void test_string_nocase_hash(void)
{
	char test1[] = "this is a test";
	char test2[] = "this is a tesu";
	char test3[] = "this is a test ";
	char test4[] = "this is a test";
	char test5[] = "This is a test";

	/* Contents affect the hash */

	assert(string_nocase_hash(test1) != string_nocase_hash(test2));

	/* Length affects the hash */

	assert(string_nocase_hash(test1) != string_nocase_hash(test3));

	/* Case insensitive */

	assert(string_nocase_hash(test1) == string_nocase_hash(test5));

	/* The same strings give the same hash */

	assert(string_nocase_hash(test1) == string_nocase_hash(test4));
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_pointer_hash,
	test_int_hash,
	test_string_hash,
	test_string_nocase_hash,
	NULL
};

// 识别到的函数定义
// 函数: main (line 152)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
