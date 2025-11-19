use ::libc;
extern "C" {
    pub type ht;
    fn __assert_fail(
        __assertion: *const libc::c_char,
        __file: *const libc::c_char,
        __line: libc::c_uint,
        __function: *const libc::c_char,
    ) -> !;
    fn printf(_: *const libc::c_char, _: ...) -> libc::c_int;
    fn malloc(_: libc::c_ulong) -> *mut libc::c_void;
    fn free(_: *mut libc::c_void);
    fn ht_create() -> *mut ht;
    fn ht_destroy(table: *mut ht);
    fn ht_get(table: *mut ht, key: *const libc::c_char) -> *mut libc::c_void;
    fn ht_set(
        table: *mut ht,
        key: *const libc::c_char,
        value: *mut libc::c_void,
    ) -> *const libc::c_char;
    fn ht_length(table: *mut ht) -> size_t;
    fn ht_iterator(table: *mut ht) -> hti;
    fn ht_next(it: *mut hti) -> bool;
}
pub type size_t = libc::c_ulong;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct hti {
    pub key: *const libc::c_char,
    pub value: *mut libc::c_void,
    pub _table: *mut ht,
    pub _index: size_t,
}
#[no_mangle]
pub unsafe extern "C" fn test_ht_create_and_destroy() {
    let mut table: *mut ht = ht_create();
    if !table.is_null() {} else {
        __assert_fail(
            b"table != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            9 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 34],
                &[libc::c_char; 34],
            >(b"void test_ht_create_and_destroy()\0"))
                .as_ptr(),
        );
    }
    'c_1986: {
        if !table.is_null() {} else {
            __assert_fail(
                b"table != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                9 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 34],
                    &[libc::c_char; 34],
                >(b"void test_ht_create_and_destroy()\0"))
                    .as_ptr(),
            );
        }
    };
    if ht_length(table) == 0 as libc::c_int as size_t {} else {
        __assert_fail(
            b"ht_length(table) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            10 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 34],
                &[libc::c_char; 34],
            >(b"void test_ht_create_and_destroy()\0"))
                .as_ptr(),
        );
    }
    'c_1936: {
        if ht_length(table) == 0 as libc::c_int as size_t {} else {
            __assert_fail(
                b"ht_length(table) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                10 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 34],
                    &[libc::c_char; 34],
                >(b"void test_ht_create_and_destroy()\0"))
                    .as_ptr(),
            );
        }
    };
    ht_destroy(table);
}
#[no_mangle]
pub unsafe extern "C" fn test_ht_set_and_get() {
    let mut table: *mut ht = ht_create();
    if !table.is_null() {} else {
        __assert_fail(
            b"table != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            16 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2419: {
        if !table.is_null() {} else {
            __assert_fail(
                b"table != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                16 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value1: libc::c_int = 42 as libc::c_int;
    let mut key1: *const libc::c_char = b"key1\0" as *const u8 as *const libc::c_char;
    if !(ht_set(table, key1, &mut value1 as *mut libc::c_int as *mut libc::c_void))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, key1, &value1) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            21 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2361: {
        if !(ht_set(table, key1, &mut value1 as *mut libc::c_int as *mut libc::c_void))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, key1, &value1) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                21 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut retrieved_value: *mut libc::c_int = ht_get(table, key1) as *mut libc::c_int;
    if !retrieved_value.is_null() {} else {
        __assert_fail(
            b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            25 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2319: {
        if !retrieved_value.is_null() {} else {
            __assert_fail(
                b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                25 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    if *retrieved_value == value1 {} else {
        __assert_fail(
            b"*retrieved_value == value1\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            26 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2275: {
        if *retrieved_value == value1 {} else {
            __assert_fail(
                b"*retrieved_value == value1\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                26 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value2: libc::c_int = 84 as libc::c_int;
    let mut key2: *const libc::c_char = b"key2\0" as *const u8 as *const libc::c_char;
    if !(ht_set(table, key2, &mut value2 as *mut libc::c_int as *mut libc::c_void))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, key2, &value2) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            31 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2215: {
        if !(ht_set(table, key2, &mut value2 as *mut libc::c_int as *mut libc::c_void))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, key2, &value2) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                31 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    retrieved_value = ht_get(table, key2) as *mut libc::c_int;
    if !retrieved_value.is_null() {} else {
        __assert_fail(
            b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            35 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2159: {
        if !retrieved_value.is_null() {} else {
            __assert_fail(
                b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                35 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    if *retrieved_value == value2 {} else {
        __assert_fail(
            b"*retrieved_value == value2\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            36 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2101: {
        if *retrieved_value == value2 {} else {
            __assert_fail(
                b"*retrieved_value == value2\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                36 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    if ht_length(table) == 2 as libc::c_int as size_t {} else {
        __assert_fail(
            b"ht_length(table) == 2\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            39 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 27],
                &[libc::c_char; 27],
            >(b"void test_ht_set_and_get()\0"))
                .as_ptr(),
        );
    }
    'c_2056: {
        if ht_length(table) == 2 as libc::c_int as size_t {} else {
            __assert_fail(
                b"ht_length(table) == 2\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                39 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 27],
                    &[libc::c_char; 27],
                >(b"void test_ht_set_and_get()\0"))
                    .as_ptr(),
            );
        }
    };
    ht_destroy(table);
}
#[no_mangle]
pub unsafe extern "C" fn test_ht_update_value() {
    let mut table: *mut ht = ht_create();
    if !table.is_null() {} else {
        __assert_fail(
            b"table != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            46 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2747: {
        if !table.is_null() {} else {
            __assert_fail(
                b"table != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                46 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value1: libc::c_int = 42 as libc::c_int;
    let mut key: *const libc::c_char = b"key\0" as *const u8 as *const libc::c_char;
    if !(ht_set(table, key, &mut value1 as *mut libc::c_int as *mut libc::c_void))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, key, &value1) != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            51 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2687: {
        if !(ht_set(table, key, &mut value1 as *mut libc::c_int as *mut libc::c_void))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, key, &value1) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                51 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value2: libc::c_int = 84 as libc::c_int;
    if !(ht_set(table, key, &mut value2 as *mut libc::c_int as *mut libc::c_void))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, key, &value2) != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            55 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2628: {
        if !(ht_set(table, key, &mut value2 as *mut libc::c_int as *mut libc::c_void))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, key, &value2) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                55 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut retrieved_value: *mut libc::c_int = ht_get(table, key) as *mut libc::c_int;
    if !retrieved_value.is_null() {} else {
        __assert_fail(
            b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            59 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2586: {
        if !retrieved_value.is_null() {} else {
            __assert_fail(
                b"retrieved_value != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                59 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    if *retrieved_value == value2 {} else {
        __assert_fail(
            b"*retrieved_value == value2\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            60 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2529: {
        if *retrieved_value == value2 {} else {
            __assert_fail(
                b"*retrieved_value == value2\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                60 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    if ht_length(table) == 1 as libc::c_int as size_t {} else {
        __assert_fail(
            b"ht_length(table) == 1\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            63 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 28],
                &[libc::c_char; 28],
            >(b"void test_ht_update_value()\0"))
                .as_ptr(),
        );
    }
    'c_2484: {
        if ht_length(table) == 1 as libc::c_int as size_t {} else {
            __assert_fail(
                b"ht_length(table) == 1\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                63 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 28],
                    &[libc::c_char; 28],
                >(b"void test_ht_update_value()\0"))
                    .as_ptr(),
            );
        }
    };
    ht_destroy(table);
}
#[no_mangle]
pub unsafe extern "C" fn test_ht_iterator() {
    let mut table: *mut ht = ht_create();
    if !table.is_null() {} else {
        __assert_fail(
            b"table != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            70 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 24],
                &[libc::c_char; 24],
            >(b"void test_ht_iterator()\0"))
                .as_ptr(),
        );
    }
    'c_3137: {
        if !table.is_null() {} else {
            __assert_fail(
                b"table != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                70 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value1: libc::c_int = 1 as libc::c_int;
    let mut value2: libc::c_int = 2 as libc::c_int;
    let mut value3: libc::c_int = 3 as libc::c_int;
    if !(ht_set(
        table,
        b"key1\0" as *const u8 as *const libc::c_char,
        &mut value1 as *mut libc::c_int as *mut libc::c_void,
    ))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, \"key1\", &value1) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            74 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 24],
                &[libc::c_char; 24],
            >(b"void test_ht_iterator()\0"))
                .as_ptr(),
        );
    }
    'c_3077: {
        if !(ht_set(
            table,
            b"key1\0" as *const u8 as *const libc::c_char,
            &mut value1 as *mut libc::c_int as *mut libc::c_void,
        ))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, \"key1\", &value1) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                74 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
    };
    if !(ht_set(
        table,
        b"key2\0" as *const u8 as *const libc::c_char,
        &mut value2 as *mut libc::c_int as *mut libc::c_void,
    ))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, \"key2\", &value2) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            75 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 24],
                &[libc::c_char; 24],
            >(b"void test_ht_iterator()\0"))
                .as_ptr(),
        );
    }
    'c_3017: {
        if !(ht_set(
            table,
            b"key2\0" as *const u8 as *const libc::c_char,
            &mut value2 as *mut libc::c_int as *mut libc::c_void,
        ))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, \"key2\", &value2) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                75 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
    };
    if !(ht_set(
        table,
        b"key3\0" as *const u8 as *const libc::c_char,
        &mut value3 as *mut libc::c_int as *mut libc::c_void,
    ))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, \"key3\", &value3) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            76 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 24],
                &[libc::c_char; 24],
            >(b"void test_ht_iterator()\0"))
                .as_ptr(),
        );
    }
    'c_2957: {
        if !(ht_set(
            table,
            b"key3\0" as *const u8 as *const libc::c_char,
            &mut value3 as *mut libc::c_int as *mut libc::c_void,
        ))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, \"key3\", &value3) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                76 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut it: hti = ht_iterator(table);
    let mut count: libc::c_int = 0 as libc::c_int;
    while ht_next(&mut it) {
        if !(it.key).is_null() {} else {
            __assert_fail(
                b"it.key != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                82 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
        'c_2907: {
            if !(it.key).is_null() {} else {
                __assert_fail(
                    b"it.key != NULL\0" as *const u8 as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                        as *const libc::c_char,
                    82 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 24],
                        &[libc::c_char; 24],
                    >(b"void test_ht_iterator()\0"))
                        .as_ptr(),
                );
            }
        };
        if !(it.value).is_null() {} else {
            __assert_fail(
                b"it.value != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                83 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
        'c_2857: {
            if !(it.value).is_null() {} else {
                __assert_fail(
                    b"it.value != NULL\0" as *const u8 as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                        as *const libc::c_char,
                    83 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 24],
                        &[libc::c_char; 24],
                    >(b"void test_ht_iterator()\0"))
                        .as_ptr(),
                );
            }
        };
        count += 1;
        count;
    }
    if count == 3 as libc::c_int {} else {
        __assert_fail(
            b"count == 3\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            88 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 24],
                &[libc::c_char; 24],
            >(b"void test_ht_iterator()\0"))
                .as_ptr(),
        );
    }
    'c_2811: {
        if count == 3 as libc::c_int {} else {
            __assert_fail(
                b"count == 3\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                88 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 24],
                    &[libc::c_char; 24],
                >(b"void test_ht_iterator()\0"))
                    .as_ptr(),
            );
        }
    };
    ht_destroy(table);
}
#[no_mangle]
pub unsafe extern "C" fn test_ht_memory_management() {
    let mut table: *mut ht = ht_create();
    if !table.is_null() {} else {
        __assert_fail(
            b"table != NULL\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            95 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 33],
                &[libc::c_char; 33],
            >(b"void test_ht_memory_management()\0"))
                .as_ptr(),
        );
    }
    'c_3362: {
        if !table.is_null() {} else {
            __assert_fail(
                b"table != NULL\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                95 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 33],
                    &[libc::c_char; 33],
                >(b"void test_ht_memory_management()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut value1: *mut libc::c_int = malloc(
        ::core::mem::size_of::<libc::c_int>() as libc::c_ulong,
    ) as *mut libc::c_int;
    let mut value2: *mut libc::c_int = malloc(
        ::core::mem::size_of::<libc::c_int>() as libc::c_ulong,
    ) as *mut libc::c_int;
    *value1 = 42 as libc::c_int;
    *value2 = 84 as libc::c_int;
    if !(ht_set(
        table,
        b"key1\0" as *const u8 as *const libc::c_char,
        value1 as *mut libc::c_void,
    ))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, \"key1\", value1) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            103 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 33],
                &[libc::c_char; 33],
            >(b"void test_ht_memory_management()\0"))
                .as_ptr(),
        );
    }
    'c_3288: {
        if !(ht_set(
            table,
            b"key1\0" as *const u8 as *const libc::c_char,
            value1 as *mut libc::c_void,
        ))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, \"key1\", value1) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                103 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 33],
                    &[libc::c_char; 33],
                >(b"void test_ht_memory_management()\0"))
                    .as_ptr(),
            );
        }
    };
    if !(ht_set(
        table,
        b"key2\0" as *const u8 as *const libc::c_char,
        value2 as *mut libc::c_void,
    ))
        .is_null()
    {} else {
        __assert_fail(
            b"ht_set(table, \"key2\", value2) != NULL\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                as *const libc::c_char,
            104 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 33],
                &[libc::c_char; 33],
            >(b"void test_ht_memory_management()\0"))
                .as_ptr(),
        );
    }
    'c_3221: {
        if !(ht_set(
            table,
            b"key2\0" as *const u8 as *const libc::c_char,
            value2 as *mut libc::c_void,
        ))
            .is_null()
        {} else {
            __assert_fail(
                b"ht_set(table, \"key2\", value2) != NULL\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-ht.c\0" as *const u8
                    as *const libc::c_char,
                104 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 33],
                    &[libc::c_char; 33],
                >(b"void test_ht_memory_management()\0"))
                    .as_ptr(),
            );
        }
    };
    let mut it: hti = ht_iterator(table);
    while ht_next(&mut it) {
        free(it.value);
    }
    ht_destroy(table);
}
unsafe fn main_0() -> libc::c_int {
    test_ht_create_and_destroy();
    test_ht_set_and_get();
    test_ht_update_value();
    test_ht_iterator();
    test_ht_memory_management();
    printf(b"All tests passed!\n\0" as *const u8 as *const libc::c_char);
    return 0 as libc::c_int;
}
pub fn main() {
    unsafe { ::std::process::exit(main_0() as i32) }
}
