// 识别到的宏定义
#define ALGORITHM_QUEUE_H

// 识别到的typedef定义
typedef struct _Queue Queue;
typedef void *QueueValue;

// 识别到的宏定义
#define QUEUE_NULL ((void *) 0)

// 识别到的函数定义
// 函数: queue_new (line 73)
Queue *queue_new(void);

// 函数: queue_free (line 81)
void queue_free(Queue *queue);

// 函数: queue_push_head (line 93)
int queue_push_head(Queue *queue, QueueValue data);

// 函数: queue_pop_head (line 103)
QueueValue queue_pop_head(Queue *queue);

// 函数: queue_peek_head (line 114)
QueueValue queue_peek_head(Queue *queue);

// 函数: queue_push_tail (line 126)
int queue_push_tail(Queue *queue, QueueValue data);

// 函数: queue_pop_tail (line 136)
QueueValue queue_pop_tail(Queue *queue);

// 函数: queue_peek_tail (line 147)
QueueValue queue_peek_tail(Queue *queue);

// 函数: queue_is_empty (line 157)
int queue_is_empty(Queue *queue);
