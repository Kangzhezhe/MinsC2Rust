// 识别到的包含指令
#include "tinyexpr.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include "alloc-testing.h"
#include "framework.h"

// 识别到的全局变量
_Atomic size_t num_assert = 0;

// 识别到的宏定义
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */
#define LTEST_FLOAT_TOLERANCE 0.001
#define assert_float_equal(a, b) do {\
    const double __LF_COMPARE = fabs((double)(a)-(double)(b));\
    if (__LF_COMPARE > LTEST_FLOAT_TOLERANCE || (__LF_COMPARE != __LF_COMPARE)) {\
        printf("%s:%d (%f != %f)\n", __FILE__, __LINE__, (double)(a), (double)(b));\
        assert(0);\
    }} while (0)

// 识别到的typedef定义
typedef struct {
    const char *expr;
    double answer;
} test_case;
typedef struct {
    const char *expr1;
    const char *expr2;
} test_equ;

// 识别到的函数定义
// 函数: test_results (line 67)
void test_results() {
    test_case cases[] = {
        {"1", 1},
        {"1 ", 1},
        {"(1)", 1},

        {"pi", 3.14159},
        {"atan(1)*4 - pi", 0},
        {"e", 2.71828},

        {"2+1", 2+1},
        {"(((2+(1))))", 2+1},
        {"3+2", 3+2},

        {"3+2+4", 3+2+4},
        {"(3+2)+4", 3+2+4},
        {"3+(2+4)", 3+2+4},
        {"(3+2+4)", 3+2+4},

        {"3*2*4", 3*2*4},
        {"(3*2)*4", 3*2*4},
        {"3*(2*4)", 3*2*4},
        {"(3*2*4)", 3*2*4},

        {"3-2-4", 3-2-4},
        {"(3-2)-4", (3-2)-4},
        {"3-(2-4)", 3-(2-4)},
        {"(3-2-4)", 3-2-4},

        {"3/2/4", 3.0/2.0/4.0},
        {"(3/2)/4", (3.0/2.0)/4.0},
        {"3/(2/4)", 3.0/(2.0/4.0)},
        {"(3/2/4)", 3.0/2.0/4.0},

        {"(3*2/4)", 3.0*2.0/4.0},
        {"(3/2*4)", 3.0/2.0*4.0},
        {"3*(2/4)", 3.0*(2.0/4.0)},

        {"asin sin .5", 0.5},
        {"sin asin .5", 0.5},
        {"ln exp .5", 0.5},
        {"exp ln .5", 0.5},

        {"asin sin-.5", -0.5},
        {"asin sin-0.5", -0.5},
        {"asin sin -0.5", -0.5},
        {"asin (sin -0.5)", -0.5},
        {"asin (sin (-0.5))", -0.5},
        {"asin sin (-0.5)", -0.5},
        {"(asin sin (-0.5))", -0.5},

        {"log10 1000", 3},
        {"log10 1e3", 3},
        {"log10 1000", 3},
        {"log10 1e3", 3},
        {"log10(1000)", 3},
        {"log10(1e3)", 3},
        {"log10 1.0e3", 3},
        {"10^5*5e-5", 5},

#ifdef TE_NAT_LOG
        {"log 1000", 6.9078},
        {"log e", 1},
        {"log (e^10)", 10},
#else
        {"log 1000", 3},
#endif

        {"ln (e^10)", 10},
        {"100^.5+1", 11},
        {"100 ^.5+1", 11},
        {"100^+.5+1", 11},
        {"100^--.5+1", 11},
        {"100^---+-++---++-+-+-.5+1", 11},

        {"100^-.5+1", 1.1},
        {"100^---.5+1", 1.1},
        {"100^+---.5+1", 1.1},
        {"1e2^+---.5e0+1e0", 1.1},
        {"--(1e2^(+(-(-(-.5e0))))+1e0)", 1.1},

        {"sqrt 100 + 7", 17},
        {"sqrt 100 * 7", 70},
        {"sqrt (100 * 100)", 100},

        {"1,2", 2},
        {"1,2+1", 3},
        {"1+1,2+2,2+1", 3},
        {"1,2,3", 3},
        {"(1,2),3", 3},
        {"1,(2,3)", 3},
        {"-(1,(2,3))", -3},

        {"2^2", 4},
        {"pow(2,2)", 4},

        {"atan2(1,1)", 0.7854},
        {"atan2(1,2)", 0.4636},
        {"atan2(2,1)", 1.1071},
        {"atan2(3,4)", 0.6435},
        {"atan2(3+3,4*2)", 0.6435},
        {"atan2(3+3,(4*2))", 0.6435},
        {"atan2((3+3),4*2)", 0.6435},
        {"atan2((3+3),(4*2))", 0.6435},

    };


    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_case); ++i) {
        const char *expr = cases[i].expr;
        const double answer = cases[i].answer;

        int err;
        const double ev = te_interp(expr, &err);
        assert(!err);
        assert_float_equal(ev, answer);

        if (err) {
            printf("FAILED: %s (%d)\n", expr, err);
        }
    }
}

// 函数: test_syntax (line 192)
void test_syntax() {
    test_case errors[] = {
        {"", 1},
        {"1+", 2},
        {"1)", 2},
        {"(1", 2},
        {"1**1", 3},
        {"1*2(+4", 4},
        {"1*2(1+4", 4},
        {"a+5", 1},
        {"!+5", 1},
        {"_a+5", 1},
        {"#a+5", 1},
        {"1^^5", 3},
        {"1**5", 3},
        {"sin(cos5", 8},
    };


    int i;
    for (i = 0; i < sizeof(errors) / sizeof(test_case); ++i) {
        const char *expr = errors[i].expr;
        const int e = errors[i].answer;

        int err;
        const double r = te_interp(expr, &err);
        assert(err == e);
        assert(r != r);

        te_expr *n = te_compile(expr, 0, 0, &err);
        assert(err == e);
        assert(!n);

        if (err != e) {
            printf("FAILED: %s\n", expr);
        }

        const double k = te_interp(expr, 0);
        assert(k != k);
    }
}

// 函数: test_nans (line 235)
void test_nans() {

    const char *nans[] = {
        "0/0",
        "1%0",
        "1%(1%0)",
        "(1%0)%1",
        "fac(-1)",
        "ncr(2, 4)",
        "ncr(-2, 4)",
        "ncr(2, -4)",
        "npr(2, 4)",
        "npr(-2, 4)",
        "npr(2, -4)",
    };

    int i;
    for (i = 0; i < sizeof(nans) / sizeof(const char *); ++i) {
        const char *expr = nans[i];

        int err;
        const double r = te_interp(expr, &err);
        assert(err == 0);
        assert(r != r);

        te_expr *n = te_compile(expr, 0, 0, &err);
        assert(n);
        assert(err == 0);
        const double c = te_eval(n);
        assert(c != c);
        te_free(n);
    }
}

// 函数: test_infs (line 270)
void test_infs() {

    const char *infs[] = {
            "1/0",
            "log(0)",
            "pow(2,10000000)",
            "fac(300)",
            "ncr(300,100)",
            "ncr(300000,100)",
            "ncr(300000,100)*8",
            "npr(3,2)*ncr(300000,100)",
            "npr(100,90)",
            "npr(30,25)",
    };

    int i;
    for (i = 0; i < sizeof(infs) / sizeof(const char *); ++i) {
        const char *expr = infs[i];

        int err;
        const double r = te_interp(expr, &err);
        assert(err == 0);
        assert(r == r + 1);

        te_expr *n = te_compile(expr, 0, 0, &err);
        assert(n);
        assert(err == 0);
        const double c = te_eval(n);
        assert(c == c + 1);
        te_free(n);
    }
}

// 函数: test_variables (line 304)
void test_variables() {

    double x, y, test;
    te_variable lookup[] = {{"x", &x}, {"y", &y}, {"te_st", &test}};

    int err;

    te_expr *expr1 = te_compile("cos x + sin y", lookup, 2, &err);
    assert(expr1);
    assert(!err);

    te_expr *expr2 = te_compile("x+x+x-y", lookup, 2, &err);
    assert(expr2);
    assert(!err);

    te_expr *expr3 = te_compile("x*y^3", lookup, 2, &err);
    assert(expr3);
    assert(!err);

    te_expr *expr4 = te_compile("te_st+5", lookup, 3, &err);
    assert(expr4);
    assert(!err);

    for (y = 2; y < 3; ++y) {
        for (x = 0; x < 5; ++x) {
            double ev;

            ev = te_eval(expr1);
            assert_float_equal(ev, cos(x) + sin(y));

            ev = te_eval(expr2);
            assert_float_equal(ev, x+x+x-y);

            ev = te_eval(expr3);
            assert_float_equal(ev, x*y*y*y);

            test = x;
            ev = te_eval(expr4);
            assert_float_equal(ev, x+5);
        }
    }

    te_free(expr1);
    te_free(expr2);
    te_free(expr3);
    te_free(expr4);



    te_expr *expr5 = te_compile("xx*y^3", lookup, 2, &err);
    assert(!expr5);
    assert(err);

    te_expr *expr6 = te_compile("tes", lookup, 3, &err);
    assert(!expr6);
    assert(err);

    te_expr *expr7 = te_compile("sinn x", lookup, 2, &err);
    assert(!expr7);
    assert(err);

    te_expr *expr8 = te_compile("si x", lookup, 2, &err);
    assert(!expr8);
    assert(err);
}

// 识别到的宏定义
#define cross_check(a, b) do {\
    if ((b)!=(b)) break;\
    expr = te_compile((a), lookup, 2, &err);\
    assert_float_equal(te_eval(expr), (b));\
    assert(!err);\
    te_free(expr);\
}while(0)

// 识别到的函数定义
// 函数: test_functions (line 380)
void test_functions() {

    double x, y;
    te_variable lookup[] = {{"x", &x}, {"y", &y}};

    int err;
    te_expr *expr;

    for (x = -5; x < 5; x += .2) {
        cross_check("abs x", fabs(x));
        cross_check("acos x", acos(x));
        cross_check("asin x", asin(x));
        cross_check("atan x", atan(x));
        cross_check("ceil x", ceil(x));
        cross_check("cos x", cos(x));
        cross_check("cosh x", cosh(x));
        cross_check("exp x", exp(x));
        cross_check("floor x", floor(x));
        cross_check("ln x", log(x));
        cross_check("log10 x", log10(x));
        cross_check("sin x", sin(x));
        cross_check("sinh x", sinh(x));
        cross_check("sqrt x", sqrt(x));
        cross_check("tan x", tan(x));
        cross_check("tanh x", tanh(x));

        for (y = -2; y < 2; y += .2) {
            if (fabs(x) < 0.01) break;
            cross_check("atan2(x,y)", atan2(x, y));
            cross_check("pow(x,y)", pow(x, y));
        }
    }
}

// 函数: sum0 (line 415)
double sum0() {
    return 6;
}

// 函数: sum1 (line 418)
double sum1(double a) {
    return a * 2;
}

// 函数: sum2 (line 421)
double sum2(double a, double b) {
    return a + b;
}

// 函数: sum3 (line 424)
double sum3(double a, double b, double c) {
    return a + b + c;
}

// 函数: sum4 (line 427)
double sum4(double a, double b, double c, double d) {
    return a + b + c + d;
}

// 函数: sum5 (line 430)
double sum5(double a, double b, double c, double d, double e) {
    return a + b + c + d + e;
}

// 函数: sum6 (line 433)
double sum6(double a, double b, double c, double d, double e, double f) {
    return a + b + c + d + e + f;
}

// 函数: sum7 (line 436)
double sum7(double a, double b, double c, double d, double e, double f, double g) {
    return a + b + c + d + e + f + g;
}

// 函数: test_dynamic (line 441)
void test_dynamic() {

    double x, f;
    te_variable lookup[] = {
        {"x", &x},
        {"f", &f},
        {"sum0", sum0, TE_FUNCTION0},
        {"sum1", sum1, TE_FUNCTION1},
        {"sum2", sum2, TE_FUNCTION2},
        {"sum3", sum3, TE_FUNCTION3},
        {"sum4", sum4, TE_FUNCTION4},
        {"sum5", sum5, TE_FUNCTION5},
        {"sum6", sum6, TE_FUNCTION6},
        {"sum7", sum7, TE_FUNCTION7},
    };

    test_case cases[] = {
        {"x", 2},
        {"f+x", 7},
        {"x+x", 4},
        {"x+f", 7},
        {"f+f", 10},
        {"f+sum0", 11},
        {"sum0+sum0", 12},
        {"sum0()+sum0", 12},
        {"sum0+sum0()", 12},
        {"sum0()+(0)+sum0()", 12},
        {"sum1 sum0", 12},
        {"sum1(sum0)", 12},
        {"sum1 f", 10},
        {"sum1 x", 4},
        {"sum2 (sum0, x)", 8},
        {"sum3 (sum0, x, 2)", 10},
        {"sum2(2,3)", 5},
        {"sum3(2,3,4)", 9},
        {"sum4(2,3,4,5)", 14},
        {"sum5(2,3,4,5,6)", 20},
        {"sum6(2,3,4,5,6,7)", 27},
        {"sum7(2,3,4,5,6,7,8)", 35},
    };

    x = 2;
    f = 5;

    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_case); ++i) {
        const char *expr = cases[i].expr;
        const double answer = cases[i].answer;

        int err;
        te_expr *ex = te_compile(expr, lookup, sizeof(lookup)/sizeof(te_variable), &err);
        assert(ex);
        assert_float_equal(te_eval(ex), answer);
        te_free(ex);
    }
}

// 函数: clo0 (line 499)
double clo0(void *context) {
    if (context) return *((double*)context) + 6;
    return 6;
}

// 函数: clo1 (line 503)
double clo1(void *context, double a) {
    if (context) return *((double*)context) + a * 2;
    return a * 2;
}

// 函数: clo2 (line 507)
double clo2(void *context, double a, double b) {
    if (context) return *((double*)context) + a + b;
    return a + b;
}

// 函数: cell (line 512)
double cell(void *context, double a) {
    double *c = context;
    return c[(int)a];
}

// 函数: test_closure (line 517)
void test_closure() {

    double extra;
    double c[] = {5,6,7,8,9};

    te_variable lookup[] = {
        {"c0", clo0, TE_CLOSURE0, &extra},
        {"c1", clo1, TE_CLOSURE1, &extra},
        {"c2", clo2, TE_CLOSURE2, &extra},
        {"cell", cell, TE_CLOSURE1, c},
    };

    test_case cases[] = {
        {"c0", 6},
        {"c1 4", 8},
        {"c2 (10, 20)", 30},
    };

    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_case); ++i) {
        const char *expr = cases[i].expr;
        const double answer = cases[i].answer;

        int err;
        te_expr *ex = te_compile(expr, lookup, sizeof(lookup)/sizeof(te_variable), &err);
        assert(ex);

        extra = 0;
        assert_float_equal(te_eval(ex), answer + extra);

        extra = 10;
        assert_float_equal(te_eval(ex), answer + extra);

        te_free(ex);
    }


    test_case cases2[] = {
        {"cell 0", 5},
        {"cell 1", 6},
        {"cell 0 + cell 1", 11},
        {"cell 1 * cell 3 + cell 4", 57},
    };

    for (i = 0; i < sizeof(cases2) / sizeof(test_case); ++i) {
        const char *expr = cases2[i].expr;
        const double answer = cases2[i].answer;

        int err;
        te_expr *ex = te_compile(expr, lookup, sizeof(lookup)/sizeof(te_variable), &err);
        assert(ex);
        assert_float_equal(te_eval(ex), answer);
        te_free(ex);
    }
}

// 函数: test_optimize (line 573)
void test_optimize() {

    test_case cases[] = {
        {"5+5", 10},
        {"pow(2,2)", 4},
        {"sqrt 100", 10},
        {"pi * 2", 6.2832},
    };

    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_case); ++i) {
        const char *expr = cases[i].expr;
        const double answer = cases[i].answer;

        int err;
        te_expr *ex = te_compile(expr, 0, 0, &err);
        assert(ex);

        /* The answer should be know without
         * even running eval. */
        assert_float_equal(ex->value, answer);
        assert_float_equal(te_eval(ex), answer);

        te_free(ex);
    }
}

// 函数: test_pow (line 600)
void test_pow() {
#ifdef TE_POW_FROM_RIGHT
    test_equ cases[] = {
        {"2^3^4", "2^(3^4)"},
        {"-2^2", "-(2^2)"},
        {"--2^2", "(2^2)"},
        {"---2^2", "-(2^2)"},
        {"-(2*1)^2", "-(2^2)"},
        {"-2^2", "-4"},
        {"2^1.1^1.2^1.3", "2^(1.1^(1.2^1.3))"},
        {"-a^b", "-(a^b)"},
        {"-a^-b", "-(a^-b)"},
        {"1^0", "1"},
        {"(1)^0", "1"},
        {"-(2)^2", "-(2^2)"}
        /* TODO POW FROM RIGHT IS STILL BUGGY
        {"(-2)^2", "4"},
        {"(-1)^0", "1"},
        {"(-5)^0", "1"},
        {"-2^-3^-4", "-(2^(-(3^-4)))"}*/
    };
#else
    test_equ cases[] = {
        {"2^3^4", "(2^3)^4"},
        {"-2^2", "(-2)^2"},
        {"(-2)^2", "4"},
        {"--2^2", "2^2"},
        {"---2^2", "(-2)^2"},
        {"-2^2", "4"},
        {"2^1.1^1.2^1.3", "((2^1.1)^1.2)^1.3"},
        {"-a^b", "(-a)^b"},
        {"-a^-b", "(-a)^(-b)"},
        {"1^0", "1"},
        {"(1)^0", "1"},
        {"(-1)^0", "1"},
        {"(-5)^0", "1"},
        {"-2^-3^-4", "((-2)^(-3))^(-4)"}
    };
#endif

    double a = 2, b = 3;

    te_variable lookup[] = {
        {"a", &a},
        {"b", &b}
    };

    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_equ); ++i) {
        const char *expr1 = cases[i].expr1;
        const char *expr2 = cases[i].expr2;

        te_expr *ex1 = te_compile(expr1, lookup, sizeof(lookup)/sizeof(te_variable), 0);
        te_expr *ex2 = te_compile(expr2, lookup, sizeof(lookup)/sizeof(te_variable), 0);

        assert(ex1);
        assert(ex2);

        double r1 = te_eval(ex1);
        double r2 = te_eval(ex2);

        fflush(stdout);
        assert_float_equal(r1, r2);

        te_free(ex1);
        te_free(ex2);
    }

}

// 函数: test_combinatorics (line 670)
void test_combinatorics() {
    test_case cases[] = {
            {"fac(0)", 1},
            {"fac(0.2)", 1},
            {"fac(1)", 1},
            {"fac(2)", 2},
            {"fac(3)", 6},
            {"fac(4.8)", 24},
            {"fac(10)", 3628800},

            {"ncr(0,0)", 1},
            {"ncr(10,1)", 10},
            {"ncr(10,0)", 1},
            {"ncr(10,10)", 1},
            {"ncr(16,7)", 11440},
            {"ncr(16,9)", 11440},
            {"ncr(100,95)", 75287520},

            {"npr(0,0)", 1},
            {"npr(10,1)", 10},
            {"npr(10,0)", 1},
            {"npr(10,10)", 3628800},
            {"npr(20,5)", 1860480},
            {"npr(100,4)", 94109400},
    };


    int i;
    for (i = 0; i < sizeof(cases) / sizeof(test_case); ++i) {
        const char *expr = cases[i].expr;
        const double answer = cases[i].answer;

        int err;
        const double ev = te_interp(expr, &err);
        assert(!err);
        assert_float_equal(ev, answer);

        if (err) {
            printf("FAILED: %s (%d)\n", expr, err);
        }
    }
}

// 识别到的全局变量
static UnitTestFunction tests[] = {
	test_results,
	test_syntax,
	test_nans,
	test_infs,
	test_variables,
	test_functions,
	test_dynamic,
	test_closure,
	test_optimize,
	test_pow,
	test_combinatorics,
	NULL
};

// 识别到的函数定义
// 函数: main (line 729)
int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
