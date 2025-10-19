#include <stdio.h>
#include "common.h"

int main(void) {
    int value_a = module_a_value();
    int value_b = module_b_value();
    int result = value_a - value_b;
    printf("Result: %d\n", result);
    return result == 18 ? 0 : 1;
}
