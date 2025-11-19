use ::libc;
extern "C" {
    pub type _IO_wide_data;
    pub type _IO_codecvt;
    pub type _IO_marker;
    static mut stderr: *mut FILE;
    fn fprintf(_: *mut FILE, _: *const libc::c_char, _: ...) -> libc::c_int;
    fn printf(_: *const libc::c_char, _: ...) -> libc::c_int;
    fn memset(
        _: *mut libc::c_void,
        _: libc::c_int,
        _: libc::c_ulong,
    ) -> *mut libc::c_void;
    fn strstr(_: *const libc::c_char, _: *const libc::c_char) -> *mut libc::c_char;
    fn strlen(_: *const libc::c_char) -> libc::c_ulong;
}
pub type size_t = libc::c_ulong;
pub type __off_t = libc::c_long;
pub type __off64_t = libc::c_long;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct _IO_FILE {
    pub _flags: libc::c_int,
    pub _IO_read_ptr: *mut libc::c_char,
    pub _IO_read_end: *mut libc::c_char,
    pub _IO_read_base: *mut libc::c_char,
    pub _IO_write_base: *mut libc::c_char,
    pub _IO_write_ptr: *mut libc::c_char,
    pub _IO_write_end: *mut libc::c_char,
    pub _IO_buf_base: *mut libc::c_char,
    pub _IO_buf_end: *mut libc::c_char,
    pub _IO_save_base: *mut libc::c_char,
    pub _IO_backup_base: *mut libc::c_char,
    pub _IO_save_end: *mut libc::c_char,
    pub _markers: *mut _IO_marker,
    pub _chain: *mut _IO_FILE,
    pub _fileno: libc::c_int,
    pub _flags2: libc::c_int,
    pub _old_offset: __off_t,
    pub _cur_column: libc::c_ushort,
    pub _vtable_offset: libc::c_schar,
    pub _shortbuf: [libc::c_char; 1],
    pub _lock: *mut libc::c_void,
    pub _offset: __off64_t,
    pub _codecvt: *mut _IO_codecvt,
    pub _wide_data: *mut _IO_wide_data,
    pub _freeres_list: *mut _IO_FILE,
    pub _freeres_buf: *mut libc::c_void,
    pub __pad5: size_t,
    pub _mode: libc::c_int,
    pub _unused2: [libc::c_char; 20],
}
pub type _IO_lock_t = ();
pub type FILE = _IO_FILE;
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
pub unsafe extern "C" fn ParseURL(
    mut URL: *mut libc::c_char,
    mut pURL_Parts: *mut URL_PARTS,
) -> bool {
    let mut i: libc::c_int = 0;
    let mut c: libc::c_uchar = 0;
    let mut b: bool = 0 as libc::c_int != 0;
    memset(
        pURL_Parts as *mut libc::c_void,
        0 as libc::c_int,
        ::core::mem::size_of::<URL_PARTS>() as libc::c_ulong,
    );
    let mut string: *mut libc::c_char = URL;
    let mut authority: *mut libc::c_char = strstr(
        string,
        b"//\0" as *const u8 as *const libc::c_char,
    );
    if authority.is_null() {
        authority = string;
    } else {
        i = 0 as libc::c_int;
        while string < authority {
            let mut c_0: libc::c_uchar = *string as libc::c_uchar;
            if c_0 as libc::c_int == ':' as i32 {
                break;
            } else {
                if c_0 as libc::c_int == '/' as i32 {
                    break;
                }
                if i == 32 as libc::c_int - 1 as libc::c_int {
                    return 0 as libc::c_int != 0;
                }
                (*pURL_Parts).scheme[i as usize] = c_0 as libc::c_char;
                string = string.offset(1);
                string;
                i += 1;
                i;
            }
        }
        authority = authority.offset(2 as libc::c_int as isize);
    }
    c = *authority as libc::c_uchar;
    if c as libc::c_int == '[' as i32 {
        b = 1 as libc::c_int != 0;
        authority = authority.offset(1);
        authority;
    }
    i = 0 as libc::c_int;
    loop {
        c = *authority as libc::c_uchar;
        if !(c as libc::c_int != 0 as libc::c_int) {
            break;
        }
        if c as libc::c_int == ' ' as i32 {
            authority = authority.offset(1);
            authority;
        } else {
            if c as libc::c_int == '/' as i32 {
                break;
            }
            if c as libc::c_int == ':' as i32 {
                if !b {
                    break;
                }
            }
            if c as libc::c_int == '?' as i32 {
                break;
            }
            if c as libc::c_int == '#' as i32 {
                break;
            }
            if b {
                if c as libc::c_int == ']' as i32 {
                    authority = authority.offset(1);
                    authority;
                    break;
                }
            }
            if i == 512 as libc::c_int - 1 as libc::c_int {
                return 0 as libc::c_int != 0;
            }
            (*pURL_Parts).authority[i as usize] = c as libc::c_char;
            authority = authority.offset(1);
            authority;
            i += 1;
            i;
        }
    }
    string = authority;
    if *string as libc::c_int == ':' as i32 {
        string = string.offset(1);
        string;
        i = 0 as libc::c_int;
        loop {
            c = *string as libc::c_uchar;
            if !(c as libc::c_int != 0 as libc::c_int) {
                break;
            }
            if c as libc::c_int == '/' as i32 {
                break;
            }
            if c as libc::c_int == '?' as i32 {
                break;
            }
            if c as libc::c_int == '#' as i32 {
                break;
            }
            if i == 64 as libc::c_int - 1 as libc::c_int {
                return 0 as libc::c_int != 0;
            }
            (*pURL_Parts).port[i as usize] = c as libc::c_char;
            string = string.offset(1);
            string;
            i += 1;
            i;
        }
    }
    if *string as libc::c_int == '/' as i32 {
        i = 0 as libc::c_int;
        loop {
            c = *string as libc::c_uchar;
            if !(c as libc::c_int != 0 as libc::c_int) {
                break;
            }
            if c as libc::c_int == '?' as i32 {
                break;
            }
            if c as libc::c_int == '#' as i32 {
                break;
            }
            if i == 1024 as libc::c_int - 1 as libc::c_int {
                return 0 as libc::c_int != 0;
            }
            (*pURL_Parts).path[i as usize] = c as libc::c_char;
            string = string.offset(1);
            string;
            i += 1;
            i;
        }
    }
    if *string as libc::c_int == '?' as i32 {
        i = 0 as libc::c_int;
        loop {
            c = *string as libc::c_uchar;
            if !(c as libc::c_int != 0 as libc::c_int) {
                break;
            }
            if c as libc::c_int == '#' as i32 {
                break;
            }
            if i == 1024 as libc::c_int - 1 as libc::c_int {
                return 0 as libc::c_int != 0;
            }
            (*pURL_Parts).query[i as usize] = c as libc::c_char;
            string = string.offset(1);
            string;
            i += 1;
            i;
        }
    }
    if *string as libc::c_int == '#' as i32 {
        i = 0 as libc::c_int;
        loop {
            c = *string as libc::c_uchar;
            if !(c as libc::c_int != 0 as libc::c_int) {
                break;
            }
            if i == 256 as libc::c_int - 1 as libc::c_int {
                return 0 as libc::c_int != 0;
            }
            (*pURL_Parts).fragment[i as usize] = c as libc::c_char;
            string = string.offset(1);
            string;
            i += 1;
            i;
        }
    }
    return 1 as libc::c_int != 0;
}
#[no_mangle]
pub unsafe extern "C" fn PrintURL(mut pURL_Parts: *mut URL_PARTS) {
    if pURL_Parts.is_null() {
        fprintf(
            stderr,
            b"%s\n\0" as *const u8 as *const libc::c_char,
            b"PrintURL Error: Parameter 'pURL_Parts' is NULL\0" as *const u8
                as *const libc::c_char,
        );
        return;
    }
    printf(
        b"Scheme: %s\nAuthority: %s\nPort: %s\nPath: %s\nQuery: %s\nFragment: %s\n\0"
            as *const u8 as *const libc::c_char,
        ((*pURL_Parts).scheme).as_mut_ptr(),
        ((*pURL_Parts).authority).as_mut_ptr(),
        ((*pURL_Parts).port).as_mut_ptr(),
        ((*pURL_Parts).path).as_mut_ptr(),
        ((*pURL_Parts).query).as_mut_ptr(),
        ((*pURL_Parts).fragment).as_mut_ptr(),
    );
    if strlen(((*pURL_Parts).scheme).as_mut_ptr()) != 0 as libc::c_int as libc::c_ulong {
        printf(
            b"%s://%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).scheme).as_mut_ptr(),
            ((*pURL_Parts).authority).as_mut_ptr(),
        );
    } else if strlen(((*pURL_Parts).authority).as_mut_ptr())
        != 0 as libc::c_int as libc::c_ulong
    {
        printf(
            b"%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).authority).as_mut_ptr(),
        );
    }
    if strlen(((*pURL_Parts).port).as_mut_ptr()) != 0 as libc::c_int as libc::c_ulong {
        printf(
            b":%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).port).as_mut_ptr(),
        );
    }
    if strlen(((*pURL_Parts).path).as_mut_ptr()) != 0 as libc::c_int as libc::c_ulong {
        printf(
            b"%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).path).as_mut_ptr(),
        );
    }
    if strlen(((*pURL_Parts).query).as_mut_ptr()) != 0 as libc::c_int as libc::c_ulong {
        printf(
            b"%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).query).as_mut_ptr(),
        );
    }
    if strlen(((*pURL_Parts).fragment).as_mut_ptr()) != 0 as libc::c_int as libc::c_ulong
    {
        printf(
            b"%s\0" as *const u8 as *const libc::c_char,
            ((*pURL_Parts).fragment).as_mut_ptr(),
        );
    }
    printf(
        b"%s\0" as *const u8 as *const libc::c_char,
        b"\n\0" as *const u8 as *const libc::c_char,
    );
}
