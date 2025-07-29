pub const BUFFER_DEFAULT_SIZE: usize = 1024;

#[derive(Clone)]
pub struct Buffer {
    pub len: usize,
    pub alloc: String,
    pub data: String,
}