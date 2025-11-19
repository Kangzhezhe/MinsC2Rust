use ::libc;
extern "C" {
    fn __assert_fail(
        __assertion: *const libc::c_char,
        __file: *const libc::c_char,
        __line: libc::c_uint,
        __function: *const libc::c_char,
    ) -> !;
    fn printf(_: *const libc::c_char, _: ...) -> libc::c_int;
    fn strcmp(_: *const libc::c_char, _: *const libc::c_char) -> libc::c_int;
    fn strlen(_: *const libc::c_char) -> libc::c_ulong;
    fn ParseURL(URL: *mut libc::c_char, pURL_Parts: *mut URL_PARTS) -> bool;
}
#[derive(Copy, Clone)]
#[repr(C)]
pub struct URL_PARTS {
    pub scheme: [libc::c_char; 32],
    pub authority: [libc::c_char; 512],
    pub port: [libc::c_char; 64],
    pub path: [libc::c_char; 1024],
    pub query: [libc::c_char; 1024],
    pub fragment: [libc::c_char; 256],
}
#[no_mangle]
pub unsafe extern "C" fn test_parse_url() {
    let mut url_parts: URL_PARTS = URL_PARTS {
        scheme: [0; 32],
        authority: [0; 512],
        port: [0; 64],
        path: [0; 1024],
        query: [0; 1024],
        fragment: [0; 256],
    };
    if ParseURL(
        b"http://sullewarehouse.com/login\0" as *const u8 as *const libc::c_char
            as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"http://sullewarehouse.com/login\", &url_parts)\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            11 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3980: {
        if ParseURL(
            b"http://sullewarehouse.com/login\0" as *const u8 as *const libc::c_char
                as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"http://sullewarehouse.com/login\", &url_parts)\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                11 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.scheme).as_mut_ptr(),
        b"http\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.scheme, \"http\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            12 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3930: {
        if strcmp(
            (url_parts.scheme).as_mut_ptr(),
            b"http\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.scheme, \"http\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                12 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            13 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3880: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                13 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            14 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3832: {
        if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                14 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/login\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/login\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            15 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3782: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/login\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/login\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                15 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            16 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3734: {
        if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                16 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            17 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3686: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                17 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if ParseURL(
        b"https://sullewarehouse.com:1000/login\0" as *const u8 as *const libc::c_char
            as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"https://sullewarehouse.com:1000/login\", &url_parts)\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            20 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3640: {
        if ParseURL(
            b"https://sullewarehouse.com:1000/login\0" as *const u8
                as *const libc::c_char as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"https://sullewarehouse.com:1000/login\", &url_parts)\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                20 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.scheme).as_mut_ptr(),
        b"https\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            21 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3590: {
        if strcmp(
            (url_parts.scheme).as_mut_ptr(),
            b"https\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                21 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            22 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3540: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                22 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.port).as_mut_ptr(),
        b"1000\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.port, \"1000\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            23 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3490: {
        if strcmp(
            (url_parts.port).as_mut_ptr(),
            b"1000\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.port, \"1000\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                23 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/login\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/login\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            24 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3439: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/login\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/login\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                24 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            25 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3391: {
        if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                25 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            26 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3343: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                26 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if ParseURL(
        b"https://sullewarehouse.com:1000/api/get?username=myuser\0" as *const u8
            as *const libc::c_char as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"https://sullewarehouse.com:1000/api/get?username=myuser\", &url_parts)\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            29 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3296: {
        if ParseURL(
            b"https://sullewarehouse.com:1000/api/get?username=myuser\0" as *const u8
                as *const libc::c_char as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"https://sullewarehouse.com:1000/api/get?username=myuser\", &url_parts)\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                29 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.scheme).as_mut_ptr(),
        b"https\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            30 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3246: {
        if strcmp(
            (url_parts.scheme).as_mut_ptr(),
            b"https\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                30 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            31 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3196: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                31 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.port).as_mut_ptr(),
        b"1000\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.port, \"1000\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            32 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3146: {
        if strcmp(
            (url_parts.port).as_mut_ptr(),
            b"1000\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.port, \"1000\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                32 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/api/get\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/api/get\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            33 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3096: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/api/get\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/api/get\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                33 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.query).as_mut_ptr(),
        b"?username=myuser\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.query, \"?username=myuser\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            34 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_3044: {
        if strcmp(
            (url_parts.query).as_mut_ptr(),
            b"?username=myuser\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.query, \"?username=myuser\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                34 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            35 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2996: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                35 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if ParseURL(
        b"sullewarehouse.com/register\0" as *const u8 as *const libc::c_char
            as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"sullewarehouse.com/register\", &url_parts)\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            38 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2950: {
        if ParseURL(
            b"sullewarehouse.com/register\0" as *const u8 as *const libc::c_char
                as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"sullewarehouse.com/register\", &url_parts)\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                38 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.scheme).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.scheme) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            39 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2901: {
        if strlen((url_parts.scheme).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.scheme) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                39 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            40 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2850: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"sullewarehouse.com\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"sullewarehouse.com\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                40 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            41 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2802: {
        if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                41 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/register\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/register\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            42 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2750: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/register\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/register\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                42 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            43 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2702: {
        if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                43 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            44 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2654: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                44 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if ParseURL(
        b"http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage\0" as *const u8
            as *const libc::c_char as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage\", &url_parts)\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            47 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2607: {
        if ParseURL(
            b"http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage\0" as *const u8
                as *const libc::c_char as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage\", &url_parts)\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                47 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.scheme).as_mut_ptr(),
        b"http\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.scheme, \"http\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            48 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2556: {
        if strcmp(
            (url_parts.scheme).as_mut_ptr(),
            b"http\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.scheme, \"http\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                48 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"2001:0db8:85a3:0000:0000:8a2e:0370:7334\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"2001:0db8:85a3:0000:0000:8a2e:0370:7334\") == 0\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            49 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2506: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"2001:0db8:85a3:0000:0000:8a2e:0370:7334\0" as *const u8
                as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"2001:0db8:85a3:0000:0000:8a2e:0370:7334\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                49 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            50 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2457: {
        if strlen((url_parts.port).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.port) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                50 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/newpage\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/newpage\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            51 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2406: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/newpage\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/newpage\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                51 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            52 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2358: {
        if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                52 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            53 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2310: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                53 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if ParseURL(
        b"https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog\0" as *const u8
            as *const libc::c_char as *mut libc::c_char,
        &mut url_parts,
    ) {} else {
        __assert_fail(
            b"ParseURL(\"https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog\", &url_parts)\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            56 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2262: {
        if ParseURL(
            b"https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog\0" as *const u8
                as *const libc::c_char as *mut libc::c_char,
            &mut url_parts,
        ) {} else {
            __assert_fail(
                b"ParseURL(\"https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog\", &url_parts)\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                56 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.scheme).as_mut_ptr(),
        b"https\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            57 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2211: {
        if strcmp(
            (url_parts.scheme).as_mut_ptr(),
            b"https\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.scheme, \"https\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                57 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.authority).as_mut_ptr(),
        b"2001:0db8:85a3:0000:0000:8a2e:0370:7334\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.authority, \"2001:0db8:85a3:0000:0000:8a2e:0370:7334\") == 0\0"
                as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            58 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2159: {
        if strcmp(
            (url_parts.authority).as_mut_ptr(),
            b"2001:0db8:85a3:0000:0000:8a2e:0370:7334\0" as *const u8
                as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.authority, \"2001:0db8:85a3:0000:0000:8a2e:0370:7334\") == 0\0"
                    as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                58 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.port).as_mut_ptr(),
        b"2678\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.port, \"2678\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            59 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2107: {
        if strcmp(
            (url_parts.port).as_mut_ptr(),
            b"2678\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.port, \"2678\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                59 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strcmp(
        (url_parts.path).as_mut_ptr(),
        b"/blog\0" as *const u8 as *const libc::c_char,
    ) == 0 as libc::c_int
    {} else {
        __assert_fail(
            b"strcmp(url_parts.path, \"/blog\") == 0\0" as *const u8
                as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            60 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2054: {
        if strcmp(
            (url_parts.path).as_mut_ptr(),
            b"/blog\0" as *const u8 as *const libc::c_char,
        ) == 0 as libc::c_int
        {} else {
            __assert_fail(
                b"strcmp(url_parts.path, \"/blog\") == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                60 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            61 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_2005: {
        if strlen((url_parts.query).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.query) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                61 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
    {} else {
        __assert_fail(
            b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
            b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                as *const libc::c_char,
            62 as libc::c_int as libc::c_uint,
            (*::core::mem::transmute::<
                &[u8; 22],
                &[libc::c_char; 22],
            >(b"void test_parse_url()\0"))
                .as_ptr(),
        );
    }
    'c_1950: {
        if strlen((url_parts.fragment).as_mut_ptr()) == 0 as libc::c_int as libc::c_ulong
        {} else {
            __assert_fail(
                b"strlen(url_parts.fragment) == 0\0" as *const u8 as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-urlparser.c\0" as *const u8
                    as *const libc::c_char,
                62 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 22],
                    &[libc::c_char; 22],
                >(b"void test_parse_url()\0"))
                    .as_ptr(),
            );
        }
    };
    printf(b"All tests passed!\n\0" as *const u8 as *const libc::c_char);
}
unsafe fn main_0() -> libc::c_int {
    test_parse_url();
    return 0 as libc::c_int;
}
pub fn main() {
    unsafe { ::std::process::exit(main_0() as i32) }
}
