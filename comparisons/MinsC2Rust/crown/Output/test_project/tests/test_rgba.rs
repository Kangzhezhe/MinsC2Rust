use test_project::rgba::{
    h, rgba_from_hex3_string, rgba_from_hex6_string, rgba_from_hex_string, rgba_from_name_string,
    rgba_from_rgb, rgba_from_rgb_string, rgba_from_rgba, rgba_from_rgba_string, rgba_from_string,
    rgba_new, rgba_to_string, NamedColor, Rgba, NAMED_COLORS,
};

use ntest::timeout;
#[test]
#[timeout(60000)]
pub fn test_to_string() {
    let mut buf = String::new();
    let color = rgba_new(0xffcc00ff);
    rgba_to_string(color, &mut buf, 256);
    assert_eq!("#ffcc00", buf);

    let color = rgba_new(0xffcc0050);
    rgba_to_string(color, &mut buf, 256);
    assert_eq!("rgba(255, 204, 0, 0.31)", buf);
}

#[test]
#[timeout(60000)]
pub fn test_rgba() {
    let mut ok: i16 = 0;
    let mut val = rgba_from_string("rgba(255, 30   , 0, .5)", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xff1e007f, val);

    val = rgba_from_string("rgba(0,0,0, 1)", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0x000000ff, val);
}

#[test]
#[timeout(60000)]
pub fn test_hex() {
    let mut ok: i16 = 0;
    let mut val = rgba_from_string("#ff1e00", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xff1e00ff, val);

    val = rgba_from_string("#ffffff", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xffffffff, val);

    val = rgba_from_string("#ffcc00", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xffcc00ff, val);

    val = rgba_from_string("#fco", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xffcc00ff, val);
}

#[test]
#[timeout(60000)]
pub fn test_rgb() {
    let mut ok: i16 = 0;
    let val = rgba_from_string("rgb(255, 30   , 0)", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0xff1e00ff, val);

    let val = rgba_from_string("rgb(0,0,0)", &mut ok);
    assert_eq!(ok, 1);
    assert_eq!(0x000000ff, val);
}
