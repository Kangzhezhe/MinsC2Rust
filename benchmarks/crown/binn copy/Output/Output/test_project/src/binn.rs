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

pub fn binn_get_type_info(long_type: i32, pstorage_type: Option<&mut i32>, pextra_type: Option<&mut i32>) -> bool {
    let mut storage_type: i32;
    let mut extra_type: i32;
    let mut retval: bool = true;

    let mut long_type = long_type;

    loop {
        if long_type < 0 {
            storage_type = -1;
            extra_type = -1;
            retval = false;
            break;
        } else if long_type <= 0xff {
            storage_type = long_type & BINN_STORAGE_MASK;
            extra_type = long_type & BINN_TYPE_MASK;
            break;
        } else if long_type <= 0xffff {
            storage_type = long_type & BINN_STORAGE_MASK16;
            storage_type >>= 8;
            extra_type = long_type & BINN_TYPE_MASK16;
            extra_type >>= 4;
            break;
        } else if long_type & BINN_STORAGE_VIRTUAL != 0 {
            long_type &= 0xffff;
            continue;
        } else {
            storage_type = -1;
            extra_type = -1;
            retval = false;
            break;
        }
    }

    if let Some(pstorage_type) = pstorage_type {
        *pstorage_type = storage_type;
    }
    if let Some(pextra_type) = pextra_type {
        *pextra_type = extra_type;
    }

    retval
}

pub fn copy_be32(pdest: &mut [u8; 4], psource: &u32) {
    let source_bytes = psource.to_be_bytes();
    pdest.copy_from_slice(&source_bytes);
}

pub fn check_alloc_functions() {
    unsafe {
        if malloc_fn.is_none() {
            malloc_fn = Some(Box::new(|size: usize| -> Vec<u8> {
                vec![0; size]
            }));
        }
        if realloc_fn.is_none() {
            realloc_fn = Some(Box::new(|mut vec: Vec<u8>, new_size: usize| -> Vec<u8> {
                vec.resize(new_size, 0);
                vec
            }));
        }
        if free_fn.is_none() {
            free_fn = Some(Box::new(|_vec: Vec<u8>| {}));
        }
    }
}

pub fn binn_get_write_storage(type_: i32) -> i32 {
    let mut storage_type: i32 = 0;

    match type_ {
        BINN_SINGLE_STR => BINN_STORAGE_STRING,
        BINN_DOUBLE_STR => BINN_STORAGE_STRING,
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
        calc_size <<= 1;  // same as *= 2
        //calc_size += CHUNK_SIZE;  -- this is slower than the above line, because there are more reallocations
    }
    calc_size
}

pub fn int_type(type_: i32) -> i32 {
    match type_ {
        BINN_INT8 | BINN_INT16 | BINN_INT32 | BINN_INT64 => BINN_SIGNED_INT,
        BINN_UINT8 | BINN_UINT16 | BINN_UINT32 | BINN_UINT64 => BINN_UNSIGNED_INT,
        _ => 0,
    }
}

pub fn copy_be16(pdest: &mut u16, psource: &u16) {
    *pdest = psource.to_be();
}

pub fn binn_get_ptr_type<T>(ptr: Option<T>) -> i32 {
    if ptr.is_none() {
        return BINN_BUFFER;
    }

    match ptr {
        Some(_) => BINN_STRUCT,
        None => BINN_BUFFER,
    }
}

pub fn binn_save_header(item: &mut Binn) -> bool {
    if item.pbuf.is_empty() {
        return false;
    }

    let mut p: usize;
    let mut size: i32;

    p = item.pbuf.len() - MAX_BINN_HEADER as usize;
    size = item.used_size - MAX_BINN_HEADER + 3;

    if item.count > 127 {
        p -= 4;
        size += 3;
        let int32 = item.count as u32 | 0x80000000;
        let mut dest = [0u8; 4];
        copy_be32(&mut dest, &int32);
        item.pbuf[p..p + 4].copy_from_slice(&dest);
    } else {
        p -= 1;
        item.pbuf[p] = item.count as u8;
    }

    if size > 127 {
        p -= 4;
        size += 3;
        let int32 = size as u32 | 0x80000000;
        let mut dest = [0u8; 4];
        copy_be32(&mut dest, &int32);
        item.pbuf[p..p + 4].copy_from_slice(&dest);
    } else {
        p -= 1;
        item.pbuf[p] = size as u8;
    }

    p -= 1;
    item.pbuf[p] = item.type_ as u8;

    item.ptr = item.pbuf[p..].to_vec();
    item.size = size;

    item.dirty = false;

    true
}

pub fn copy_be64(pdest: &mut u64, psource: &u64) {
    *pdest = psource.to_be();
}

pub fn IsValidBinnHeader(pbuf: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32, pheadersize: &mut i32) -> bool {
    let mut p = pbuf.as_ptr();
    let mut plimit: *const u8 = std::ptr::null();
    let mut int32: i32;
    let mut type_: i32;
    let mut size: i32;
    let mut count: i32;

    if pbuf.is_empty() {
        return false;
    }

    if *psize > 0 {
        if *psize < MIN_BINN_SIZE {
            return false;
        }
        plimit = unsafe { p.offset(*psize as isize - 1) };
    }

    // get the type
    let byte = unsafe { *p };
    p = unsafe { p.offset(1) };
    if (byte as i32 & BINN_STORAGE_MASK) != BINN_STORAGE_CONTAINER {
        return false;
    }
    if byte as i32 & BINN_STORAGE_HAS_MORE != 0 {
        return false;
    }
    type_ = byte as i32;

    match type_ {
        BINN_LIST | BINN_MAP | BINN_OBJECT => (),
        _ => return false,
    }

    // get the size
    if !plimit.is_null() && p > plimit {
        return false;
    }
    int32 = unsafe { *p as i32 };
    if int32 & 0x80 != 0 {
        if !plimit.is_null() && unsafe { p.offset(3) } > plimit {
            return false;
        }
        let mut temp = [0u8; 4];
        unsafe { std::ptr::copy_nonoverlapping(p, temp.as_mut_ptr(), 4) };
        int32 = i32::from_be_bytes(temp);
        int32 &= 0x7FFFFFFF;
        p = unsafe { p.offset(4) };
    } else {
        p = unsafe { p.offset(1) };
    }
    size = int32;

    // get the count
    if !plimit.is_null() && p > plimit {
        return false;
    }
    int32 = unsafe { *p as i32 };
    if int32 & 0x80 != 0 {
        if !plimit.is_null() && unsafe { p.offset(3) } > plimit {
            return false;
        }
        let mut temp = [0u8; 4];
        unsafe { std::ptr::copy_nonoverlapping(p, temp.as_mut_ptr(), 4) };
        int32 = i32::from_be_bytes(temp);
        int32 &= 0x7FFFFFFF;
        p = unsafe { p.offset(4) };
    } else {
        p = unsafe { p.offset(1) };
    }
    count = int32;

    if size < MIN_BINN_SIZE || count < 0 {
        return false;
    }

    // return the values
    *ptype = type_;
    *pcount = count;
    *psize = size;
    *pheadersize = unsafe { p.offset_from(pbuf.as_ptr()) } as i32;
    true
}

pub fn AdvanceDataPos(p: &mut Vec<u8>, plimit: &Vec<u8>) -> Option<Vec<u8>> {
    if p.as_ptr() > plimit.as_ptr() {
        return None;
    }

    let byte = p[0] as i32;
    p.remove(0);
    let storage_type = byte & BINN_STORAGE_MASK;
    if byte & BINN_STORAGE_HAS_MORE != 0 {
        p.remove(0);
    }

    match storage_type {
        BINN_STORAGE_NOBYTES => {}
        BINN_STORAGE_STRING => {
            if p.as_ptr() > plimit.as_ptr() {
                return None;
            }
            let mut DataSize = p[0] as i32;
            if DataSize & 0x80 != 0 {
                if p.len() < 4 {
                    return None;
                }
                let mut temp = [0u8; 4];
                temp.copy_from_slice(&p[0..4]);
                DataSize = i32::from_be_bytes(temp) & 0x7FFFFFFF;
                p.drain(0..4);
            } else {
                p.remove(0);
            }
            if p.len() < DataSize as usize {
                return None;
            }
            p.drain(0..DataSize as usize);
            p.remove(0);
        }
        BINN_STORAGE_CONTAINER => {
            if p.as_ptr() > plimit.as_ptr() {
                return None;
            }
            let mut DataSize = p[0] as i32;
            if DataSize & 0x80 != 0 {
                if p.len() < 4 {
                    return None;
                }
                let mut temp = [0u8; 4];
                temp.copy_from_slice(&p[0..4]);
                DataSize = i32::from_be_bytes(temp) & 0x7FFFFFFF;
            }
            DataSize -= 1;
            if p.len() < DataSize as usize {
                return None;
            }
            p.drain(0..DataSize as usize);
        }
        _ => {
            return None;
        }
    }

    Some(p.clone())
}

pub fn copy_int_value(psource: &i64, pdest: &mut i64, source_type: i32, dest_type: i32) -> bool {
    let mut vuint64: u64 = 0;
    let mut vint64: i64 = 0;

    match source_type {
        BINN_INT8 => vint64 = *psource as i8 as i64,
        BINN_INT16 => vint64 = *psource as i16 as i64,
        BINN_INT32 => vint64 = *psource as i32 as i64,
        BINN_INT64 => vint64 = *psource,

        BINN_UINT8 => vuint64 = *psource as u8 as u64,
        BINN_UINT16 => vuint64 = *psource as u16 as u64,
        BINN_UINT32 => vuint64 = *psource as u32 as u64,
        BINN_UINT64 => vuint64 = *psource as u64,

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
            if vint64 < i8::MIN as i64 || vint64 > i8::MAX as i64 {
                return false;
            }
            *pdest = vint64 as i8 as i64;
        }
        BINN_INT16 => {
            if vint64 < i16::MIN as i64 || vint64 > i16::MAX as i64 {
                return false;
            }
            *pdest = vint64 as i16 as i64;
        }
        BINN_INT32 => {
            if vint64 < i32::MIN as i64 || vint64 > i32::MAX as i64 {
                return false;
            }
            *pdest = vint64 as i32 as i64;
        }
        BINN_INT64 => *pdest = vint64,

        BINN_UINT8 => {
            if vuint64 > u8::MAX as u64 {
                return false;
            }
            *pdest = vuint64 as u8 as i64;
        }
        BINN_UINT16 => {
            if vuint64 > u16::MAX as u64 {
                return false;
            }
            *pdest = vuint64 as u16 as i64;
        }
        BINN_UINT32 => {
            if vuint64 > u32::MAX as u64 {
                return false;
            }
            *pdest = vuint64 as u32 as i64;
        }
        BINN_UINT64 => *pdest = vuint64 as i64,

        _ => return false,
    }

    true
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

pub fn copy_float_value<T: Into<f64> + From<f64> + From<f32>>(psource: T, pdest: &mut T, source_type: i32, dest_type: i32) -> bool {
    match source_type {
        BINN_FLOAT32 => {
            *pdest = T::from(psource.into() as f32);
            true
        }
        BINN_FLOAT64 => {
            *pdest = T::from(psource.into());
            true
        }
        _ => false,
    }
}

pub fn copy_raw_value<T>(psource: T, mut pdest: T, data_store: i32) -> bool {
    match data_store {
        BINN_STORAGE_NOBYTES => {}
        BINN_STORAGE_BYTE => {
            pdest = psource;
        }
        BINN_STORAGE_WORD => {
            pdest = psource;
        }
        BINN_STORAGE_DWORD => {
            pdest = psource;
        }
        BINN_STORAGE_QWORD => {
            pdest = psource;
        }
        BINN_STORAGE_BLOB => {
            pdest = psource;
        }
        BINN_STORAGE_STRING => {
            pdest = psource;
        }
        BINN_STORAGE_CONTAINER => {
            pdest = psource;
        }
        _ => return false,
    }
    true
}

pub fn strlen2(str: Option<String>) -> usize {
    match str {
        Some(s) => s.len(),
        None => 0,
    }
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

pub fn binn_malloc(size: i32) -> Vec<u8> {
    check_alloc_functions();
    unsafe {
        if let Some(malloc_fn_wrap) = &malloc_fn {
            malloc_fn_wrap(size as usize)
        } else {
            vec![]
        }
    }
}

pub fn GetValue(p: &mut Vec<u8>, plimit: &mut Vec<u8>, value: &mut Binn) -> bool {
    let mut byte: u8;
    let mut data_type: i32;
    let mut storage_type: i32;
    let mut data_size: i32;
    let mut p2: Vec<u8> = Vec::new();

    if value.is_null() {
        return false;
    }
    *value = Binn::default();
    value.header = BINN_MAGIC;

    p2 = p.clone();

    if p > plimit {
        return false;
    }
    byte = p[0];
    p.remove(0);
    storage_type = (byte as i32) & BINN_STORAGE_MASK;
    if (byte as i32) & BINN_STORAGE_HAS_MORE != 0 {
        data_type = (byte as i32) << 8;
        if p > plimit {
            return false;
        }
        byte = p[0];
        p.remove(0);
        data_type |= byte as i32;
    } else {
        data_type = byte as i32;
    }

    value.type_ = data_type;

    match storage_type {
        BINN_STORAGE_NOBYTES => (),
        BINN_STORAGE_STRING => {
            if p > plimit {
                return false;
            }
            data_size = p[0] as i32;
            if (data_size & 0x80) != 0 {
                if p.len() + 3 > plimit.len() {
                    return false;
                }
                let mut data_size_bytes = [0u8; 4];
                copy_be32(&mut data_size_bytes, &(i32::from_be_bytes([p[0], p[1], p[2], p[3]]) as u32));
                data_size = i32::from_be_bytes(data_size_bytes);
                data_size &= 0x7FFFFFFF;
                p.drain(0..4);
            } else {
                p.remove(0);
            }
            if p.len() + data_size as usize - 1 > plimit.len() {
                return false;
            }
            value.size = data_size;
            value.ptr = p.clone();
        }
        BINN_STORAGE_CONTAINER => {
            value.ptr = p2.clone();
            if !IsValidBinnHeader(&p2, &mut 0, &mut value.count, &mut value.size, &mut 0) {
                return false;
            }
        }
        _ => return false,
    }

    match value.type_ {
        BINN_TRUE => {
            value.type_ = BINN_BOOL;
            value.vbool = true;
            value.ptr = vec![value.vbool as u8];
        }
        BINN_FALSE => {
            value.type_ = BINN_BOOL;
            value.vbool = false;
            value.ptr = vec![value.vbool as u8];
        }
        _ => (),
    }

    true
}

pub fn SearchForKey(p: &mut Vec<u8>, header_size: i32, size: i32, numitems: i32, key: &str) -> Option<Vec<u8>> {
    let mut base = p.clone();
    let plimit = p.len() as i32 - 1;
    let mut p = p.split_off(header_size as usize);
    let keylen = key.len() as i32;

    for _ in 0..numitems {
        if p.len() as i32 > plimit {
            break;
        }
        let len = p[0] as i32;
        p.remove(0);
        if p.len() as i32 + len > plimit {
            break;
        }
        if len > 0 {
            if p[0..len as usize].eq_ignore_ascii_case(key.as_bytes()) {
                if keylen == len {
                    p.drain(0..len as usize);
                    return Some(p);
                }
            }
            p.drain(0..len as usize);
        } else if len == keylen {
            return Some(p);
        }
        p = match AdvanceDataPos(&mut p, &base) {
            Some(new_p) => new_p,
            None => break,
        };
        if p.len() < base.len() {
            break;
        }
    }

    None
}

pub fn binn_ptr<T: AsRef<[u8]>>(ptr: Option<T>) -> Option<Vec<u8>> {
    match binn_get_ptr_type(ptr.as_ref().map(|_| ())) {
        BINN_STRUCT => {
            let mut item = Binn::default();
            if item.writable && item.dirty {
                binn_save_header(&mut item);
            }
            Some(item.ptr.clone())
        }
        BINN_BUFFER => Some(ptr.unwrap().as_ref().to_vec()),
        _ => None,
    }
}

pub fn binn_get_read_storage(type_: i32) -> i32 {
    let mut storage_type: i32 = 0;

    match type_ {
        BINN_SINGLE_STR => return BINN_STORAGE_DWORD,
        BINN_DOUBLE_STR => return BINN_STORAGE_QWORD,
        BINN_BOOL => return BINN_STORAGE_DWORD,
        BINN_TRUE => return BINN_STORAGE_DWORD,
        BINN_FALSE => return BINN_STORAGE_DWORD,
        _ => {
            binn_get_type_info(type_, Some(&mut storage_type), None);
            return storage_type;
        }
    }
}

pub fn read_map_id(pp: &mut Vec<u8>, plimit: &Vec<u8>) -> i32 {
    let mut p = pp.clone();
    let mut id: i32 = 0;
    let mut extra_bytes: i32 = 0;
    let mut sign: u8 = 0;
    let mut type_: u8 = 0;

    if p.len() > plimit.len() {
        return 0;
    }

    let c = p.remove(0);

    if c & 0x80 != 0 {
        extra_bytes = (((c & 0x60) >> 5) as i32) + 1;
        if p.len() + extra_bytes as usize > plimit.len() {
            *pp = p;
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
        id = (id << 8) | p.remove(0) as i32;
    } else if type_ == 0xA0 {
        id = (c & 0x0F) as i32;
        id = (id << 8) | p.remove(0) as i32;
        id = (id << 8) | p.remove(0) as i32;
    } else if type_ == 0xC0 {
        id = (c & 0x0F) as i32;
        id = (id << 8) | p.remove(0) as i32;
        id = (id << 8) | p.remove(0) as i32;
        id = (id << 8) | p.remove(0) as i32;
    } else if type_ == 0xE0 {
        let mut id_bytes = [0u8; 4];
        id_bytes.copy_from_slice(&p[0..4]);
        id = i32::from_be_bytes(id_bytes);
        p.drain(0..4);
    } else {
        *pp = plimit.clone();
        return 0;
    }

    if sign != 0 {
        id = -id;
    }

    *pp = p;

    id
}

pub fn binn_create(item: &mut Binn, type_: i32, size: i32, pointer: Option<Vec<u8>>) -> bool {
    let mut retval = false;

    match type_ {
        BINN_LIST | BINN_MAP | BINN_OBJECT => (),
        _ => return retval,
    }

    if size < 0 {
        return retval;
    }

    let mut alloc_size = size;
    if size < MIN_BINN_SIZE {
        if pointer.is_some() {
            return retval;
        } else {
            alloc_size = 0;
        }
    }

    *item = Binn::default();

    if let Some(pointer) = pointer {
        item.pre_allocated = true;
        item.pbuf = pointer;
    } else {
        item.pre_allocated = false;
        let alloc_size = if alloc_size == 0 { CHUNK_SIZE } else { alloc_size };
        let pointer = binn_malloc(alloc_size);
        if pointer.is_empty() {
            return retval;
        }
        item.pbuf = pointer;
    }

    item.alloc_size = size;
    item.header = BINN_MAGIC;
    item.writable = true;
    item.used_size = MAX_BINN_HEADER;
    item.type_ = type_;
    item.dirty = true;

    retval = true;
    retval
}

pub fn binn_object_get_value<T: AsRef<[u8]>>(ptr: Option<T>, key: &str, value: &mut Binn) -> bool {
    let ptr = binn_ptr(ptr.as_ref().map(|x| x.as_ref()));
    if ptr.is_none() || key.is_empty() || value.is_null() {
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

    if type_ != BINN_OBJECT {
        return false;
    }

    if count == 0 {
        return false;
    }

    let mut p = ptr.unwrap();
    let plimit = p.len() as i32 - 1;

    let p = SearchForKey(&mut p, header_size, size, count, key);
    if p.is_none() {
        return false;
    }

    let mut p = p.unwrap();
    let mut plimit_vec = p.clone();
    plimit_vec.truncate(plimit as usize);

    GetValue(&mut p, &mut plimit_vec, value)
}

pub fn copy_value<T: Into<i64> + From<i64> + Into<f64> + From<f64> + From<f32>>(psource: T, mut pdest: T, source_type: i32, dest_type: i32, data_store: i32) -> bool {
    if type_family(source_type) != type_family(dest_type) {
        return false;
    }

    if type_family(source_type) == BINN_FAMILY_INT && source_type != dest_type {
        let psource_wrap: i64 = psource.into();
        let mut pdest_wrap: i64 = pdest.into();
        let result = copy_int_value(&psource_wrap, &mut pdest_wrap, source_type, dest_type);
        pdest = T::from(pdest_wrap);
        return result;
    } else if type_family(source_type) == BINN_FAMILY_FLOAT && source_type != dest_type {
        return copy_float_value(psource, &mut pdest, source_type, dest_type);
    } else {
        return copy_raw_value(psource, pdest, data_store);
    }
}

pub fn zero_value<T>(pvalue: &mut T, type_: i32) {
    match binn_get_read_storage(type_) {
        BINN_STORAGE_NOBYTES => {}
        BINN_STORAGE_BYTE => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_WORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_DWORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_QWORD => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_BLOB => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_STRING => *pvalue = unsafe { std::mem::zeroed() },
        BINN_STORAGE_CONTAINER => *pvalue = unsafe { std::mem::zeroed() },
        _ => {}
    }
}

pub fn SearchForID(p: &mut Vec<u8>, header_size: i32, size: i32, numitems: i32, id: i32) -> Option<Vec<u8>> {
    let mut base = p.clone();
    let plimit = base.len() as i32 - 1;
    let mut p = base.split_off(header_size as usize);

    for _ in 0..numitems {
        let int32 = read_map_id(&mut p, &base);
        if p.len() > plimit as usize {
            break;
        }
        if int32 == id {
            return Some(p);
        }
        match AdvanceDataPos(&mut p, &base) {
            Some(new_p) => p = new_p,
            None => break,
        }
        if p.len() < base.len() {
            break;
        }
    }

    None
}

pub fn binn_list_get_value<T: AsRef<[u8]>>(ptr: Option<T>, pos: i32, value: &mut Binn) -> bool {
    let mut i: i32;
    let mut type_: i32 = 0;
    let mut count: i32 = 0;
    let mut size: i32 = 0;
    let mut header_size: i32 = 0;
    let mut p: Vec<u8>;
    let mut plimit: Vec<u8>;
    let mut base: Vec<u8>;

    let ptr = binn_ptr(ptr);
    if ptr.is_none() || value.is_null() {
        return false;
    }

    let ptr = ptr.unwrap();

    if !IsValidBinnHeader(&ptr, &mut type_, &mut count, &mut size, &mut header_size) {
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

    p = ptr.clone();
    base = p.clone();
    plimit = p.clone();
    plimit.truncate((size - 1) as usize);
    p.truncate(header_size as usize);

    for i in 0..pos {
        if let Some(new_p) = AdvanceDataPos(&mut p, &plimit) {
            p = new_p;
        } else {
            return false;
        }
    }

    GetValue(&mut p, &mut plimit, value)
}

pub fn binn_new(type_: i32, size: i32, pointer: Option<Vec<u8>>) -> Option<Binn> {
    let mut item = Binn::default();

    if !binn_create(&mut item, type_, size, pointer) {
        return None;
    }

    item.allocated = true;
    Some(item)
}

pub fn GetWriteConvertedData(ptype: &mut i32, ppvalue: &mut Option<Vec<u8>>, psize: &mut i32) -> bool {
    let mut type_ = *ptype;
    let mut f1: f32 = 0.0;
    let mut d1: f64 = 0.0;
    let mut pstr: String = String::with_capacity(128);

    if ppvalue.is_none() {
        match type_ {
            BINN_NULL | BINN_TRUE | BINN_FALSE => {}
            BINN_STRING | BINN_BLOB => {
                if *psize == 0 {}
            }
            _ => return false,
        }
    }

    match type_ {
        #[cfg(feature = "BINN_EXTENDED")]
        BINN_SINGLE => {
            f1 = unsafe { *(*(ppvalue.as_ref().unwrap().as_ptr() as *const *const f32)) };
            d1 = f1 as f64;
            type_ = BINN_SINGLE_STR;
            pstr = format!("{:.17e}", d1);
            *ppvalue = Some(pstr.into_bytes());
            *ptype = type_;
        }
        #[cfg(feature = "BINN_EXTENDED")]
        BINN_DOUBLE => {
            d1 = unsafe { *(*(ppvalue.as_ref().unwrap().as_ptr() as *const *const f64)) };
            type_ = BINN_DOUBLE_STR;
            pstr = format!("{:.17e}", d1);
            *ppvalue = Some(pstr.into_bytes());
            *ptype = type_;
        }
        BINN_DECIMAL | BINN_CURRENCYSTR => {
            return true;
        }
        BINN_DATE | BINN_DATETIME | BINN_TIME => {
            return true;
        }
        BINN_BOOL => {
            let bool_value = unsafe { *(*(ppvalue.as_ref().unwrap().as_ptr() as *const *const bool)) };
            if bool_value {
                type_ = BINN_TRUE;
            } else {
                type_ = BINN_FALSE;
            }
            *ptype = type_;
        }
        _ => {}
    }

    true
}

pub fn store_value(value: &Binn) -> i32 {
    let mut local_value = value.clone();

    match binn_get_read_storage(value.type_) {
        BINN_STORAGE_NOBYTES | BINN_STORAGE_WORD | BINN_STORAGE_DWORD | BINN_STORAGE_QWORD => local_value.vint32,
        _ => i32::from(value.ptr[0]),
    }
}

pub fn binn_buf_size(pbuf: &Vec<u8>) -> i32 {
    let mut size: i32 = 0;

    if !IsValidBinnHeader(pbuf, &mut 0, &mut 0, &mut size, &mut 0) {
        return 0;
    }

    size
}

pub fn binn_is_valid_ex2(ptr: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32) -> bool {
    let mut type_: i32 = 0;
    let mut count: i32 = 0;
    let mut size: i32 = 0;
    let mut header_size: i32 = 0;

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

    let mut p = ptr.clone();
    let base = p.clone();
    let plimit = p.len() as i32 - 1;

    p.drain(0..header_size as usize);

    for _ in 0..count {
        match type_ {
            BINN_OBJECT => {
                if p.is_empty() {
                    return false;
                }
                let len = p[0] as i32;
                p.remove(0);
                p.drain(0..len as usize);
            }
            BINN_MAP => {
                if read_map_id(&mut p, &plimit.to_be_bytes().to_vec()) == 0 {
                    return false;
                }
            }
            BINN_LIST => {}
            _ => {
                return false;
            }
        }

        if p.is_empty() {
            return false;
        }

        if (p[0] as i32 & BINN_STORAGE_MASK) == BINN_STORAGE_CONTAINER {
            let mut size2 = plimit - p.len() as i32 + 1;
            if !binn_is_valid_ex2(&p, &mut 0, &mut 0, &mut size2) {
                return false;
            }
            p.drain(0..size2 as usize);
        } else {
            if let Some(new_p) = AdvanceDataPos(&mut p, &plimit.to_be_bytes().to_vec()) {
                p = new_p;
            } else {
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
    *psize = size;

    true
}

pub fn binn_read_pair(expected_type: i32, ptr: Option<Vec<u8>>, pos: i32, pid: &mut i32, pkey: &mut String, value: &mut Binn) -> bool {
    let mut type_: i32 = 0;
    let mut count: i32 = 0;
    let mut size: i32 = 0;
    let mut header_size: i32 = 0;

    let ptr = match ptr {
        Some(p) => p,
        None => return false,
    };

    if !IsValidBinnHeader(&ptr, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != expected_type || count == 0 || pos < 1 || pos > count {
        return false;
    }

    let mut p = ptr.clone();
    let base = p.as_ptr();
    let plimit = p.as_ptr().wrapping_add(size as usize - 1);
    p.drain(0..header_size as usize);

    let mut id = 0;
    let mut key = String::new();
    let mut len = 0;
    let mut counter = 0;

    for i in 0..count {
        match type_ {
            BINN_MAP => {
                let int32 = read_map_id(&mut p, &ptr);
                if p.as_ptr() > plimit {
                    return false;
                }
                id = int32;
            }
            BINN_OBJECT => {
                len = p[0] as usize;
                p.remove(0);
                if p.as_ptr() > plimit {
                    return false;
                }
                key = String::from_utf8(p[0..len].to_vec()).unwrap();
                p.drain(0..len);
                if p.as_ptr() > plimit {
                    return false;
                }
            }
            _ => {}
        }
        counter += 1;
        if counter == pos {
            break;
        }

        if let Some(new_p) = AdvanceDataPos(&mut p, &ptr) {
            p = new_p;
        } else {
            return false;
        }
    }

    match type_ {
        BINN_MAP => {
            *pid = id;
        }
        BINN_OBJECT => {
            *pkey = key;
        }
        _ => {}
    }

    GetValue(&mut p, &mut ptr.clone(), value)
}

pub fn binn_map_get_value<T: AsRef<[u8]>>(ptr: Option<T>, id: i32, value: &mut Binn) -> bool {
    let mut type_: i32 = 0;
    let mut count: i32 = 0;
    let mut size: i32 = 0;
    let mut header_size: i32 = 0;

    let ptr = binn_ptr(ptr);
    if ptr.is_none() || value.is_null() {
        return false;
    }

    let pbuf = ptr.unwrap();

    if !IsValidBinnHeader(&pbuf, &mut type_, &mut count, &mut size, &mut header_size) {
        return false;
    }

    if type_ != BINN_MAP {
        return false;
    }

    if count == 0 {
        return false;
    }

    let mut p = pbuf.clone();
    let plimit = pbuf.len() - 1;

    let p = SearchForID(&mut p, header_size, size, count, id);
    if p.is_none() {
        return false;
    }

    GetValue(&mut p.unwrap(), &mut pbuf[plimit..].to_vec(), value)
}

pub fn binn_is_valid_ex(ptr: &Vec<u8>, ptype: &mut i32, pcount: &mut i32, psize: &mut i32) -> bool {
    let mut size: i32 = 0;

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

pub fn binn_free(item: Option<Binn>) {
    if item.is_none() {
        return;
    }
    let mut item = item.unwrap();
    if item.writable && !item.pre_allocated {
        if let Some(free_fn_wrap) = unsafe { &mut free_fn } {
            free_fn_wrap(item.pbuf.clone());
        }
    }
    if let Some(freefn) = item.freefn {
        freefn(item.ptr);
    }
    if item.allocated {
        if let Some(free_fn_wrap) = unsafe { &mut free_fn } {
            free_fn_wrap(item.pbuf);
        }
    } else {
        item = Binn::default();
        item.header = BINN_MAGIC;
    }
}

pub fn binn_list() -> Option<Binn> {
    binn_new(BINN_LIST, 0, None)
}

pub fn binn_list_read<T: AsRef<[u8]>>(list: Option<T>, pos: i32, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<Vec<u8>> {
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

    Some(store_value(&value).to_be_bytes().to_vec())
}

pub fn binn_object_read<T: AsRef<[u8]>>(obj: Option<T>, key: &str, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<i32> {
    let mut value = Binn::default();
    if !binn_object_get_value(obj, key, &mut value) {
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

pub fn binn_map() -> Option<Binn> {
    binn_new(BINN_MAP, 0, None)
}

pub fn binn_object() -> Option<Binn> {
    binn_new(BINN_OBJECT, 0, None)
}

pub fn binn_map_read<T: AsRef<[u8]>>(map: Option<T>, id: i32, ptype: Option<&mut i32>, psize: Option<&mut i32>) -> Option<i32> {
    let mut value = Binn::default();

    if !binn_map_get_value(map, id, &mut value) {
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

pub fn binn_list_blob(list: Option<&Vec<u8>>, pos: i32, psize: Option<&mut i32>) -> Option<Vec<u8>> {
    let mut value = Vec::new();
    let mut size = 0;
    if binn_list_get(list, pos, BINN_BLOB, &mut value, &mut size) {
        if let Some(psize) = psize {
            *psize = size;
        }
        Some(value)
    } else {
        None
    }
}

pub fn binn_list_get(ptr: Option<&Vec<u8>>, pos: i32, type_: i32, pvalue: &mut Vec<u8>, psize: &mut i32) -> bool {
    let mut value = Binn::default();
    let storage_type = binn_get_read_storage(type_);

    if storage_type != BINN_STORAGE_NOBYTES && pvalue.is_empty() {
        return false;
    }

    zero_value(pvalue, type_);

    if !binn_list_get_value(ptr, pos, &mut value) {
        return false;
    }

    if !copy_raw_value(value.ptr.clone(), pvalue.to_vec(), storage_type) {
        return false;
    }

    if psize != &mut 0 {
        *psize = value.size;
    }

    true
}

pub fn binn_map_get_pair(ptr: Option<Vec<u8>>, pos: i32, pid: &mut i32, value: &mut Binn) -> bool {
    binn_read_pair(BINN_MAP, ptr, pos, pid, &mut String::new(), value)
}

pub fn binn_size(ptr: Option<&Binn>) -> i32 {
    match ptr {
        Some(item) => {
            if item.writable && item.dirty {
                binn_save_header(&mut item.clone());
            }
            item.size
        }
        None => 0,
    }
}

pub fn binn_object_str<T: AsRef<[u8]>>(obj: Option<T>, key: &str) -> Option<String> {
    let mut value = String::new();
    if binn_object_get(obj, key, BINN_STRING, &mut value, None) {
        Some(value)
    } else {
        None
    }
}

pub fn binn_object_get<T: AsRef<[u8]>>(ptr: Option<T>, key: &str, type_: i32, pvalue: &mut String, psize: Option<&mut i32>) -> bool {
    let storage_type = binn_get_read_storage(type_);
    if storage_type != BINN_STORAGE_NOBYTES && pvalue.is_empty() {
        return false;
    }

    zero_value(pvalue, type_);

    let mut value = Binn::default();
    if !binn_object_get_value(ptr, key, &mut value) {
        return false;
    }

    let value_wrap = String::from_utf8(value.ptr).unwrap_or_default();
    *pvalue = value_wrap;

    if let Some(size) = psize {
        *size = value.size;
    }

    true
}

pub fn binn_version() -> String {
    "3.0.0".to_string()
}

