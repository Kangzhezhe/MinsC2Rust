// 识别到的宏定义
#define ALGORITHM_HASH_TABLE_H

// 识别到的typedef定义
typedef struct _HashTable HashTable;
typedef struct _HashTableIterator HashTableIterator;
typedef struct _HashTableEntry HashTableEntry;
typedef void *HashTableKey;
typedef void *HashTableValue;
typedef struct _HashTablePair{
	HashTableKey key;
	HashTableValue value;
} HashTablePair;

// 识别到的结构体定义
struct _HashTableIterator {
	HashTable *hash_table;
	HashTableEntry *next_entry;
	unsigned int next_chain;
};

// 识别到的宏定义
#define HASH_TABLE_NULL ((void *) 0)

// 识别到的typedef定义
typedef unsigned int (*HashTableHashFunc)(HashTableKey value);
typedef int (*HashTableEqualFunc)(HashTableKey value1, HashTableKey value2);
typedef void (*HashTableKeyFreeFunc)(HashTableKey value);
typedef void (*HashTableValueFreeFunc)(HashTableValue value);

// 识别到的函数定义
// 函数: hash_table_new (line 153)
HashTable *hash_table_new(HashTableHashFunc hash_func,
                          HashTableEqualFunc equal_func);

// 函数: hash_table_free (line 162)
void hash_table_free(HashTable *hash_table);

// 函数: hash_table_register_free_functions (line 173)
void hash_table_register_free_functions(HashTable *hash_table,
                                        HashTableKeyFreeFunc key_free_func,
                                        HashTableValueFreeFunc value_free_func);

// 函数: hash_table_insert (line 189)
int hash_table_insert(HashTable *hash_table,
                      HashTableKey key,
                      HashTableValue value);

// 函数: hash_table_lookup (line 202)
HashTableValue hash_table_lookup(HashTable *hash_table,
                                 HashTableKey key);

// 函数: hash_table_remove (line 214)
int hash_table_remove(HashTable *hash_table, HashTableKey key);

// 函数: hash_table_num_entries (line 223)
unsigned int hash_table_num_entries(HashTable *hash_table);

// 函数: hash_table_iterate (line 233)
void hash_table_iterate(HashTable *hash_table, HashTableIterator *iter);

// 函数: hash_table_iter_has_more (line 245)
int hash_table_iter_has_more(HashTableIterator *iterator);

// 函数: hash_table_iter_next (line 262)
HashTablePair hash_table_iter_next(HashTableIterator *iterator);
