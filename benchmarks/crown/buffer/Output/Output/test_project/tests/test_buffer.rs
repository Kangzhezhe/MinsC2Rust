use ntest::timeout;
use test_project::buffer::{
    buffer_append, buffer_append_n, buffer_appendf, buffer_clear, buffer_compact, buffer_equals,
    buffer_fill, buffer_free, buffer_indexof, buffer_length, buffer_new, buffer_new_with_copy,
    buffer_new_with_size, buffer_prepend, buffer_size, buffer_slice, buffer_trim, buffer_trim_left,
    buffer_trim_right, Buffer, BUFFER_DEFAULT_SIZE,
};
#[test]
#[timeout(60000)]
pub fn test_buffer_prepend() {
    let mut buf = buffer_new().unwrap();
    assert_eq!(0, buffer_append(&mut buf, " World"));
    assert_eq!(0, buffer_prepend(&mut buf, "Hello".to_string()));
    assert_eq!("Hello World".len(), buffer_length(&buf));
    equal("Hello World", &buf.data);
    buffer_free(buf);
}

pub fn equal(a: &str, b: &str) {
    if a != b {
        println!();
        println!("  expected: '{}'", a);
        println!("    actual: '{}'", b);
        println!();
        std::process::exit(1);
    }
}

#[test]
#[timeout(60000)]
pub fn test_buffer_new() {
    let buf = buffer_new().unwrap();
    assert_eq!(BUFFER_DEFAULT_SIZE, buffer_size(&buf));
    assert_eq!(0, buffer_length(&buf));
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_new_with_size() {
    let buf = buffer_new_with_size(1024).unwrap();
    assert_eq!(1024, buffer_size(&buf));
    assert_eq!(0, buffer_length(&buf));
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_slice__end_overflow() {
    let buf = buffer_new_with_copy("Tobi Ferret".to_string()).unwrap();
    let a = buffer_slice(&buf, 5, 1000).unwrap();
    equal("Tobi Ferret", &buf.data);
    equal("Ferret", &a.data);
    buffer_free(a);
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_compact() {
    let mut buf = buffer_new_with_copy("  Hello\n\n ".to_string()).unwrap();
    buffer_trim(&mut buf);
    assert_eq!(5, buffer_length(&buf));
    assert_eq!(10, buffer_size(&buf));

    let removed = buffer_compact(&mut buf);
    assert_eq!(5, removed);
    assert_eq!(5, buffer_length(&buf));
    assert_eq!(5, buffer_size(&buf));
    equal("Hello", &buf.data);

    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_append() {
    let mut buf = buffer_new().unwrap();
    assert_eq!(0, buffer_append(&mut buf, "Hello"));
    assert_eq!(0, buffer_append(&mut buf, " World"));
    assert_eq!("Hello World".len(), buffer_length(&buf));
    equal("Hello World", &buf.data);
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_append_n() {
    let mut buf = buffer_new().unwrap();
    assert_eq!(0, buffer_append_n(&mut buf, "subway", 3));
    assert_eq!(0, buffer_append_n(&mut buf, "marines", 6));
    assert_eq!("submarine".len(), buffer_length(&buf));
    equal("submarine", &buf.data);
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_append__grow() {
    let mut buf = buffer_new_with_size(10).unwrap();
    assert_eq!(0, buffer_append(&mut buf, "Hello"));
    assert_eq!(0, buffer_append(&mut buf, " tobi"));
    assert_eq!(0, buffer_append(&mut buf, " was"));
    assert_eq!(0, buffer_append(&mut buf, " here"));

    let str = "Hello tobi was here";
    equal(str, &buf.data);
    assert_eq!(1024, buffer_size(&buf));
    assert_eq!(str.len(), buffer_length(&buf));
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_prepend_issue_15() {
    let mut file = buffer_new().unwrap();
    assert_eq!(0, buffer_append(&mut file, "layout.bk.html"));
    assert_eq!(0, buffer_prepend(&mut file, "./example/".to_string()));
    assert_eq!("./example/layout.bk.html".len(), buffer_length(&file));
    equal("./example/layout.bk.html", &file.data);
    buffer_free(file);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_fill() {
    let mut buf = buffer_new_with_copy("Hello".to_string()).unwrap();
    assert_eq!(5, buffer_length(&buf));

    buffer_fill(&mut buf, 0);
    assert_eq!(0, buffer_length(&buf));
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_indexof() {
    let buf = buffer_new_with_copy(String::from("Tobi is a ferret")).unwrap();

    let i = buffer_indexof(&buf, String::from("is"));
    assert_eq!(5, i);

    let i = buffer_indexof(&buf, String::from("a"));
    assert_eq!(8, i);

    let i = buffer_indexof(&buf, String::from("something"));
    assert_eq!(-1, i);

    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_trim() {
    let mut buf = buffer_new_with_copy("  Hello\n\n ".to_string()).unwrap();
    buffer_trim(&mut buf);
    equal("Hello", &buf.data);

    buffer_free(buf);

    let mut buf = buffer_new_with_copy("  Hello\n\n ".to_string()).unwrap();
    buffer_trim_left(&mut buf);
    equal("Hello\n\n ", &buf.data);

    buffer_free(buf);

    let mut buf = buffer_new_with_copy("  Hello\n\n ".to_string()).unwrap();
    buffer_trim_right(&mut buf);
    equal("  Hello", &buf.data);

    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_slice__range_error() {
    let buf = buffer_new_with_copy("Tobi Ferret".to_string()).unwrap();
    let a = buffer_slice(&buf, 10, 2);
    assert!(a.is_err());
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_slice__end() {
    let buf = buffer_new_with_copy("Tobi Ferret".to_string()).unwrap();

    let a = buffer_slice(&buf, 5, -1).unwrap();
    equal("Tobi Ferret", &buf.data);
    equal("Ferret", &a.data);

    let b = buffer_slice(&buf, 5, -3).unwrap();
    equal("Ferr", &b.data);

    let c = buffer_slice(&buf, 8, -1).unwrap();
    equal("ret", &c.data);

    buffer_free(buf);
    buffer_free(a);
    buffer_free(b);
    buffer_free(c);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_clear() {
    let mut buf = buffer_new_with_copy("Hello".to_string()).unwrap();
    assert_eq!(5, buffer_length(&buf));

    buffer_clear(&mut buf);
    assert_eq!(0, buffer_length(&buf));
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_formatting() {
    let mut buf = buffer_new().expect("Failed to create buffer");
    let result = buffer_appendf(
        &mut buf,
        "%d %s".to_string(),
        vec!["3".to_string(), "cow".to_string()],
    );
    assert_eq!(0, result);
    equal("3 cow", &buf.data);
    let result = buffer_appendf(
        &mut buf,
        " - 0x%08X".to_string(),
        vec!["0xDEADBEEF".to_string()],
    );
    assert_eq!(0, result);
    equal("3 cow - 0xDEADBEEF", &buf.data);
    buffer_free(buf);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_equals() {
    let a = buffer_new_with_copy("Hello".to_string()).unwrap();
    let b = buffer_new_with_copy("Hello".to_string()).unwrap();

    assert!(buffer_equals(&a, &b));

    buffer_append(&mut b.clone(), " World");
    assert!(!buffer_equals(&a, &b));

    buffer_free(a);
    buffer_free(b);
}

#[test]
#[timeout(60000)]
pub fn test_buffer_slice() {
    let mut buf = buffer_new().unwrap();
    buffer_append(&mut buf, "Tobi Ferret");

    let a = buffer_slice(&buf, 2, 8).unwrap();
    equal("Tobi Ferret", &buf.data);
    equal("bi Fer", &a.data);

    buffer_free(buf);
    buffer_free(a);
}

fn nearest_multiple_of(base: usize, n: usize) -> usize {
    ((n + base - 1) / base) * base
}
