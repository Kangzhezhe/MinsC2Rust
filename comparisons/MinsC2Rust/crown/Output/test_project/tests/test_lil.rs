pub static mut test_exit_code: i32 = 0;
pub static mut test_running: i32 = 1;
use ntest::timeout;
use std::fmt::Debug;
use std::str::FromStr;
use test_project::lil::{
    alloc_value, alloc_value_len, lil_alloc_string, lil_to_integer, lil_to_string, ExprEvalType,
    Expreval, LilCallbackProc, LilEnv, LilFunc, LilList, LilStruct, LilValue, CALLBACKS,
};
pub fn do_system(argc: usize, argv: Vec<String>) -> Option<String> {
    if argc == 0 {
        return None;
    }

    if argv[0] == "echo" && argc > 1 {
        let mut result = argv[1].clone();
        result.push('\n');
        return Some(result);
    }

    None
}

pub fn do_exit<T: Clone>(lil: &LilStruct<T>, val: &LilValue<T>) {
    unsafe {
        test_running = 0;
        test_exit_code = lil_to_integer(val) as i32;
    }
}

pub fn fnc_system<T: Clone + FromStr + Into<String>>(
    lil: &LilStruct<T>,
    argc: usize,
    argv: Vec<LilValue<T>>,
) -> Option<LilValue<T>>
where
    <T as FromStr>::Err: Debug,
{
    if argc == 0 {
        return None;
    }

    let mut sargv: Vec<String> = Vec::with_capacity(argc);
    for arg in argv.iter().take(argc) {
        sargv.push(lil_to_string(arg));
    }

    let rv = do_system(argc, sargv);
    rv.and_then(|s| alloc_value(Some(s)))
}

pub fn fnc_readline<T: Clone>(
    lil: &LilStruct<T>,
    argc: usize,
    argv: &[LilValue<T>],
) -> Option<LilValue<String>> {
    lil_alloc_string(Some("test_input".to_string()))
}

pub fn fnc_writechar<T: Clone>(
    lil: &LilStruct<T>,
    argc: usize,
    argv: &[LilValue<T>],
) -> Option<LilValue<T>> {
    if argc == 0 {
        return None;
    }
    print!("{}", lil_to_integer(&argv[0]) as u8 as char);
    None
}
