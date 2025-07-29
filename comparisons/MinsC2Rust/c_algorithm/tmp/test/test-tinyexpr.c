/*
 * TINYEXPR - Tiny recursive descent parser and evaluation engine in C
 *
 * Copyright (c) 2015-2020 Lewis Van Winkle
 *
 * http://CodePlea.com
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software
 * in a product, an acknowledgement in the product documentation would be
 * appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

// SPDX-License-Identifier: Zlib
/*
 * TINYEXPR - Tiny recursive descent parser and evaluation engine in C
 *
 * Copyright (c) 2015-2020 Lewis Van Winkle
 *
 * http://CodePlea.com
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software
 * in a product, an acknowledgement in the product documentation would be
 * appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

#ifndef TINYEXPR_H
#define TINYEXPR_H


#ifdef __cplusplus
extern "C" {
#endif



typedef struct te_expr {
    int type;
    union {double value; const double *bound; const void *function;};
    void *parameters[1];
} te_expr;


enum {
    TE_VARIABLE = 0,

    TE_FUNCTION0 = 8, TE_FUNCTION1, TE_FUNCTION2, TE_FUNCTION3,
    TE_FUNCTION4, TE_FUNCTION5, TE_FUNCTION6, TE_FUNCTION7,

    TE_CLOSURE0 = 16, TE_CLOSURE1, TE_CLOSURE2, TE_CLOSURE3,
    TE_CLOSURE4, TE_CLOSURE5, TE_CLOSURE6, TE_CLOSURE7,

    TE_FLAG_PURE = 32
};

typedef struct te_variable {
    const char *name;
    const void *address;
    int type;
    void *context;
} te_variable;



/* Parses the input expression, evaluates it, and frees it. */
/* Returns NaN on error. */
double te_interp(const char *expression, int *error);

/* Parses the input expression and binds variables. */
/* Returns NULL on error. */
te_expr *te_compile(const char *expression, const te_variable *variables, int var_count, int *error);

/* Evaluates the expression. */
double te_eval(const te_expr *n);

/* Prints debugging information on the syntax tree. */
void te_print(const te_expr *n);

/* Frees the expression. */
/* This is safe to call on NULL pointers. */
void te_free(te_expr *n);


#ifdef __cplusplus
}
#endif

#endif /*TINYEXPR_H*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

/**
 * @file alloc-testing.h
 *
 * @brief Memory allocation testing framework.
 *
 * This file uses the preprocessor to redefine the standard C dynamic memory
 * allocation functions for testing purposes.  This allows checking that
 * code under test correctly frees back all memory allocated, as well as
 * the ability to impose artificial limits on allocation, to test that
 * code correctly handles out-of-memory scenarios.
 */

#ifndef ALLOC_TESTING_H
#define ALLOC_TESTING_H

/* Don't redefine the functions in the alloc-testing.c, as we need the
 * standard malloc/free functions. */

#ifndef ALLOC_TESTING_C
#undef malloc
#define malloc   alloc_test_malloc
#undef free
#define free     alloc_test_free
#undef realloc
#define realloc  alloc_test_realloc
#undef calloc
#define calloc   alloc_test_calloc
#undef strdup
#define strdup   alloc_test_strdup
#endif

/**
 * Allocate a block of memory.
 *
 * @param bytes          Number of bytes to allocate.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_malloc(size_t bytes);

/**
 * Free a block of memory.
 *
 * @param ptr            Pointer to the block to free.
 */

void alloc_test_free(void *ptr);

/**
 * Reallocate a previously-allocated block to a new size, preserving
 * contents.
 *
 * @param ptr            Pointer to the existing block.
 * @param bytes          Size of the new block, in bytes.
 * @return               Pointer to the new block, or NULL if it was not
 *                       possible to allocate the new block.
 */

void *alloc_test_realloc(void *ptr, size_t bytes);

/**
 * Allocate a block of memory for an array of structures, initialising
 * the contents to zero.
 *
 * @param nmemb          Number of structures to allocate for.
 * @param bytes          Size of each structure, in bytes.
 * @return               Pointer to the new memory block for the array,
 *                       or NULL if it was not possible to allocate the
 *                       new block.
 */

void *alloc_test_calloc(size_t nmemb, size_t bytes);

/**
 * Allocate a block of memory containing a copy of a string.
 *
 * @param string         The string to copy.
 * @return               Pointer to the new memory block containing the
 *                       copied string, or NULL if it was not possible
 *                       to allocate the new block.
 */

char *alloc_test_strdup(const char *string);

/**
 * Set an artificial limit on the amount of memory that can be
 * allocated.
 *
 * @param alloc_count    Number of allocations that are possible after
 *                       this call.  For example, if this has a value
 *                       of 3, malloc() can be called successfully
 *                       three times, but all allocation attempts
 *                       after this will fail.  If this has a negative
 *                       value, the allocation limit is disabled.
 */

void alloc_test_set_limit(signed int alloc_count);

/**
 * Get a count of the number of bytes currently allocated.
 *
 * @return               The number of bytes currently allocated by
 *                       the allocation system.
 */

size_t alloc_test_get_allocated(void);

#endif /* #ifndef ALLOC_TESTING_H */

/*

Copyright (c) 2005-2008, Simon Howard

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file framework.h
 *
 * @brief Framework for running unit tests.
 */

/**
 * A unit test.
 */

typedef void (*UnitTestFunction)(void);

/**
 * Run a list of unit tests.  The provided array contains a list of
 * pointers to test functions to invoke; the last entry is denoted
 * by a NULL pointer.
 *
 * @param tests          List of tests to invoke.
 */

void run_tests(UnitTestFunction *tests);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef TEST_FRAMEWORK_H */


_Atomic size_t num_assert = 0;
#undef assert
#define assert(expr)                                                           \
  num_assert += 1;                                                             \
  ((void)sizeof((expr) ? 1 : 0), __extension__({                               \
     if (expr)                                                                 \
       ; /* empty */                                                           \
     else                                                                      \
       __assert_fail(#expr, __FILE__, __LINE__, __ASSERT_FUNCTION);            \
   }))

#define LTEST_FLOAT_TOLERANCE 0.001

#define assert_float_equal(a, b) do {\
    const double __LF_COMPARE = fabs((double)(a)-(double)(b));\
    if (__LF_COMPARE > LTEST_FLOAT_TOLERANCE || (__LF_COMPARE != __LF_COMPARE)) {\
        printf("%s:%d (%f != %f)\n", __FILE__, __LINE__, (double)(a), (double)(b));\
        assert(0);\
    }} while (0)


typedef struct {
    const char *expr;
    double answer;
} test_case;

typedef struct {
    const char *expr1;
    const char *expr2;
} test_equ;



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



#define cross_check(a, b) do {\
    if ((b)!=(b)) break;\
    expr = te_compile((a), lookup, 2, &err);\
    assert_float_equal(te_eval(expr), (b));\
    assert(!err);\
    te_free(expr);\
}while(0)

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


double sum0() {
    return 6;
}
double sum1(double a) {
    return a * 2;
}
double sum2(double a, double b) {
    return a + b;
}
double sum3(double a, double b, double c) {
    return a + b + c;
}
double sum4(double a, double b, double c, double d) {
    return a + b + c + d;
}
double sum5(double a, double b, double c, double d, double e) {
    return a + b + c + d + e;
}
double sum6(double a, double b, double c, double d, double e, double f) {
    return a + b + c + d + e + f;
}
double sum7(double a, double b, double c, double d, double e, double f, double g) {
    return a + b + c + d + e + f + g;
}


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


double clo0(void *context) {
    if (context) return *((double*)context) + 6;
    return 6;
}
double clo1(void *context, double a) {
    if (context) return *((double*)context) + a * 2;
    return a * 2;
}
double clo2(void *context, double a, double b) {
    if (context) return *((double*)context) + a + b;
    return a + b;
}

double cell(void *context, double a) {
    double *c = context;
    return c[(int)a];
}

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

int main(int argc, char *argv[])
{
	run_tests(tests);
  printf("num_assert: %lu\n", num_assert);
	return 0;
}
