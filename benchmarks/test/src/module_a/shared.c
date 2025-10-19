#include "common.h"

int module_b_value = 20;

int module_a_value(void) {
    return 42;
}

int main() {
    return module_a_value() + module_b_value;
}