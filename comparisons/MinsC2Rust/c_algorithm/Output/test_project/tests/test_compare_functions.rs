use test_project::compare_int::{int_compare, int_equal};
use test_project::compare_pointer::{pointer_compare, pointer_equal};
use test_project::compare_string::{
    string_compare, string_equal, string_nocase_compare, string_nocase_equal,
};
#[test]
pub fn test_string_compare() {
    let test1 = "Apple";
    let test2 = "Orange";
    let test3 = "Apple";

    assert!(string_compare(test1, test2) < 0);
    assert!(string_compare(test2, test1) > 0);
    assert!(string_compare(test1, test3) == 0);
}

#[test]
pub fn test_string_nocase_compare() {
    let test1 = "Apple";
    let test2 = "Orange";
    let test3 = "Apple";
    let test4 = "Alpha";
    let test5 = "bravo";
    let test6 = "Charlie";

    // Negative if first argument should be sorted before the second
    assert!(string_nocase_compare(test1, test2) < 0);

    // Positive if the second argument should be sorted before the first
    assert!(string_nocase_compare(test2, test1) > 0);

    // Zero if the two arguments are equal
    assert!(string_nocase_compare(test1, test3) == 0);

    // Check ordering is independent of case
    assert!(string_nocase_compare(test4, test5) < 0);
    assert!(string_nocase_compare(test5, test6) < 0);
}

#[test]
pub fn test_string_nocase_equal() {
    let test1 = "this is a test string";
    let test2 = "this is a test string ";
    let test3 = "this is a test strin";
    let test4 = "this is a test strinG";
    let test5 = "this is a test string";

    // Non-zero (true) if the two strings are equal
    assert!(string_nocase_equal(test1, test5));

    // Zero (false) if the two strings are different

    // Check that length affects the result
    assert!(!string_nocase_equal(test1, test2));
    assert!(!string_nocase_equal(test1, test3));

    // Case insensitive
    assert!(string_nocase_equal(test1, test4));
}

#[test]
pub fn test_int_compare() {
    let mut a = 4;
    let mut b = 8;
    let mut c = 4;

    // If first is less than second, result is negative
    assert!(int_compare(&a, &b) < 0);

    // If first is more than second, result is positive
    assert!(int_compare(&b, &a) > 0);

    // If both are equal, result is zero
    assert!(int_compare(&a, &c) == 0);
}

#[test]
pub fn test_int_equal() {
    let mut a: i32 = 4;
    let mut b: i32 = 8;
    let mut c: i32 = 4;

    assert!(int_equal(&a, &c));
    assert!(!int_equal(&a, &b));
}

#[test]
pub fn test_pointer_equal() {
    let mut a = 0;
    let mut b = 0;

    // Non-zero (true) if the two pointers are equal
    assert!(pointer_equal(&a, &a));

    // Zero (false) if the two pointers are not equal
    assert!(!pointer_equal(&a, &b));
}

#[test]
pub fn test_pointer_compare() {
    let mut array = [0; 5];

    // Negative if first argument is a lower memory address than the second
    assert!(pointer_compare(&array[0], &array[4]) < 0);

    // Positive if the first argument is a higher memory address than the second
    assert!(pointer_compare(&array[3], &array[2]) > 0);

    // Zero if the two arguments are equal
    assert!(pointer_compare(&array[4], &array[4]) == 0);
}

#[test]
pub fn test_string_equal() {
    let test1 = "this is a test string";
    let test2 = "this is a test string ";
    let test3 = "this is a test strin";
    let test4 = "this is a test strinG";
    let test5 = "this is a test string";

    assert!(string_equal(test1, test5));

    assert!(!string_equal(test1, test2));
    assert!(!string_equal(test1, test3));
    assert!(!string_equal(test1, test4));
}
