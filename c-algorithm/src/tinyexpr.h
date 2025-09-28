// 识别到的宏定义
#define TINYEXPR_H

// 识别到的typedef定义
typedef struct te_expr {
    int type;
    union {double value; const double *bound; const void *function;};
    void *parameters[1];
} te_expr;

// 识别到的枚举定义
enum {
    TE_VARIABLE = 0,

    TE_FUNCTION0 = 8, TE_FUNCTION1, TE_FUNCTION2, TE_FUNCTION3,
    TE_FUNCTION4, TE_FUNCTION5, TE_FUNCTION6, TE_FUNCTION7,

    TE_CLOSURE0 = 16, TE_CLOSURE1, TE_CLOSURE2, TE_CLOSURE3,
    TE_CLOSURE4, TE_CLOSURE5, TE_CLOSURE6, TE_CLOSURE7,

    TE_FLAG_PURE = 32
};

// 识别到的typedef定义
typedef struct te_variable {
    const char *name;
    const void *address;
    int type;
    void *context;
} te_variable;

// 识别到的函数定义
// 函数: te_interp (line 66)
double te_interp(const char *expression, int *error);

// 函数: te_compile (line 70)
te_expr *te_compile(const char *expression, const te_variable *variables, int var_count, int *error);

// 函数: te_eval (line 73)
double te_eval(const te_expr *n);

// 函数: te_print (line 76)
void te_print(const te_expr *n);

// 函数: te_free (line 80)
void te_free(te_expr *n);
