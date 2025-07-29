use ::libc;
extern "C" {
    pub type bst;
    fn printf(_: *const libc::c_char, _: ...) -> libc::c_int;
    fn __assert_fail(
        __assertion: *const libc::c_char,
        __file: *const libc::c_char,
        __line: libc::c_uint,
        __function: *const libc::c_char,
    ) -> !;
    fn bst_create() -> *mut bst;
    fn bst_free(bst: *mut bst);
    fn bst_insert(val: libc::c_int, bst: *mut bst);
    fn bst_remove(val: libc::c_int, bst: *mut bst);
    fn bst_contains(val: libc::c_int, bst: *mut bst) -> libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn test_bst() {
    let mut bst: *mut bst = bst_create();
    let mut good_nums: [libc::c_int; 8] = [
        32 as libc::c_int,
        16 as libc::c_int,
        8 as libc::c_int,
        12 as libc::c_int,
        4 as libc::c_int,
        64 as libc::c_int,
        48 as libc::c_int,
        80 as libc::c_int,
    ];
    let mut bad_nums: [libc::c_int; 8] = [
        1 as libc::c_int,
        3 as libc::c_int,
        5 as libc::c_int,
        7 as libc::c_int,
        9 as libc::c_int,
        11 as libc::c_int,
        13 as libc::c_int,
        15 as libc::c_int,
    ];
    let mut i: libc::c_int = 0 as libc::c_int;
    while i < 8 as libc::c_int {
        bst_insert(good_nums[i as usize], bst);
        i += 1;
        i;
    }
    let mut i_0: libc::c_int = 0 as libc::c_int;
    while i_0 < 8 as libc::c_int {
        if bst_contains(good_nums[i_0 as usize], bst) == 1 as libc::c_int {} else {
            __assert_fail(
                b"bst_contains(good_nums[i], bst) == 1\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                    as *const libc::c_char,
                19 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 16],
                    &[libc::c_char; 16],
                >(b"void test_bst()\0"))
                    .as_ptr(),
            );
        }
        'c_942: {
            if bst_contains(good_nums[i_0 as usize], bst) == 1 as libc::c_int {} else {
                __assert_fail(
                    b"bst_contains(good_nums[i], bst) == 1\0" as *const u8
                        as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                        as *const libc::c_char,
                    19 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 16],
                        &[libc::c_char; 16],
                    >(b"void test_bst()\0"))
                        .as_ptr(),
                );
            }
        };
        i_0 += 1;
        i_0;
    }
    printf(
        b"== Verified that BST contains all the expected values.\n\0" as *const u8
            as *const libc::c_char,
    );
    let mut i_1: libc::c_int = 0 as libc::c_int;
    while i_1 < 8 as libc::c_int {
        if bst_contains(bad_nums[i_1 as usize], bst) == 0 as libc::c_int {} else {
            __assert_fail(
                b"bst_contains(bad_nums[i], bst) == 0\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                    as *const libc::c_char,
                24 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 16],
                    &[libc::c_char; 16],
                >(b"void test_bst()\0"))
                    .as_ptr(),
            );
        }
        'c_859: {
            if bst_contains(bad_nums[i_1 as usize], bst) == 0 as libc::c_int {} else {
                __assert_fail(
                    b"bst_contains(bad_nums[i], bst) == 0\0" as *const u8
                        as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                        as *const libc::c_char,
                    24 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 16],
                        &[libc::c_char; 16],
                    >(b"void test_bst()\0"))
                        .as_ptr(),
                );
            }
        };
        i_1 += 1;
        i_1;
    }
    printf(
        b"== Verified that BST contains none of the unexpected values.\n\0" as *const u8
            as *const libc::c_char,
    );
    let mut i_2: libc::c_int = 0 as libc::c_int;
    while i_2 < 8 as libc::c_int {
        bst_remove(good_nums[i_2 as usize], bst);
        if bst_contains(good_nums[i_2 as usize], bst) == 0 {} else {
            __assert_fail(
                b"!bst_contains(good_nums[i], bst)\0" as *const u8
                    as *const libc::c_char,
                b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                    as *const libc::c_char,
                34 as libc::c_int as libc::c_uint,
                (*::core::mem::transmute::<
                    &[u8; 16],
                    &[libc::c_char; 16],
                >(b"void test_bst()\0"))
                    .as_ptr(),
            );
        }
        'c_779: {
            if bst_contains(good_nums[i_2 as usize], bst) == 0 {} else {
                __assert_fail(
                    b"!bst_contains(good_nums[i], bst)\0" as *const u8
                        as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                        as *const libc::c_char,
                    34 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 16],
                        &[libc::c_char; 16],
                    >(b"void test_bst()\0"))
                        .as_ptr(),
                );
            }
        };
        let mut j: libc::c_int = i_2 + 1 as libc::c_int;
        while j < 8 as libc::c_int {
            if bst_contains(good_nums[j as usize], bst) != 0 {} else {
                __assert_fail(
                    b"bst_contains(good_nums[j], bst)\0" as *const u8
                        as *const libc::c_char,
                    b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                        as *const libc::c_char,
                    36 as libc::c_int as libc::c_uint,
                    (*::core::mem::transmute::<
                        &[u8; 16],
                        &[libc::c_char; 16],
                    >(b"void test_bst()\0"))
                        .as_ptr(),
                );
            }
            'c_700: {
                if bst_contains(good_nums[j as usize], bst) != 0 {} else {
                    __assert_fail(
                        b"bst_contains(good_nums[j], bst)\0" as *const u8
                            as *const libc::c_char,
                        b"/home/mins01/exp1/Input/test/test-bst.c\0" as *const u8
                            as *const libc::c_char,
                        36 as libc::c_int as libc::c_uint,
                        (*::core::mem::transmute::<
                            &[u8; 16],
                            &[libc::c_char; 16],
                        >(b"void test_bst()\0"))
                            .as_ptr(),
                    );
                }
            };
            j += 1;
            j;
        }
        i_2 += 1;
        i_2;
    }
    printf(
        b"== Verified removal works as expected.\n\0" as *const u8 as *const libc::c_char,
    );
    bst_free(bst);
}
unsafe fn main_0(
    mut argc: libc::c_int,
    mut argv: *mut *mut libc::c_char,
) -> libc::c_int {
    test_bst();
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
                args.as_mut_ptr() as *mut *mut libc::c_char,
            ) as i32,
        )
    }
}
