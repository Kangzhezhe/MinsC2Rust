// 识别到的包含指令
#include <stdlib.h>
#include "queue.h"
#include "alloc-testing.h"

// 识别到的typedef定义
typedef struct _QueueEntry QueueEntry;

// 识别到的结构体定义
struct _QueueEntry {
	QueueValue data;
	QueueEntry *prev;
	QueueEntry *next;
};

struct _Queue {
	QueueEntry *head;
	QueueEntry *tail;
};

// 识别到的函数定义
// 函数: queue_new (line 46)
Queue *queue_new(void)
{
	Queue *queue;

	queue = (Queue *) malloc(sizeof(Queue));

	if (queue == NULL) {
		return NULL;
	}

	queue->head = NULL;
	queue->tail = NULL;

	return queue;
}

// 函数: queue_free (line 62)
void queue_free(Queue *queue)
{
	/* Empty the queue */

	while (!queue_is_empty(queue)) {
		queue_pop_head(queue);
	}

	/* Free back the queue */

	free(queue);
}

// 函数: queue_push_head (line 75)
int queue_push_head(Queue *queue, QueueValue data)
{
	QueueEntry *new_entry;

	/* Create the new entry and fill in the fields in the structure */

	new_entry = malloc(sizeof(QueueEntry));

	if (new_entry == NULL) {
		return 0;
	}

	new_entry->data = data;
	new_entry->prev = NULL;
	new_entry->next = queue->head;

	/* Insert into the queue */

	if (queue->head == NULL) {

		/* If the queue was previously empty, both the head and
		 * tail must be pointed at the new entry */

		queue->head = new_entry;
		queue->tail = new_entry;

	} else {

		/* First entry in the list must have prev pointed back to this
		 * new entry */

		queue->head->prev = new_entry;

		/* Only the head must be pointed at the new entry */

		queue->head = new_entry;
	}

	return 1;
}

// 函数: queue_pop_head (line 116)
QueueValue queue_pop_head(Queue *queue)
{
	QueueEntry *entry;
	QueueValue result;

	/* Check the queue is not empty */

	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	}

	/* Unlink the first entry from the head of the queue */

	entry = queue->head;
	queue->head = entry->next;
	result = entry->data;

	if (queue->head == NULL) {

		/* If doing this has unlinked the last entry in the queue, set
		 * tail to NULL as well. */

		queue->tail = NULL;
	} else {

		/* The new first in the queue has no previous entry */

		queue->head->prev = NULL;
	}

	/* Free back the queue entry structure */

	free(entry);

	return result;
}

// 函数: queue_peek_head (line 153)
QueueValue queue_peek_head(Queue *queue)
{
	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	} else {
		return queue->head->data;
	}
}

// 函数: queue_push_tail (line 162)
int queue_push_tail(Queue *queue, QueueValue data)
{
	QueueEntry *new_entry;

	/* Create the new entry and fill in the fields in the structure */

	new_entry = malloc(sizeof(QueueEntry));

	if (new_entry == NULL) {
		return 0;
	}

	new_entry->data = data;
	new_entry->prev = queue->tail;
	new_entry->next = NULL;

	/* Insert into the queue tail */

	if (queue->tail == NULL) {

		/* If the queue was previously empty, both the head and
		 * tail must be pointed at the new entry */

		queue->head = new_entry;
		queue->tail = new_entry;

	} else {

		/* The current entry at the tail must have next pointed to this
		 * new entry */

		queue->tail->next = new_entry;

		/* Only the tail must be pointed at the new entry */

		queue->tail = new_entry;
	}

	return 1;
}

// 函数: queue_pop_tail (line 203)
QueueValue queue_pop_tail(Queue *queue)
{
	QueueEntry *entry;
	QueueValue result;

	/* Check the queue is not empty */

	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	}

	/* Unlink the first entry from the tail of the queue */

	entry = queue->tail;
	queue->tail = entry->prev;
	result = entry->data;

	if (queue->tail == NULL) {

		/* If doing this has unlinked the last entry in the queue, set
		 * head to NULL as well. */

		queue->head = NULL;

	} else {

		/* The new entry at the tail has no next entry. */

		queue->tail->next = NULL;
	}

	/* Free back the queue entry structure */

	free(entry);

	return result;
}

// 函数: queue_peek_tail (line 241)
QueueValue queue_peek_tail(Queue *queue)
{
	if (queue_is_empty(queue)) {
		return QUEUE_NULL;
	} else {
		return queue->tail->data;
	}
}

// 函数: queue_is_empty (line 250)
int queue_is_empty(Queue *queue)
{
	return queue->head == NULL;
}
