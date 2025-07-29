use ::libc;
extern "C" {
    fn malloc(_: libc::c_ulong) -> *mut libc::c_void;
    fn free(_: *mut libc::c_void);
    fn __assert_fail(
        __assertion: *const libc::c_char,
        __file: *const libc::c_char,
        __line: libc::c_uint,
        __function: *const libc::c_char,
    ) -> !;
}
#[derive(Copy, Clone)]
#[repr(C)]
pub struct bst {
    pub root: *mut bst_node,
}
#[derive(Copy, Clone)]
#[repr(C)]
pub struct bst_node {
    pub val: libc::c_int,
    pub left: *mut bst_node,
    pub right: *mut bst_node,
}
#[no_mangle]
pub unsafe extern "C" fn bst_create() -> *mut bst {
    let mut bst: *mut bst = malloc(::core::mem::size_of::<bst>() as libc::c_ulong)
        as *mut bst;
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            28 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 25],
                &[libc::c_char; 25],
            >(b"struct bst *bst_create()\0"))
                .as_ptr(),
        );
    }
    'c_1616: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                28 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 25],
                    &[libc::c_char; 25],
                >(b"struct bst *bst_create()\0"))
                    .as_ptr(),
            );
        }
    };
    (*bst).root = 0 as *mut bst_node;
    return bst;
}
#[no_mangle]
pub unsafe extern "C" fn bst_free(mut bst: *mut bst) {
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            35 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void bst_free(struct bst *)\0"))
                .as_ptr(),
        );
    }
    'c_2009: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                35 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void bst_free(struct bst *)\0"))
                    .as_ptr(),
            );
        }
    };
    while bst_isempty(bst) == 0 {
        bst_remove((*(*bst).root).val, bst);
    }
    free(bst as *mut libc::c_void);
}
#[no_mangle]
pub unsafe extern "C" fn bst_isempty(mut bst: *mut bst) -> libc::c_int {
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            50 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 30],
                &[libc::c_char; 30],
            >(b"int bst_isempty(struct bst *)\0"))
                .as_ptr(),
        );
    }
    'c_1976: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                50 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 30],
                    &[libc::c_char; 30],
                >(b"int bst_isempty(struct bst *)\0"))
                    .as_ptr(),
            );
        }
    };
    return ((*bst).root == 0 as *mut libc::c_void as *mut bst_node) as libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn _bst_node_create(mut val: libc::c_int) -> *mut bst_node {
    let mut n: *mut bst_node = malloc(
        ::core::mem::size_of::<bst_node>() as libc::c_ulong,
    ) as *mut bst_node;
    if !n.is_null() {} else {
        __assert_fail(
            b"n\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            60 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 39],
                &[libc::c_char; 39],
            >(b"struct bst_node *_bst_node_create(int)\0"))
                .as_ptr(),
        );
    }
    'c_2149: {
        if !n.is_null() {} else {
            __assert_fail(
                b"n\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                60 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 39],
                    &[libc::c_char; 39],
                >(b"struct bst_node *_bst_node_create(int)\0"))
                    .as_ptr(),
            );
        }
    };
    (*n).val = val;
    (*n).right = 0 as *mut bst_node;
    (*n).left = (*n).right;
    return n;
}
#[no_mangle]
pub unsafe extern "C" fn _bst_subtree_insert(
    mut val: libc::c_int,
    mut n: *mut bst_node,
) -> *mut bst_node {
    if n.is_null() {
        return _bst_node_create(val)
    } else if val < (*n).val {
        (*n).left = _bst_subtree_insert(val, (*n).left);
    } else {
        (*n).right = _bst_subtree_insert(val, (*n).right);
    }
    return n;
}
#[no_mangle]
pub unsafe extern "C" fn bst_insert(mut val: libc::c_int, mut bst: *mut bst) {
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            118 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 35],
                &[libc::c_char; 35],
            >(b"void bst_insert(int, struct bst *)\0"))
                .as_ptr(),
        );
    }
    'c_2191: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                118 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 35],
                    &[libc::c_char; 35],
                >(b"void bst_insert(int, struct bst *)\0"))
                    .as_ptr(),
            );
        }
    };
    (*bst).root = _bst_subtree_insert(val, (*bst).root);
}
#[no_mangle]
pub unsafe extern "C" fn _bst_subtree_min_val(mut n: *mut bst_node) -> libc::c_int {
    while !((*n).left).is_null() {
        n = (*n).left;
    }
    return (*n).val;
}
#[no_mangle]
pub unsafe extern "C" fn _bst_subtree_remove(
    mut val: libc::c_int,
    mut n: *mut bst_node,
) -> *mut bst_node {
    if n.is_null() {
        return 0 as *mut bst_node
    } else if val < (*n).val {
        (*n).left = _bst_subtree_remove(val, (*n).left);
        return n;
    } else if val > (*n).val {
        (*n).right = _bst_subtree_remove(val, (*n).right);
        return n;
    } else if !((*n).left).is_null() && !((*n).right).is_null() {
        (*n).val = _bst_subtree_min_val((*n).right);
        (*n).right = _bst_subtree_remove((*n).val, (*n).right);
        return n;
    } else if !((*n).left).is_null() {
        let mut left_child: *mut bst_node = (*n).left;
        free(n as *mut libc::c_void);
        return left_child;
    } else if !((*n).right).is_null() {
        let mut right_child: *mut bst_node = (*n).right;
        free(n as *mut libc::c_void);
        return right_child;
    } else {
        free(n as *mut libc::c_void);
        return 0 as *mut bst_node;
    };
}
#[no_mangle]
pub unsafe extern "C" fn bst_remove(mut val: libc::c_int, mut bst: *mut bst) {
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            242 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 35],
                &[libc::c_char; 35],
            >(b"void bst_remove(int, struct bst *)\0"))
                .as_ptr(),
        );
    }
    'c_1922: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                242 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 35],
                    &[libc::c_char; 35],
                >(b"void bst_remove(int, struct bst *)\0"))
                    .as_ptr(),
            );
        }
    };
    (*bst).root = _bst_subtree_remove(val, (*bst).root);
}
#[no_mangle]
pub unsafe extern "C" fn bst_contains(
    mut val: libc::c_int,
    mut bst: *mut bst,
) -> libc::c_int {
    if !bst.is_null() {} else {
        __assert_fail(
            b"bst\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8 as *const libc::c_char,
            255 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 36],
                &[libc::c_char; 36],
            >(b"int bst_contains(int, struct bst *)\0"))
                .as_ptr(),
        );
    }
    'c_2281: {
        if !bst.is_null() {} else {
            __assert_fail(
                b"bst\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/src/bst.c\0" as *const u8
                    as *const libc::c_char,
                255 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 36],
                    &[libc::c_char; 36],
                >(b"int bst_contains(int, struct bst *)\0"))
                    .as_ptr(),
            );
        }
    };
    let mut cur: *mut bst_node = (*bst).root;
    while !cur.is_null() {
        if val == (*cur).val {
            return 1 as libc::c_int
        } else if val < (*cur).val {
            cur = (*cur).left;
        } else {
            cur = (*cur).right;
        }
    }
    return 0 as libc::c_int;
}
