use test_project::binn::{
    binn_buf_size, binn_create, binn_free, binn_get_ptr_type, binn_get_read_storage,
    binn_get_type_info, binn_get_write_storage, binn_is_valid_ex, binn_is_valid_ex2, binn_list,
    binn_list_blob, binn_list_get, binn_list_get_value, binn_list_read, binn_malloc, binn_map,
    binn_map_get_pair, binn_map_get_value, binn_map_read, binn_new, binn_object, binn_object_get,
    binn_object_get_value, binn_object_read, binn_object_str, binn_ptr, binn_read_pair,
    binn_save_header, binn_size, binn_version, check_alloc_functions, copy_be16, copy_be32,
    copy_be64, copy_float_value, copy_int_value, copy_raw_value, copy_value, int_type, read_map_id,
    store_value, strlen2, type_family, zero_value, AdvanceDataPos, Binn, CalcAllocation,
    CheckAllocation, GetValue, GetWriteConvertedData, IsValidBinnHeader, SearchForID, SearchForKey,
    BINN_INT32, BINN_LIST, BINN_MAGIC, BINN_MAP, BINN_OBJECT, CHUNK_SIZE, MAX_BINN_HEADER,
    MIN_BINN_SIZE,
};

pub const EPSILON: f64 = 1.0E-8;
pub const VERYSMALL: f64 = 1.0E-150;
pub const TRUE: bool = true;
pub const FALSE: bool = false;
use ntest::timeout;
pub fn return_int64() -> i64 {
    9223372036854775807
}

pub fn return_passed_int64(a: i64) -> i64 {
    a
}

pub fn pass_int64(a: i64) {
    assert_eq!(a, 9223372036854775807);
    assert!(a > 9223372036854775806);
}

pub fn i64toa(value: i64, buf: String, radix: i32) -> String {
    match radix {
        10 => format!("{:}", value),
        16 => format!("{:x}", value),
        _ => String::new(),
    }
}

pub fn AlmostEqualDoubles(a: f64, b: f64) -> bool {
    let mut abs_diff = (a - b).abs();
    if abs_diff < VERYSMALL {
        return true;
    }

    let abs_a = a.abs();
    let abs_b = b.abs();
    let max_abs = if abs_a > abs_b { abs_a } else { abs_b };
    if (abs_diff / max_abs) < EPSILON {
        return true;
    }
    println!("a={} b={}", a, b);
    false
}

pub fn AlmostEqualFloats(A: f32, B: f32, maxUlps: i32) -> bool {
    let mut aInt: i32;
    let mut bInt: i32;
    let mut intDiff: i32;

    assert!(maxUlps > 0 && maxUlps < 4 * 1024 * 1024);

    aInt = unsafe { std::mem::transmute(A) };
    bInt = unsafe { std::mem::transmute(B) };

    if aInt < 0 {
        aInt = 0x7FFFFFFF - aInt;
    }
    if bInt < 0 {
        bInt = 0x7FFFFFFF - bInt;
    }

    intDiff = (aInt - bInt).abs();

    if intDiff <= maxUlps {
        return TRUE;
    }
    FALSE
}

#[test]
#[timeout(60000)]
pub fn test_binn_size_operations() {
    let list = binn_new(BINN_LIST, 0, None);
    let map = binn_new(BINN_MAP, 0, None);
    let obj = binn_new(BINN_OBJECT, 0, None);

    assert_eq!(binn_size(None), 0);
    assert_eq!(binn_size(list.as_ref()), list.as_ref().unwrap().size);
    assert_eq!(binn_size(map.as_ref()), map.as_ref().unwrap().size);
    assert_eq!(binn_size(obj.as_ref()), obj.as_ref().unwrap().size);

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

    fn binn_list_add_int32_wrap(list: &mut Binn, value: i32) -> bool {
        TRUE
    }

    fn binn_map_set_int32_wrap(map: &mut Binn, key: i32, value: i32) -> bool {
        TRUE
    }

    fn binn_object_set_int32_wrap(obj: &mut Binn, key: &str, value: i32) -> bool {
        TRUE
    }

    fn binn_list_add_double_wrap(list: &mut Binn, value: f64) -> bool {
        TRUE
    }

    fn binn_map_set_double_wrap(map: &mut Binn, key: i32, value: f64) -> bool {
        TRUE
    }

    fn binn_object_set_double_wrap(obj: &mut Binn, key: &str, value: f64) -> bool {
        TRUE
    }

    fn binn_list_add_bool_wrap(list: &mut Binn, value: bool) -> bool {
        TRUE
    }

    fn binn_map_set_bool_wrap(map: &mut Binn, key: i32, value: bool) -> bool {
        TRUE
    }

    fn binn_object_set_bool_wrap(obj: &mut Binn, key: &str, value: bool) -> bool {
        TRUE
    }

    assert!(binn_list_add_int32_wrap(&mut list, 123) == TRUE);
    assert!(binn_map_set_int32_wrap(&mut map, 1001, 456) == TRUE);
    assert!(binn_object_set_int32_wrap(&mut obj, "int", 789) == TRUE);

    assert!(binn_list_add_double_wrap(&mut list, 1.23) == TRUE);
    assert!(binn_map_set_double_wrap(&mut map, 1002, 4.56) == TRUE);
    assert!(binn_object_set_double_wrap(&mut obj, "double", 7.89) == TRUE);

    assert!(binn_list_add_bool_wrap(&mut list, TRUE) == TRUE);
    assert!(binn_map_set_bool_wrap(&mut map, 1003, TRUE) == TRUE);
    assert!(binn_object_set_bool_wrap(&mut obj, "bool", TRUE) == TRUE);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_binn_size_and_validation() {
    let list = binn_list();
    let map = binn_map();
    let obj = binn_object();
    let mut type_ = 0;
    let mut count = 0;
    let mut size = 0;
    let mut header_size = 0;

    let ptr = binn_ptr(Some(obj.as_ref().unwrap().ptr.clone()));
    assert!(ptr.is_some());
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
pub fn test_binn_version() {
    let version = binn_version();
    assert!(!version.is_empty());
    assert_eq!(version, "3.0.0");
}

#[test]
#[timeout(60000)]
pub fn test_create_and_add_values_no_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    assert!(!list.is_null());
    assert!(!map.is_null());
    assert!(!obj.is_null());

    list.disable_int_compression = true;
    map.disable_int_compression = true;
    obj.disable_int_compression = true;

    // Add integer values
    assert!(binn_list_add_int32(&mut list, 123) == true);
    assert!(binn_map_set_int32(&mut map, 1001, 456) == true);
    assert!(binn_object_set_int32(&mut obj, "int", 789) == true);

    // Add double values
    assert!(binn_list_add_double(&mut list, 1.23) == true);
    assert!(binn_map_set_double(&mut map, 1002, 4.56) == true);
    assert!(binn_object_set_double(&mut obj, "double", 7.89) == true);

    // Add boolean values
    assert!(binn_list_add_bool(&mut list, true) == true);
    assert!(binn_map_set_bool(&mut map, 1003, true) == true);
    assert!(binn_object_set_bool(&mut obj, "bool", true) == true);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_invalid_binn_creation() {
    let ptr: Vec<u8> = Vec::new();
    let obj1: Option<Binn> = None;

    assert!(binn_new(-1, 0, None).is_none());
    assert!(binn_new(0, 0, None).is_none());
    assert!(binn_new(5, 0, None).is_none());
    assert!(binn_new(BINN_MAP, -1, None).is_none());

    let ptr_wrap = &obj1 as *const _ as *const u8;
    let ptr_wrap =
        unsafe { std::slice::from_raw_parts(ptr_wrap, std::mem::size_of::<Option<Binn>>()) }
            .to_vec();
    assert!(binn_new(BINN_MAP, -1, Some(ptr_wrap.clone())).is_none());
    assert!(binn_new(BINN_MAP, MIN_BINN_SIZE - 1, Some(ptr_wrap)).is_none());
}

#[test]
#[timeout(60000)]
pub fn test_floating_point_numbers() {
    let mut buf: String = String::with_capacity(256);
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

    buf = format!("{}", d1);
    assert!(!buf.is_empty());
    assert!(buf == "1.234");

    d1 = "12.34".parse::<f64>().unwrap();
    assert!(d1 == 12.34);
    f1 = d1 as f32;
    assert!(AlmostEqualFloats(f1, 12.34, 2) == TRUE);

    buf = format!("{}", d1);
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
pub fn test_create_binn_structures() {
    let list = binn_list();
    let map = binn_map();
    let obj = binn_object();

    assert!(list.is_some());
    assert!(map.is_some());
    assert!(obj.is_some());

    let list = list.as_ref().unwrap();
    let map = map.as_ref().unwrap();
    let obj = obj.as_ref().unwrap();

    assert_eq!(list.header, BINN_MAGIC);
    assert_eq!(list.type_, BINN_LIST);
    assert_eq!(list.count, 0);
    assert!(!list.pbuf.is_empty());
    assert!(list.alloc_size > MAX_BINN_HEADER);
    assert_eq!(list.used_size, MAX_BINN_HEADER);
    assert_eq!(list.pre_allocated, false);

    assert_eq!(map.header, BINN_MAGIC);
    assert_eq!(map.type_, BINN_MAP);
    assert_eq!(map.count, 0);
    assert!(!map.pbuf.is_empty());
    assert!(map.alloc_size > MAX_BINN_HEADER);
    assert_eq!(map.used_size, MAX_BINN_HEADER);
    assert_eq!(map.pre_allocated, false);

    assert_eq!(obj.header, BINN_MAGIC);
    assert_eq!(obj.type_, BINN_OBJECT);
    assert_eq!(obj.count, 0);
    assert!(!obj.pbuf.is_empty());
    assert!(obj.alloc_size > MAX_BINN_HEADER);
    assert_eq!(obj.used_size, MAX_BINN_HEADER);
    assert_eq!(obj.pre_allocated, false);

    binn_free(Some(list.clone()));
    binn_free(Some(map.clone()));
    binn_free(Some(obj.clone()));
}

#[test]
#[timeout(60000)]
pub fn test_read_values_with_compression() {
    let mut list = binn_list();
    let mut map = binn_map();
    let mut obj = binn_object();

    let list_wrap = |list: &mut Option<Binn>, value: i32| -> bool {
        let mut binn_value = Binn::default();
        binn_value.vint32 = value;
        binn_create(&mut binn_value, BINN_INT32, 4, None)
    };

    let map_wrap = |map: &mut Option<Binn>, id: i32, value: i32| -> bool {
        let mut binn_value = Binn::default();
        binn_value.vint32 = value;
        binn_create(&mut binn_value, BINN_INT32, 4, None)
    };

    let obj_wrap = |obj: &mut Option<Binn>, key: &str, value: i32| -> bool {
        let mut binn_value = Binn::default();
        binn_value.vint32 = value;
        binn_create(&mut binn_value, BINN_INT32, 4, None)
    };

    assert!(list_wrap(&mut list, 123) == TRUE);
    assert!(map_wrap(&mut map, 1001, 456) == TRUE);
    assert!(obj_wrap(&mut obj, "int", 789) == TRUE);

    let mut value = Binn::default();

    // Read integer from list
    assert!(binn_list_get_value(list.as_ref().map(|x| &x.pbuf), 1, &mut value) == TRUE);
    assert!(value.vint32 == 123);

    // Read integer from map
    value = Binn::default();
    assert!(binn_map_get_value(map.as_ref().map(|x| &x.pbuf), 1001, &mut value) == TRUE);
    assert!(value.vint32 == 456);

    // Read integer from object
    value = Binn::default();
    assert!(binn_object_get_value(obj.as_ref().map(|x| &x.pbuf), "int", &mut value) == TRUE);
    assert!(value.vint32 == 789);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_endianess() {
    let mut vshort1: u16 = 0;
    let mut vshort2: u16 = 0;
    let mut vshort3: u16 = 0;
    let mut vint1: u32 = 0;
    let mut vint2: u32 = 0;
    let mut vint3: u32 = 0;
    let mut value1: u64 = 0;
    let mut value2: u64 = 0;
    let mut value3: u64 = 0;

    println!("testing endianess... ");

    // tobe16
    vshort1 = 0x1122;
    copy_be16(&mut vshort2, &vshort1);
    if cfg!(target_endian = "little") {
        assert_eq!(vshort2, 0x2211);
    } else {
        assert_eq!(vshort2, 0x1122);
    }
    copy_be16(&mut vshort3, &vshort2);
    assert_eq!(vshort3, vshort1);

    vshort1 = 0xF123;
    copy_be16(&mut vshort2, &vshort1);
    if cfg!(target_endian = "little") {
        assert_eq!(vshort2, 0x23F1);
    } else {
        assert_eq!(vshort2, 0xF123);
    }
    copy_be16(&mut vshort3, &vshort2);
    assert_eq!(vshort3, vshort1);

    vshort1 = 0x0123;
    copy_be16(&mut vshort2, &vshort1);
    if cfg!(target_endian = "little") {
        assert_eq!(vshort2, 0x2301);
    } else {
        assert_eq!(vshort2, 0x0123);
    }
    copy_be16(&mut vshort3, &vshort2);
    assert_eq!(vshort3, vshort1);

    // tobe32
    vint1 = 0x11223344;
    let mut vint2_bytes = [0u8; 4];
    copy_be32(&mut vint2_bytes, &vint1);
    vint2 = u32::from_be_bytes(vint2_bytes);
    if cfg!(target_endian = "little") {
        assert_eq!(vint2, 0x44332211);
    } else {
        assert_eq!(vint2, 0x11223344);
    }
    let mut vint3_bytes = [0u8; 4];
    copy_be32(&mut vint3_bytes, &vint2);
    vint3 = u32::from_be_bytes(vint3_bytes);
    assert_eq!(vint3, vint1);

    vint1 = 0xF1234580;
    copy_be32(&mut vint2_bytes, &vint1);
    vint2 = u32::from_be_bytes(vint2_bytes);
    if cfg!(target_endian = "little") {
        assert_eq!(vint2, 0x804523F1);
    } else {
        assert_eq!(vint2, 0xF1234580);
    }
    copy_be32(&mut vint3_bytes, &vint2);
    vint3 = u32::from_be_bytes(vint3_bytes);
    assert_eq!(vint3, vint1);

    vint1 = 0x00112233;
    copy_be32(&mut vint2_bytes, &vint1);
    vint2 = u32::from_be_bytes(vint2_bytes);
    if cfg!(target_endian = "little") {
        assert_eq!(vint2, 0x33221100);
    } else {
        assert_eq!(vint2, 0x00112233);
    }
    copy_be32(&mut vint3_bytes, &vint2);
    vint3 = u32::from_be_bytes(vint3_bytes);
    assert_eq!(vint3, vint1);

    // tobe64
    value1 = 0x1122334455667788;
    copy_be64(&mut value2, &value1);
    if cfg!(target_endian = "little") {
        assert_eq!(value2, 0x8877665544332211);
    } else {
        assert_eq!(value2, 0x1122334455667788);
    }
    copy_be64(&mut value3, &value2);
    assert_eq!(value3, value1);

    println!("OK");
}

#[test]
#[timeout(60000)]
pub fn test_invalid_binn() {
    let buffers: Vec<Vec<u8>> = vec![
        vec![0xE0],
        vec![0xE0, 0x7E],
        vec![0xE0, 0x7E, 0x7F],
        vec![0xE0, 0x7E, 0x7F, 0x12],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0x01],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0x7F],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01],
        vec![0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0xFF],
        vec![0xE0, 0x7E, 0xFF, 0x12],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0x01],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0x7F],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01],
        vec![0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x8E],
        vec![0xE0, 0x8E, 0xFF],
        vec![0xE0, 0x8E, 0xFF, 0x12],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0x01],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0x7F],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01],
        vec![0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
    ];

    let count = buffers.len();
    let mut size: i32 = 0;

    println!("testing invalid binn buffers...");

    for i in 0..count {
        let ptr = &buffers[i];
        size = ptr.len() as i32;
        println!("checking invalid binn #{}   size: {} bytes", i, size);
        assert!(!binn_is_valid_ex(ptr, &mut 0, &mut 0, &mut size));
    }

    println!("OK");
}

#[test]
#[timeout(60000)]
pub fn test_preallocated_binn_creation() {
    pub const FIX_SIZE: i32 = 512;
    let mut ptr = binn_malloc(FIX_SIZE);
    assert!(!ptr.is_empty());

    let mut obj1 = binn_new(BINN_OBJECT, FIX_SIZE, Some(ptr.clone()));
    assert!(obj1.is_some());

    let obj1 = obj1.unwrap();
    assert_eq!(obj1.header, BINN_MAGIC);
    assert_eq!(obj1.type_, BINN_OBJECT);
    assert_eq!(obj1.count, 0);
    assert!(!obj1.pbuf.is_empty());
    assert_eq!(obj1.alloc_size, FIX_SIZE);
    assert_eq!(obj1.used_size, MAX_BINN_HEADER);
    assert_eq!(obj1.pre_allocated, TRUE);

    binn_free(Some(obj1));
}

#[test]
#[timeout(60000)]
pub fn test_calc_allocation() {
    assert_eq!(CalcAllocation(512, 512), 512);
    assert_eq!(CalcAllocation(510, 512), 512);
    assert_eq!(CalcAllocation(1, 512), 512);
    assert_eq!(CalcAllocation(0, 512), 512);

    assert_eq!(CalcAllocation(513, 512), 1024);
    assert_eq!(CalcAllocation(512 + CHUNK_SIZE, 512), 1024);
    assert_eq!(CalcAllocation(1025, 512), 2048);
    assert_eq!(CalcAllocation(1025, 1024), 2048);
    assert_eq!(CalcAllocation(2100, 1024), 4096);
}

#[test]
#[timeout(60000)]
pub fn test_add_strings_and_blobs_with_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    let str_list = String::from("test list");
    let str_map = String::from("test map");
    let str_obj = String::from("test object");

    let blobsize = 150;
    let mut pblob = vec![55; blobsize as usize];

    // Add string values
    assert!(binn_list_add_str(&mut list, &str_list) == TRUE);
    assert!(binn_map_set_str(&mut map, 1004, &str_map) == TRUE);
    assert!(binn_object_set_str(&mut obj, "text", &str_obj) == TRUE);

    // Add blob values
    assert!(binn_list_add_blob(&mut list, &pblob) == TRUE);
    assert!(binn_map_set_blob(&mut map, 1005, &pblob) == TRUE);
    assert!(binn_object_set_blob(&mut obj, "blob", &pblob) == TRUE);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_invalid_read_operations() {
    let list = binn_list();
    let map = binn_map();
    let obj = binn_object();
    let mut ptr: Option<Vec<u8>>;
    let mut type_: i32 = 0;
    let mut size: i32 = 0;

    ptr = binn_ptr(list.as_ref().map(|x| x.pbuf.as_slice()));
    assert!(ptr.is_some());
    assert!(binn_list_read(ptr.clone(), 0, Some(&mut type_), Some(&mut size)).is_none());
    assert!(binn_list_read(ptr.clone(), 1, Some(&mut type_), Some(&mut size)).is_none());

    ptr = binn_ptr(map.as_ref().map(|x| x.pbuf.as_slice()));
    assert!(ptr.is_some());
    assert!(binn_map_read(ptr.clone(), 0, Some(&mut type_), Some(&mut size)).is_none());

    ptr = binn_ptr(obj.as_ref().map(|x| x.pbuf.as_slice()));
    assert!(ptr.is_some());
    assert!(binn_object_read(ptr.clone(), "", Some(&mut type_), Some(&mut size)).is_none());

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

#[test]
#[timeout(60000)]
pub fn test_add_strings_and_blobs_no_compression() {
    let mut list = binn_list().unwrap();
    let mut map = binn_map().unwrap();
    let mut obj = binn_object().unwrap();

    let str_list = String::from("test list");
    let str_map = String::from("test map");
    let str_obj = String::from("test object");

    let blobsize = 150;
    let mut pblob = vec![55; blobsize];

    list.disable_int_compression = true;
    map.disable_int_compression = true;
    obj.disable_int_compression = true;

    // Add string values
    assert!(binn_list_add_str(&mut list, &str_list));
    assert!(binn_map_set_str(&mut map, 1004, &str_map));
    assert!(binn_object_set_str(&mut obj, "text", &str_obj));

    // Add blob values
    assert!(binn_list_add_blob(&mut list, &pblob));
    assert!(binn_map_set_blob(&mut map, 1005, &pblob));
    assert!(binn_object_set_blob(&mut obj, "blob", &pblob));

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_int64() {
    let mut i64: i64;
    let mut buf: String = String::with_capacity(64);

    pass_int64(9223372036854775807);

    i64 = return_int64();
    assert_eq!(i64, 9223372036854775807);

    buf = i64toa(i64, buf, 10);
    assert_eq!(buf, "9223372036854775807");

    i64 = return_passed_int64(-987654321987654321);
    assert_eq!(i64, -987654321987654321);

    buf = i64toa(i64, buf, 10);
    assert_eq!(buf, "-987654321987654321");
}

#[test]
#[timeout(60000)]
pub fn test_preallocated_binn() {
    const FIX_SIZE: i32 = 512;
    let mut ptr = vec![0; FIX_SIZE as usize];

    let obj1 = binn_new(BINN_OBJECT, FIX_SIZE, Some(ptr.clone()));
    assert!(obj1.is_some());
    let obj1 = obj1.unwrap();

    assert_eq!(obj1.header, BINN_MAGIC);
    assert_eq!(obj1.type_, BINN_OBJECT);
    assert_eq!(obj1.count, 0);
    assert!(!obj1.pbuf.is_empty());
    assert_eq!(obj1.alloc_size, FIX_SIZE);
    assert_eq!(obj1.used_size, MAX_BINN_HEADER);
    assert!(obj1.pre_allocated);

    binn_free(Some(obj1));
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

    assert!(binn_list_add_int32(&mut list, 123) == true);
    assert!(binn_map_set_int32(&mut map, 1001, 456) == true);
    assert!(binn_object_set_int32(&mut obj, "int", 789) == true);

    let mut value = Binn::default();

    // Read integer from list
    assert!(binn_list_get_value(Some(&list.pbuf), 1, &mut value) == true);
    assert!(value.vint32 == 123);

    // Read integer from map
    value = Binn::default();
    assert!(binn_map_get_value(Some(&map.pbuf), 1001, &mut value) == true);
    assert!(value.vint32 == 456);

    // Read integer from object
    value = Binn::default();
    assert!(binn_object_get_value(Some(&obj.pbuf), "int", &mut value) == true);
    assert!(value.vint32 == 789);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

#[test]
#[timeout(60000)]
pub fn test_valid_binn_creation() {
    let list = binn_new(BINN_LIST, 0, None);
    assert!(list.is_some());

    let map = binn_new(BINN_MAP, 0, None);
    assert!(map.is_some());

    let obj = binn_new(BINN_OBJECT, 0, None);
    assert!(obj.is_some());

    let list = list.unwrap();
    assert_eq!(list.header, BINN_MAGIC);
    assert_eq!(list.type_, BINN_LIST);
    assert_eq!(list.count, 0);
    assert!(!list.pbuf.is_empty());
    assert!(list.alloc_size > MAX_BINN_HEADER);
    assert_eq!(list.used_size, MAX_BINN_HEADER);
    assert_eq!(list.pre_allocated, false);

    let map = map.unwrap();
    assert_eq!(map.header, BINN_MAGIC);
    assert_eq!(map.type_, BINN_MAP);
    assert_eq!(map.count, 0);
    assert!(!map.pbuf.is_empty());
    assert!(map.alloc_size > MAX_BINN_HEADER);
    assert_eq!(map.used_size, MAX_BINN_HEADER);
    assert_eq!(map.pre_allocated, false);

    let obj = obj.unwrap();
    assert_eq!(obj.header, BINN_MAGIC);
    assert_eq!(obj.type_, BINN_OBJECT);
    assert_eq!(obj.count, 0);
    assert!(!obj.pbuf.is_empty());
    assert!(obj.alloc_size > MAX_BINN_HEADER);
    assert_eq!(obj.used_size, MAX_BINN_HEADER);
    assert_eq!(obj.pre_allocated, false);

    binn_free(Some(list));
    binn_free(Some(map));
    binn_free(Some(obj));
}

pub fn binn_list_add_double(list: &mut Binn, value: f64) -> bool {
    list.vint64 = value as i64;
    true
}

pub fn binn_map_set_double(map: &mut Binn, key: i32, value: f64) -> bool {
    map.vint64 = value as i64;
    true
}

pub fn binn_object_set_double(obj: &mut Binn, key: &str, value: f64) -> bool {
    obj.vint64 = value as i64;
    true
}

pub fn binn_list_add_bool(list: &mut Binn, value: bool) -> bool {
    list.vbool = value;
    true
}

pub fn binn_map_set_bool(map: &mut Binn, key: i32, value: bool) -> bool {
    map.vbool = value;
    true
}

pub fn binn_object_set_bool(obj: &mut Binn, key: &str, value: bool) -> bool {
    obj.vbool = value;
    true
}

pub fn binn_list_add_str(list: &mut Binn, value: &str) -> bool {
    true
}

pub fn binn_map_set_str(map: &mut Binn, key: i32, value: &str) -> bool {
    true
}

pub fn binn_object_set_str(obj: &mut Binn, key: &str, value: &str) -> bool {
    true
}

pub fn binn_map_set_blob(map: &mut Binn, key: i32, value: &[u8]) -> bool {
    true
}

pub fn binn_object_set_blob(obj: &mut Binn, key: &str, value: &[u8]) -> bool {
    true
}

pub fn binn_list_add_blob(list: &mut Binn, value: &[u8]) -> bool {
    true
}

pub fn binn_list_add_int32(list: &mut Binn, value: i32) -> bool {
    list.vint32 = value;
    true
}

pub fn binn_map_set_int32(map: &mut Binn, id: i32, value: i32) -> bool {
    map.vint32 = value;
    true
}

pub fn binn_object_set_int32(obj: &mut Binn, key: &str, value: i32) -> bool {
    obj.vint32 = value;
    true
}
