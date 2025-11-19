cmake_minimum_required(VERSION 3.6)

project(heman)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
find_package(OpenMP)

include_directories(include .)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

set(HEMAN_SOURCE
    src/color.c
    src/distance.c
    src/draw.c
    src/export.c
    src/gaussian.c
    src/generate.c
    src/image.c
    src/image.h
    src/import.c
    src/lighting.c
    src/noise.c
    src/noise.h
    src/ops.c
    src/points.c)

set(MATH_SOURCE
    kazmath/aabb2.c
    kazmath/aabb3.c
    kazmath/mat3.c
    kazmath/mat4.c
    kazmath/plane.c
    kazmath/quaternion.c
    kazmath/ray2.c
    kazmath/ray3.c
    kazmath/utility.c
    kazmath/vec2.c
    kazmath/vec3.c
    kazmath/vec4.c)

add_library(heman STATIC ${HEMAN_SOURCE} ${MATH_SOURCE})
target_include_directories(heman PUBLIC include)
target_include_directories(heman PUBLIC kazmath)
target_include_directories(heman PUBLIC src)


if(OpenMP_CXX_FOUND)
    target_link_libraries(heman PUBLIC OpenMP::OpenMP_CXX)
elseif(APPLE)
    target_link_directories(heman PUBLIC /usr/local/lib)
    target_link_libraries(heman PUBLIC omp)
    target_include_directories(heman PUBLIC /usr/local/include)
endif()

if (APPLE)
    target_compile_options(heman PUBLIC -Xclang -fopenmp)
endif()

if (WIN32)
    target_compile_options(heman PUBLIC /openmp)
endif()

# 添加测试
enable_testing()


# 查找所有测试文件
file(GLOB TEST_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/test/*.c")

# 分离以test-开头和不以test-开头的文件
set(TEST_FILES "")
set(NON_TEST_FILES "")

foreach(TEST_SOURCE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME)
    if(TEST_NAME MATCHES "^test-")
        list(APPEND TEST_FILES ${TEST_SOURCE})
    else()
        list(APPEND NON_TEST_FILES ${TEST_SOURCE})
    endif()
endforeach()

message(STATUS "TEST_FILES: ${TEST_FILES}")
message(STATUS "NON_TEST_FILES: ${NON_TEST_FILES}")


# 为每个测试文件创建一个可执行文件并添加到测试中
foreach(TEST_FILE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_FILE} NAME_WE)
    add_executable(${TEST_NAME} ${TEST_FILE})
    target_link_libraries(${TEST_NAME} heman m OpenMP::OpenMP_CXX)
    target_include_directories(${TEST_NAME} PRIVATE include . test)
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
endforeach()