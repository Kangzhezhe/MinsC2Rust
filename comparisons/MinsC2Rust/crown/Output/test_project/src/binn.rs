pub const BINN_TYPE_MASK: u32 = 0x0F;
pub const BINN_STORAGE_MASK: u32 = 0xE0;
pub const BINN_TYPE_MASK16: u32 = 0x0FFF;
pub const BINN_STORAGE_MASK16: u32 = 0xE000;
pub const BINN_STORAGE_VIRTUAL: u32 = 0x80000;
pub const BINN_STORAGE_STRING: i32 = 0xA0;
pub const BINN_STORAGE_NOBYTES: i32 = 0x00;
pub const BINN_SINGLE_STR: i32 = 0xA6;
pub const BINN_DOUBLE_STR: i32 = 0xA7;
pub const BINN_BOOL: i32 = 0x80061;
pub const CHUNK_SIZE: i32 = 256;
pub const BIG_ENDIAN: u32 = 0x1000;
pub const LITTLE_ENDIAN: u32 = 0x0001;
pub const BINN_INT64: i32 = 0x81;
pub const BINN_INT32: i32 = 0x61;
pub const BINN_INT16: i32 = 0x41;
pub const BINN_INT8: i32 = 0x21;
pub const BINN_UINT64: i32 = 0x80;
pub const BINN_UINT32: i32 = 0x60;
pub const BINN_UINT16: i32 = 0x40;
pub const BINN_UINT8: i32 = 0x20;
pub const BINN_STORAGE_BYTE: i32 = 0x20;
pub const INT8_MIN: i64 = -128;
pub const INT16_MIN: i64 = -32768;
pub const INT32_MIN: i64 = -2147483648;
pub const INT8_MAX: i64 = 127;
pub const INT16_MAX: i64 = 32767;
pub const INT32_MAX: i64 = 2147483647;
pub const UINT8_MAX: u64 = 255;
pub const UINT16_MAX: u64 = 65535;
pub const UINT32_MAX: u64 = 4294967295;
pub const BINN_UNSIGNED_INT: i32 = 22;
pub const BINN_SIGNED_INT: i32 = 11;
pub const BINN_STORAGE_BLOB: i32 = 0xC0;
pub const BINN_STORAGE_HAS_MORE: u8 = 0x80;
pub const BINN_STORAGE_WORD: i32 = 0x40;
pub const BINN_STORAGE_DWORD: i32 = 0x60;
pub const BINN_STORAGE_QWORD: i32 = 0x80;
pub const BINN_STORAGE_CONTAINER: i32 = 0xE0;
pub const MIN_BINN_SIZE: i32 = 3;
pub const MAX_BINN_HEADER: usize = 9;
pub const NULL: i32 = 0;
pub const BINN_STRUCT: i32 = 1;
pub const BINN_BUFFER: i32 = 2;
pub const BINN_MAGIC: u32 = 0x1F22B11F;
pub const BINN_FLOAT64: i32 = 0x82;
pub const BINN_LIST: i32 = 0xE0;
pub const BINN_GIF: i32 = 0xD002;
pub const BINN_DOUBLE: i32 = BINN_FLOAT64;
pub const BINN_HTML: i32 = 0xB001;
pub const BINN_BLOB: i32 = 0xC0;
pub const BINN_FAMILY_NULL: i32 = 0xF1;
pub const BINN_FAMILY_FLOAT: i32 = 0xF3;
pub const BINN_JPEG: i32 = 0xD001;
pub const BINN_CSS: i32 = 0xB005;
pub const BINN_STRING: i32 = 0xA0;
pub const BINN_FAMILY_BLOB: i32 = 0xF5;
pub const BINN_JAVASCRIPT: i32 = 0xB004;
pub const BINN_FAMILY_INT: i32 = 0xF2;
pub const BINN_JSON: i32 = 0xB003;
pub const BINN_OBJECT: i32 = 0xE2;
pub const BINN_SINGLE: i32 = BINN_FLOAT32;
pub const BINN_FLOAT32: i32 = 0x62;
pub const BINN_FAMILY_BOOL: i32 = 0xF6;
pub const BINN_DATE: i32 = 0xA2;
pub const BINN_NULL: i32 = 0x00;
pub const BINN_DATETIME: i32 = 0xA1;
pub const BINN_BMP: i32 = 0xD004;
pub const BINN_MAP: i32 = 0xE1;
pub const BINN_PNG: i32 = 0xD003;
pub const BINN_CURRENCY: i32 = 0x83;
pub const BINN_DECIMAL: i32 = 0xA4;
pub const BINN_TIME: i32 = 0xA3;
pub const BINN_XML: i32 = 0xB002;
pub const BINN_FAMILY_NONE: i32 = 0x00;
pub const BINN_FAMILY_STRING: i32 = 0xF4;
pub const BINN_FAMILY_BINN: i32 = 0xF7;
pub const BINN_TRUE: i32 = 0x01;
pub const BINN_FALSE: i32 = 0x02;
pub const BINN_CURRENCYSTR: i32 = 0xA5;
pub const INT64_MIN: i64 = -9223372036854775808;
pub const INT64_MAX: i64 = 9223372036854775807;

pub static mut malloc_fn: Option<fn(usize) -> Option<Box<[u8]>>> = None;
pub static mut realloc_fn: Option<fn(Option<Box<[u8]>>, usize) -> Option<Box<[u8]>>> = None;
pub static mut free_fn: Option<fn(Option<Box<[u8]>>)> = None;

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
    pub freefn: Option<fn(Vec<u8>)>,
    pub vint8: i8,
    pub vint16: i16,
    pub vint32: i32,
    pub vint64: i64,
    pub vuint8: u8,
    pub vuint16: u16,
    pub vuint32: u32,
    pub vuint64: u64,
    pub vchar: i8,
    pub vuchar: u8,
    pub vshort: i16,
    pub vushort: u16,
    pub vint: i32,
    pub vuint: u32,
    pub vfloat: f32,
    pub vdouble: f64,
    pub vbool: bool,
    pub disable_int_compression: bool,
}

impl Clone for Binn {
    fn clone(&self) -> Self {
        Binn {
            header: self.header,
            allocated: self.allocated,
            writable: self.writable,
            dirty: self.dirty,
            pbuf: self.pbuf.clone(),
            pre_allocated: self.pre_allocated,
            alloc_size: self.alloc_size,
            used_size: self.used_size,
            type_: self.type_,
            ptr: self.ptr.clone(),
            size: self.size,
            count: self.count,
            freefn: self.freefn,
            vint8: self.vint8,
            vint16: self.vint16,
            vint32: self.vint32,
            vint64: self.vint64,
            vuint8: self.vuint8,
            vuint16: self.vuint16,
            vuint32: self.vuint32,
            vuint64: self.vuint64,
            vchar: self.vchar,
            vuchar: self.vuchar,
            vshort: self.vshort,
            vushort: self.vushort,
            vint: self.vint,
            vuint: self.vuint,
            vfloat: self.vfloat,
            vdouble: self.vdouble,
            vbool: self.vbool,
            disable_int_compression: self.disable_int_compression,
        }
    }
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
            vint8: 0,
            vint16: 0,
            vint32: 0,
            vint64: 0,
            vuint8: 0,
            vuint16: 0,
            vuint32: 0,
            vuint64: 0,
            vchar: 0,
            vuchar: 0,
            vshort: 0,
            vushort: 0,
            vint: 0,
            vuint: 0,
            vfloat: 0.0,
            vdouble: 0.0,
            vbool: false,
            disable_int_compression: false,
        }
    }
}

impl Binn {
    pub fn is_null(&self) -> bool {
        self.header == 0
    }
}

pub const BINN_VERSION: &str = "3.0.0";

pub struct BinnIter {
    pub pnext: Vec<u8>,
    pub plimit: Vec<u8>,
    pub current: i32,
    pub count: i32,
    pub type_: i32,
}

impl Default for BinnIter {
    fn default() -> Self {
        BinnIter {
            pnext: Vec::new(),
            plimit: Vec::new(),
            current: 0,
            count: 0,
            type_: 0,
        }
    }
}

impl BinnIter {
    pub fn is_null(&self) -> bool {
        self.pnext.is_empty()
    }
}

pub const INVALID_BINN: i32 = 0;
pub const BINN_STORAGE_MAX: i32 = BINN_STORAGE_CONTAINER;
pub const BINN_STORAGE_MIN: i32 = BINN_STORAGE_NOBYTES;

pub fn binn_get_type_info(long_type: i32, pstorage_type: Option<&mut i32>, pextra_type: Option<&mut i32>) -> bool {
    let mut storage_type: i32;
    let mut extra_type: i32;
    let mut retval = true;
    let mut current_type = long_type;

    loop {
        if current_type < 0 {
            storage_type = -1;
            extra_type = -1;
            retval = false;
            break;
        } else if current_type <= 0xff {
            storage_type = (current_type & BINN_STORAGE_MASK as i32) as i32;
            extra_type = (current_type & BINN_TYPE_MASK as i32) as i32;
            break;
        } else if current_type <= 0xffff {
            storage_type = (current_type & BINN_STORAGE_MASK16 as i32) as i32;
            storage_type >>= 8;
            extra_type = (current_type & BINN_TYPE_MASK16 as i32) as i32;
            extra_type >>= 4;
            break;
        } else if (current_type & BINN_STORAGE_VIRTUAL as i32) != 0 {
            current_type &= 0xffff;
            continue;
        } else {
            storage_type = -1;
            extra_type = -1;
            retval = false;
            break;
        }
    }

    if let Some(storage) = pstorage_type {
        *storage = storage_type;
    }
    if let Some(extra) = pextra_type {
        *extra = extra_type;
    }

    retval
}

pub fn binn_get_write_storage(type_: i32) -> i32 {
    let mut storage_type: i32 = 0;

    match type_ {
        BINN_SINGLE_STR | BINN_DOUBLE_STR => BINN_STORAGE_STRING,
        BINN_BOOL => BINN_STORAGE_NOBYTES,
        _ => {
            binn_get_type_info(type_, Some(&mut storage_type), None);
            storage_type
        }
    }
}

pub fn CalcAllocation(needed_size: i32, alloc_size: i32) -> i32 {
    let mut calc_size = alloc_size;
    while calc_size < needed_size {
        calc_size <<= 1;
    }
    calc_size
}

pub fn copy_be32(pdest: &mut [u8; 4], psource: &u32) {
    *pdest = psource.to_be_bytes();
}

pub fn check_alloc_functions() {
    unsafe {
        if malloc_fn.is_none() {
            malloc_fn = Some(|size| vec![0u8; size].into_boxed_slice().into());
        }
        if realloc_fn.is_none() {
            realloc_fn = Some(|ptr, size| {
                let mut new_vec = vec![0u8; size];
                if let Some(p) = ptr {
                    let len = std::cmp::min(p.len(), size);
                    new_vec[..len].copy_from_slice(&p[..len]);
                }
                new_vec.into_boxed_slice().into()
            });
        }
        if free_fn.is_none() {
            free_fn = Some(|_| {});
        }
    }
}

pub fn copy_be16(pdest: &mut [u8; 2], psource: &u16) {
    *pdest = psource.to_be_bytes();
}

pub fn compress_int<'a>(pstorage_type: &mut i32, ptype: &mut i32, psource: &'a mut [u8]) -> &'a mut [u8] {
    let mut storage_type = *pstorage_type;
    if storage_type == BINN_STORAGE_BYTE {
        return psource;
    }

    let type_ = *ptype;
    let mut type2 = 0;
    let mut vint: i64 = 0;
    let mut vuint: u64 = 0;

    match type_ {
        BINN_INT64 => {
            let mut buf = [0u8; 8];
            buf.copy_from_slice(&psource[..8]);
            vint = i64::from_le_bytes(buf);
            if vint >= 0 {
                vuint = vint as u64;
                if vuint <= UINT8_MAX {
                    type2 = BINN_UINT8;
                } else if vuint <= UINT16_MAX {
                    type2 = BINN_UINT16;
                } else if vuint <= UINT32_MAX {
                    type2 = BINN_UINT32;
                }
            } else {
                if vint >= INT8_MIN {
                    type2 = BINN_INT8;
                } else if vint >= INT16_MIN {
                    type2 = BINN_INT16;
                } else if vint >= INT32_MIN {
                    type2 = BINN_INT32;
                }
            }
        },
        BINN_INT32 => {
            let mut buf = [0u8; 4];
            buf.copy_from_slice(&psource[..4]);
            vint = i32::from_le_bytes(buf) as i64;
            if vint >= 0 {
                vuint = vint as u64;
                if vuint <= UINT8_MAX {
                    type2 = BINN_UINT8;
                } else if vuint <= UINT16_MAX {
                    type2 = BINN_UINT16;
                } else if vuint <= UINT32_MAX {
                    type2 = BINN_UINT32;
                }
            } else {
                if vint >= INT8_MIN {
                    type2 = BINN_INT8;
                } else if vint >= INT16_MIN {
                    type2 = BINN_INT16;
                } else if vint >= INT32_MIN {
                    type2 = BINN_INT32;
                }
            }
        },
        BINN_INT16 => {
            let mut buf = [0u8; 2];
            buf.copy_from_slice(&psource[..2]);
            vint = i16::from_le_bytes(buf) as i64;
            if vint >= 0 {
                vuint = vint as u64;
                if vuint <= UINT8_MAX {
                    type2 = BINN_UINT8;
                } else if vuint <= UINT16_MAX {
                    type2 = BINN_UINT16;
                } else if vuint <= UINT32_MAX {
                    type2 = BINN_UINT32;
                }
            } else {
                if vint >= INT8_MIN {
                    type2 = BINN_INT8;
                } else if vint >= INT16_MIN {
                    type2 = BINN_INT16;
                } else if vint >= INT32_MIN {
                    type2 = BINN_INT32;
                }
            }
        },
        BINN_UINT64 => {
            let mut buf = [0u8; 8];
            buf.copy_from_slice(&psource[..8]);
            vuint = u64::from_le_bytes(buf);
            if vuint <= UINT8_MAX {
                type2 = BINN_UINT8;
            } else if vuint <= UINT16_MAX {
                type2 = BINN_UINT16;
            } else if vuint <= UINT32_MAX {
                type2 = BINN_UINT32;
            }
        },
        BINN_UINT32 => {
            let mut buf = [0u8; 4];
            buf.copy_from_slice(&psource[..4]);
            vuint = u32::from_le_bytes(buf) as u64;
            if vuint <= UINT8_MAX {
                type2 = BINN_UINT8;
            } else if vuint <= UINT16_MAX {
                type2 = BINN_UINT16;
            } else if vuint <= UINT32_MAX {
                type2 = BINN_UINT32;
            }
        },
        BINN_UINT16 => {
            let mut buf = [0u8; 2];
            buf.copy_from_slice(&psource[..2]);
            vuint = u16::from_le_bytes(buf) as u64;
            if vuint <= UINT8_MAX {
                type2 = BINN_UINT8;
            } else if vuint <= UINT16_MAX {
                type2 = BINN_UINT16;
            } else if vuint <= UINT32_MAX {
                type2 = BINN_UINT32;
            }
        },
        _ => return psource,
    }

    if type2 != 0 && type2 != type_ {
        *ptype = type2;
        let storage_type2 = binn_get_write_storage(type2);
        *pstorage_type = storage_type2;
    }

    psource
}

pub fn int_type(type_: i32) -> i32 {
    match type_ {
        BINN_INT8 | BINN_INT16 | BINN_INT32 | BINN_INT64 => BINN_SIGNED_INT,
        BINN_UINT8 | BINN_UINT16 | BINN_UINT32 | BINN_UINT64 => BINN_UNSIGNED_INT,
        _ => 0,
    }
}

pub fn AdvanceDataPos(p: &mut Vec<u8>, plimit: usize) -> Option<usize> {
    if p.len() > plimit {
        return None;
    }

    let byte = p[0];
    let storage_type = byte as i32 & BINN_STORAGE_MASK as i32;
    let mut pos = 1;

    if byte & BINN_STORAGE_HAS_MORE != 0 {
        pos += 1;
    }

    match storage_type {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_BYTE => pos += 1,
        BINN_STORAGE_WORD => pos += 2,
        BINN_STORAGE_DWORD => pos += 4,
        BINN_STORAGE_QWORD => pos += 8,
        BINN_STORAGE_BLOB => {
            if pos > plimit {
                return None;
            }
            let mut data_size = p[pos] as u32;
            if data_size & 0x80 != 0 {
                if pos + 4 - 1 > plimit {
                    return None;
                }
                let size_bytes = u32::from_be_bytes([p[pos], p[pos+1], p[pos+2], p[pos+3]]);
                data_size = size_bytes & 0x7FFFFFFF;
                pos += 4;
            } else {
                pos += 1;
            }
            pos += data_size as usize;
        },
        BINN_STORAGE_STRING => {
            if pos > plimit {
                return None;
            }
            let mut data_size = p[pos] as u32;
            if data_size & 0x80 != 0 {
                if pos + 4 - 1 > plimit {
                    return None;
                }
                let size_bytes = u32::from_be_bytes([p[pos], p[pos+1], p[pos+2], p[pos+3]]);
                data_size = size_bytes & 0x7FFFFFFF;
                pos += 4;
            } else {
                pos += 1;
            }
            pos += data_size as usize;
            pos += 1;
        },
        BINN_STORAGE_CONTAINER => {
            if pos > plimit {
                return None;
            }
            let mut data_size = p[pos] as u32;
            if data_size & 0x80 != 0 {
                if pos + 4 - 1 > plimit {
                    return None;
                }
                let size_bytes = u32::from_be_bytes([p[pos], p[pos+1], p[pos+2], p[pos+3]]);
                data_size = size_bytes & 0x7FFFFFFF;
            }
            data_size -= 1;
            pos += data_size as usize;
        },
        _ => return None,
    }

    if pos > plimit {
        None
    } else {
        Some(pos)
    }
}

pub fn binn_save_header(item: &mut Binn) -> bool {
    if item.pbuf.is_empty() {
        return false;
    }

    let mut p = item.pbuf[MAX_BINN_HEADER..].to_vec();
    let mut size = item.used_size - MAX_BINN_HEADER as i32 + 3;

    if item.count > 127 {
        p = p[4..].to_vec();
        size += 3;
        let int32 = (item.count as u32) | 0x80000000;
        let mut dest = [0; 4];
        copy_be32(&mut dest, &int32);
        p[..4].copy_from_slice(&dest);
    } else {
        p = p[1..].to_vec();
        p[0] = item.count as u8;
    }

    if size > 127 {
        p = p[4..].to_vec();
        size += 3;
        let int32 = (size as u32) | 0x80000000;
        let mut dest = [0; 4];
        copy_be32(&mut dest, &int32);
        p[..4].copy_from_slice(&dest);
    } else {
        p = p[1..].to_vec();
        p[0] = size as u8;
    }

    p = p[1..].to_vec();
    p[0] = item.type_ as u8;

    item.ptr = p;
    item.size = size;
    item.dirty = false;

    true
}

pub fn binn_get_ptr_type(ptr: Option<&Vec<u8>>) -> i32 {
    if ptr.is_none() {
        return 0;
    }
    let ptr = ptr.unwrap();
    if ptr.len() < 4 {
        return BINN_BUFFER;
    }
    let magic = (ptr[0] as u32) << 24 | (ptr[1] as u32) << 16 | (ptr[2] as u32) << 8 | ptr[3] as u32;
    if magic == BINN_MAGIC {
        BINN_STRUCT
    } else {
        BINN_BUFFER
    }
}

pub fn copy_be64(pdest: &mut [u8; 8], psource: &u64) {
    *pdest = psource.to_be_bytes();
}

pub fn IsValidBinnHeader(pbuf: &[u8], ptype: &mut i32, pcount: &mut i32, psize: &mut i32, pheadersize: &mut i32) -> bool {
    let mut p = 0;
    let mut plimit = 0usize;
    let mut int32: i32;
    let mut type_: i32;
    let mut size: i32;
    let mut count: i32;

    if pbuf.is_empty() {
        return false;
    }

    if *psize > 0 {
        if *psize < 3 {
            return false;
        }
        plimit = (*psize - 1) as usize;
    }

    let byte = pbuf[p];
    p += 1;
    if (byte & (BINN_STORAGE_MASK as u8)) != (BINN_STORAGE_CONTAINER as u8) {
        return false;
    }
    if (byte & (BINN_STORAGE_HAS_MORE as u8)) != 0 {
        return false;
    }
    type_ = byte as i32;

    match type_ {
        0xE0 | 0xE1 | 0xE2 => (),
        _ => return false,
    }

    if plimit > 0 && p > plimit {
        return false;
    }
    int32 = pbuf[p] as i32;
    if (int32 & 0x80) != 0 {
        if plimit > 0 && p + 4 - 1 > plimit {
            return false;
        }
        let mut bytes = [0u8; 4];
        bytes.copy_from_slice(&pbuf[p..p+4]);
        int32 = i32::from_be_bytes(bytes) & 0x7FFFFFFF;
        p += 4;
    } else {
        p += 1;
    }
    size = int32;

    if plimit > 0 && p > plimit {
        return false;
    }
    int32 = pbuf[p] as i32;
    if (int32 & 0x80) != 0 {
        if plimit > 0 && p + 4 - 1 > plimit {
            return false;
        }
        let mut bytes = [0u8; 4];
        bytes.copy_from_slice(&pbuf[p..p+4]);
        int32 = i32::from_be_bytes(bytes) & 0x7FFFFFFF;
        p += 4;
    } else {
        p += 1;
    }
    count = int32;

    if size < 3 || count < 0 {
        return false;
    }

    if *ptype != 0 {
        *ptype = type_;
    }
    if *pcount != 0 {
        *pcount = count;
    }
    if *psize != 0 {
        *psize = size;
    }
    if *pheadersize != 0 {
        *pheadersize = p as i32;
    }
    true
}

pub fn CheckAllocation(item: &mut Binn, add_size: i32) -> bool {
    if item.used_size + add_size > item.alloc_size {
        if item.pre_allocated {
            return false;
        }
        let alloc_size = CalcAllocation(item.used_size + add_size, item.alloc_size);
        let mut new_buf = Vec::with_capacity(alloc_size as usize);
        new_buf.extend_from_slice(&item.pbuf);
        item.pbuf = new_buf;
        item.alloc_size = alloc_size;
    }
    true
}

pub fn strlen2(str: String) -> usize {
    if str.is_empty() {
        return 0;
    }
    str.len()
}

pub fn type_family(type_: i32) -> i32 {
    match type_ {
        BINN_LIST | BINN_MAP | BINN_OBJECT => BINN_FAMILY_BINN,
        BINN_INT8 | BINN_INT16 | BINN_INT32 | BINN_INT64 | BINN_UINT8 | BINN_UINT16 | BINN_UINT32 | BINN_UINT64 => BINN_FAMILY_INT,
        BINN_FLOAT32 | BINN_FLOAT64 | BINN_SINGLE_STR | BINN_DOUBLE_STR => BINN_FAMILY_FLOAT,
        BINN_STRING | BINN_HTML | BINN_CSS | BINN_XML | BINN_JSON | BINN_JAVASCRIPT => BINN_FAMILY_STRING,
        BINN_BLOB | BINN_JPEG | BINN_GIF | BINN_PNG | BINN_BMP => BINN_FAMILY_BLOB,
        BINN_DECIMAL | BINN_CURRENCY | BINN_DATE | BINN_TIME | BINN_DATETIME => BINN_FAMILY_STRING,
        BINN_BOOL => BINN_FAMILY_BOOL,
        BINN_NULL => BINN_FAMILY_NULL,
        _ => BINN_FAMILY_NONE,
    }
}

pub fn read_map_id(pp: &mut Vec<u8>, plimit: &u8) -> i32 {
    let mut p = pp.clone();
    let mut id: i32 = 0;
    let mut extra_bytes: i32 = 0;
    let mut sign: u8 = 0;
    let mut type_: u8 = 0;

    if p.len() == 0 || &p[0] > plimit {
        return 0;
    }

    let c = p.remove(0);

    if c & 0x80 != 0 {
        extra_bytes = (((c & 0x60) >> 5) as i32) + 1;
        if p.len() < extra_bytes as usize || &p[extra_bytes as usize - 1] > plimit {
            *pp = p[extra_bytes as usize..].to_vec();
            return 0;
        }
    }

    type_ = c & 0xE0;
    sign = c & 0x10;

    if (c & 0x80) == 0 {
        sign = c & 0x40;
        id = (c & 0x3F) as i32;
    } else if type_ == 0x80 {
        id = (c & 0x0F) as i32;
        id = (id << 8) | (p.remove(0) as i32);
    } else if type_ == 0xA0 {
        id = (c & 0x0F) as i32;
        id = (id << 8) | (p.remove(0) as i32);
        id = (id << 8) | (p.remove(0) as i32);
    } else if type_ == 0xC0 {
        id = (c & 0x0F) as i32;
        id = (id << 8) | (p.remove(0) as i32);
        id = (id << 8) | (p.remove(0) as i32);
        id = (id << 8) | (p.remove(0) as i32);
    } else if type_ == 0xE0 {
        let mut bytes = [0u8; 4];
        bytes.copy_from_slice(&p[0..4]);
        id = i32::from_be_bytes(bytes);
        p.drain(0..4);
    } else {
        *pp = vec![];
        return 0;
    }

    if sign != 0 {
        id = -id;
    }

    *pp = p;

    id
}

pub fn binn_get_read_storage(type_: i32) -> i32 {
    let mut storage_type = 0;

    match type_ {
        BINN_SINGLE_STR => BINN_STORAGE_DWORD,
        BINN_DOUBLE_STR => BINN_STORAGE_QWORD,
        BINN_BOOL | BINN_TRUE | BINN_FALSE => BINN_STORAGE_DWORD,
        _ => {
            binn_get_type_info(type_, Some(&mut storage_type), None);
            storage_type
        }
    }
}

pub fn copy_raw_value<T: Copy>(psource: &T, pdest: &mut T, data_store: i32) -> bool {
    match data_store {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_BYTE => *pdest = *psource,
        BINN_STORAGE_WORD => *pdest = *psource,
        BINN_STORAGE_DWORD => *pdest = *psource,
        BINN_STORAGE_QWORD => *pdest = *psource,
        BINN_STORAGE_BLOB | BINN_STORAGE_STRING | BINN_STORAGE_CONTAINER => *pdest = *psource,
        _ => return false,
    }
    true
}

pub fn copy_int_value(psource: &dyn std::any::Any, pdest: &mut dyn std::any::Any, source_type: i32, dest_type: i32) -> bool {
    let mut vuint64: u64 = 0;
    let mut vint64: i64 = 0;

    match source_type {
        BINN_INT8 => {
            if let Some(v) = psource.downcast_ref::<i8>() {
                vint64 = *v as i64;
            } else {
                return false;
            }
        },
        BINN_INT16 => {
            if let Some(v) = psource.downcast_ref::<i16>() {
                vint64 = *v as i64;
            } else {
                return false;
            }
        },
        BINN_INT32 => {
            if let Some(v) = psource.downcast_ref::<i32>() {
                vint64 = *v as i64;
            } else {
                return false;
            }
        },
        BINN_INT64 => {
            if let Some(v) = psource.downcast_ref::<i64>() {
                vint64 = *v;
            } else {
                return false;
            }
        },

        BINN_UINT8 => {
            if let Some(v) = psource.downcast_ref::<u8>() {
                vuint64 = *v as u64;
            } else {
                return false;
            }
        },
        BINN_UINT16 => {
            if let Some(v) = psource.downcast_ref::<u16>() {
                vuint64 = *v as u64;
            } else {
                return false;
            }
        },
        BINN_UINT32 => {
            if let Some(v) = psource.downcast_ref::<u32>() {
                vuint64 = *v as u64;
            } else {
                return false;
            }
        },
        BINN_UINT64 => {
            if let Some(v) = psource.downcast_ref::<u64>() {
                vuint64 = *v;
            } else {
                return false;
            }
        },

        _ => return false,
    }

    if int_type(source_type) == BINN_UNSIGNED_INT && int_type(dest_type) == BINN_SIGNED_INT {
        if vuint64 > i64::MAX as u64 {
            return false;
        }
        vint64 = vuint64 as i64;
    } else if int_type(source_type) == BINN_SIGNED_INT && int_type(dest_type) == BINN_UNSIGNED_INT {
        if vint64 < 0 {
            return false;
        }
        vuint64 = vint64 as u64;
    }

    match dest_type {
        BINN_INT8 => {
            if vint64 < INT8_MIN as i64 || vint64 > INT8_MAX as i64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<i8>() {
                *p = vint64 as i8;
            } else {
                return false;
            }
        },
        BINN_INT16 => {
            if vint64 < INT16_MIN as i64 || vint64 > INT16_MAX as i64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<i16>() {
                *p = vint64 as i16;
            } else {
                return false;
            }
        },
        BINN_INT32 => {
            if vint64 < INT32_MIN as i64 || vint64 > INT32_MAX as i64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<i32>() {
                *p = vint64 as i32;
            } else {
                return false;
            }
        },
        BINN_INT64 => {
            if let Some(p) = pdest.downcast_mut::<i64>() {
                *p = vint64;
            } else {
                return false;
            }
        },

        BINN_UINT8 => {
            if vuint64 > UINT8_MAX as u64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<u8>() {
                *p = vuint64 as u8;
            } else {
                return false;
            }
        },
        BINN_UINT16 => {
            if vuint64 > UINT16_MAX as u64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<u16>() {
                *p = vuint64 as u16;
            } else {
                return false;
            }
        },
        BINN_UINT32 => {
            if vuint64 > UINT32_MAX as u64 {
                return false;
            }
            if let Some(p) = pdest.downcast_mut::<u32>() {
                *p = vuint64 as u32;
            } else {
                return false;
            }
        },
        BINN_UINT64 => {
            if let Some(p) = pdest.downcast_mut::<u64>() {
                *p = vuint64;
            } else {
                return false;
            }
        },

        _ => return false,
    }

    true
}

pub fn copy_float_value(psource: f32, pdest: &mut f64, source_type: i32, dest_type: i32) -> bool {
    match source_type {
        BINN_FLOAT32 => {
            *pdest = f64::from(psource);
            true
        }
        BINN_FLOAT64 => {
            *pdest = psource as f64;
            true
        }
        _ => false,
    }
}

pub fn SearchForKey(p: &mut Vec<u8>, header_size: usize, size: usize, numitems: usize, key: &str) -> Option<usize> {
    let base = 0;
    let plimit = size - 1;
    let mut pos = header_size;
    let keylen = key.len();

    for _ in 0..numitems {
        if pos > plimit {
            break;
        }
        let len = p[pos] as usize;
        pos += 1;
        if pos + len > plimit {
            break;
        }
        if len > 0 {
            if key.len() >= len && key[..len].eq_ignore_ascii_case(&String::from_utf8_lossy(&p[pos..pos+len])) {
                if keylen == len {
                    pos += len;
                    return Some(pos);
                }
            }
            pos += len;
        } else if keylen == 0 {
            return Some(pos);
        }
        match AdvanceDataPos(&mut p[pos..].to_vec(), plimit - pos) {
            Some(advance) => pos += advance,
            None => break,
        }
        if pos < base {
            break;
        }
    }

    None
}

pub fn binn_ptr(ptr: Option<&Vec<u8>>) -> Option<Vec<u8>> {
    let item_type = binn_get_ptr_type(ptr);
    match item_type {
        BINN_STRUCT => {
            if let Some(ptr_data) = ptr {
                let mut item = Binn {
                    header: 0,
                    allocated: false,
                    writable: false,
                    dirty: false,
                    pbuf: ptr_data.clone(),
                    pre_allocated: false,
                    alloc_size: 0,
                    used_size: 0,
                    type_: 0,
                    ptr: Vec::new(),
                    size: 0,
                    count: 0,
                    freefn: None,
                    vint8: 0,
                    vint16: 0,
                    vint32: 0,
                    vint64: 0,
                    vuint8: 0,
                    vuint16: 0,
                    vuint32: 0,
                    vuint64: 0,
                    vchar: 0,
                    vuchar: 0,
                    vshort: 0,
                    vushort: 0,
                    vint: 0,
                    vuint: 0,
                    vfloat: 0.0,
                    vdouble: 0.0,
                    vbool: false,
                    disable_int_compression: false,
                };
                if item.writable && item.dirty {
                    binn_save_header(&mut item);
                }
                Some(item.ptr)
            } else {
                None
            }
        },
        BINN_BUFFER => ptr.cloned(),
        _ => None,
    }
}

pub fn GetValue(p: &mut Vec<u8>, plimit: &mut Vec<u8>, value: &mut Binn) -> bool {
    let mut byte: u8;
    let mut data_type: i32;
    let mut storage_type: i32;
    let mut data_size: i32;
    let p2 = p.clone();

    if value.is_null() {
        return false;
    }
    *value = Binn::default();
    value.header = BINN_MAGIC as i32;

    if p.len() > plimit.len() {
        return false;
    }
    byte = p.remove(0);
    storage_type = (byte & (BINN_STORAGE_MASK as u8)) as i32;
    if (byte & BINN_STORAGE_HAS_MORE) != 0 {
        data_type = (byte as i32) << 8;
        if p.len() > plimit.len() {
            return false;
        }
        byte = p.remove(0);
        data_type |= byte as i32;
    } else {
        data_type = byte as i32;
    }

    value.type_ = data_type;

    match storage_type {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_BYTE => {
            if p.len() > plimit.len() {
                return false;
            }
            value.vuint8 = p.remove(0);
            value.ptr = vec![value.vuint8];
        },
        BINN_STORAGE_WORD => {
            if p.len() + 1 > plimit.len() {
                return false;
            }
            let mut vint16_bytes = [0u8; 2];
            vint16_bytes.copy_from_slice(&p[..2]);
            value.vint16 = i16::from_be_bytes(vint16_bytes);
            p.drain(..2);
            value.ptr = value.vint16.to_be_bytes().to_vec();
        },
        BINN_STORAGE_DWORD => {
            if p.len() + 3 > plimit.len() {
                return false;
            }
            let mut vint32_bytes = [0u8; 4];
            vint32_bytes.copy_from_slice(&p[..4]);
            value.vint32 = i32::from_be_bytes(vint32_bytes);
            p.drain(..4);
            value.ptr = value.vint32.to_be_bytes().to_vec();
        },
        BINN_STORAGE_QWORD => {
            if p.len() + 7 > plimit.len() {
                return false;
            }
            let mut vint64_bytes = [0u8; 8];
            vint64_bytes.copy_from_slice(&p[..8]);
            value.vint64 = i64::from_be_bytes(vint64_bytes);
            p.drain(..8);
            value.ptr = value.vint64.to_be_bytes().to_vec();
        },
        BINN_STORAGE_BLOB | BINN_STORAGE_STRING => {
            if p.len() > plimit.len() {
                return false;
            }
            data_size = p.remove(0) as i32;
            if (data_size & 0x80) != 0 {
                if p.len() + 3 > plimit.len() {
                    return false;
                }
                let mut data_size_bytes = [0u8; 4];
                data_size_bytes.copy_from_slice(&p[..4]);
                data_size = i32::from_be_bytes(data_size_bytes) & 0x7FFFFFFF;
                p.drain(..4);
            } else {
                data_size &= 0x7F;
            }
            if p.len() + data_size as usize - 1 > plimit.len() {
                return false;
            }
            value.size = data_size;
            value.ptr = p.drain(..data_size as usize).collect();
        },
        BINN_STORAGE_CONTAINER => {
            let mut count = 0;
            let mut size = 0;
            if !IsValidBinnHeader(&p2, &mut 0, &mut count, &mut size, &mut 0) {
                return false;
            }
            value.ptr = p2;
            value.count = count;
            value.size = size;
        },
        _ => return false,
    }

    match value.type_ {
        BINN_TRUE => {
            value.type_ = BINN_BOOL;
            value.vbool = true;
            value.ptr = vec![if value.vbool { 1 } else { 0 }];
        },
        BINN_FALSE => {
            value.type_ = BINN_BOOL;
            value.vbool = false;
            value.ptr = vec![if value.vbool { 1 } else { 0 }];
        },
        _ => (),
    }

    true
}

pub fn binn_malloc(size: i32) -> Option<Box<[u8]>> {
    check_alloc_functions();
    unsafe {
        if let Some(alloc_fn) = malloc_fn {
            alloc_fn(size as usize)
        } else {
            None
        }
    }
}

pub fn AddValue(item: &mut Binn, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    let mut storage_type = 0;
    let mut extra_type = 0;
    binn_get_type_info(type_, Some(&mut storage_type), Some(&mut extra_type));

    if pvalue.is_none() {
        match storage_type {
            BINN_STORAGE_NOBYTES => (),
            BINN_STORAGE_BLOB | BINN_STORAGE_STRING => {
                if size == 0 {
                    ()
                } else {
                    return false;
                }
            },
            _ => return false,
        }
    }

    let compressed_value;
    let mut compressed_pvalue = pvalue;
    if type_family(type_) == BINN_FAMILY_INT && !item.disable_int_compression {
        let mut temp_storage = storage_type;
        let mut temp_type = type_;
        let value = pvalue.unwrap().clone();
        let mut temp_vec = value.to_vec();
        let compressed = compress_int(&mut temp_storage, &mut temp_type, &mut temp_vec);
        compressed_value = compressed.to_vec();
        compressed_pvalue = Some(&compressed_value);
    }

    let (size, arg_size) = match storage_type {
        BINN_STORAGE_NOBYTES => (0, 0),
        BINN_STORAGE_BYTE => (1, 1),
        BINN_STORAGE_WORD => (2, 2),
        BINN_STORAGE_DWORD => (4, 4),
        BINN_STORAGE_QWORD => (8, 8),
        BINN_STORAGE_BLOB => {
            if size < 0 {
                return false;
            }
            (size, size + 4)
        },
        BINN_STORAGE_STRING => {
            if size < 0 {
                return false;
            }
            let actual_size = if size == 0 {
                strlen2(String::from_utf8(pvalue.unwrap().clone()).unwrap())
            } else {
                size as usize
            };
            (actual_size as i32, actual_size as i32 + 5)
        },
        BINN_STORAGE_CONTAINER => {
            if size <= 0 {
                return false;
            }
            (size, size)
        },
        _ => return false,
    };

    let arg_size = arg_size + 2;
    if !CheckAllocation(item, arg_size) {
        return false;
    }

    let p = &mut item.pbuf[item.used_size as usize..];
    let mut p_idx = 0;

    if storage_type != BINN_STORAGE_CONTAINER {
        if type_ > 255 {
            let type16 = type_ as u16;
            let mut dest = [0u8; 2];
            copy_be16(&mut dest, &type16);
            p[p_idx..p_idx+2].copy_from_slice(&dest);
            p_idx += 2;
            item.used_size += 2;
        } else {
            p[p_idx] = type_ as u8;
            p_idx += 1;
            item.used_size += 1;
        }
    }

    match storage_type {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_BYTE => {
            p[p_idx] = pvalue.unwrap()[0];
            item.used_size += 1;
        },
        BINN_STORAGE_WORD => {
            let val = u16::from_be_bytes([pvalue.unwrap()[0], pvalue.unwrap()[1]]);
            let mut dest = [0u8; 2];
            copy_be16(&mut dest, &val);
            p[p_idx..p_idx+2].copy_from_slice(&dest);
            item.used_size += 2;
        },
        BINN_STORAGE_DWORD => {
            let val = u32::from_be_bytes([pvalue.unwrap()[0], pvalue.unwrap()[1], pvalue.unwrap()[2], pvalue.unwrap()[3]]);
            let mut dest = [0u8; 4];
            copy_be32(&mut dest, &val);
            p[p_idx..p_idx+4].copy_from_slice(&dest);
            item.used_size += 4;
        },
        BINN_STORAGE_QWORD => {
            let val = u64::from_be_bytes([
                pvalue.unwrap()[0], pvalue.unwrap()[1], pvalue.unwrap()[2], pvalue.unwrap()[3],
                pvalue.unwrap()[4], pvalue.unwrap()[5], pvalue.unwrap()[6], pvalue.unwrap()[7],
            ]);
            let mut dest = [0u8; 8];
            copy_be64(&mut dest, &val);
            p[p_idx..p_idx+8].copy_from_slice(&dest);
            item.used_size += 8;
        },
        BINN_STORAGE_BLOB | BINN_STORAGE_STRING => {
            if size > 127 {
                let int32 = (size as u32) | 0x80000000;
                let mut dest = [0u8; 4];
                copy_be32(&mut dest, &int32);
                p[p_idx..p_idx+4].copy_from_slice(&dest);
                p_idx += 4;
                item.used_size += 4;
            } else {
                p[p_idx] = size as u8;
                p_idx += 1;
                item.used_size += 1;
            }
            p[p_idx..p_idx + size as usize].copy_from_slice(&pvalue.unwrap()[..size as usize]);
            if storage_type == BINN_STORAGE_STRING {
                p[p_idx + size as usize] = 0;
                item.used_size += size + 1;
            } else {
                item.used_size += size;
            }
        },
        BINN_STORAGE_CONTAINER => {
            p[p_idx..p_idx + size as usize].copy_from_slice(&pvalue.unwrap()[..size as usize]);
            item.used_size += size;
        },
        _ => return false,
    }

    item.dirty = true;
    true
}

pub fn SearchForID(p: &mut Vec<u8>, header_size: i32, size: i32, numitems: i32, id: i32) -> Option<Vec<u8>> {
    let mut base = p.clone();
    let plimit = size - 1;
    let mut p = p.clone();
    p.drain(0..header_size as usize);

    for _ in 0..numitems {
        let int32 = read_map_id(&mut p, &(plimit as u8));
        if p.is_empty() || p.len() > plimit as usize {
            break;
        }
        if int32 == id {
            return Some(p);
        }
        match AdvanceDataPos(&mut p, plimit as usize) {
            Some(new_pos) => {
                p.drain(0..new_pos);
                if p.len() < base.len() {
                    break;
                }
            }
            None => break,
        }
    }

    None
}

pub fn zero_value<T>(pvalue: &mut T, type_: i32) {
    match binn_get_read_storage(type_) {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_BYTE => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_WORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_DWORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_QWORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_BLOB | BINN_STORAGE_STRING | BINN_STORAGE_CONTAINER => *pvalue = unsafe { std::mem::zeroed() },
        _ => (),
    }
}

pub fn copy_value<T: Copy + 'static>(psource: &T, pdest: &mut T, source_type: i32, dest_type: i32, data_store: i32) -> bool {
    if type_family(source_type) != type_family(dest_type) {
        return false;
    }

    if type_family(source_type) == BINN_FAMILY_INT && source_type != dest_type {
        let psource_wrap: &dyn std::any::Any = psource;
        let pdest_wrap: &mut dyn std::any::Any = pdest;
        copy_int_value(psource_wrap, pdest_wrap, source_type, dest_type)
    } else if type_family(source_type) == BINN_FAMILY_FLOAT && source_type != dest_type {
        let mut temp_dest = 0.0f64;
        let result = copy_float_value(*unsafe { &*(psource as *const T as *const f32) }, &mut temp_dest, source_type, dest_type);
        if result {
            *pdest = unsafe { std::mem::transmute_copy(&temp_dest) };
        }
        result
    } else {
        copy_raw_value(psource, pdest, data_store)
    }
}

pub fn binn_object_get_value(ptr: Option<&Vec<u8>>, key: &str, value: &mut Binn) -> bool {
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    let ptr = binn_ptr(ptr);
    if ptr.is_none() || key.is_empty() || value.is_null() {
        return false;
    }

    let ptr_ref = ptr.as_ref().unwrap();
    if !IsValidBinnHeader(ptr_ref, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != BINN_OBJECT {
        return false;
    }
    if count == 0 {
        return false;
    }

    let mut p = ptr_ref.clone();
    let plimit = p.len() - 1;

    let pos = SearchForKey(&mut p, header_size as usize, size as usize, count as usize, key);
    if pos.is_none() {
        return false;
    }

    let mut p_slice = p[pos.unwrap()..].to_vec();
    let mut plimit_slice = p[plimit..].to_vec();
    GetValue(&mut p_slice, &mut plimit_slice, value)
}

pub fn binn_create(item: &mut Binn, type_: i32, size: i32, pointer: Option<Vec<u8>>) -> bool {
    let mut retval = false;
    let mut size = size;

    match type_ {
        BINN_LIST | BINN_MAP | BINN_OBJECT => (),
        _ => return retval,
    }

    if size < 0 {
        return retval;
    }
    if size < MIN_BINN_SIZE {
        if pointer.is_some() {
            return retval;
        } else {
            size = 0;
        }
    }

    *item = Binn::default();

    if let Some(ptr) = pointer {
        item.pre_allocated = true;
        item.pbuf = ptr;
    } else {
        item.pre_allocated = false;
        let alloc_size = if size == 0 { CHUNK_SIZE } else { size };
        if let Some(allocated) = binn_malloc(alloc_size) {
            item.pbuf = allocated.to_vec();
        } else {
            return false;
        }
    }

    item.alloc_size = size;
    item.header = BINN_MAGIC as i32;
    item.writable = true;
    item.used_size = MAX_BINN_HEADER as i32;
    item.type_ = type_;
    item.dirty = true;

    true
}

pub fn binn_list_get_value(ptr: Option<&Vec<u8>>, pos: i32, value: &mut Binn) -> bool {
    let ptr = binn_ptr(ptr);
    if ptr.is_none() || value.is_null() {
        return false;
    }

    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    let ptr_ref = ptr.as_ref().unwrap();
    if !IsValidBinnHeader(ptr_ref, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != BINN_LIST {
        return false;
    }
    if count == 0 {
        return false;
    }
    if pos <= 0 || pos > count {
        return false;
    }
    let pos = pos - 1;

    let base = ptr_ref.clone();
    let plimit = base.len().min(size as usize);
    let mut p = base[header_size as usize..].to_vec();

    for _ in 0..pos {
        let new_pos = AdvanceDataPos(&mut p, plimit);
        if new_pos.is_none() {
            return false;
        }
        p = base[new_pos.unwrap()..].to_vec();
        if p.len() < base.len() {
            return false;
        }
    }

    GetValue(&mut p, &mut base.clone(), value)
}

pub fn binn_map_set_raw(item: &mut Binn, id: i32, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    if item.is_null() || item.type_ != BINN_MAP || !item.writable {
        return false;
    }

    let mut p = SearchForID(&mut item.pbuf, MAX_BINN_HEADER as i32, item.used_size, item.count, id);
    if p.is_some() {
        return false;
    }

    if !CheckAllocation(item, 5) {
        return false;
    }

    let mut base = item.used_size as usize;
    let mut sign = id < 0;
    let mut id = if sign { -id } else { id };

    let mut id_size = 0;
    let mut p = item.used_size as usize;

    if id <= 0x3F {
        item.pbuf[p] = ((sign as u8) << 6) | (id as u8);
        p += 1;
        id_size = 1;
    } else if id <= 0xFFF {
        item.pbuf[p] = 0x80 | ((sign as u8) << 4) | (((id & 0xF00) >> 8) as u8);
        p += 1;
        item.pbuf[p] = (id & 0xFF) as u8;
        p += 1;
        id_size = 2;
    } else if id <= 0xFFFFF {
        item.pbuf[p] = 0xA0 | ((sign as u8) << 4) | (((id & 0xF0000) >> 16) as u8);
        p += 1;
        item.pbuf[p] = ((id & 0xFF00) >> 8) as u8;
        p += 1;
        item.pbuf[p] = (id & 0xFF) as u8;
        p += 1;
        id_size = 3;
    } else if id <= 0xFFFFFFF {
        item.pbuf[p] = 0xC0 | ((sign as u8) << 4) | (((id & 0xF000000) >> 24) as u8);
        p += 1;
        item.pbuf[p] = ((id & 0xFF0000) >> 16) as u8;
        p += 1;
        item.pbuf[p] = ((id & 0xFF00) >> 8) as u8;
        p += 1;
        item.pbuf[p] = (id & 0xFF) as u8;
        p += 1;
        id_size = 4;
    } else {
        item.pbuf[p] = 0xE0;
        p += 1;
        if sign {
            id = -id;
        }
        let id_bytes = id.to_be_bytes();
        item.pbuf[p..p+4].copy_from_slice(&id_bytes);
        p += 4;
        id_size = 5;
    }

    item.used_size += id_size;

    if !AddValue(item, type_, pvalue, size) {
        item.used_size -= id_size;
        return false;
    }

    item.count += 1;

    true
}

pub fn GetWriteConvertedData(ptype: &mut i32, ppvalue: &mut Option<Box<[u8]>>, psize: &mut i32) -> bool {
    let mut type_ = *ptype;
    let mut f1: f32 = 0.0;
    let mut d1: f64 = 0.0;
    let mut pstr: [u8; 128] = [0; 128];

    if ppvalue.is_none() {
        match type_ {
            BINN_NULL | BINN_TRUE | BINN_FALSE => (),
            BINN_STRING | BINN_BLOB => {
                if *psize == 0 {
                    ()
                } else {
                    return false;
                }
            }
            _ => return false,
        }
    }

    match type_ {
        BINN_SINGLE => {
            if let Some(ref mut value) = ppvalue {
                f1 = f32::from_ne_bytes([value[0], value[1], value[2], value[3]]);
                d1 = f1 as f64;
                type_ = BINN_SINGLE_STR;
            } else {
                return false;
            }
        }
        BINN_DOUBLE => {
            if let Some(ref mut value) = ppvalue {
                d1 = f64::from_ne_bytes([
                    value[0], value[1], value[2], value[3],
                    value[4], value[5], value[6], value[7],
                ]);
                type_ = BINN_DOUBLE_STR;
            } else {
                return false;
            }
        }
        BINN_BOOL => {
            if let Some(ref mut value) = ppvalue {
                if value[0] == BINN_FALSE as u8 {
                    type_ = BINN_FALSE;
                } else {
                    type_ = BINN_TRUE;
                }
                *ptype = type_;
            } else {
                return false;
            }
            return true;
        }
        BINN_DECIMAL => return true,
        BINN_CURRENCYSTR => return true,
        BINN_DATE => return true,
        BINN_DATETIME => return true,
        BINN_TIME => return true,
        _ => (),
    }

    if type_ == BINN_SINGLE_STR || type_ == BINN_DOUBLE_STR {
        let formatted = format!("{:.17e}", d1);
        let bytes = formatted.into_bytes();
        *ppvalue = Some(bytes.into_boxed_slice());
        *ptype = type_;
    }

    true
}

pub fn binn_list_add_raw(item: &mut Binn, type_: i32, pvalue: Option<&[u8]>, size: i32) -> bool {
    if item.is_null() || item.type_ != BINN_LIST || !item.writable {
        return false;
    }

    let pvalue_vec = pvalue.map(|v| v.to_vec());
    if !AddValue(item, type_, pvalue_vec.as_ref(), size) {
        return false;
    }

    item.count += 1;
    true
}

pub fn binn_object_set_raw(item: &mut Binn, key: &str, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    if item.is_null() || item.type_ != BINN_OBJECT || !item.writable {
        return false;
    }

    if key.is_empty() {
        return false;
    }
    let keylen = key.len();
    if keylen > 255 {
        return false;
    }

    if SearchForKey(&mut item.pbuf, MAX_BINN_HEADER, item.used_size as usize, item.count as usize, key).is_some() {
        return false;
    }

    if !CheckAllocation(item, 1 + keylen as i32) {
        return false;
    }

    let mut p = item.used_size as usize;
    let len = keylen as u8;
    item.pbuf[p] = len;
    p += 1;
    item.pbuf[p..p+keylen].copy_from_slice(key.as_bytes());
    let mut total_size = keylen + 1;
    item.used_size += total_size as i32;

    if !AddValue(item, type_, pvalue, size) {
        item.used_size -= total_size as i32;
        return false;
    }

    item.count += 1;
    true
}

pub fn binn_buf_size(pbuf: &[u8]) -> i32 {
    let mut size = 0;
    if !IsValidBinnHeader(pbuf, &mut 0, &mut 0, &mut size, &mut 0) {
        return 0;
    }
    size
}

pub fn binn_object_get<T: Copy + 'static>(ptr: Option<&Vec<u8>>, key: &str, type_: i32, pvalue: &mut T, psize: Option<&mut i32>) -> bool {
    let mut storage_type = binn_get_read_storage(type_);
    if storage_type != BINN_STORAGE_NOBYTES && pvalue as *const _ == std::ptr::null() {
        return false;
    }

    zero_value(pvalue, type_);

    let mut value = Binn::default();
    if !binn_object_get_value(ptr, key, &mut value) {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_BLOB || type_family(value.type_) == BINN_FAMILY_STRING {
        *pvalue = unsafe { std::mem::transmute_copy(&value.ptr) };
    } else {
        let temp: T = unsafe { std::ptr::read(value.ptr.as_ptr() as *const T) };
        if !copy_value(&temp, pvalue, value.type_, type_, storage_type) {
            return false;
        }
    }

    if let Some(size) = psize {
        *size = value.size;
    }

    true
}

pub fn binn_new(type_: i32, size: i32, pointer: Option<Vec<u8>>) -> Option<Box<Binn>> {
    let mut item = Box::new(Binn::default());
    
    if !binn_create(&mut item, type_, size, pointer) {
        return None;
    }

    item.allocated = true;
    Some(item)
}

pub fn binn_list_get<T>(ptr: Option<&Vec<u8>>, pos: i32, type_: i32, pvalue: &mut T, psize: Option<&mut i32>) -> bool 
where
    T: 'static,
{
    let storage_type = binn_get_read_storage(type_);
    if storage_type != BINN_STORAGE_NOBYTES && pvalue as *const _ == std::ptr::null() {
        return false;
    }

    zero_value(pvalue, type_);

    let mut value = Binn::default();
    if !binn_list_get_value(ptr, pos, &mut value) {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_INT && value.type_ != type_ {
        let psource_wrap: &dyn std::any::Any = &value.ptr;
        let pdest_wrap: &mut dyn std::any::Any = pvalue;
        copy_int_value(psource_wrap, pdest_wrap, value.type_, type_)
    } else if type_family(value.type_) == BINN_FAMILY_FLOAT && value.type_ != type_ {
        let mut temp_dest = 0.0f64;
        let result = if value.type_ == BINN_FLOAT32 {
            let src = unsafe { std::ptr::read_unaligned(value.ptr.as_ptr() as *const f32) };
            copy_float_value(src, &mut temp_dest, value.type_, type_)
        } else {
            let src = unsafe { std::ptr::read_unaligned(value.ptr.as_ptr() as *const f64) };
            copy_float_value(src as f32, &mut temp_dest, value.type_, type_)
        };
        if result {
            unsafe { std::ptr::write(pvalue as *mut T as *mut f64, temp_dest) };
        }
        result
    } else {
        unsafe {
            std::ptr::copy_nonoverlapping(value.ptr.as_ptr(), pvalue as *mut T as *mut u8, std::mem::size_of::<T>());
            true
        }
    }
}

pub fn binn_read_pair(expected_type: i32, ptr: Option<&Vec<u8>>, pos: i32, pid: &mut i32, pkey: &mut String, value: &mut Binn) -> bool {
    let ptr = match binn_ptr(ptr) {
        Some(p) => p,
        None => return false,
    };

    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    if !IsValidBinnHeader(&ptr, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != expected_type || count == 0 || pos < 1 || pos > count {
        return false;
    }

    let mut p = ptr[header_size as usize..].to_vec();
    let base = ptr.as_ptr() as usize;
    let plimit = base + size as usize - 1;
    let mut counter = 0;
    let mut id = 0;
    let mut key = Vec::new();
    let mut len = 0;

    for _ in 0..count {
        match type_ {
            BINN_MAP => {
                let plimit_u8 = (plimit - base) as u8;
                id = read_map_id(&mut p, &plimit_u8);
                if p.is_empty() || p.as_ptr() as usize > plimit {
                    return false;
                }
            },
            BINN_OBJECT => {
                len = p.remove(0) as usize;
                if p.len() < len || p.as_ptr() as usize + len > plimit {
                    return false;
                }
                key = p[..len].to_vec();
                p.drain(..len);
            },
            _ => return false,
        }

        counter += 1;
        if counter == pos {
            match type_ {
                BINN_MAP => {
                    *pid = id;
                },
                BINN_OBJECT => {
                    if let Ok(s) = String::from_utf8(key) {
                        *pkey = s;
                    } else {
                        return false;
                    }
                },
                _ => return false,
            }

            let mut plimit_vec = Vec::new();
            return GetValue(&mut p, &mut plimit_vec, value);
        }

        match AdvanceDataPos(&mut p, plimit) {
            Some(new_pos) => p = ptr[new_pos..].to_vec(),
            None => return false,
        }
    }

    false
}

pub fn binn_map_get_value(ptr: Option<&Vec<u8>>, id: i32, value: &mut Binn) -> bool {
    let ptr = binn_ptr(ptr);
    if ptr.is_none() || value.is_null() {
        return false;
    }

    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;
    let ptr_val = ptr.unwrap();

    if !IsValidBinnHeader(&ptr_val, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != BINN_MAP {
        return false;
    }
    if count == 0 {
        return false;
    }

    let mut p = ptr_val.clone();
    let plimit = p.len() - 1;

    let found = SearchForID(&mut p, header_size, size, count, id);
    if found.is_none() {
        return false;
    }

    let mut p_found = found.unwrap();
    GetValue(&mut p_found, &mut p, value)
}

pub fn store_value(value: &Binn) -> Vec<u8> {
    let mut local_value = Binn::default();
    local_value.header = value.header;
    local_value.allocated = value.allocated;
    local_value.writable = value.writable;
    local_value.dirty = value.dirty;
    local_value.pbuf = value.pbuf.clone();
    local_value.pre_allocated = value.pre_allocated;
    local_value.alloc_size = value.alloc_size;
    local_value.used_size = value.used_size;
    local_value.type_ = value.type_;
    local_value.ptr = value.ptr.clone();
    local_value.size = value.size;
    local_value.count = value.count;
    local_value.freefn = value.freefn;
    local_value.vint8 = value.vint8;
    local_value.vint16 = value.vint16;
    local_value.vint32 = value.vint32;
    local_value.vint64 = value.vint64;
    local_value.vuint8 = value.vuint8;
    local_value.vuint16 = value.vuint16;
    local_value.vuint32 = value.vuint32;
    local_value.vuint64 = value.vuint64;
    local_value.vchar = value.vchar;
    local_value.vuchar = value.vuchar;
    local_value.vshort = value.vshort;
    local_value.vushort = value.vushort;
    local_value.vint = value.vint;
    local_value.vuint = value.vuint;
    local_value.vfloat = value.vfloat;
    local_value.vdouble = value.vdouble;
    local_value.vbool = value.vbool;
    local_value.disable_int_compression = value.disable_int_compression;

    match binn_get_read_storage(value.type_) {
        BINN_STORAGE_NOBYTES | BINN_STORAGE_WORD | BINN_STORAGE_DWORD | BINN_STORAGE_QWORD => {
            let mut result = Vec::new();
            result.extend_from_slice(&local_value.vint32.to_le_bytes());
            result
        }
        _ => value.ptr.clone()
    }
}

pub fn binn_map_set(map: &mut Binn, id: i32, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    let mut type_ = type_;
    let mut pvalue = pvalue;
    let mut size = size;

    if !GetWriteConvertedData(&mut type_, &mut pvalue.map(|v| v.clone().into_boxed_slice()), &mut size) {
        return false;
    }

    binn_map_set_raw(map, id, type_, pvalue, size)
}

pub fn binn_list_add(list: &mut Binn, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    let mut type_mut = type_;
    let mut pvalue_mut = pvalue.map(|v| v.clone().into_boxed_slice());
    let mut size_mut = size;

    if !GetWriteConvertedData(&mut type_mut, &mut pvalue_mut, &mut size_mut) {
        return false;
    }

    let pvalue_ref = pvalue_mut.as_ref().map(|v| v.as_ref());
    binn_list_add_raw(list, type_mut, pvalue_ref, size_mut)
}

pub fn binn_object_set(obj: &mut Binn, key: &str, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    let mut type_ = type_;
    let mut pvalue = pvalue;
    let mut size = size;

    if !GetWriteConvertedData(&mut type_, &mut pvalue.map(|v| v.clone().into_boxed_slice()), &mut size) {
        return false;
    }

    binn_object_set_raw(obj, key, type_, pvalue, size)
}

pub fn binn_is_valid_ex2(ptr: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32) -> bool {
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    if ptr.is_empty() {
        return false;
    }

    if *psize > 0 {
        size = *psize;
    } else {
        size = 0;
    }

    if !IsValidBinnHeader(ptr, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if *psize > 0 {
        if size > *psize {
            return false;
        }
    }

    if *pcount > 0 {
        if count != *pcount {
            return false;
        }
    }

    if *ptype != 0 {
        if type_ != *ptype {
            return false;
        }
    }

    let mut p = 0;
    let base = 0;
    let plimit = ptr.len() - 1;
    p += header_size as usize;

    for _ in 0..count {
        match type_ {
            BINN_OBJECT => {
                if p > plimit {
                    return false;
                }
                let len = ptr[p] as usize;
                p += 1;
                p += len;
            }
            BINN_MAP => {
                let mut p_slice = ptr[p..].to_vec();
                let plimit_slice = ptr[plimit];
                if read_map_id(&mut p_slice, &plimit_slice) == 0 {
                    return false;
                }
                p += p_slice.len();
            }
            BINN_LIST => {}
            _ => return false,
        }

        if p > plimit {
            return false;
        }

        if (ptr[p] & (BINN_STORAGE_MASK as u8)) == (BINN_STORAGE_CONTAINER as u8) {
            let size2 = plimit - p + 1;
            let mut dummy_type = 0;
            let mut dummy_count = 0;
            let mut dummy_size = size2 as i32;
            if !binn_is_valid_ex2(&ptr[p..].to_vec(), &mut dummy_type, &mut dummy_count, &mut dummy_size) {
                return false;
            }
            p += dummy_size as usize;
        } else {
            match AdvanceDataPos(&mut ptr[p..].to_vec(), plimit) {
                Some(new_p) => p += new_p,
                None => return false,
            }
            if p < base {
                return false;
            }
        }
    }

    if *ptype == 0 {
        *ptype = type_;
    }
    if *pcount == 0 {
        *pcount = count;
    }
    if *psize != 0 {
        *psize = size;
    }
    true
}

pub fn binn_size(ptr: Option<&Binn>) -> i32 {
    match binn_get_ptr_type(ptr.map(|p| &p.ptr)) {
        BINN_STRUCT => {
            let mut item = ptr.unwrap().clone();
            if item.writable && item.dirty {
                binn_save_header(&mut item);
            }
            item.size
        }
        BINN_BUFFER => binn_buf_size(&ptr.unwrap().ptr),
        _ => 0,
    }
}

pub fn binn_object_str(obj: Option<&Vec<u8>>, key: &str) -> String {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        return String::new();
    }
    if value.type_ != BINN_STRING {
        return String::new();
    }
    String::from_utf8_lossy(&value.ptr).into_owned()
}

pub fn binn_object() -> Option<Box<Binn>> {
    binn_new(BINN_OBJECT, 0, None)
}

pub fn binn_is_valid_ex(ptr: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32) -> bool {
    let mut size;

    if *psize > 0 {
        size = *psize;
    } else {
        size = 0;
    }

    if !binn_is_valid_ex2(ptr, ptype, pcount, &mut size) {
        return false;
    }

    if *psize > 0 {
        if size != *psize {
            return false;
        }
    } else if *psize == 0 {
        *psize = size;
    }

    true
}

pub fn binn_map_get_pair(ptr: Option<&Vec<u8>>, pos: i32, pid: &mut i32, value: &mut Binn) -> bool {
    let mut key = String::new();
    binn_read_pair(BINN_MAP, ptr, pos, pid, &mut key, value)
}

pub fn binn_free(mut item: Option<Box<Binn>>) {
    if item.is_none() {
        return;
    }
    let mut item = item.take().unwrap();

    if item.writable && !item.pre_allocated {
        if let Some(free) = unsafe { free_fn } {
            let slice = item.pbuf.clone().into_boxed_slice();
            free(Some(slice));
        }
    }

    if let Some(freefn) = item.freefn {
        freefn(item.ptr.clone());
    }

    if item.allocated {
        if let Some(free) = unsafe { free_fn } {
            let slice = item.pbuf.into_boxed_slice();
            free(Some(slice));
        }
    } else {
        *item = Binn::default();
        item.header = BINN_MAGIC as i32;
    }
}

pub fn binn_map() -> Option<Box<Binn>> {
    binn_new(BINN_MAP, 0, None)
}

pub fn binn_object_read<T>(obj: Option<&Vec<u8>>, key: &str, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();

    if !binn_object_get_value(obj, key, &mut value) {
        return None;
    }
    if let Some(pt) = ptype {
        *pt = value.type_;
    }
    if let Some(ps) = psize {
        *ps = value.size;
    }
    if cfg!(target_endian = "little") {
        Some(store_value(&value))
    } else {
        None
    }
}

pub fn binn_list_read(list: Option<&Vec<u8>>, pos: i32, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_list_get_value(list, pos, &mut value) {
        return None;
    }
    if let Some(ptype) = ptype {
        *ptype = value.type_;
    }
    if let Some(psize) = psize {
        *psize = value.size;
    }
    Some(store_value(&value))
}

pub fn binn_list() -> Option<Box<Binn>> {
    binn_new(BINN_LIST, 0, None)
}

pub fn binn_map_read(map: Option<&Vec<u8>>, id: i32, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_map_get_value(map, id, &mut value) {
        return None;
    }
    if let Some(pt) = ptype {
        *pt = value.type_;
    }
    if let Some(ps) = psize {
        *ps = value.size;
    }
    Some(store_value(&value))
}

pub fn binn_map_set_int32(map: &mut Binn, id: i32, value: i32) -> bool {
    let bytes = value.to_le_bytes().to_vec();
    binn_map_set(map, id, BINN_INT32, Some(&bytes), 0)
}

pub fn binn_object_set_int32(obj: &mut Binn, key: &str, value: i32) -> bool {
    binn_object_set(obj, key, BINN_INT32, Some(&vec![value as u8]), 0)
}

pub fn binn_list_add_int32(list: &mut Binn, value: i32) -> bool {
    binn_list_add(list, BINN_INT32, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_set_bool(map: &mut Binn, id: i32, value: bool) -> bool {
    let value = if value { BINN_TRUE } else { BINN_FALSE };
    binn_map_set(map, id, BINN_BOOL, Some(&vec![value as u8]), 0)
}

pub fn binn_list_add_double(list: &mut Binn, value: f64) -> bool {
    binn_list_add(list, BINN_FLOAT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_set_bool(obj: &mut Binn, key: &str, value: bool) -> bool {
    binn_object_set(obj, key, BINN_BOOL, Some(&vec![value as u8]), 0)
}

pub fn binn_object_set_double(obj: &mut Binn, key: &str, value: f64) -> bool {
    binn_object_set(obj, key, BINN_FLOAT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_set_double(map: &mut Binn, id: i32, value: f64) -> bool {
    binn_map_set(map, id, BINN_FLOAT64, Some(&value.to_le_bytes().to_vec()), 0)
}

pub fn binn_list_add_bool(list: &mut Binn, value: bool) -> bool {
    binn_list_add(list, BINN_BOOL, Some(&vec![if value { BINN_TRUE as u8 } else { BINN_FALSE as u8 }]), 0)
}

pub fn binn_list_get_int32(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut i32) -> bool {
    binn_list_get(list, pos, BINN_INT32, pvalue, None)
}

pub fn binn_list_blob(list: Option<&Vec<u8>>, pos: i32, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_list_get_value(list, pos, &mut value) {
        return None;
    }
    if value.type_ != BINN_BLOB {
        return None;
    }
    if let Some(size) = psize {
        *size = value.size;
    }
    Some(value.ptr)
}

pub fn binn_map_set_str(map: &mut Binn, id: i32, str: String) -> bool {
    binn_map_set(map, id, BINN_STRING, Some(&str.into_bytes()), 0)
}

pub fn binn_list_add_str(list: &mut Binn, str: String) -> bool {
    binn_list_add(list, BINN_STRING, Some(&str.into_bytes()), 0)
}

pub fn binn_list_add_blob(list: &mut Binn, ptr: Option<&Vec<u8>>, size: i32) -> bool {
    binn_list_add(list, BINN_BLOB, ptr, size)
}

pub fn binn_object_set_blob(obj: &mut Binn, key: &str, ptr: Vec<u8>, size: i32) -> bool {
    binn_object_set(obj, key, BINN_BLOB, Some(&ptr), size)
}

pub fn binn_object_set_str(obj: &mut Binn, key: &str, str: String) -> bool {
    binn_object_set(obj, key, BINN_STRING, Some(&str.into_bytes()), 0)
}

pub fn binn_map_set_blob(map: &mut Binn, id: i32, ptr: Option<&Vec<u8>>, size: i32) -> bool {
    binn_map_set(map, id, BINN_BLOB, ptr, size)
}

pub fn binn_version() -> String {
    BINN_VERSION.to_string()
}

pub fn binn_alloc_item() -> Option<Binn> {
    let mut item = Binn::default();
    item.header = BINN_MAGIC as i32;
    item.allocated = true;
    Some(item)
}

pub fn binn_memdup(src: &[u8], size: i32) -> Option<Vec<u8>> {
    if src.is_empty() || size <= 0 {
        return None;
    }
    let mut dest = binn_malloc(size)?.to_vec();
    dest[..size as usize].copy_from_slice(&src[..size as usize]);
    Some(dest)
}

pub fn binn_read_next_pair(expected_type: i32, iter: &mut BinnIter, pid: &mut i32, pkey: &mut String, value: &mut Binn) -> bool {
    let mut int32: i32;
    let mut id: i32;
    let mut p: Vec<u8>;
    let mut key: Vec<u8>;
    let mut len: u16;

    if iter.pnext.is_empty() || iter.pnext.len() > iter.plimit.len() || iter.current > iter.count || iter.type_ != expected_type {
        return false;
    }

    iter.current += 1;
    if iter.current > iter.count {
        return false;
    }

    p = iter.pnext.clone();
    let p_len = p.len();

    let result = match expected_type {
        BINN_MAP => {
            int32 = read_map_id(&mut p, &iter.plimit[0]);
            if p.len() > iter.plimit.len() {
                return false;
            }
            id = int32;
            if pid != &mut 0 {
                *pid = id;
            }
            true
        },
        BINN_OBJECT => {
            len = p.remove(0) as u16;
            key = p.drain(..len as usize).collect();
            if p.len() > iter.plimit.len() {
                return false;
            }
            if !pkey.is_empty() {
                *pkey = String::from_utf8(key).unwrap();
            }
            true
        },
        _ => false,
    };

    if !result {
        return false;
    }

    let new_pos = match AdvanceDataPos(&mut p, iter.plimit.len()) {
        Some(pos) => pos,
        None => return false,
    };

    let mut p_clone = p.clone();
    iter.pnext = p;
    if !iter.pnext.is_empty() && iter.pnext.len() < p_len {
        return false;
    }

    GetValue(&mut p_clone, &mut iter.plimit, value)
}

pub fn is_integer(p: String) -> bool {
    let mut retval = true;

    if p.is_empty() {
        return false;
    }

    let mut chars = p.chars();
    if let Some(c) = chars.next() {
        if c == '-' {
            if chars.next().is_none() {
                return false;
            }
        }
    }

    for c in chars {
        if !c.is_ascii_digit() {
            retval = false;
        }
    }

    retval
}

pub fn atoi64(str: String) -> i64 {
    let mut retval: i64 = 0;
    let mut is_negative = false;
    let mut chars = str.chars();

    if let Some('-') = chars.next() {
        is_negative = true;
    } else {
        chars = str.chars();
    }

    for c in chars {
        if c.is_digit(10) {
            retval = 10 * retval + c.to_digit(10).unwrap() as i64;
        }
    }

    if is_negative {
        retval *= -1;
    }

    retval
}

pub fn is_float(p: &str) -> bool {
    let mut number_found = false;
    let mut retval = true;
    let mut chars = p.chars();
    
    if p.is_empty() {
        return false;
    }
    
    let mut first_char = chars.next().unwrap();
    if first_char == '-' {
        if let Some(c) = chars.next() {
            first_char = c;
        } else {
            return false;
        }
    }
    
    for c in chars {
        if c == '.' || c == ',' {
            if !number_found {
                retval = false;
            }
        } else if c >= '0' && c <= '9' {
            number_found = true;
        } else {
            return false;
        }
    }
    
    retval
}

pub fn binn_buf_type(pbuf: &[u8]) -> i32 {
    let mut type_ = 0;
    if !IsValidBinnHeader(pbuf, &mut type_, &mut 0, &mut 0, &mut 0) {
        return INVALID_BINN;
    }
    type_
}

pub fn binn_is_valid(ptr: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32) -> bool {
    if ptype as *mut _ != std::ptr::null_mut() {
        *ptype = 0;
    }
    if pcount as *mut _ != std::ptr::null_mut() {
        *pcount = 0;
    }
    if psize as *mut _ != std::ptr::null_mut() {
        *psize = 0;
    }

    binn_is_valid_ex(ptr, ptype, pcount, psize)
}

pub fn binn_value(type_: i32, pvalue: &Vec<u8>, size: i32, freefn: Option<fn(Vec<u8>)>) -> Option<Binn> {
    let mut storage_type = 0;
    let mut item = binn_alloc_item()?;
    item.type_ = type_;
    binn_get_type_info(type_, Some(&mut storage_type), None);
    match storage_type {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_STRING => {
            let mut adjusted_size = size;
            if size == 0 {
                adjusted_size = pvalue.len() as i32 + 1;
            }
            if freefn.is_none() {
                item.ptr = binn_memdup(pvalue, adjusted_size)?;
                item.freefn = Some(|v| {});
                if storage_type == BINN_STORAGE_STRING {
                    adjusted_size -= 1;
                }
            } else {
                item.ptr = pvalue.clone();
                item.freefn = freefn;
            }
            item.size = adjusted_size;
        }
        BINN_STORAGE_BLOB | BINN_STORAGE_CONTAINER => {
            if freefn.is_none() {
                item.ptr = binn_memdup(pvalue, size)?;
                item.freefn = Some(|v| {});
            } else {
                item.ptr = pvalue.clone();
                item.freefn = freefn;
            }
            item.size = size;
        }
        _ => {
            item.ptr = Vec::new();
            if pvalue.len() > 0 {
                item.ptr.extend_from_slice(pvalue);
            }
        }
    }
    Some(item)
}

pub fn binn_map_get<T>(ptr: Option<&Vec<u8>>, id: i32, type_: i32, pvalue: &mut T, psize: &mut i32) -> bool {
    let storage_type = binn_get_read_storage(type_);
    if storage_type != BINN_STORAGE_NOBYTES && std::mem::size_of_val(pvalue) == 0 {
        return false;
    }

    zero_value(pvalue, type_);

    let mut value = Binn::default();
    if !binn_map_get_value(ptr, id, &mut value) {
        return false;
    }

    let mut temp_value = value.ptr[0];
    let temp_copy = temp_value;
    if !copy_value(&temp_copy, &mut temp_value, value.type_, type_, storage_type) {
        return false;
    }

    unsafe {
        std::ptr::copy_nonoverlapping(&temp_value as *const u8, pvalue as *mut T as *mut u8, std::mem::size_of::<T>());
    }

    *psize = value.size;

    true
}

pub fn binn_object_next(iter: &mut BinnIter, pkey: &mut String, value: &mut Binn) -> bool {
    binn_read_next_pair(BINN_OBJECT, iter, &mut 0, pkey, value)
}

pub fn is_bool_str(str: String, pbool: &mut bool) -> bool {
    let mut vint: i64;
    let mut vdouble: f64;

    if str.is_empty() {
        return false;
    }

    if str.eq_ignore_ascii_case("true") {
        *pbool = true;
        return true;
    }
    if str.eq_ignore_ascii_case("yes") {
        *pbool = true;
        return true;
    }
    if str.eq_ignore_ascii_case("on") {
        *pbool = true;
        return true;
    }

    if str.eq_ignore_ascii_case("false") {
        *pbool = false;
        return true;
    }
    if str.eq_ignore_ascii_case("no") {
        *pbool = false;
        return true;
    }
    if str.eq_ignore_ascii_case("off") {
        *pbool = false;
        return true;
    }

    if is_integer(str.clone()) {
        vint = atoi64(str);
        *pbool = vint != 0;
        true
    } else {
        let s = str.as_str();
        if is_float(s) {
            vdouble = s.parse::<f64>().unwrap();
            *pbool = vdouble != 0.0;
            true
        } else {
            false
        }
    }
}

pub fn binn_map_next(iter: &mut BinnIter, pid: &mut i32, value: &mut Binn) -> bool {
    binn_read_next_pair(BINN_MAP, iter, pid, &mut String::new(), value)
}

pub fn binn_type(ptr: Option<&Vec<u8>>) -> i32 {
    match binn_get_ptr_type(ptr) {
        BINN_STRUCT => {
            let item = ptr.unwrap();
            if item.len() > 4 {
                let type_byte = item[4];
                type_byte as i32
            } else {
                -1
            }
        }
        BINN_BUFFER => binn_buf_type(ptr.unwrap()),
        _ => -1,
    }
}

pub fn binn_load(data: &Vec<u8>, value: &mut Binn) -> bool {
    if data.is_empty() || value.is_null() {
        return false;
    }
    *value = Binn::default();
    value.header = BINN_MAGIC as i32;

    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    if !binn_is_valid(data, &mut type_, &mut count, &mut size) {
        return false;
    }
    value.type_ = type_;
    value.count = count;
    value.size = size;
    value.ptr = data.clone();
    true
}

pub fn binn_object_get_pair(ptr: Option<&Vec<u8>>, pos: i32, pkey: &mut String, value: &mut Binn) -> bool {
    let mut dummy_id = 0;
    binn_read_pair(BINN_OBJECT, ptr, pos, &mut dummy_id, pkey, value)
}

pub fn binn_map_set_value(map: &mut Binn, id: i32, value: &Binn) -> bool {
    let ptr = value.ptr.clone();
    binn_map_set(map, id, value.type_, Some(&ptr), binn_size(Some(value)))
}

pub fn binn_list_next(iter: &mut BinnIter, value: &mut Binn) -> bool {
    let mut pnow: Vec<u8>;

    if iter.is_null() || iter.pnext.is_empty() || iter.pnext > iter.plimit || iter.current > iter.count || iter.type_ != BINN_LIST {
        return false;
    }

    iter.current += 1;
    if iter.current > iter.count {
        return false;
    }

    pnow = iter.pnext.clone();
    if let Some(pos) = AdvanceDataPos(&mut pnow, iter.plimit.len()) {
        iter.pnext = pnow[pos..].to_vec();
    } else {
        return false;
    }

    GetValue(&mut pnow, &mut iter.plimit, value)
}

pub fn binn_buf_count(pbuf: &[u8]) -> i32 {
    let mut nitems = 0;
    if !IsValidBinnHeader(pbuf, &mut 0, &mut nitems, &mut 0, &mut 0) {
        return 0;
    }
    nitems
}

pub fn binn_object_set_value(obj: &mut Binn, key: &str, value: &Binn) -> bool {
    let ptr = value.ptr.as_ref();
    binn_object_set(obj, key, value.type_, Some(ptr), binn_size(Some(value)))
}

pub fn binn_load_ex(data: &Vec<u8>, size: i32, value: &mut Binn) -> bool {
    if data.is_empty() || size <= 0 {
        return false;
    }
    *value = Binn::default();
    value.header = BINN_MAGIC as i32;

    let mut type_ = 0;
    let mut count = 0;
    let mut size = size;
    if !binn_is_valid_ex(data, &mut type_, &mut count, &mut size) {
        return false;
    }
    value.type_ = type_;
    value.count = count;
    value.ptr = data.clone();
    value.size = size;
    true
}

pub fn binn_list_add_value(list: &mut Binn, value: &Binn) -> bool {
    binn_list_add(list, value.type_, binn_ptr(Some(&value.ptr)).as_ref(), binn_size(Some(value)))
}

pub fn binn_is_struct(ptr: &Vec<u8>) -> bool {
    if ptr.is_empty() {
        return false;
    }

    if ptr.len() >= 4 && u32::from_le_bytes([ptr[0], ptr[1], ptr[2], ptr[3]]) == BINN_MAGIC {
        true
    } else {
        false
    }
}

pub fn binn_create_type(storage_type: i32, data_type_index: i32) -> i32 {
  if data_type_index < 0 { return -1; }
  if storage_type < BINN_STORAGE_MIN || storage_type > BINN_STORAGE_MAX { return -1; }
  if data_type_index < 16 {
    return storage_type | data_type_index;
  } else if data_type_index < 4096 {
    let mut storage_type = storage_type | (BINN_STORAGE_HAS_MORE as i32);
    storage_type <<= 8;
    let data_type_index = data_type_index >> 4;
    return storage_type | data_type_index;
  } else {
    return -1;
  }
}

pub fn binn_set_alloc_functions(new_malloc: Option<fn(usize) -> Option<Box<[u8]>>>, new_realloc: Option<fn(Option<Box<[u8]>>, usize) -> Option<Box<[u8]>>>, new_free: Option<fn(Option<Box<[u8]>>)>) {
    unsafe {
        malloc_fn = new_malloc;
        realloc_fn = new_realloc;
        free_fn = new_free;
    }
}

pub fn binn_is_container(item: Option<&Binn>) -> bool {
    if item.is_none() {
        return false;
    }
    let item = item.unwrap();
    match item.type_ {
        BINN_LIST | BINN_MAP | BINN_OBJECT => true,
        _ => false,
    }
}

pub fn binn_int64(value: i64) -> Option<Binn> {
    binn_value(BINN_INT64, &value.to_ne_bytes().to_vec(), 0, None)
}

pub fn binn_map_get_uint16(map: Option<&Vec<u8>>, id: i32, pvalue: &mut u16) -> bool {
    let mut size = 0;
    binn_map_get(map, id, BINN_UINT16, pvalue, &mut size)
}

pub fn binn_map_set_list(map: &mut Binn, id: i32, list: Option<&Binn>) -> bool {
    let ptr = list.map(|x| &x.ptr);
    binn_map_set(map, id, BINN_LIST, ptr, binn_size(list))
}

pub fn binn_object_set_int8(obj: &mut Binn, key: &str, value: i8) -> bool {
    binn_object_set(obj, key, BINN_INT8, Some(&vec![value as u8]), 0)
}

pub fn binn_list_add_null(list: &mut Binn) -> bool {
    binn_list_add(list, BINN_NULL, None, 0)
}

pub fn binn_object_get_int64(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut i64) -> bool {
    binn_object_get(obj, key, BINN_INT64, pvalue, None)
}

pub fn binn_double(value: f64) -> Option<Binn> {
    let value_bytes = value.to_ne_bytes().to_vec();
    binn_value(BINN_DOUBLE, &value_bytes, 0, None)
}

pub fn binn_object_get_map(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        return false;
    }
    *pvalue = Some(value.ptr);
    true
}

pub fn binn_map_get_float(map: Option<&Vec<u8>>, id: i32, pvalue: &mut f32) -> bool {
    binn_map_get(map, id, BINN_FLOAT32, pvalue, &mut 0)
}

pub fn binn_object_get_uint32(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut u32) -> bool {
    binn_object_get(obj, key, BINN_UINT32, pvalue, None)
}

pub fn binn_null() -> Option<Binn> {
    binn_value(BINN_NULL, &Vec::new(), 0, None)
}

pub fn binn_map_get_int32(map: Option<&Vec<u8>>, id: i32, pvalue: &mut i32) -> bool {
    binn_map_get(map, id, BINN_INT32, pvalue, &mut 0)
}

pub fn binn_object_set_int64(obj: &mut Binn, key: &str, value: i64) -> bool {
    binn_object_set(obj, key, BINN_INT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_get_blob<T: Copy + 'static>(ptr: Option<&Vec<u8>>, id: i32, pvalue: &mut T, psize: &mut i32) -> bool {
    binn_map_get(ptr, id, BINN_BLOB, pvalue, psize)
}

pub fn binn_map_set_int64(map: &mut Binn, id: i32, value: i64) -> bool {
    binn_map_set(map, id, BINN_INT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_get_object<T: Copy + Default + 'static>(map: Option<&Vec<u8>>, id: i32, pvalue: &mut Option<Vec<T>>) -> bool {
    let mut temp = T::default();
    let mut size = 0;
    let result = binn_map_get(map, id, BINN_OBJECT, &mut temp, &mut size);
    if result {
        *pvalue = Some(vec![temp]);
    }
    result
}

pub fn binn_uint32(value: u32) -> Option<Binn> {
    binn_value(BINN_UINT32, &value.to_ne_bytes().to_vec(), 0, None)
}

pub fn binn_object_set_uint64(obj: &mut Binn, key: &str, value: u64) -> bool {
    binn_object_set(obj, key, BINN_UINT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_list_add_uint32(list: &mut Binn, value: u32) -> bool {
    binn_list_add(list, BINN_UINT32, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_get_int32(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut i32) -> bool {
    binn_object_get(obj, key, BINN_INT32, pvalue, None)
}

pub fn binn_object_get_int16(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut i16) -> bool {
    binn_object_get(obj, key, BINN_INT16, pvalue, None)
}

pub fn binn_map_get_bool(map: Option<&Vec<u8>>, id: i32, pvalue: &mut bool) -> bool {
    binn_map_get(map, id, BINN_BOOL, pvalue, &mut 0)
}

pub fn binn_list_add_int64(list: &mut Binn, value: i64) -> bool {
    binn_list_add(list, BINN_INT64, Some(&vec![value.to_be_bytes().to_vec()].concat()), 0)
}

pub fn binn_list_add_int8(list: &mut Binn, value: i8) -> bool {
    binn_list_add(list, BINN_INT8, Some(&vec![value as u8]), 0)
}

pub fn binn_uint16(value: u16) -> Option<Binn> {
    binn_value(BINN_UINT16, &value.to_be_bytes().to_vec(), 0, None)
}

pub fn binn_list_get_float(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut f32) -> bool {
    binn_list_get(list, pos, BINN_FLOAT32, pvalue, None)
}

pub fn binn_object_get_str(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut String) -> bool {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        return false;
    }
    if value.type_ != BINN_STRING {
        return false;
    }
    *pvalue = String::from_utf8_lossy(&value.ptr).into_owned();
    true
}

pub fn binn_list_get_object(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut temp = Vec::new();
    let result = binn_list_get_value(list, pos, &mut Binn {
        ptr: temp.clone(),
        ..Default::default()
    });
    if result {
        *pvalue = Some(temp);
    }
    result
}

pub fn binn_string(str: String, freefn: Option<fn(Vec<u8>)>) -> Option<Binn> {
    binn_value(BINN_STRING, &str.into_bytes(), 0, freefn)
}

pub fn binn_map_get_str(map: Option<&Vec<u8>>, id: i32, pvalue: &mut String) -> bool {
    let mut size = 0;
    let mut temp = String::new();
    let result = binn_map_get(map, id, BINN_STRING, &mut temp, &mut size);
    if result {
        *pvalue = temp;
    }
    result
}

pub fn binn_int8(value: i8) -> Option<Binn> {
    binn_value(BINN_INT8, &value.to_be_bytes().to_vec(), 0, None)
}

pub fn binn_list_get_int8(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut i8) -> bool {
    binn_list_get(list, pos, BINN_INT8, pvalue, None)
}

pub fn binn_object_set_uint16(obj: &mut Binn, key: &str, value: u16) -> bool {
    binn_object_set(obj, key, BINN_UINT16, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_get_map(ptr: Option<&Vec<u8>>, id: i32, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut size = 0;
    binn_map_get(ptr, id, BINN_MAP, pvalue, &mut size)
}

pub fn binn_object_set_list(obj: &mut Binn, key: &str, list: &Binn) -> bool {
    let ptr = binn_ptr(Some(&list.ptr));
    binn_object_set(obj, key, BINN_LIST, ptr.as_ref(), binn_size(Some(list)))
}

pub fn binn_map_set_map(map: &mut Binn, id: i32, map2: Option<&Binn>) -> bool {
    let ptr = map2.map(|m| &m.ptr);
    binn_map_set(map, id, BINN_MAP, ptr, binn_size(map2))
}

pub fn binn_bool(value: bool) -> Option<Binn> {
    let bytes = if value { [1u8] } else { [0u8] };
    binn_value(BINN_BOOL, &bytes.to_vec(), 0, None)
}

pub fn binn_blob(ptr: Vec<u8>, size: i32, freefn: Option<fn(Vec<u8>)>) -> Option<Binn> {
    binn_value(BINN_BLOB, &ptr, size, freefn)
}

pub fn binn_object_get_uint8(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut u8) -> bool {
    binn_object_get(obj, key, BINN_UINT8, pvalue, None)
}

pub fn binn_map_set_float(map: &mut Binn, id: i32, value: f32) -> bool {
    binn_map_set(map, id, BINN_FLOAT32, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_set_null(map: &mut Binn, id: i32) -> bool {
    binn_map_set(map, id, BINN_NULL, None, 0)
}

pub fn binn_object_get_object(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        return false;
    }
    *pvalue = Some(value.ptr);
    true
}

pub fn binn_list_get_bool(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut bool) -> bool {
    binn_list_get(list, pos, BINN_BOOL, pvalue, None)
}

pub fn binn_uint64(value: u64) -> Option<Binn> {
    binn_value(BINN_UINT64, &value.to_ne_bytes().to_vec(), 0, None)
}

pub fn binn_list_add_int16(list: &mut Binn, value: i16) -> bool {
    binn_list_add(list, BINN_INT16, Some(&vec![value as u8, (value >> 8) as u8]), 0)
}

pub fn binn_list_add_uint64(list: &mut Binn, value: u64) -> bool {
    binn_list_add(list, BINN_UINT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_get_int64(map: Option<&Vec<u8>>, id: i32, pvalue: &mut i64) -> bool {
    let mut size = 0;
    binn_map_get(map, id, BINN_INT64, pvalue, &mut size)
}

pub fn binn_object_get_list<T>(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut Option<Vec<T>>) -> bool {
    let mut temp = Binn::default();
    if !binn_object_get_value(obj, key, &mut temp) {
        return false;
    }
    if temp.type_ != BINN_LIST {
        return false;
    }
    *pvalue = Some(temp.ptr.chunks(std::mem::size_of::<T>()).map(|chunk| {
        unsafe { std::ptr::read(chunk.as_ptr() as *const T) }
    }).collect());
    true
}

pub fn binn_object_get_uint16(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut u16) -> bool {
    binn_object_get(obj, key, BINN_UINT16, pvalue, None)
}

pub fn binn_object_get_float(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut f32) -> bool {
    binn_object_get(obj, key, BINN_FLOAT32, pvalue, None)
}

pub fn binn_map_set_uint32(map: &mut Binn, id: i32, value: u32) -> bool {
    binn_map_set(map, id, BINN_UINT32, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_set_object(obj: &mut Binn, key: &str, obj2: Option<&Binn>) -> bool {
    let ptr = obj2.map(|o| &o.ptr);
    binn_object_set(obj, key, BINN_OBJECT, ptr, binn_size(obj2))
}

pub fn binn_list_add_uint8(list: &mut Binn, value: u8) -> bool {
    let value_vec = vec![value];
    binn_list_add(list, BINN_UINT8, Some(&value_vec), 0)
}

pub fn binn_list_get_uint64(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut u64) -> bool {
    binn_list_get(list, pos, BINN_UINT64, pvalue, None)
}

pub fn binn_object_set_map(obj: &mut Binn, key: &str, map: Option<&Binn>) -> bool {
    let ptr = match map {
        Some(m) => Some(&m.ptr),
        None => None
    };
    binn_object_set(obj, key, BINN_MAP, ptr, binn_size(map))
}

pub fn binn_list_get_list(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut temp = [0u8; std::mem::size_of::<Vec<u8>>()];
    let result = binn_list_get(list, pos, BINN_LIST, &mut temp, None);
    if result {
        *pvalue = Some(temp.to_vec());
    }
    result
}

pub fn binn_list_get_str(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut Option<String>) -> bool {
    let mut temp: [u8; 256] = [0; 256];
    let result = binn_list_get(list, pos, BINN_STRING, &mut temp, None);
    if result {
        *pvalue = Some(String::from_utf8_lossy(&temp).trim_end_matches('\0').to_string());
    }
    result
}

pub fn binn_object_set_uint8(obj: &mut Binn, key: &str, value: u8) -> bool {
    binn_object_set(obj, key, BINN_UINT8, Some(&vec![value]), 0)
}

pub fn binn_object_get_double(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut f64) -> bool {
    binn_object_get(obj, key, BINN_FLOAT64, pvalue, None)
}

pub fn binn_int16(value: i16) -> Option<Binn> {
    binn_value(BINN_INT16, &value.to_ne_bytes().to_vec(), 0, None)
}

pub fn binn_object_set_uint32(obj: &mut Binn, key: &str, value: u32) -> bool {
    binn_object_set(obj, key, BINN_UINT32, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_set_null(obj: &mut Binn, key: &str) -> bool {
    binn_object_set(obj, key, BINN_NULL, None, 0)
}

pub fn binn_list_add_map(list: &mut Binn, map: Option<&Binn>) -> bool {
    binn_list_add(list, BINN_MAP, binn_ptr(map.map(|m| &m.ptr)).as_ref(), binn_size(map))
}

pub fn binn_list_get_int64(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut i64) -> bool {
    binn_list_get(list, pos, BINN_INT64, pvalue, None)
}

pub fn binn_list_get_int16(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut i16) -> bool {
    binn_list_get(list, pos, BINN_INT16, pvalue, None)
}

pub fn binn_list_get_blob(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut Vec<u8>, psize: &mut i32) -> bool {
    let mut value = Binn::default();
    let result = binn_list_get_value(list, pos, &mut value);
    if result {
        *pvalue = value.ptr;
        *psize = value.size;
    }
    result
}

pub fn binn_list_add_float(list: &mut Binn, value: f32) -> bool {
    binn_list_add(list, BINN_FLOAT32, Some(&vec![value.to_le_bytes().to_vec()].concat()), 0)
}

pub fn binn_list_get_double(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut f64) -> bool {
    binn_list_get(list, pos, BINN_FLOAT64, pvalue, None)
}

pub fn binn_list_add_uint16(list: &mut Binn, value: u16) -> bool {
    binn_list_add(list, BINN_UINT16, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_get_bool(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut bool) -> bool {
    binn_object_get(obj, key, BINN_BOOL, pvalue, None)
}

pub fn binn_list_get_uint32(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut u32) -> bool {
    binn_list_get(list, pos, BINN_UINT32, pvalue, None)
}

pub fn binn_map_set_uint64(map: &mut Binn, id: i32, value: u64) -> bool {
    binn_map_set(map, id, BINN_UINT64, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_get_int8(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut i8) -> bool {
    binn_object_get(obj, key, BINN_INT8, pvalue, None)
}

pub fn binn_int32(value: i32) -> Option<Binn> {
    binn_value(BINN_INT32, &vec![], 0, None)
}

pub fn binn_map_get_int16(map: Option<&Vec<u8>>, id: i32, pvalue: &mut i16) -> bool {
    binn_map_get(map, id, BINN_INT16, pvalue, &mut 0)
}

pub fn binn_uint8(value: u8) -> Option<Binn> {
    binn_value(BINN_UINT8, &vec![value], 0, None)
}

pub fn binn_map_get_uint8(map: Option<&Vec<u8>>, id: i32, pvalue: &mut u8) -> bool {
    binn_map_get(map, id, BINN_UINT8, pvalue, &mut 0)
}

pub fn binn_object_set_float(obj: &mut Binn, key: &str, value: f32) -> bool {
    let bytes = value.to_le_bytes();
    binn_object_set(obj, key, BINN_FLOAT32, Some(&bytes.to_vec()), 0)
}

pub fn binn_object_get_uint64(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut u64) -> bool {
    binn_object_get(obj, key, BINN_UINT64, pvalue, None)
}

pub fn binn_list_get_map(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut Option<Vec<u8>>) -> bool {
    let mut value = Binn {
        ptr: Vec::new(),
        type_: BINN_MAP,
        ..Default::default()
    };
    let result = binn_list_get_value(list, pos, &mut value);
    if result {
        *pvalue = Some(value.ptr);
    }
    result
}

pub fn binn_map_get_list<T>(map: Option<&Vec<u8>>, id: i32, pvalue: &mut T) -> bool {
    binn_map_get(map, id, BINN_LIST, pvalue, &mut 0)
}

pub fn binn_map_get_double(map: Option<&Vec<u8>>, id: i32, pvalue: &mut f64) -> bool {
    binn_map_get(map, id, BINN_FLOAT64, pvalue, &mut 0)
}

pub fn binn_map_set_uint16(map: &mut Binn, id: i32, value: u16) -> bool {
    binn_map_set(map, id, BINN_UINT16, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_map_set_uint8(map: &mut Binn, id: i32, value: u8) -> bool {
    binn_map_set(map, id, BINN_UINT8, Some(&vec![value]), 0)
}

pub fn binn_list_get_uint16(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut u16) -> bool {
    binn_list_get(list, pos, BINN_UINT16, pvalue, None)
}

pub fn binn_map_set_int8(map: &mut Binn, id: i32, value: i8) -> bool {
    binn_map_set(map, id, BINN_INT8, Some(&vec![value as u8]), 0)
}

pub fn binn_list_get_uint8(list: Option<&Vec<u8>>, pos: i32, pvalue: &mut u8) -> bool {
    binn_list_get(list, pos, BINN_UINT8, pvalue, None)
}

pub fn binn_object_get_blob(obj: Option<&Vec<u8>>, key: &str, pvalue: &mut Option<Vec<u8>>, psize: Option<&mut i32>) -> bool {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        return false;
    }
    
    if value.type_ != BINN_BLOB {
        return false;
    }
    
    *pvalue = Some(value.ptr);
    if let Some(size) = psize {
        *size = value.size;
    }
    true
}

pub fn binn_map_get_uint32(map: Option<&Vec<u8>>, id: i32, pvalue: &mut u32) -> bool {
    let mut size = 0;
    binn_map_get(map, id, BINN_UINT32, pvalue, &mut size)
}

pub fn binn_float(value: f32) -> Option<Binn> {
    binn_value(BINN_FLOAT32, &value.to_ne_bytes().to_vec(), 0, None)
}

pub fn binn_map_set_object(map: &mut Binn, id: i32, obj: Option<&Binn>) -> bool {
    binn_map_set(map, id, BINN_OBJECT, binn_ptr(obj.map(|o| &o.ptr)).as_ref(), binn_size(obj))
}

pub fn binn_list_add_list(list: &mut Binn, list2: Option<&Binn>) -> bool {
    binn_list_add(list, BINN_LIST, binn_ptr(list2.map(|l| &l.ptr)).as_ref(), binn_size(list2))
}

pub fn binn_list_add_object(list: &mut Binn, obj: Option<&Binn>) -> bool {
    binn_list_add(list, BINN_OBJECT, binn_ptr(obj.map(|o| &o.ptr)).as_ref(), binn_size(obj))
}

pub fn binn_map_set_int16(map: &mut Binn, id: i32, value: i16) -> bool {
    binn_map_set(map, id, BINN_INT16, Some(&value.to_be_bytes().to_vec()), 0)
}

pub fn binn_object_set_int16(obj: &mut Binn, key: &str, value: i16) -> bool {
    binn_object_set(obj, key, BINN_INT16, Some(&vec![value as u8]), 0)
}

pub fn binn_map_get_uint64(map: Option<&Vec<u8>>, id: i32, pvalue: &mut u64) -> bool {
    binn_map_get(map, id, BINN_UINT64, pvalue, &mut 0)
}

pub fn binn_map_get_int8(map: Option<&Vec<u8>>, id: i32, pvalue: &mut i8) -> bool {
    binn_map_get(map, id, BINN_INT8, pvalue, &mut 0)
}

pub fn binn_object_next_value(iter: &mut BinnIter, pkey: &mut String) -> Option<Binn> {
    let mut value = Binn::default();
    if !binn_object_next(iter, pkey, &mut value) {
        None
    } else {
        value.allocated = true;
        Some(value)
    }
}

pub fn binn_list_int16(list: Option<&Vec<u8>>, pos: i32) -> i16 {
    let mut value: i16 = 0;
    binn_list_get(list, pos, BINN_INT16, &mut value, None);
    value
}

pub fn binn_list_uint32(list: Option<&Vec<u8>>, pos: i32) -> u32 {
    let mut value: u32 = 0;
    binn_list_get(list, pos, BINN_UINT32, &mut value, None);
    value
}

pub fn binn_list_map(list: Option<&Vec<u8>>, pos: i32) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if binn_list_get_value(list, pos, &mut value) {
        Some(value.ptr)
    } else {
        None
    }
}

pub fn binn_map_blob(map: Option<&Vec<u8>>, id: i32, psize: &mut i32) -> Option<Vec<u8>> {
    let mut value = Vec::new();
    if !binn_map_get(map, id, BINN_BLOB, &mut value, psize) {
        None
    } else {
        Some(value)
    }
}

pub fn binn_list_value(ptr: Option<&Vec<u8>>, pos: i32) -> Option<Binn> {
    let mut value = Binn::default();
    
    if !binn_list_get_value(ptr, pos, &mut value) {
        return None;
    }

    value.allocated = true;
    Some(value)
}

pub fn binn_get_int32(value: &Binn, pint: &mut i32) -> bool {
    if value.is_null() {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_INT {
        return copy_int_value(&value.ptr, pint, value.type_, BINN_INT32);
    }

    match value.type_ {
        BINN_FLOAT32 => {
            if value.vfloat < (INT32_MIN as f32) || value.vfloat > (INT32_MAX as f32) {
                return false;
            }
            *pint = (value.vfloat + 0.5) as i32;
            true
        }
        BINN_FLOAT64 => {
            if value.vdouble < (INT32_MIN as f64) || value.vdouble > (INT32_MAX as f64) {
                return false;
            }
            *pint = (value.vdouble + 0.5) as i32;
            true
        }
        BINN_STRING => {
            let s = String::from_utf8_lossy(&value.ptr).into_owned();
            if is_integer(s.clone()) {
                *pint = s.parse::<i32>().unwrap_or(0);
                true
            } else if is_float(&s) {
                *pint = (s.parse::<f64>().unwrap_or(0.0) + 0.5) as i32;
                true
            } else {
                false
            }
        }
        BINN_BOOL => {
            *pint = if value.vbool { 1 } else { 0 };
            true
        }
        _ => false,
    }
}

pub fn binn_list_uint8(list: Option<&Vec<u8>>, pos: i32) -> u8 {
    let mut value: u8 = 0;
    binn_list_get(list, pos, BINN_UINT8, &mut value, None);
    value
}

pub fn binn_list_double(list: Option<&Vec<u8>>, pos: i32) -> f64 {
    let mut value: f64 = 0.0;
    binn_list_get(list, pos, BINN_FLOAT64, &mut value, None);
    value
}

pub fn binn_get_bool(value: &Binn, pbool: &mut bool) -> bool {
    let mut vint: i64 = 0;

    if value.is_null() {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_INT {
        if !copy_int_value(&value.ptr, &mut vint, value.type_, BINN_INT64) {
            return false;
        }
        *pbool = vint != 0;
        return true;
    }

    match value.type_ {
        BINN_BOOL => {
            *pbool = value.vbool;
        }
        BINN_FLOAT => {
            *pbool = value.vfloat != 0.0;
        }
        BINN_DOUBLE => {
            *pbool = value.vdouble != 0.0;
        }
        BINN_STRING => {
            let s = String::from_utf8_lossy(&value.ptr).into_owned();
            return is_bool_str(s, pbool);
        }
        _ => {
            return false;
        }
    }

    true
}

pub fn binn_map_bool(map: Option<&Vec<u8>>, id: i32) -> bool {
    let mut value = false;
    binn_map_get(map, id, BINN_BOOL, &mut value, &mut 0);
    value
}

pub fn binn_map_uint16(map: Option<&Vec<u8>>, id: i32) -> u16 {
    let mut value: u16 = 0;
    let mut size = 0;
    binn_map_get(map, id, BINN_UINT16, &mut value, &mut size);
    value
}

pub fn binn_object_null(obj: Option<&Vec<u8>>, key: &str) -> bool {
    binn_object_get(obj, key, BINN_NULL, &mut 0, None)
}

pub fn binn_object_uint32(obj: Option<&Vec<u8>>, key: &str) -> u32 {
    let mut value: u32 = 0;
    binn_object_get(obj, key, BINN_UINT32, &mut value, None);
    value
}

pub fn binn_set_blob(mut item: Binn, ptr: Vec<u8>, size: i32, pfree: Option<fn(Vec<u8>)>) -> bool {
    if item.is_null() || ptr.is_empty() {
        return false;
    }

    if pfree.is_none() {
        item.ptr = binn_memdup(&ptr, size).unwrap_or_default();
        if item.ptr.is_empty() {
            return false;
        }
        item.freefn = Some(|_| {});
    } else {
        item.ptr = ptr;
        item.freefn = pfree;
    }

    item.type_ = BINN_BLOB;
    item.size = size;
    true
}

pub fn binn_map_uint32(map: Option<&Vec<u8>>, id: i32) -> u32 {
    let mut value: u32 = 0;
    binn_map_get(map, id, BINN_UINT32, &mut value, &mut 0);
    value
}

pub fn binn_map_int32(map: Option<&Vec<u8>>, id: i32) -> i32 {
    let mut value = 0;
    binn_map_get(map, id, BINN_INT32, &mut value, &mut 0);
    value
}

pub fn binn_map_float(map: Option<&Vec<u8>>, id: i32) -> f32 {
    let mut value: f32 = 0.0;
    binn_map_get(map, id, BINN_FLOAT32, &mut value, &mut 0);
    value
}

pub fn binn_list_int8(list: Option<&Vec<u8>>, pos: i32) -> i8 {
    let mut value: i8 = 0;
    binn_list_get(list, pos, BINN_INT8, &mut value, None);
    value
}

pub fn binn_list_null(list: Option<&Vec<u8>>, pos: i32) -> bool {
    binn_list_get::<i32>(list, pos, BINN_NULL, &mut 0, None)
}

pub fn binn_list_str(list: Option<&Vec<u8>>, pos: i32) -> String {
    let mut value = String::new();
    unsafe {
        binn_list_get(list, pos, BINN_STRING, &mut value, None);
    }
    value
}

pub fn binn_map_read_pair(ptr: Option<&Vec<u8>>, pos: i32, pid: &mut i32, ptype: &mut i32, psize: &mut i32) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_map_get_pair(ptr, pos, pid, &mut value) {
        return None;
    }
    if *ptype != NULL {
        *ptype = value.type_;
    }
    if *psize != NULL {
        *psize = value.size;
    }
    if cfg!(target_endian = "little") {
        Some(store_value(&value))
    } else {
        None
    }
}

pub fn binn_object_double(obj: Option<&Vec<u8>>, key: &str) -> f64 {
    let mut value = 0.0;
    binn_object_get(obj, key, BINN_FLOAT64, &mut value, None);
    value
}

pub fn binn_map_read_next(iter: &mut BinnIter, pid: &mut i32, ptype: &mut i32, psize: &mut i32) -> Vec<u8> {
    let mut value = Binn::default();
    if !binn_map_next(iter, pid, &mut value) {
        return Vec::new();
    }
    if *ptype != NULL {
        *ptype = value.type_;
    }
    if *psize != NULL {
        *psize = value.size;
    }
    store_value(&value)
}

pub fn binn_create_list(list: &mut Binn) -> bool {
    binn_create(list, BINN_LIST, 0, None)
}

pub fn binn_object_uint64(obj: Option<&Vec<u8>>, key: &str) -> u64 {
    let mut value: u64 = 0;
    binn_object_get(obj, key, BINN_UINT64, &mut value, None);
    value
}

pub fn binn_object_int64(obj: Option<&Vec<u8>>, key: &str) -> i64 {
    let mut value: i64 = 0;
    binn_object_get(obj, key, BINN_INT64, &mut value, None);
    value
}

pub fn binn_object_int16(obj: Option<&Vec<u8>>, key: &str) -> i16 {
    let mut value: i16 = 0;
    binn_object_get(obj, key, BINN_INT16, &mut value, None);
    value
}

pub fn binn_object_uint16(obj: Option<&Vec<u8>>, key: &str) -> u16 {
    let mut value: u16 = 0;
    binn_object_get(obj, key, BINN_UINT16, &mut value, None);
    value
}

pub fn binn_iter_init(iter: &mut BinnIter, ptr: Option<&Vec<u8>>, expected_type: i32) -> bool {
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    let ptr = if let Some(p) = binn_ptr(ptr) {
        p
    } else {
        return false;
    };

    if iter.is_null() {
        return false;
    }

    *iter = BinnIter::default();

    if !IsValidBinnHeader(&ptr, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != expected_type {
        return false;
    }

    iter.plimit = ptr.clone();
    iter.plimit.truncate(size as usize - 1);
    iter.pnext = ptr.clone();
    iter.pnext.drain(0..header_size as usize);
    iter.count = count;
    iter.current = 0;
    iter.type_ = type_;

    true
}

pub fn binn_add_value(item: &mut Binn, binn_type: i32, id: i32, name: &str, type_: i32, pvalue: Option<&Vec<u8>>, size: i32) -> bool {
    match binn_type {
        BINN_LIST => binn_list_add(item, type_, pvalue, size),
        BINN_MAP => binn_map_set(item, id, type_, pvalue, size),
        BINN_OBJECT => binn_object_set(item, name, type_, pvalue, size),
        _ => false,
    }
}

pub fn binn_get_int64(value: &Binn, pint: &mut i64) -> bool {
    if value.is_null() {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_INT {
        return copy_int_value(&value.ptr, pint, value.type_, BINN_INT64);
    }

    match value.type_ {
        BINN_FLOAT32 => {
            if value.vfloat < (INT64_MIN as f32) || value.vfloat > (INT64_MAX as f32) {
                return false;
            }
            *pint = if value.vfloat >= 0.0 {
                (value.vfloat + 0.5) as i64
            } else {
                if (value.vfloat - (value.vfloat as i64 as f32)) <= -0.5 {
                    value.vfloat as i64
                } else {
                    (value.vfloat - 0.5) as i64
                }
            };
            true
        }
        BINN_FLOAT64 => {
            if value.vdouble < (INT64_MIN as f64) || value.vdouble > (INT64_MAX as f64) {
                return false;
            }
            *pint = if value.vdouble >= 0.0 {
                (value.vdouble + 0.5) as i64
            } else {
                if (value.vdouble - (value.vdouble as i64 as f64)) <= -0.5 {
                    value.vdouble as i64
                } else {
                    (value.vdouble - 0.5) as i64
                }
            };
            true
        }
        BINN_STRING => {
            let s = String::from_utf8(value.ptr.clone()).unwrap_or_default();
            if is_integer(s.clone()) {
                *pint = atoi64(s);
                true
            } else if is_float(&s) {
                *pint = if let Ok(f) = s.parse::<f64>() {
                    if f >= 0.0 {
                        (f + 0.5) as i64
                    } else {
                        if (f - (f as i64 as f64)) <= -0.5 {
                            f as i64
                        } else {
                            (f - 0.5) as i64
                        }
                    }
                } else {
                    0
                };
                true
            } else {
                false
            }
        }
        BINN_BOOL => {
            *pint = if value.vbool { 1 } else { 0 };
            true
        }
        _ => false,
    }
}

pub fn binn_get_double(value: &Binn, pfloat: &mut f64) -> bool {
    let mut vint: i64 = 0;

    if value.is_null() {
        return false;
    }

    if type_family(value.type_) == BINN_FAMILY_INT {
        if !copy_int_value(&value.ptr, &mut vint, value.type_, BINN_INT64) {
            return false;
        }
        *pfloat = vint as f64;
        return true;
    }

    match value.type_ {
        BINN_FLOAT32 => {
            *pfloat = value.vfloat as f64;
        }
        BINN_FLOAT64 => {
            *pfloat = value.vdouble;
        }
        BINN_STRING => {
            if is_integer(String::from_utf8(value.ptr.clone()).unwrap()) {
                *pfloat = atoi64(String::from_utf8(value.ptr.clone()).unwrap()) as f64;
            } else if is_float(&String::from_utf8(value.ptr.clone()).unwrap()) {
                *pfloat = String::from_utf8(value.ptr.clone())
                    .unwrap()
                    .parse::<f64>()
                    .unwrap();
            } else {
                return false;
            }
        }
        BINN_BOOL => {
            *pfloat = value.vbool as i32 as f64;
        }
        _ => {
            return false;
        }
    }

    true
}

pub fn binn_object_bool(obj: Option<&Vec<u8>>, key: &str) -> bool {
    let mut value = false;
    binn_object_get(obj, key, BINN_BOOL, &mut value, None);
    value
}

pub fn binn_open(data: &Vec<u8>) -> Option<Binn> {
    let mut item = Binn::default();
    if !binn_load(data, &mut item) {
        return None;
    }
    item.allocated = true;
    Some(item)
}

pub fn binn_list_object(list: Option<&Vec<u8>>, pos: i32) -> Option<Vec<u8>> {
    let mut value = Vec::new();
    if !binn_list_get(list, pos, BINN_OBJECT, &mut value, None) {
        None
    } else {
        Some(value)
    }
}

pub fn binn_copy(old: Option<&Vec<u8>>) -> Option<Box<Binn>> {
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;
    let old_ptr = binn_ptr(old)?;
    let old_ptr_clone = old_ptr.clone();

    if !IsValidBinnHeader(&old_ptr_clone, &mut type_, &mut count, &mut size, &mut header_size) {
        return None;
    }

    let mut item = binn_new(type_, size - header_size + MAX_BINN_HEADER as i32, None)?;
    let dest_start = MAX_BINN_HEADER;
    let dest_end = dest_start + (size - header_size) as usize;
    
    item.pbuf[dest_start..dest_end].copy_from_slice(&old_ptr[header_size as usize..(header_size + size) as usize]);
    item.used_size = MAX_BINN_HEADER as i32 + size - header_size;
    item.count = count;

    Some(item)
}

pub fn binn_map_map(map: Option<&Vec<u8>>, id: i32) -> Option<Vec<u8>> {
    let mut value = Vec::new();
    let mut size = 0;
    if !binn_map_get(map, id, BINN_MAP, &mut value, &mut size) {
        None
    } else {
        Some(value)
    }
}

pub fn binn_object_map(obj: Option<&Vec<u8>>, key: &str) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
        None
    } else {
        Some(value.ptr)
    }
}

pub fn binn_map_int16(map: Option<&Vec<u8>>, id: i32) -> i16 {
    let mut value: i16 = 0;
    let mut psize: i32 = 0;
    binn_map_get(map, id, BINN_INT16, &mut value, &mut psize);
    value
}

pub fn binn_map_null(map: Option<&Vec<u8>>, id: i32) -> bool {
    let mut pvalue: i32 = 0;
    let mut psize: i32 = 0;
    binn_map_get(map, id, BINN_NULL, &mut pvalue, &mut psize)
}

pub fn binn_list_uint16(list: Option<&Vec<u8>>, pos: i32) -> u16 {
    let mut value: u16 = 0;
    binn_list_get(list, pos, BINN_UINT16, &mut value, None);
    value
}

pub fn binn_map_str(map: Option<&Vec<u8>>, id: i32) -> Option<String> {
    let mut value = String::new();
    let mut size = 0;
    if binn_map_get(map, id, BINN_STRING, &mut value, &mut size) {
        Some(value)
    } else {
        None
    }
}

pub fn binn_object_read_pair(ptr: Option<&Vec<u8>>, pos: i32, pkey: &mut String, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_object_get_pair(ptr, pos, pkey, &mut value) {
        return None;
    }
    if let Some(ptype) = ptype {
        *ptype = value.type_;
    }
    if let Some(psize) = psize {
        *psize = value.size;
    }
    Some(store_value(&value))
}

pub fn binn_map_next_value(iter: &mut BinnIter, pid: &mut i32) -> Option<Binn> {
    let mut value = Binn::default();
    if !binn_map_next(iter, pid, &mut value) {
        return None;
    }
    value.allocated = true;
    Some(value)
}

pub fn binn_map_pair(map: Option<&Vec<u8>>, pos: i32, pid: &mut i32) -> Option<Binn> {
    let mut value = Binn::default();

    if !binn_read_pair(BINN_MAP, map, pos, pid, &mut String::new(), &mut value) {
        return None;
    }

    value.allocated = true;
    Some(value)
}

pub fn binn_get_str(value: &mut Binn) -> Option<String> {
    let mut vint: i64 = 0;
    let mut buf: String = String::with_capacity(128);

    if value.is_null() {
        return None;
    }

    if type_family(value.type_) == BINN_FAMILY_INT {
        if !copy_int_value(&value.ptr, &mut vint, value.type_, BINN_INT64) {
            return None;
        }
        buf = vint.to_string();
        return Some(buf);
    }

    match value.type_ {
        BINN_FLOAT => {
            value.vdouble = value.vfloat as f64;
            buf = value.vdouble.to_string();
            Some(buf)
        }
        BINN_DOUBLE => {
            buf = value.vdouble.to_string();
            Some(buf)
        }
        BINN_STRING => {
            Some(String::from_utf8_lossy(&value.ptr).into_owned())
        }
        BINN_BOOL => {
            if value.vbool {
                Some("true".to_string())
            } else {
                Some("false".to_string())
            }
        }
        _ => None,
    }
}

pub fn binn_object_value(ptr: Option<&Vec<u8>>, key: &str) -> Option<Box<Binn>> {
    let mut value = Binn::default();
    if !binn_object_get_value(ptr, key, &mut value) {
        return None;
    }
    value.allocated = true;
    Some(Box::new(value))
}

pub fn binn_object_float(obj: Option<&Vec<u8>>, key: &str) -> f32 {
    let mut value: f32 = 0.0;
    binn_object_get(obj, key, BINN_FLOAT32, &mut value, None);
    value
}

pub fn binn_map_value(ptr: Option<&Vec<u8>>, id: i32) -> Option<Binn> {
    let mut value = Binn::default();
    if !binn_map_get_value(ptr, id, &mut value) {
        return None;
    }
    value.allocated = true;
    Some(value)
}

pub fn binn_object_int32(obj: Option<&Vec<u8>>, key: &str) -> i32 {
    let mut value = 0;
    binn_object_get(obj, key, BINN_INT32, &mut value, None);
    value
}

pub fn binn_list_int32(list: Option<&Vec<u8>>, pos: i32) -> i32 {
    let mut value = 0i32;
    binn_list_get(list, pos, BINN_INT32, &mut value, None);
    value
}

pub fn binn_list_uint64(list: Option<&Vec<u8>>, pos: i32) -> u64 {
    let mut value: u64 = 0;
    binn_list_get(list, pos, BINN_UINT64, &mut value, None);
    value
}

pub fn binn_map_list(map: Option<&Vec<u8>>, id: i32) -> Option<Vec<u8>> {
    let mut value = Vec::new();
    let mut size = 0;
    if !binn_map_get(map, id, BINN_LIST, &mut value, &mut size) {
        return None;
    }
    Some(value)
}

pub fn binn_set_string(mut item: Binn, str: String, pfree: Option<fn(Vec<u8>)>) -> bool {
    if item.is_null() || str.is_empty() {
        return false;
    }

    if pfree.is_none() {
        let bytes = str.into_bytes();
        item.ptr = binn_memdup(&bytes, bytes.len() as i32 + 1).unwrap_or_default();
        if item.ptr.is_empty() {
            return false;
        }
        item.freefn = None;
    } else {
        item.ptr = str.into_bytes();
        item.freefn = pfree;
    }

    item.type_ = BINN_STRING;
    true
}

pub fn binn_list_int64(list: Option<&Vec<u8>>, pos: i32) -> i64 {
    let mut value: i64 = 0;
    binn_list_get(list, pos, BINN_INT64, &mut value, None);
    value
}

pub fn binn_object_read_next(iter: &mut BinnIter, pkey: &mut String, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if !binn_object_next(iter, pkey, &mut value) {
        return None;
    }
    if let Some(ptype) = ptype {
        *ptype = value.type_;
    }
    if let Some(psize) = psize {
        *psize = value.size;
    }
    Some(store_value(&value))
}

pub fn binn_map_set_new(map: &mut Binn, id: i32, value: Option<Binn>) -> bool {
    let retval = match value {
        Some(ref v) => binn_map_set_value(map, id, v),
        None => false,
    };
    retval
}

pub fn binn_release(item: &mut Binn) -> Option<Vec<u8>> {
    let mut data = binn_ptr(Some(&item.pbuf));

    if let Some(ref mut data_vec) = data {
        if data_vec.as_ptr() > item.pbuf.as_ptr() {
            item.pbuf.copy_from_slice(data_vec);
            data = Some(item.pbuf.clone());
        }
    }

    if item.allocated {
        if let Some(free_func) = unsafe { free_fn } {
            let boxed_slice = item.pbuf.clone().into_boxed_slice();
            free_func(Some(boxed_slice));
        }
    } else {
        *item = Binn::default();
        item.header = BINN_MAGIC as i32;
    }

    data
}

pub fn binn_list_float(list: Option<&Vec<u8>>, pos: i32) -> f32 {
    let mut value = 0.0f32;
    binn_list_get(list, pos, BINN_FLOAT32, &mut value, None);
    value
}

pub fn binn_list_read_next(iter: &mut BinnIter, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    
    if !binn_list_next(iter, &mut value) {
        return None;
    }
    
    if let Some(pt) = ptype {
        *pt = value.type_;
    }
    if let Some(ps) = psize {
        *ps = value.size;
    }
    
    Some(store_value(&value))
}

pub fn binn_create_object(object: &mut Binn) -> bool {
    binn_create(object, BINN_OBJECT, 0, None)
}

pub fn binn_count(ptr: Option<&Vec<u8>>) -> i32 {
    match binn_get_ptr_type(ptr) {
        BINN_STRUCT => {
            let binn = unsafe { &*(ptr.unwrap().as_ptr() as *const Binn) };
            binn.count
        }
        BINN_BUFFER => binn_buf_count(ptr.unwrap()),
        _ => -1,
    }
}

pub fn binn_map_uint8(map: Option<&Vec<u8>>, id: i32) -> u8 {
    let mut value: u8 = 0;
    let mut size: i32 = 0;
    binn_map_get(map, id, BINN_UINT8, &mut value, &mut size);
    value
}

pub fn binn_object_set_new(obj: &mut Binn, key: &str, value: Option<Binn>) -> bool {
    let mut retval = false;
    if let Some(mut val) = value {
        retval = binn_object_set_value(obj, key, &val);
        if let Some(free_func) = unsafe { free_fn } {
            free_func(Some(Box::from(val.ptr)));
        }
    }
    retval
}

pub fn binn_object_int8(obj: Option<&Vec<u8>>, key: &str) -> i8 {
    let mut value: i8 = 0;
    binn_object_get(obj, key, BINN_INT8, &mut value, None);
    value
}

pub fn binn_list_next_value(iter: &mut BinnIter) -> Option<Binn> {
    let mut value = Binn::default();

    if !binn_list_next(iter, &mut value) {
        return None;
    }

    value.allocated = true;
    Some(value)
}

pub fn binn_map_object<T>(map: Option<&Vec<u8>>, id: i32) -> Option<T> {
    let mut value: T = unsafe { std::mem::zeroed() };
    let mut size = 0;
    
    if !binn_map_get(map, id, BINN_OBJECT, &mut value, &mut size) {
        None
    } else {
        Some(value)
    }
}

pub fn binn_map_int64(map: Option<&Vec<u8>>, id: i32) -> i64 {
    let mut value: i64 = 0;
    binn_map_get(map, id, BINN_INT64, &mut value, &mut 0);
    value
}

pub fn binn_open_ex<T>(data: &Vec<u8>, size: i32) -> Option<Binn> {
    let mut item = Binn::default();
    
    if !binn_load_ex(data, size, &mut item) {
        return None;
    }

    item.allocated = true;
    Some(item)
}

pub fn binn_create_map(map: &mut Binn) -> bool {
    binn_create(map, BINN_MAP, 0, None)
}

pub fn binn_list_bool(list: Option<&Vec<u8>>, pos: i32) -> bool {
    let mut value = false;
    binn_list_get(list, pos, BINN_BOOL, &mut value, None);
    value
}

pub fn binn_object_pair(obj: Option<&Vec<u8>>, pos: i32, pkey: &mut String) -> Option<Binn> {
    let mut value = Binn::default();

    if !binn_read_pair(BINN_OBJECT, obj, pos, &mut 0, pkey, &mut value) {
        return None;
    }

    value.allocated = true;
    Some(value)
}

pub fn binn_object_list(obj: Option<&Vec<u8>>, key: &str) -> Option<Vec<u8>> {
    let mut value = Binn::default();
    if binn_object_get_value(obj, key, &mut value) {
        Some(value.ptr)
    } else {
        None
    }
}

pub fn binn_list_add_new(list: &mut Binn, value: Option<Binn>) -> bool {
    let retval = match &value {
        Some(v) => binn_list_add_value(list, v),
        None => false,
    };
    retval
}

pub fn binn_map_int8(map: Option<&Vec<u8>>, id: i32) -> i8 {
    let mut value: i8 = 0;
    let mut _psize: i32 = 0;
    binn_map_get(map, id, BINN_INT8, &mut value, &mut _psize);
    value
}

pub fn binn_object_uint8(obj: Option<&Vec<u8>>, key: &str) -> u8 {
    let mut value: u8 = 0;
    binn_object_get(obj, key, BINN_UINT8, &mut value, None);
    value
}

pub fn binn_map_double(map: Option<&Vec<u8>>, id: i32) -> f64 {
    let mut value: f64 = 0.0;
    let mut size: i32 = 0;
    
    binn_map_get(map, id, BINN_FLOAT64, &mut value, &mut size);
    
    value
}

pub fn binn_list_list(list: Option<&Vec<u8>>, pos: i32) -> Option<Vec<u8>> {
    let mut value: Vec<u8> = Vec::new();
    if binn_list_get(list, pos, BINN_LIST, &mut value, None) {
        Some(value)
    } else {
        None
    }
}

pub fn binn_map_uint64(map: Option<&Vec<u8>>, id: i32) -> u64 {
    let mut value: u64 = 0;
    let mut size: i32 = 0;
    binn_map_get(map, id, BINN_UINT64, &mut value, &mut size);
    value
}

