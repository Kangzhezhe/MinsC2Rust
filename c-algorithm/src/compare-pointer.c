// 识别到的包含指令
#include "compare-pointer.h"

// 识别到的函数定义
// 函数: pointer_equal (line 25)
int pointer_equal(void *location1, void *location2)
{
	return location1 == location2;
}

// 函数: pointer_compare (line 30)
int pointer_compare(void *location1, void *location2)
{
	if (location1 < location2) {
		return -1;
	} else if (location1 > location2) {
		return 1;
	} else {
		return 0;
	}
}
