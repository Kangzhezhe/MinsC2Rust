pub const INT64_FORMAT: &str = "I64i";
pub const INT64_HEX_FORMAT: &str = "I64x";
pub const EPSILON: f64 = 1.0E-8;
pub const VERYSMALL: f64 = 1.0E-150;
pub const TRUE: bool = true;
pub const FALSE: bool = false;

use test_project::binn::{
    Binn, BinnIter, BIG_ENDIAN, BINN_BLOB, BINN_BMP, BINN_BOOL, BINN_BUFFER, BINN_CSS,
    BINN_CURRENCY, BINN_CURRENCYSTR, BINN_DATE, BINN_DATETIME, BINN_DECIMAL, BINN_DOUBLE,
    BINN_DOUBLE_STR, BINN_FALSE, BINN_FAMILY_BINN, BINN_FAMILY_BLOB, BINN_FAMILY_BOOL,
    BINN_FAMILY_FLOAT, BINN_FAMILY_INT, BINN_FAMILY_NONE, BINN_FAMILY_NULL, BINN_FAMILY_STRING,
    BINN_FLOAT32, BINN_FLOAT64, BINN_GIF, BINN_HTML, BINN_INT16, BINN_INT32, BINN_INT64, BINN_INT8,
    BINN_JAVASCRIPT, BINN_JPEG, BINN_JSON, BINN_LIST, BINN_MAGIC, BINN_MAP, BINN_NULL, BINN_OBJECT,
    BINN_PNG, BINN_SIGNED_INT, BINN_SINGLE, BINN_SINGLE_STR, BINN_STORAGE_BLOB, BINN_STORAGE_BYTE,
    BINN_STORAGE_CONTAINER, BINN_STORAGE_DWORD, BINN_STORAGE_HAS_MORE, BINN_STORAGE_MASK,
    BINN_STORAGE_MASK16, BINN_STORAGE_NOBYTES, BINN_STORAGE_QWORD, BINN_STORAGE_STRING,
    BINN_STORAGE_VIRTUAL, BINN_STORAGE_WORD, BINN_STRING, BINN_STRUCT, BINN_TIME, BINN_TRUE,
    BINN_TYPE_MASK, BINN_TYPE_MASK16, BINN_UINT16, BINN_UINT32, BINN_UINT64, BINN_UINT8,
    BINN_UNSIGNED_INT, BINN_VERSION, BINN_XML, CHUNK_SIZE, INT16_MAX, INT16_MIN, INT32_MAX,
    INT32_MIN, INT64_MAX, INT64_MIN, INT8_MAX, INT8_MIN, LITTLE_ENDIAN, MAX_BINN_HEADER,
    MIN_BINN_SIZE, NULL, UINT16_MAX, UINT32_MAX, UINT8_MAX,
};

use test_project::binn::{
    binn_buf_size, binn_create, binn_free, binn_get_ptr_type, binn_get_read_storage,
    binn_get_type_info, binn_get_write_storage, binn_list, binn_list_add, binn_list_add_blob,
    binn_list_add_bool, binn_list_add_double, binn_list_add_int32, binn_list_add_raw,
    binn_list_add_str, binn_list_blob, binn_list_get, binn_list_get_int32, binn_list_get_value,
    binn_malloc, binn_map, binn_map_get_value, binn_map_set, binn_map_set_blob, binn_map_set_bool,
    binn_map_set_double, binn_map_set_int32, binn_map_set_raw, binn_map_set_str, binn_new,
    binn_object, binn_object_get_value, binn_object_set, binn_object_set_blob,
    binn_object_set_bool, binn_object_set_double, binn_object_set_int32, binn_object_set_raw,
    binn_object_set_str, binn_ptr, binn_save_header, binn_size, check_alloc_functions,
    compress_int, copy_be16, copy_be32, copy_be64, copy_float_value, copy_int_value,
    copy_raw_value, copy_value, int_type, read_map_id, strlen2, type_family, zero_value, AddValue,
    AdvanceDataPos, CalcAllocation, CheckAllocation, GetValue, GetWriteConvertedData,
    IsValidBinnHeader, SearchForID, SearchForKey,
};

use ntest::timeout;
pub fn i64toa(value: i64, buf: &mut String, radix: i32) -> &mut String {
    match radix {
        10 => {
            *buf = format!("{}{}", INT64_FORMAT, value);
        }
        16 => {
            *buf = format!("{}{}", INT64_HEX_FORMAT, value);
        }
        _ => {
            buf.clear();
        }
    }
    buf
}

pub fn return_passed_int64(a: i64) -> i64 {
    a
}

pub fn return_int64() -> i64 {
    9223372036854775807
}

pub fn pass_int64(a: i64) {
    assert_eq!(a, 9223372036854775807);
    assert!(a > 9223372036854775806);
}

pub fn AlmostEqualDoubles(a: f64, b: f64) -> bool {
    let mut absDiff = (a - b).abs();
    if absDiff < VERYSMALL {
        return TRUE;
    }

    let mut absA = a.abs();
    let mut absB = b.abs();
    let mut maxAbs = max(absA, absB);
    if (absDiff / maxAbs) < EPSILON {
        return TRUE;
    }
    println!("a={} b={}", a, b);
    FALSE
}

pub fn max<T: PartialOrd>(a: T, b: T) -> T {
    if a > b {
        a
    } else {
        b
    }
}

pub fn AlmostEqualFloats(A: f32, B: f32, maxUlps: i32) -> bool {
    let mut aInt: u32;
    let mut bInt: u32;
    let mut intDiff: u32;
    assert!(maxUlps > 0 && maxUlps < 4 * 1024 * 1024);
    aInt = unsafe { std::mem::transmute(A) };
    bInt = unsafe { std::mem::transmute(B) };
    if (aInt as i32) < 0 {
        aInt = 0x80000000u32 - aInt;
    }
    if (bInt as i32) < 0 {
        bInt = 0x80000000u32 - bInt;
    }
    intDiff = (aInt as i32 - bInt as i32).abs() as u32;
    if intDiff <= maxUlps as u32 {
        true
    } else {
        false
    }
}

pub fn memdup<T: Clone>(src: Option<Vec<T>>, size: usize) -> Option<Vec<T>> {
    if src.is_none() || size == 0 {
        return None;
    }
    let src = src.unwrap();
    if src.len() < size {
        return None;
    }
    Some(src[..size].to_vec())
}

#[test]
#[timeout(60000)]
pub fn test_preallocated_binn() {
    const FIX_SIZE: i32 = 512;
    let mut ptr = binn_malloc(FIX_SIZE).unwrap();

    let mut obj1 = binn_new(BINN_OBJECT, FIX_SIZE, Some(ptr.to_vec()));
    assert!(obj1.is_some());

    let obj1 = obj1.as_mut().unwrap();
    assert_eq!(obj1.header, BINN_MAGIC as i32);
    assert_eq!(obj1.type_, BINN_OBJECT);
    assert_eq!(obj1.count, 0);
    assert!(!obj1.pbuf.is_empty());
    assert_eq!(obj1.alloc_size, FIX_SIZE);
    assert_eq!(obj1.used_size, MAX_BINN_HEADER as i32);
    assert!(obj1.pre_allocated);

    binn_free(Some(obj1.clone()));
}

#[test]
#[timeout(60000)]
pub fn test_read_values_with_compression() {
    let mut list = binn_list();
    let mut map = binn_map();
    let mut obj = binn_object();

    assert_eq!(binn_list_add_int32(list.as_mut().unwrap(), 123), true);
    assert_eq!(binn_map_set_int32(map.as_mut().unwrap(), 1001, 456), true);
    assert_eq!(
        binn_object_set_int32(obj.as_mut().unwrap(), "int", 789),
        true
    );

    let mut value = Binn::default();

    assert_eq!(
        binn_list_get_value(Some(&list.as_ref().unwrap().pbuf), 1, &mut value),
        true
    );
    assert_eq!(value.vint, 123);

    value = Binn::default();
    assert_eq!(
        binn_map_get_value(Some(&map.as_ref().unwrap().pbuf), 1001, &mut value),
        true
    );
    assert_eq!(value.vint, 456);

    value = Binn::default();
    assert_eq!(
        binn_object_get_value(Some(&obj.as_ref().unwrap().pbuf), "int", &mut value),
        true
    );
    assert_eq!(value.vint, 789);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_create_and_add_values_with_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    assert!(!list.is_null());
    assert!(!map.is_null());
    assert!(!obj.is_null());

    assert!(binn_list_add_int32(&mut list, 123));
    assert!(binn_map_set_int32(&mut map, 1001, 456));
    assert!(binn_object_set_int32(&mut obj, "int", 789));

    assert!(binn_list_add_double(&mut list, 1.23));
    assert!(binn_map_set_double(&mut map, 1002, 4.56));
    assert!(binn_object_set_double(&mut obj, "double", 7.89));

    assert!(binn_list_add_bool(&mut list, true));
    assert!(binn_map_set_bool(&mut map, 1003, true));
    assert!(binn_object_set_bool(&mut obj, "bool", true));

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_binn_blob_operations() {
    let mut list = binn_new(BINN_LIST, 0, None);
    let blobsize = 150;
    let mut pblob = vec![55u8; blobsize as usize];
    let mut mutable_blobsize = blobsize;

    assert!(binn_list_add(
        &mut list.as_mut().unwrap(),
        BINN_BLOB,
        Some(&pblob),
        blobsize
    ));

    let ptr = binn_list_blob(
        Some(&list.as_ref().unwrap().pbuf),
        1,
        Some(&mut mutable_blobsize),
    );
    assert!(ptr.is_some());
    assert!(ptr
        .as_ref()
        .unwrap()
        .iter()
        .zip(pblob.iter())
        .all(|(a, b)| a == b));

    binn_free(list);
}

#[test]
#[timeout(60000)]
pub fn test_valid_binn_operations() {
    let mut list = binn_new(BINN_LIST, 0, None);
    let mut map = binn_new(BINN_MAP, 0, None);
    let mut obj = binn_new(BINN_OBJECT, 0, None);
    let mut i = 0x1234i32;

    assert!(binn_list_add(
        list.as_mut().unwrap(),
        BINN_INT32,
        Some(&vec![i.to_be_bytes().to_vec()].concat()),
        0
    ));
    assert!(binn_map_set(
        map.as_mut().unwrap(),
        5501,
        BINN_INT32,
        Some(&vec![i.to_be_bytes().to_vec()].concat()),
        0
    ));
    assert!(!binn_map_set(
        map.as_mut().unwrap(),
        5501,
        BINN_INT32,
        Some(&vec![i.to_be_bytes().to_vec()].concat()),
        0
    ));
    assert!(binn_object_set(
        obj.as_mut().unwrap(),
        "test",
        BINN_INT32,
        Some(&vec![i.to_be_bytes().to_vec()].concat()),
        0
    ));
    assert!(!binn_object_set(
        obj.as_mut().unwrap(),
        "test",
        BINN_INT32,
        Some(&vec![i.to_be_bytes().to_vec()].concat()),
        0
    ));

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_invalid_binn_creation() {
    let ptr: Vec<u8> = Vec::new();
    let mut obj1: Option<Box<Binn>> = None;

    assert!(binn_new(-1, 0, None).is_none());
    assert!(binn_new(0, 0, None).is_none());
    assert!(binn_new(5, 0, None).is_none());
    assert!(binn_new(BINN_MAP, -1, None).is_none());

    let ptr_wrap = unsafe { std::mem::transmute::<_, *mut u8>(&mut obj1) };
    let ptr_vec1 = unsafe { Vec::from_raw_parts(ptr_wrap, 0, 0) };
    let ptr_vec2 = unsafe { Vec::from_raw_parts(ptr_wrap, 0, 0) };
    assert!(binn_new(BINN_MAP, -1, Some(ptr_vec1)).is_none());
    assert!(binn_new(BINN_MAP, MIN_BINN_SIZE - 1, Some(ptr_vec2)).is_none());
}

#[test]
#[timeout(60000)]
pub fn test_int64() {
    let mut i64: i64;
    let mut buf = String::with_capacity(64);

    pass_int64(9223372036854775807);

    i64 = return_int64();
    assert_eq!(i64, 9223372036854775807);

    i64toa(i64, &mut buf, 10);
    assert_eq!(buf, "9223372036854775807");

    i64 = return_passed_int64(-987654321987654321);
    assert_eq!(i64, -987654321987654321);

    i64toa(i64, &mut buf, 10);
    assert_eq!(buf, "-987654321987654321");
}

#[test]
#[timeout(60000)]
pub fn test_binn_size_operations() {
    let mut list = binn_new(BINN_LIST, 0, None);
    let mut map = binn_new(BINN_MAP, 0, None);
    let mut obj = binn_new(BINN_OBJECT, 0, None);

    assert!(binn_size(list.as_deref()) == list.as_ref().unwrap().size);
    assert!(binn_size(map.as_deref()) == map.as_ref().unwrap().size);
    assert!(binn_size(obj.as_deref()) == obj.as_ref().unwrap().size);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_binn_size_and_validation() {
    let mut list = binn_list();
    let mut map = binn_map();
    let mut obj = binn_object();
    let ptr = binn_ptr(obj.as_ref().map(|b| &b.ptr));
    assert!(ptr.is_some());
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;
    assert!(IsValidBinnHeader(
        &ptr.unwrap(),
        &mut type_,
        &mut count,
        &mut size,
        &mut header_size
    ));
    assert_eq!(type_, BINN_OBJECT);
    assert_eq!(count, 0);
    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_preallocated_binn_creation() {
    const FIX_SIZE: i32 = 512;
    let mut ptr = vec![0u8; FIX_SIZE as usize];

    let mut obj1 = binn_new(BINN_OBJECT, FIX_SIZE, Some(ptr.clone()));
    assert!(obj1.is_some());
    let obj1 = obj1.unwrap();

    assert!(obj1.header == BINN_MAGIC as i32);
    assert!(obj1.type_ == BINN_OBJECT);
    assert!(obj1.count == 0);
    assert!(!obj1.pbuf.is_empty());
    assert!(obj1.alloc_size == FIX_SIZE);
    assert!(obj1.used_size == MAX_BINN_HEADER as i32);
    assert!(obj1.pre_allocated == true);

    binn_free(Some(obj1));
}

#[test]
#[timeout(60000)]
pub fn test_add_and_read_blob() {
    let mut list = binn_list().unwrap();
    let blobsize = 150;
    let mut pblob = vec![55u8; blobsize as usize];

    assert!(binn_list_add(&mut list, BINN_BLOB, Some(&pblob), blobsize));

    let ptr = binn_list_blob(Some(&list.pbuf), 1, None);
    assert!(ptr.is_some());
    let ptr = ptr.unwrap();
    assert_eq!(ptr, pblob);

    binn_free(Some(list));
}

#[test]
#[timeout(60000)]
pub fn test_floating_point_numbers() {
    let mut buf = String::new();
    let mut f1: f32;
    let mut d1: f64;

    println!("testing floating point... ");

    f1 = 1.25;
    assert!(f1 == 1.25);
    d1 = 1.25;
    assert!(d1 == 1.25);

    d1 = 0.0;
    d1 = f1 as f64;
    assert!(d1 == 1.25);
    f1 = 0.0;
    f1 = d1 as f32;
    assert!(f1 == 1.25);

    d1 = 1.234;
    assert!(AlmostEqualDoubles(d1, 1.234) == TRUE);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 1.234, 2) == TRUE);

    d1 = 1.2345;
    assert!(AlmostEqualDoubles(d1, 1.2345) == TRUE);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 1.2345, 2) == TRUE);

    d1 = "1.234".parse::<f64>().unwrap();
    assert!(AlmostEqualDoubles(d1, 1.234) == TRUE);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 1.234, 2) == TRUE);

    buf = format!("{:.3}", d1);
    assert!(!buf.is_empty());
    assert!(buf == "1.234");

    d1 = "12.34".parse::<f64>().unwrap();
    assert!(d1 == 12.34);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 12.34, 2) == TRUE);

    buf = format!("{:.2}", d1);
    assert!(!buf.is_empty());
    assert!(buf == "12.34");

    d1 = "1.234e25".parse::<f64>().unwrap();
    assert!(AlmostEqualDoubles(d1, 1.234e25) == TRUE);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 1.234e25, 2) == TRUE);

    buf = format!("{}", d1);
    assert!(!buf.is_empty());

    println!("OK");
}

#[test]
#[timeout(60000)]
pub fn test_read_values_no_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    list.disable_int_compression = true;
    map.disable_int_compression = true;
    obj.disable_int_compression = true;

    assert!(binn_list_add_int32(&mut list, 123));
    assert!(binn_map_set_int32(&mut map, 1001, 456));
    assert!(binn_object_set_int32(&mut obj, "int", 789));

    let mut value = Binn::default();

    assert!(binn_list_get_value(Some(&list.pbuf), 1, &mut value));
    assert!(value.vint == 123);

    value = Binn::default();
    assert!(binn_map_get_value(Some(&map.pbuf), 1001, &mut value));
    assert!(value.vint == 456);

    value = Binn::default();
    assert!(binn_object_get_value(Some(&obj.pbuf), "int", &mut value));
    assert!(value.vint == 789);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

pub fn print_binn(map: &Binn) {
    let p = binn_ptr(Some(&map.ptr));
    let size = binn_size(Some(map));
    if let Some(data) = p {
        for i in 0..size {
            print!("{:02x} ", data[i as usize]);
        }
    }
    println!();
}

#[test]
#[timeout(60000)]
pub fn test_add_and_read_integer() {
    let mut list = binn_list();
    let value: i32 = 123;
    let bytes = value.to_ne_bytes();

    assert!(binn_list_add(
        &mut list.as_mut().unwrap(),
        BINN_INT32,
        Some(&bytes.to_vec()),
        0
    ));

    let mut read_value: i32 = 0;
    assert!(binn_list_get_int32(
        list.as_ref().map(|b| &b.pbuf),
        1,
        &mut read_value
    ));
    assert_eq!(read_value, value);

    binn_free(list);
}

#[test]
#[timeout(60000)]
pub fn test_add_strings_and_blobs_no_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    let str_list = "test list".to_string();
    let str_map = "test map".to_string();
    let str_obj = "test object".to_string();

    let blobsize = 150;
    let mut pblob = vec![55; blobsize as usize];

    list.disable_int_compression = true;
    map.disable_int_compression = true;
    obj.disable_int_compression = true;

    assert!(binn_list_add_str(&mut list, str_list.clone()));
    assert!(binn_map_set_str(&mut map, 1004, str_map.clone()));
    assert!(binn_object_set_str(&mut obj, "text", str_obj.clone()));

    assert!(binn_list_add_blob(&mut list, Some(&pblob), blobsize));
    assert!(binn_map_set_blob(&mut map, 1005, Some(&pblob), blobsize));
    assert!(binn_object_set_blob(
        &mut obj,
        "blob",
        pblob.clone(),
        blobsize
    ));

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}
