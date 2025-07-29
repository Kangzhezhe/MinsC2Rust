use std::rc::Rc;
use std::cell::RefCell;
use std::fmt;

const INITIAL_CAPACITY: usize = 16;

#[derive(Debug)]
pub struct HtEntry<T> {
    pub key: Option<String>,
    pub value: Option<T>,
}

#[derive(Debug)]
pub struct Ht<T> {
    pub entries: Vec<Rc<RefCell<HtEntry<T>>>>,
    pub capacity: usize,
    pub length: usize,
}

pub struct HtIterator<T> {
    pub key: Option<String>,
    pub value: Option<T>,
    pub _table: Rc<RefCell<Ht<T>>>,
    pub _index: usize,
}