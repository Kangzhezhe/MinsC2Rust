// 识别到的包含指令
#include <limits.h>
#include "hash-pointer.h"

// 识别到的函数定义
// 函数: pointer_hash (line 27)
unsigned int pointer_hash(void *location)
{
	return (unsigned int) (unsigned long) location;
}
