cmake_minimum_required(VERSION 3.10)
project(duplicate_name_test C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(include)

file(GLOB MODULE_A_SOURCES "src/module_a/*.c")
file(GLOB MODULE_B_SOURCES "src/module_b/*.c")

add_executable(duplicate_name_test
    src/main.c
    ${MODULE_A_SOURCES}
    ${MODULE_B_SOURCES}
)
