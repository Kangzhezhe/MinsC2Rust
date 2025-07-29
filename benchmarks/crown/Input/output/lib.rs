#![allow(dead_code)]
#![allow(mutable_transmutes)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(non_upper_case_globals)]
#![allow(unused_assignments)]
#![allow(unused_mut)]
#![feature(c_variadic)]
#![feature(extern_types)]
#![feature(label_break_value)]


extern crate libc;
pub mod src {
pub mod src {
pub mod bst;
pub mod buffer;
pub mod ht;
pub mod quadtree;
pub mod rgba;
pub mod urlparser;
} // mod src
pub mod test {
pub mod test_bst;
pub mod test_buffer;
pub mod test_ht;
pub mod test_quadtree;
pub mod test_rgba;
pub mod test_urlparser;
} // mod test
} // mod src
