// 识别到的包含指令
#include <stdint.h>
#include <stdio.h>

// 识别到的宏定义
#define __UTF8_DFA_DECODER_H
#define UTF8_ACCEPT 0
#define UTF8_REJECT 1

// 识别到的函数定义
// 函数: decode_utf8 (line 32)
static uint32_t inline decode_utf8(uint32_t *state, uint32_t *codepoint,
                                   uint8_t byte) {
  uint32_t type = utf8d[byte];
  *codepoint = (*state != UTF8_ACCEPT) ? (byte & 0x3fu) | (*codepoint << 6)
                                       : (0xff >> type) & (byte);
  *state = utf8d[256 + *state * 16 + type];
  return *state;
}
