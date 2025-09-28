// 识别到的宏定义
#define ALGORITHM_BLOOM_FILTER_H

// 识别到的typedef定义
typedef struct _BloomFilter BloomFilter;
typedef void *BloomFilterValue;
typedef unsigned int (*BloomFilterHashFunc)(BloomFilterValue data);

// 识别到的函数定义
// 函数: bloom_filter_new (line 89)
BloomFilter *bloom_filter_new(unsigned int table_size,
                              BloomFilterHashFunc hash_func,
                              unsigned int num_functions);

// 函数: bloom_filter_free (line 99)
void bloom_filter_free(BloomFilter *bloomfilter);

// 函数: bloom_filter_insert (line 108)
void bloom_filter_insert(BloomFilter *bloomfilter, BloomFilterValue value);

// 函数: bloom_filter_query (line 121)
int bloom_filter_query(BloomFilter *bloomfilter, BloomFilterValue value);

// 函数: bloom_filter_read (line 132)
void bloom_filter_read(BloomFilter *bloomfilter, unsigned char *array);

// 函数: bloom_filter_load (line 146)
void bloom_filter_load(BloomFilter *bloomfilter, unsigned char *array);

// 函数: bloom_filter_union (line 165)
BloomFilter *bloom_filter_union(BloomFilter *filter1,
                                BloomFilter *filter2);

// 函数: bloom_filter_intersection (line 185)
BloomFilter *bloom_filter_intersection(BloomFilter *filter1,
                                       BloomFilter *filter2);
