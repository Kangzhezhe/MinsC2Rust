#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ht.h"

void test_ht_create_and_destroy() {
    ht* table = ht_create();
    assert(table != NULL);
    assert(ht_length(table) == 0);
    ht_destroy(table);
}

void test_ht_set_and_get() {
    ht* table = ht_create();
    assert(table != NULL);

    // Insert a key-value pair
    int value1 = 42;
    const char* key1 = "key1";
    assert(ht_set(table, key1, &value1) != NULL);

    // Retrieve the value
    int* retrieved_value = (int*)ht_get(table, key1);
    assert(retrieved_value != NULL);
    assert(*retrieved_value == value1);

    // Insert another key-value pair
    int value2 = 84;
    const char* key2 = "key2";
    assert(ht_set(table, key2, &value2) != NULL);

    // Retrieve the second value
    retrieved_value = (int*)ht_get(table, key2);
    assert(retrieved_value != NULL);
    assert(*retrieved_value == value2);

    // Check the length of the hash table
    assert(ht_length(table) == 2);

    ht_destroy(table);
}

void test_ht_update_value() {
    ht* table = ht_create();
    assert(table != NULL);

    // Insert a key-value pair
    int value1 = 42;
    const char* key = "key";
    assert(ht_set(table, key, &value1) != NULL);

    // Update the value for the same key
    int value2 = 84;
    assert(ht_set(table, key, &value2) != NULL);

    // Retrieve the updated value
    int* retrieved_value = (int*)ht_get(table, key);
    assert(retrieved_value != NULL);
    assert(*retrieved_value == value2);

    // Check the length of the hash table (should still be 1)
    assert(ht_length(table) == 1);

    ht_destroy(table);
}

void test_ht_iterator() {
    ht* table = ht_create();
    assert(table != NULL);

    // Insert multiple key-value pairs
    int value1 = 1, value2 = 2, value3 = 3;
    assert(ht_set(table, "key1", &value1) != NULL);
    assert(ht_set(table, "key2", &value2) != NULL);
    assert(ht_set(table, "key3", &value3) != NULL);

    // Iterate through the hash table
    hti it = ht_iterator(table);
    int count = 0;
    while (ht_next(&it)) {
        assert(it.key != NULL);
        assert(it.value != NULL);
        count++;
    }

    // Ensure all items were iterated
    assert(count == 3);

    ht_destroy(table);
}

void test_ht_memory_management() {
    ht* table = ht_create();
    assert(table != NULL);

    // Dynamically allocate memory for values
    int* value1 = malloc(sizeof(int));
    int* value2 = malloc(sizeof(int));
    *value1 = 42;
    *value2 = 84;

    assert(ht_set(table, "key1", value1) != NULL);
    assert(ht_set(table, "key2", value2) != NULL);

    // Free values during iteration
    hti it = ht_iterator(table);
    while (ht_next(&it)) {
        free(it.value);
    }

    ht_destroy(table);
}

int main() {
    test_ht_create_and_destroy();
    test_ht_set_and_get();
    test_ht_update_value();
    test_ht_iterator();
    test_ht_memory_management();

    printf("All tests passed!\n");
    return 0;
}