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
#include "queue.h"

// 识别到的全局变量
int variable1, variable2, variable3, variable4;

// 识别到的函数定义
// 函数: generate_queue (line 43)
Queue *generate_queue(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
		queue_push_head(queue, &variable2);
		queue_push_head(queue, &variable3);
		queue_push_head(queue, &variable4);
	}

	return queue;
}

// 函数: test_queue_new_free (line 64)
void test_queue_new_free(void)
{
	int i;
	Queue *queue;

	/* Create and destroy a queue */

	queue = queue_new();

	queue_free(queue);

	/* Add lots of values and then destroy */

	queue = queue_new();

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
	}

	queue_free(queue);

	/* Test allocation when there is no free memory */

	alloc_test_set_limit(0);
	queue = queue_new();
	assert(queue == NULL);
}

// 函数: test_queue_push_head (line 92)
void test_queue_push_head(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_head(queue, &variable1);
		queue_push_head(queue, &variable2);
		queue_push_head(queue, &variable3);
		queue_push_head(queue, &variable4);
	}

	assert(!queue_is_empty(queue));

	/* Check values come out of the tail properly */

	assert(queue_pop_tail(queue) == &variable1);
	assert(queue_pop_tail(queue) == &variable2);
	assert(queue_pop_tail(queue) == &variable3);
	assert(queue_pop_tail(queue) == &variable4);

	/* Check values come back out of the head properly */

	assert(queue_pop_head(queue) == &variable4);
	assert(queue_pop_head(queue) == &variable3);
	assert(queue_pop_head(queue) == &variable2);
	assert(queue_pop_head(queue) == &variable1);

	queue_free(queue);

	/* Test behavior when running out of memory. */

	queue = queue_new();

	alloc_test_set_limit(0);
	assert(!queue_push_head(queue, &variable1));

	queue_free(queue);
}

// 函数: test_queue_pop_head (line 136)
void test_queue_pop_head(void)
{
	Queue *queue;

	/* Check popping off an empty queue */

	queue = queue_new();

	assert(queue_pop_head(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_pop_head(queue) == &variable4);
		assert(queue_pop_head(queue) == &variable3);
		assert(queue_pop_head(queue) == &variable2);
		assert(queue_pop_head(queue) == &variable1);
	}

	assert(queue_pop_head(queue) == NULL);

	queue_free(queue);
}

// 函数: test_queue_peek_head (line 164)
void test_queue_peek_head(void)
{
	Queue *queue;

	/* Check peeking into an empty queue */

	queue = queue_new();

	assert(queue_peek_head(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue, making sure that peek
	 * has the correct value beforehand */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_peek_head(queue) == &variable4);
		assert(queue_pop_head(queue) == &variable4);
		assert(queue_peek_head(queue) == &variable3);
		assert(queue_pop_head(queue) == &variable3);
		assert(queue_peek_head(queue) == &variable2);
		assert(queue_pop_head(queue) == &variable2);
		assert(queue_peek_head(queue) == &variable1);
		assert(queue_pop_head(queue) == &variable1);
	}

	assert(queue_peek_head(queue) == NULL);

	queue_free(queue);
}

// 函数: test_queue_push_tail (line 197)
void test_queue_push_tail(void)
{
	Queue *queue;
	int i;

	queue = queue_new();

	/* Add some values */

	for (i=0; i<1000; ++i) {
		queue_push_tail(queue, &variable1);
		queue_push_tail(queue, &variable2);
		queue_push_tail(queue, &variable3);
		queue_push_tail(queue, &variable4);
	}

	assert(!queue_is_empty(queue));

	/* Check values come out of the head properly */

	assert(queue_pop_head(queue) == &variable1);
	assert(queue_pop_head(queue) == &variable2);
	assert(queue_pop_head(queue) == &variable3);
	assert(queue_pop_head(queue) == &variable4);

	/* Check values come back out of the tail properly */

	assert(queue_pop_tail(queue) == &variable4);
	assert(queue_pop_tail(queue) == &variable3);
	assert(queue_pop_tail(queue) == &variable2);
	assert(queue_pop_tail(queue) == &variable1);

	queue_free(queue);

	/* Test behavior when running out of memory. */

	queue = queue_new();

	alloc_test_set_limit(0);
	assert(!queue_push_tail(queue, &variable1));

	queue_free(queue);
}

// 函数: test_queue_pop_tail (line 241)
void test_queue_pop_tail(void)
{
	Queue *queue;

	/* Check popping off an empty queue */

	queue = queue_new();

	assert(queue_pop_tail(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_pop_tail(queue) == &variable1);
		assert(queue_pop_tail(queue) == &variable2);
		assert(queue_pop_tail(queue) == &variable3);
		assert(queue_pop_tail(queue) == &variable4);
	}

	assert(queue_pop_tail(queue) == NULL);

	queue_free(queue);
}

// 函数: test_queue_peek_tail (line 269)
void test_queue_peek_tail(void)
{
	Queue *queue;

	/* Check peeking into an empty queue */

	queue = queue_new();

	assert(queue_peek_tail(queue) == NULL);

	queue_free(queue);

	/* Pop off all the values from the queue, making sure that peek
	 * has the correct value beforehand */

	queue = generate_queue();

	while (!queue_is_empty(queue)) {
		assert(queue_peek_tail(queue) == &variable1);
		assert(queue_pop_tail(queue) == &variable1);
		assert(queue_peek_tail(queue) == &variable2);
		assert(queue_pop_tail(queue) == &variable2);
		assert(queue_peek_tail(queue) == &variable3);
		assert(queue_pop_tail(queue) == &variable3);
		assert(queue_peek_tail(queue) == &variable4);
		assert(queue_pop_tail(queue) == &variable4);
	}

	assert(queue_peek_tail(queue) == NULL);

	queue_free(queue);
}

// 函数: test_queue_is_empty (line 302)
void test_queue_is_empty(void)
{
	Queue *queue;

	queue = queue_new();

	assert(queue_is_empty(queue));

	queue_push_head(queue, &variable1);

	assert(!queue_is_empty(queue));

	queue_pop_head(queue);

	assert(queue_is_empty(queue));

	queue_push_tail(queue, &variable1);

	assert(!queue_is_empty(queue));

	queue_pop_tail(queue);

	assert(queue_is_empty(queue));

	queue_free(queue);
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_queue_new_free,
	test_queue_push_head,
	test_queue_pop_head,
	test_queue_peek_head,
	test_queue_push_tail,
	test_queue_pop_tail,
	test_queue_peek_tail,
	test_queue_is_empty,
	NULL
};

// 识别到的函数定义
// 函数: main (line 341)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
