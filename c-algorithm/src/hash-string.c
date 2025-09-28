// 识别到的包含指令
#include <ctype.h>
#include "hash-string.h"

// 识别到的函数定义
// 函数: string_hash (line 27)
unsigned int string_hash(void *string)
{
	/* This is the djb2 string hash function */

	unsigned int result = 5381;
	unsigned char *p;

	p = (unsigned char *) string;

	while (*p != '\0') {
		result = (result << 5) + result + *p;
		++p;
	}

	return result;
}

// 函数: string_nocase_hash (line 47)
unsigned int string_nocase_hash(void *string)
{
	unsigned int result = 5381;
	unsigned char *p;

	p = (unsigned char *) string;

	while (*p != '\0') {
		result = (result << 5) + result + (unsigned int) tolower(*p);
		++p;
	}

	return result;
}
