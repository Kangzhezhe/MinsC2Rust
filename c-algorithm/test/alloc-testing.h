// 识别到的宏定义
#define ALLOC_TESTING_H
#define malloc   alloc_test_malloc
#define free     alloc_test_free
#define realloc  alloc_test_realloc
#define calloc   alloc_test_calloc
#define strdup   alloc_test_strdup

// 识别到的函数定义
// 函数: alloc_test_malloc (line 60)
void *alloc_test_malloc(size_t bytes);

// 函数: alloc_test_free (line 68)
void alloc_test_free(void *ptr);

// 函数: alloc_test_realloc (line 80)
void *alloc_test_realloc(void *ptr, size_t bytes);

// 函数: alloc_test_calloc (line 93)
void *alloc_test_calloc(size_t nmemb, size_t bytes);

// 函数: alloc_test_strdup (line 104)
char *alloc_test_strdup(const char *string);

// 函数: alloc_test_set_limit (line 118)
void alloc_test_set_limit(signed int alloc_count);

// 函数: alloc_test_get_allocated (line 127)
size_t alloc_test_get_allocated(void);
