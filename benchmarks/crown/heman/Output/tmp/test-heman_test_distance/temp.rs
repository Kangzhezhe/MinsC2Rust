pub const SIZE: i32 = 512;
pub type HEMAN_FLOAT = f64;

pub struct HemanImage {
    pub width: i32,
    pub height: i32,
    pub channels: i32,
    pub data: Vec<HEMAN_FLOAT>,
}

pub const COUNT_CP_COLORS: usize = 7;
pub const CP_LOCATIONS: [i32; COUNT_CP_COLORS] = [0, 126, 127, 128, 160, 200, 255];
pub const CP_COLORS: [u32; COUNT_CP_COLORS] = [
    0x001070, 0x2C5A7C, 0xE0F0A0, 0x5D943C, 0x606011, 0xFFFFFF, 0xFFFFFF,
];
pub const OUTFOLDER: &str = "./";











































pub fn draw_circle() -> HemanImage {
    let mut img = heman_image_create(SIZE, SIZE, 1);
    let inv = 1.0f32 / SIZE as f32;

    for y in 0..SIZE {
        let v = y as f32 * inv;
        let dv2 = (v - 0.5f32) * (v - 0.5f32);
        let dst_start = (y * SIZE) as usize;
        let dst_end = dst_start + SIZE as usize;
        let dst = &mut img.data[dst_start..dst_end];

        for x in 0..SIZE {
            let u = x as f32 * inv;
            let du2 = (u - 0.5f32) * (u - 0.5f32);
            dst[x as usize] = if du2 + dv2 < 0.0625f32 { 1.0 } else { 0.0 };
        }
    }

    img
}



pub fn test_distance() {
    let img = draw_circle();
    let begin = std::time::Instant::now();
    let sdf = heman_distance_create_sdf(&img);
    let duration = begin.elapsed().as_secs_f64();
    println!("Distance field generated in {:.3} seconds.", duration);
    hut_write_image(OUTFOLDER.to_string() + "distance.png", &sdf, -1, 1);
}

fn main(){}