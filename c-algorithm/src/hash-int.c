// 识别到的包含指令
#include "hash-int.h"

// 识别到的函数定义
// 函数: int_hash (line 25)
unsigned int int_hash(void *vlocation)
{
	int *location;

	location = (int *) vlocation;

	return (unsigned int) *location;
}
