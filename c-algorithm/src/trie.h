// 识别到的宏定义
#define ALGORITHM_TRIE_H

// 识别到的typedef定义
typedef struct _Trie Trie;
typedef void *TrieValue;

// 识别到的宏定义
#define TRIE_NULL ((void *) 0)

// 识别到的函数定义
// 函数: trie_new (line 73)
Trie *trie_new(void);

// 函数: trie_free (line 81)
void trie_free(Trie *trie);

// 函数: trie_insert (line 95)
int trie_insert(Trie *trie, char *key, TrieValue value);

// 函数: trie_insert_binary (line 110)
int trie_insert_binary(Trie *trie, unsigned char *key,
                       int key_length, TrieValue value);

// 函数: trie_lookup (line 124)
TrieValue trie_lookup(Trie *trie, char *key);

// 函数: trie_lookup_binary (line 138)
TrieValue trie_lookup_binary(Trie *trie, unsigned char *key, int key_length);

// 函数: trie_remove (line 151)
int trie_remove(Trie *trie, char *key);

// 函数: trie_remove_binary (line 165)
int trie_remove_binary(Trie *trie, unsigned char *key, int key_length);

// 函数: trie_num_entries (line 174)
unsigned int trie_num_entries(Trie *trie);
