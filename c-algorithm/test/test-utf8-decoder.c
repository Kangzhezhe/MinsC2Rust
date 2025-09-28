// 识别到的包含指令
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "alloc-testing.h"
#include "framework.h"
#include "utf8-decoder.h"

// 识别到的全局变量
_Atomic size_t num_assert = 0;

// 识别到的宏定义
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */

// 识别到的函数定义
// 函数: test_decode_chinese (line 23)
void test_decode_chinese() {
  const char *s = "成为更健康、更长久的世界一流企业";
  uint32_t res[64] = {};
  uint32_t codepoint;
  size_t count = 0;
  uint32_t state = 0;
  for (; *s; ++s) {
    if (!decode_utf8(&state, &codepoint, *s))
      res[count++] = codepoint;
  }
  assert(state == UTF8_ACCEPT);
  assert(count == 16);
  assert(res[1] == 0x4e3a);
  assert(res[2] == 0x66f4);
  assert(res[4] == 0x5eb7);
  assert(res[8] == 0x4e45);
}

static UnitTestFunction tests[

// 识别到的全局变量
= {
    test_decode_chinese,
    NULL,
};

int main(int argc, char *argv[

// 识别到的函数定义
// 函数:  run (line 46)
 {
  run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
  return 0;
}

