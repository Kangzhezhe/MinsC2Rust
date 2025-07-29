use ::libc;
extern "C" {
    fn __assert_fail(
        __assertion: *const libc::c_char,
        __file: *const libc::c_char,
        __line: libc::c_uint,
        __function: *const libc::c_char,
    ) -> !;
    fn printf(_: *const libc::c_char, _: ...) -> libc::c_int;
    fn puts(__s: *const libc::c_char) -> libc::c_int;
    fn free(_: *mut libc::c_void);
    fn quadtree_point_new(x: libc::c_double, y: libc::c_double) -> *mut quadtree_point_t;
    fn quadtree_point_free(point: *mut quadtree_point_t);
    fn quadtree_bounds_new() -> *mut quadtree_bounds_t;
    fn quadtree_bounds_extend(
        bounds: *mut quadtree_bounds_t,
        x: libc::c_double,
        y: libc::c_double,
    );
    fn quadtree_bounds_free(bounds: *mut quadtree_bounds_t);
    fn quadtree_node_new() -> *mut quadtree_node_t;
    fn quadtree_node_ispointer(node: *mut quadtree_node_t) -> libc::c_int;
    fn quadtree_node_isempty(node: *mut quadtree_node_t) -> libc::c_int;
    fn quadtree_node_isleaf(node: *mut quadtree_node_t) -> libc::c_int;
    fn quadtree_new(
        minx: libc::c_double,
        miny: libc::c_double,
        maxx: libc::c_double,
        maxy: libc::c_double,
    ) -> *mut quadtree_t;
    fn quadtree_free(tree: *mut quadtree_t);
    fn quadtree_search(
        tree: *mut quadtree_t,
        x: libc::c_double,
        y: libc::c_double,
    ) -> *mut quadtree_point_t;
    fn quadtree_insert(
        tree: *mut quadtree_t,
        x: libc::c_double,
        y: libc::c_double,
        key: *mut libc::c_void,
    ) -> libc::c_int;
    fn quadtree_walk(
        root: *mut quadtree_node_t,
        descent_0: Option::<unsafe extern "C" fn(*mut quadtree_node_t) -> ()>,
        ascent_0: Option::<unsafe extern "C" fn(*mut quadtree_node_t) -> ()>,
    );
}
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_point {
    pub x: libc::c_double,
    pub y: libc::c_double,
}
pub type quadtree_point_t = quadtree_point;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_bounds {
    pub nw: *mut quadtree_point_t,
    pub se: *mut quadtree_point_t,
    pub width: libc::c_double,
    pub height: libc::c_double,
}
pub type quadtree_bounds_t = quadtree_bounds;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_node {
    pub ne: *mut quadtree_node,
    pub nw: *mut quadtree_node,
    pub se: *mut quadtree_node,
    pub sw: *mut quadtree_node,
    pub bounds: *mut quadtree_bounds_t,
    pub point: *mut quadtree_point_t,
    pub key: *mut libc::c_void,
}
pub type quadtree_node_t = quadtree_node;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree {
    pub root: *mut quadtree_node_t,
    pub key_free: Option::<unsafe extern "C" fn(*mut libc::c_void) -> ()>,
    pub length: libc::c_uint,
}
pub type quadtree_t = quadtree;
#[no_mangle]
pub unsafe extern "C" fn descent(mut node: *mut quadtree_node_t) {}
#[no_mangle]
pub unsafe extern "C" fn ascent(mut node: *mut quadtree_node_t) {}
unsafe extern "C" fn test_node() {
    let mut node: *mut quadtree_node_t = quadtree_node_new();
    if quadtree_node_isleaf(node) == 0 {} else {
        __assert_fail(
            b"!quadtree_node_isleaf(node)\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            20 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_node(void)\0"))
                .as_ptr(),
        );
    }
    'c_3064: {
        if quadtree_node_isleaf(node) == 0 {} else {
            __assert_fail(
                b"!quadtree_node_isleaf(node)\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                20 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_node(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_node_isempty(node) != 0 {} else {
        __assert_fail(
            b"quadtree_node_isempty(node)\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            21 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_node(void)\0"))
                .as_ptr(),
        );
    }
    'c_3025: {
        if quadtree_node_isempty(node) != 0 {} else {
            __assert_fail(
                b"quadtree_node_isempty(node)\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                21 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_node(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_node_ispointer(node) == 0 {} else {
        __assert_fail(
            b"!quadtree_node_ispointer(node)\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            22 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_node(void)\0"))
                .as_ptr(),
        );
    }
    'c_2979: {
        if quadtree_node_ispointer(node) == 0 {} else {
            __assert_fail(
                b"!quadtree_node_ispointer(node)\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                22 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_node(void)\0"))
                    .as_ptr(),
            );
        }
    };
    free(node as *mut libc::c_void);
}
unsafe extern "C" fn test_bounds() {
    let mut bounds: *mut quadtree_bounds_t = quadtree_bounds_new();
    if !bounds.is_null() {} else {
        __assert_fail(
            b"bounds\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            30 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3605: {
        if !bounds.is_null() {} else {
            __assert_fail(
                b"bounds\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                30 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).nw).x == ::core::f32::INFINITY as libc::c_double {} else {
        __assert_fail(
            b"bounds->nw->x == INFINITY\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            31 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3552: {
        if (*(*bounds).nw).x == ::core::f32::INFINITY as libc::c_double {} else {
            __assert_fail(
                b"bounds->nw->x == INFINITY\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                31 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).se).x == -::core::f32::INFINITY as libc::c_double {} else {
        __assert_fail(
            b"bounds->se->x == -INFINITY\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            32 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3493: {
        if (*(*bounds).se).x == -::core::f32::INFINITY as libc::c_double {} else {
            __assert_fail(
                b"bounds->se->x == -INFINITY\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                32 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    quadtree_bounds_extend(bounds, 5.0f64, 5.0f64);
    if (*(*bounds).nw).x == 5.0f64 {} else {
        __assert_fail(
            b"bounds->nw->x == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            35 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3442: {
        if (*(*bounds).nw).x == 5.0f64 {} else {
            __assert_fail(
                b"bounds->nw->x == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                35 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).se).x == 5.0f64 {} else {
        __assert_fail(
            b"bounds->se->x == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            36 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3398: {
        if (*(*bounds).se).x == 5.0f64 {} else {
            __assert_fail(
                b"bounds->se->x == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                36 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    quadtree_bounds_extend(bounds, 10.0f64, 10.0f64);
    if (*(*bounds).nw).y == 10.0f64 {} else {
        __assert_fail(
            b"bounds->nw->y == 10.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            39 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3346: {
        if (*(*bounds).nw).y == 10.0f64 {} else {
            __assert_fail(
                b"bounds->nw->y == 10.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                39 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).nw).y == 10.0f64 {} else {
        __assert_fail(
            b"bounds->nw->y == 10.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            40 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3302: {
        if (*(*bounds).nw).y == 10.0f64 {} else {
            __assert_fail(
                b"bounds->nw->y == 10.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                40 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).se).y == 5.0f64 {} else {
        __assert_fail(
            b"bounds->se->y == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            41 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3258: {
        if (*(*bounds).se).y == 5.0f64 {} else {
            __assert_fail(
                b"bounds->se->y == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                41 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*bounds).se).y == 5.0f64 {} else {
        __assert_fail(
            b"bounds->se->y == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            42 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3214: {
        if (*(*bounds).se).y == 5.0f64 {} else {
            __assert_fail(
                b"bounds->se->y == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                42 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*bounds).width == 5.0f64 {} else {
        __assert_fail(
            b"bounds->width == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            44 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3174: {
        if (*bounds).width == 5.0f64 {} else {
            __assert_fail(
                b"bounds->width == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                44 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*bounds).height == 5.0f64 {} else {
        __assert_fail(
            b"bounds->height == 5.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            45 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_bounds(void)\0"))
                .as_ptr(),
        );
    }
    'c_3132: {
        if (*bounds).height == 5.0f64 {} else {
            __assert_fail(
                b"bounds->height == 5.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                45 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_bounds(void)\0"))
                    .as_ptr(),
            );
        }
    };
    quadtree_bounds_free(bounds);
}
unsafe extern "C" fn test_tree() {
    let mut val: libc::c_int = 10 as libc::c_int;
    let mut tree: *mut quadtree_t = quadtree_new(
        1 as libc::c_int as libc::c_double,
        1 as libc::c_int as libc::c_double,
        10 as libc::c_int as libc::c_double,
        10 as libc::c_int as libc::c_double,
    );
    if (*(*(*(*tree).root).bounds).nw).x == 1 as libc::c_int as libc::c_double {} else {
        __assert_fail(
            b"tree->root->bounds->nw->x == 1\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            56 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4552: {
        if (*(*(*(*tree).root).bounds).nw).x == 1 as libc::c_int as libc::c_double
        {} else {
            __assert_fail(
                b"tree->root->bounds->nw->x == 1\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                56 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*(*(*tree).root).bounds).nw).y == 10.0f64 {} else {
        __assert_fail(
            b"tree->root->bounds->nw->y == 10.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            57 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4500: {
        if (*(*(*(*tree).root).bounds).nw).y == 10.0f64 {} else {
            __assert_fail(
                b"tree->root->bounds->nw->y == 10.0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                57 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*(*(*tree).root).bounds).se).x == 10.0f64 {} else {
        __assert_fail(
            b"tree->root->bounds->se->x == 10.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            58 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4447: {
        if (*(*(*(*tree).root).bounds).se).x == 10.0f64 {} else {
            __assert_fail(
                b"tree->root->bounds->se->x == 10.0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                58 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*(*(*tree).root).bounds).se).y == 1 as libc::c_int as libc::c_double {} else {
        __assert_fail(
            b"tree->root->bounds->se->y == 1\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            59 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4393: {
        if (*(*(*(*tree).root).bounds).se).y == 1 as libc::c_int as libc::c_double
        {} else {
            __assert_fail(
                b"tree->root->bounds->se->y == 1\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                59 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        0 as libc::c_int as libc::c_double,
        0 as libc::c_int as libc::c_double,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 0, 0, &val) == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            62 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4336: {
        if quadtree_insert(
            tree,
            0 as libc::c_int as libc::c_double,
            0 as libc::c_int as libc::c_double,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 0, 0, &val) == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                62 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        110.0f64,
        110.0f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 110.0, 110.0, &val) == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            63 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4283: {
        if quadtree_insert(
            tree,
            110.0f64,
            110.0f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 110.0, 110.0, &val) == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                63 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        8.0f64,
        2.0f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) != 0 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 8.0, 2.0, &val) != 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            65 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4231: {
        if quadtree_insert(
            tree,
            8.0f64,
            2.0f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) != 0 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 8.0, 2.0, &val) != 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                65 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*tree).length == 1 as libc::c_int as libc::c_uint {} else {
        __assert_fail(
            b"tree->length == 1\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            66 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4189: {
        if (*tree).length == 1 as libc::c_int as libc::c_uint {} else {
            __assert_fail(
                b"tree->length == 1\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                66 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*(*tree).root).point).x == 8.0f64 {} else {
        __assert_fail(
            b"tree->root->point->x == 8.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            67 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4141: {
        if (*(*(*tree).root).point).x == 8.0f64 {} else {
            __assert_fail(
                b"tree->root->point->x == 8.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                67 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*(*(*tree).root).point).y == 2.0f64 {} else {
        __assert_fail(
            b"tree->root->point->y == 2.0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            68 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4093: {
        if (*(*(*tree).root).point).y == 2.0f64 {} else {
            __assert_fail(
                b"tree->root->point->y == 2.0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                68 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        0.0f64,
        1.0f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 0.0, 1.0, &val) == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            70 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_4041: {
        if quadtree_insert(
            tree,
            0.0f64,
            1.0f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 0.0, 1.0, &val) == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                70 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        2.0f64,
        3.0f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 1 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 2.0, 3.0, &val) == 1\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            71 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3989: {
        if quadtree_insert(
            tree,
            2.0f64,
            3.0f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 1 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 2.0, 3.0, &val) == 1\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                71 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        2.0f64,
        3.0f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 2 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 2.0, 3.0, &val) == 2\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            72 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3937: {
        if quadtree_insert(
            tree,
            2.0f64,
            3.0f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 2 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 2.0, 3.0, &val) == 2\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                72 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*tree).length == 2 as libc::c_int as libc::c_uint {} else {
        __assert_fail(
            b"tree->length == 2\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            73 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3895: {
        if (*tree).length == 2 as libc::c_int as libc::c_uint {} else {
            __assert_fail(
                b"tree->length == 2\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                73 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if ((*(*tree).root).point).is_null() {} else {
        __assert_fail(
            b"tree->root->point == NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            74 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3845: {
        if ((*(*tree).root).point).is_null() {} else {
            __assert_fail(
                b"tree->root->point == NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                74 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if quadtree_insert(
        tree,
        3.0f64,
        1.1f64,
        &mut val as *mut libc::c_int as *mut libc::c_void,
    ) == 1 as libc::c_int
    {} else {
        __assert_fail(
            b"quadtree_insert(tree, 3.0, 1.1, &val) == 1\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            76 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3789: {
        if quadtree_insert(
            tree,
            3.0f64,
            1.1f64,
            &mut val as *mut libc::c_int as *mut libc::c_void,
        ) == 1 as libc::c_int
        {} else {
            __assert_fail(
                b"quadtree_insert(tree, 3.0, 1.1, &val) == 1\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                76 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*tree).length == 3 as libc::c_int as libc::c_uint {} else {
        __assert_fail(
            b"tree->length == 3\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            77 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3746: {
        if (*tree).length == 3 as libc::c_int as libc::c_uint {} else {
            __assert_fail(
                b"tree->length == 3\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                77 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*quadtree_search(tree, 3.0f64, 1.1f64)).x == 3.0f64 {} else {
        __assert_fail(
            b"quadtree_search(tree, 3.0, 1.1)->x == 3.0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            78 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 21],
                &[libc::c_char; 21],
            >(b"void test_tree(void)\0"))
                .as_ptr(),
        );
    }
    'c_3694: {
        if (*quadtree_search(tree, 3.0f64, 1.1f64)).x == 3.0f64 {} else {
            __assert_fail(
                b"quadtree_search(tree, 3.0, 1.1)->x == 3.0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                78 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 21],
                    &[libc::c_char; 21],
                >(b"void test_tree(void)\0"))
                    .as_ptr(),
            );
        }
    };
    quadtree_walk(
        (*tree).root,
        Some(ascent as unsafe extern "C" fn(*mut quadtree_node_t) -> ()),
        Some(descent as unsafe extern "C" fn(*mut quadtree_node_t) -> ()),
    );
    quadtree_free(tree);
}
unsafe extern "C" fn test_points() {
    let mut point: *mut quadtree_point_t = quadtree_point_new(
        5 as libc::c_int as libc::c_double,
        6 as libc::c_int as libc::c_double,
    );
    if (*point).x == 5 as libc::c_int as libc::c_double {} else {
        __assert_fail(
            b"point->x == 5\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            86 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_points(void)\0"))
                .as_ptr(),
        );
    }
    'c_4670: {
        if (*point).x == 5 as libc::c_int as libc::c_double {} else {
            __assert_fail(
                b"point->x == 5\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                86 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_points(void)\0"))
                    .as_ptr(),
            );
        }
    };
    if (*point).y == 6 as libc::c_int as libc::c_double {} else {
        __assert_fail(
            b"point->y == 6\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                as *const libc::c_char,
            87 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 23],
                &[libc::c_char; 23],
            >(b"void test_points(void)\0"))
                .as_ptr(),
        );
    }
    'c_4627: {
        if (*point).y == 6 as libc::c_int as libc::c_double {} else {
            __assert_fail(
                b"point->y == 6\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-quadtree.c\0" as *const u8
                    as *const libc::c_char,
                87 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 23],
                    &[libc::c_char; 23],
                >(b"void test_points(void)\0"))
                    .as_ptr(),
            );
        }
    };
    quadtree_point_free(point);
}
unsafe fn main_0(
    mut argc: libc::c_int,
    mut argv: *mut *const libc::c_char,
) -> libc::c_int {
    printf(b"\x1B[33mtree\x1B[0m \0" as *const u8 as *const libc::c_char);
    test_tree();
    puts(b"\x1B[1;32m\xE2\x9C\x93\x1B[0m\0" as *const u8 as *const libc::c_char);
    printf(b"\x1B[33mnode\x1B[0m \0" as *const u8 as *const libc::c_char);
    test_node();
    puts(b"\x1B[1;32m\xE2\x9C\x93\x1B[0m\0" as *const u8 as *const libc::c_char);
    printf(b"\x1B[33mbounds\x1B[0m \0" as *const u8 as *const libc::c_char);
    test_bounds();
    puts(b"\x1B[1;32m\xE2\x9C\x93\x1B[0m\0" as *const u8 as *const libc::c_char);
    printf(b"\x1B[33mpoints\x1B[0m \0" as *const u8 as *const libc::c_char);
    test_points();
    puts(b"\x1B[1;32m\xE2\x9C\x93\x1B[0m\0" as *const u8 as *const libc::c_char);
    return 0;
}
pub fn main() {
    let mut args: Vec::<*mut libc::c_char> = Vec::new();
    for arg in ::std::env::args() {
        args.push(
            (::std::ffi::CString::new(arg))
                .expect("Failed to convert argument into CString.")
                .into_raw(),
        );
    }
    args.push(::core::ptr::null_mut());
    unsafe {
        ::std::process::exit(
            main_0(
                (args.len() - 1) as libc::c_int,
                args.as_mut_ptr() as *mut *const libc::c_char,
            ) as i32,
        )
    }
}
