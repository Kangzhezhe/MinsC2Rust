cmake_minimum_required(VERSION 3.20.0)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
project(TranspileSource)
add_library(adt STATIC
  src/arraylist.c
  src/compare-int.c
)
target_include_directories(adt PRIVATE src test)
add_compile_definitions(ALLOC_TESTING)

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
add_adt_test(alloc-testing)
add_adt_test(arraylist)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/test/test-cpp.cpp")
  add_executable(test-cpp test/test-cpp.cpp test/framework.c test/alloc-testing.c)
  target_include_directories(test-cpp PRIVATE src test)
  target_link_libraries(test-cpp adt)
endif()
