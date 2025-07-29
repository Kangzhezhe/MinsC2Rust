cmake_minimum_required(VERSION 3.20.0)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
project(TranspileSource)
add_library(adt STATIC
  src/arraylist.c
  src/avl-tree.c
  src/binary-heap.c
  src/binomial-heap.c
  src/bloom-filter.c
  src/compare-int.c
  src/compare-pointer.c
  src/compare-string.c
  src/hash-int.c
  src/hash-pointer.c
  src/hash-string.c
  src/hash-table.c
  src/list.c
  src/queue.c
  src/rb-tree.c
  src/set.c
  src/slist.c
  src/sortedarray.c
  src/trie.c
  src/tinyexpr.c
   src/utf8-decoder.c
)
target_include_directories(adt PRIVATE src test)
# add_compile_definitions(ALLOC_TESTING)

function(add_adt_test suffix)
  add_executable(test-${suffix} test/test-${suffix}.c test/framework.c test/alloc-testing.c)
  target_include_directories(test-${suffix} PRIVATE src test)
  target_link_libraries(test-${suffix} adt)
  add_test(
    NAME test-${suffix}
    COMMAND test-${suffix}
  )
endfunction()

enable_testing()
add_adt_test(utf8-decoder)
add_adt_test(alloc-testing)
add_adt_test(arraylist)
add_adt_test(avl-tree)
add_adt_test(binary-heap)
add_adt_test(binomial-heap)
add_adt_test(bloom-filter)
add_adt_test(compare-functions)
add_adt_test(hash-functions)
add_adt_test(hash-table)
add_adt_test(list)
add_adt_test(queue)
add_adt_test(rb-tree)
add_adt_test(set)
add_adt_test(slist)
add_adt_test(sortedarray)
add_adt_test(trie)
add_adt_test(tinyexpr)
add_executable(test-cpp test/test-cpp.cpp test/framework.c test/alloc-testing.c)
target_include_directories(test-cpp PRIVATE src test)
target_link_libraries(test-cpp adt)
target_link_libraries(test-tinyexpr m)
add_test(
  NAME test-cpp
  COMMAND test-cpp
)
