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
#include "bloom-filter.h"
#include "hash-string.h"

// 识别到的函数定义
// 函数: test_bloom_filter_new_free (line 42)
void test_bloom_filter_new_free(void)
{
	BloomFilter *filter;

	/* One salt */

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter != NULL);

	bloom_filter_free(filter);

	/* Maximum number of salts */

	filter = bloom_filter_new(128, string_hash, 64);

	assert(filter != NULL);

	bloom_filter_free(filter);

	/* Test creation with too many salts */

	filter = bloom_filter_new(128, string_hash, 50000);

	assert(filter == NULL);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter == NULL);

	alloc_test_set_limit(1);

	filter = bloom_filter_new(128, string_hash, 1);

	assert(filter == NULL);
}

// 函数: test_bloom_filter_insert_query (line 83)
void test_bloom_filter_insert_query(void)
{
	BloomFilter *filter;

	/* Create a filter */

	filter = bloom_filter_new(128, string_hash, 4);

	/* Check values are not present at the start */

	assert(bloom_filter_query(filter, "test 1") == 0);
	assert(bloom_filter_query(filter, "test 2") == 0);

	/* Insert some values */

	bloom_filter_insert(filter, "test 1");
	bloom_filter_insert(filter, "test 2");

	/* Check they are set */

	assert(bloom_filter_query(filter, "test 1") != 0);
	assert(bloom_filter_query(filter, "test 2") != 0);

	bloom_filter_free(filter);
}

// 函数: test_bloom_filter_read_load (line 109)
void test_bloom_filter_read_load(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	unsigned char state[16];

	/* Create a filter with some values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");
	bloom_filter_insert(filter1, "test 2");

	/* Read the current state into an array */

	bloom_filter_read(filter1, state);

	bloom_filter_free(filter1);

	/* Create a new filter and load the state */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_load(filter2, state);

	/* Check the values are set in the new filter */

	assert(bloom_filter_query(filter2, "test 1") != 0);
	assert(bloom_filter_query(filter2, "test 2") != 0);

	bloom_filter_free(filter2);
}

// 函数: test_bloom_filter_intersection (line 142)
void test_bloom_filter_intersection(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	BloomFilter *result;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");
	bloom_filter_insert(filter1, "test 2");

	/* Create second filter with only one value set */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter2, "test 1");

	/* For this test, we need this to be definitely not present.
	 * Note that this could theoretically return non-zero here,
	 * depending on the hash function. */

	assert(bloom_filter_query(filter2, "test 2") == 0);

	/* Intersection */

	result = bloom_filter_intersection(filter1, filter2);

	/* test 1 should be set, as it is in both
	 * test 2 should not be set, as it is not present in both */

	assert(bloom_filter_query(result, "test 1") != 0);
	assert(bloom_filter_query(result, "test 2") == 0);

	bloom_filter_free(result);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	result = bloom_filter_intersection(filter1, filter2);
	assert(result == NULL);

	bloom_filter_free(filter1);
	bloom_filter_free(filter2);
}

// 函数: test_bloom_filter_union (line 189)
void test_bloom_filter_union(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;
	BloomFilter *result;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter1, "test 1");

	/* Create second filter with only one value set */

	filter2 = bloom_filter_new(128, string_hash, 4);

	bloom_filter_insert(filter2, "test 2");

	/* Union */

	result = bloom_filter_union(filter1, filter2);

	/* Both should be present */

	assert(bloom_filter_query(result, "test 1") != 0);
	assert(bloom_filter_query(result, "test 2") != 0);

	bloom_filter_free(result);

	/* Test out of memory scenario */

	alloc_test_set_limit(0);
	result = bloom_filter_union(filter1, filter2);
	assert(result == NULL);

	bloom_filter_free(filter1);
	bloom_filter_free(filter2);
}

// 函数: test_bloom_filter_mismatch (line 230)
void test_bloom_filter_mismatch(void)
{
	BloomFilter *filter1;
	BloomFilter *filter2;

	/* Create one filter with both values set */

	filter1 = bloom_filter_new(128, string_hash, 4);

	/* Different buffer size. */

	filter2 = bloom_filter_new(64, string_hash, 4);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	/* Different hash function */

	filter2 = bloom_filter_new(128, string_nocase_hash, 4);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	/* Different number of salts */

	filter2 = bloom_filter_new(128, string_hash, 32);
	assert(bloom_filter_intersection(filter1, filter2) == NULL);
	assert(bloom_filter_union(filter1, filter2) == NULL);
	bloom_filter_free(filter2);

	bloom_filter_free(filter1);
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_bloom_filter_new_free,
	test_bloom_filter_insert_query,
	test_bloom_filter_read_load,
	test_bloom_filter_intersection,
	test_bloom_filter_union,
	test_bloom_filter_mismatch,
	NULL
};

// 识别到的函数定义
// 函数: main (line 273)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
