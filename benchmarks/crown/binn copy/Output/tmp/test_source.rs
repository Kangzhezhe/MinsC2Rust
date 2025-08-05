pub const BINN_STORAGE_MASK: i32 = 0xE0;
pub const BINN_TYPE_MASK: i32 = 0x0F;
pub const BINN_STORAGE_MASK16: i32 = 0xE000;
pub const BINN_TYPE_MASK16: i32 = 0x0FFF;
pub const BINN_STORAGE_VIRTUAL: i32 = 0x80000;
pub const BINN_STORAGE_STRING: i32 = 0xA0;
pub const BINN_STORAGE_NOBYTES: i32 = 0x00;
pub const BINN_STORAGE_CONTAINER: i32 = 0xE0;
pub const BINN_STORAGE_HAS_MORE: i32 = 0x10;
pub const MIN_BINN_SIZE: i32 = 3;

pub const BINN_INT8: i32 = 0x21;
pub const BINN_INT16: i32 = 0x41;
pub const BINN_INT32: i32 = 0x61;
pub const BINN_INT64: i32 = 0x81;
pub const BINN_UINT8: i32 = 0x20;
pub const BINN_UINT16: i32 = 0x40;
pub const BINN_UINT32: i32 = 0x60;
pub const BINN_UINT64: i32 = 0x80;
pub const BINN_SIGNED_INT: i32 = 11;
pub const BINN_UNSIGNED_INT: i32 = 22;

pub const BINN_STRUCT: i32 = 1;
pub const BINN_BUFFER: i32 = 2;
pub const BINN_LIST: i32 = 0xE0;
pub const BINN_MAP: i32 = 0xE1;
pub const BINN_OBJECT: i32 = 0xE2;

pub const MAX_BINN_HEADER: i32 = 9;

pub const BINN_FLOAT32: i32 = 0x62;
pub const BINN_FLOAT64: i32 = 0x82;
pub const BINN_SINGLE_STR: i32 = 0xA6;
pub const BINN_DOUBLE_STR: i32 = 0xA7;

pub const BINN_STRING: i32 = 0xA0;
pub const BINN_HTML: i32 = 0xB001;
pub const BINN_CSS: i32 = 0xB005;
pub const BINN_XML: i32 = 0xB002;
pub const BINN_JSON: i32 = 0xB003;
pub const BINN_JAVASCRIPT: i32 = 0xB004;

pub const BINN_BLOB: i32 = 0xC0;
pub const BINN_JPEG: i32 = 0xD001;
pub const BINN_GIF: i32 = 0xD002;
pub const BINN_PNG: i32 = 0xD003;
pub const BINN_BMP: i32 = 0xD004;

pub const BINN_DECIMAL: i32 = 0xA4;
pub const BINN_CURRENCYSTR: i32 = 0xA5;
pub const BINN_CURRENCY: i32 = 0x83;
pub const BINN_DATE: i32 = 0xA2;
pub const BINN_TIME: i32 = 0xA3;
pub const BINN_DATETIME: i32 = 0xA1;

pub const BINN_BOOL: i32 = 0x80061;
pub const BINN_NULL: i32 = 0x00;

pub const BINN_FAMILY_BINN: i32 = 0xf7;
pub const BINN_FAMILY_INT: i32 = 0xf2;
pub const BINN_FAMILY_FLOAT: i32 = 0xf3;
pub const BINN_FAMILY_STRING: i32 = 0xf4;
pub const BINN_FAMILY_BLOB: i32 = 0xf5;
pub const BINN_FAMILY_BOOL: i32 = 0xf6;
pub const BINN_FAMILY_NULL: i32 = 0xf1;
pub const BINN_FAMILY_NONE: i32 = 0x00;

pub const BINN_MAGIC: i32 = 0x1F22B11F;

pub const BINN_STORAGE_DWORD: i32 = 0x60;
pub const BINN_STORAGE_WORD: i32 = 0x40;
pub const BINN_STORAGE_QWORD: i32 = 0x80;
pub const BINN_TRUE: i32 = 0x01;
pub const BINN_FALSE: i32 = 0x02;

pub const CHUNK_SIZE: i32 = 256;

type binn_mem_free = fn(Vec<u8>);

static mut malloc_fn: Option<Box<dyn Fn(usize) -> Vec<u8>>> = None;
static mut realloc_fn: Option<Box<dyn Fn(Vec<u8>, usize) -> Vec<u8>>> = None;
static mut free_fn: Option<Box<dyn Fn(Vec<u8>)>> = None;

#[derive(Clone)]
pub struct Binn {
    pub header: i32,
    pub allocated: bool,
    pub writable: bool,
    pub dirty: bool,
    pub pbuf: Vec<u8>,
    pub pre_allocated: bool,
    pub alloc_size: i32,
    pub used_size: i32,
    pub type_: i32,
    pub ptr: Vec<u8>,
    pub size: i32,
    pub count: i32,
    pub freefn: Option<binn_mem_free>,
    pub disable_int_compression: bool,
    pub vuint8: u8,
    pub vint16: i16,
    pub vint32: i32,
    pub vint64: i64,
    pub vbool: bool,
}

impl Default for Binn {
    fn default() -> Self {
        Binn {
            header: 0,
            allocated: false,
            writable: false,
            dirty: false,
            pbuf: Vec::new(),
            pre_allocated: false,
            alloc_size: 0,
            used_size: 0,
            type_: 0,
            ptr: Vec::new(),
            size: 0,
            count: 0,
            freefn: None,
            disable_int_compression: false,
            vuint8: 0,
            vint16: 0,
            vint32: 0,
            vint64: 0,
            vbool: false,
        }
    }
}

impl Binn {
    pub fn is_null(&self) -> bool {
        self.type_ == BINN_NULL
    }
}