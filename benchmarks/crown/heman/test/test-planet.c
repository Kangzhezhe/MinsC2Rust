#include <heman.h>
#include <assert.h>
#include "hut.h"

#define COUNT(a) (sizeof(a) / sizeof(a[0]))
#define OUTFOLDER "build/"
#define HEIGHT 128

static int CP_LOCATIONS[] = {
    000,  // Dark Blue
    126,  // Light Blue
    127,  // Yellow
    150,  // Dark Green
    170,  // Brown
    200,  // Brown
    240,  // White
    255,  // White
};

static heman_color CP_COLORS[] = {
    0x001070,  // Dark Blue
    0x2C5A7C,  // Light Blue
    0xE0F0A0,  // Yellow
    0x5D943C,  // Dark Green
    0x606011,  // Brown
    0x606011,  // Brown
    0xFFFFFF,  // White
    0xFFFFFF,  // White
};

static float LIGHTPOS[] = {-0.5f, 0.5f, 1.0f};

heman_image* make_planet(int seed, heman_image* grad)
{
    heman_image* hmap =
        heman_generate_planet_heightmap(HEIGHT * 2, HEIGHT, seed);
    heman_image* albedo = heman_color_apply_gradient(hmap, -0.5, 0.5, grad);
    heman_image* planet =
        heman_lighting_apply(hmap, albedo, 1, 1, 0.75, LIGHTPOS);
    heman_image_destroy(hmap);
    heman_image_destroy(albedo);
    return planet;
}

heman_image* make_island(int seed, heman_image* grad)
{
    heman_image* hmap = heman_generate_island_heightmap(HEIGHT, HEIGHT, seed);
    heman_image* albedo = heman_color_apply_gradient(hmap, -0.5, 0.5, grad);
    heman_image* island =
        heman_lighting_apply(hmap, albedo, 1, 1, 0.75, LIGHTPOS);
    heman_image_destroy(hmap);
    heman_image_destroy(albedo);
    return island;
}

/*************************************************************************************/

void test_gradient_creation() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    assert(grad != NULL);
    heman_image_destroy(grad);
}

void test_planet_heightmap_generation() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* planet = make_planet(1000, grad);
    assert(planet != NULL);
    
    heman_image_destroy(planet);
    heman_image_destroy(grad);
}

void test_island_heightmap_generation() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* island = make_island(1000, grad);
    assert(island != NULL);
    
    heman_image_destroy(island);
    heman_image_destroy(grad);
}

void test_multiple_planet_generation() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* planet1 = make_planet(1000, grad);
    heman_image* planet2 = make_planet(1001, grad);
    
    assert(planet1 != NULL);
    assert(planet2 != NULL);
    
    heman_image_destroy(planet1);
    heman_image_destroy(planet2);
    heman_image_destroy(grad);
}

void test_multiple_island_generation() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* island1 = make_island(1000, grad);
    heman_image* island2 = make_island(1001, grad);
    heman_image* island3 = make_island(1002, grad);
    heman_image* island4 = make_island(1003, grad);
    
    assert(island1 != NULL);
    assert(island2 != NULL);
    assert(island3 != NULL);
    assert(island4 != NULL);
    
    heman_image_destroy(island1);
    heman_image_destroy(island2);
    heman_image_destroy(island3);
    heman_image_destroy(island4);
    heman_image_destroy(grad);
}

void test_vertical_stitching() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* tiles[2];
    tiles[0] = make_planet(1000, grad);
    tiles[1] = make_planet(1001, grad);
    
    heman_image* planets = heman_ops_stitch_vertical(tiles, 2);
    assert(planets != NULL);
    
    heman_image_destroy(tiles[0]);
    heman_image_destroy(tiles[1]);
    heman_image_destroy(planets);
    heman_image_destroy(grad);
}

void test_horizontal_stitching() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* tiles[2];
    tiles[0] = make_island(1000, grad);
    tiles[1] = make_island(1001, grad);
    
    heman_image* stitched = heman_ops_stitch_horizontal(tiles, 2);
    assert(stitched != NULL);
    
    heman_image_destroy(tiles[0]);
    heman_image_destroy(tiles[1]);
    heman_image_destroy(stitched);
    heman_image_destroy(grad);
}

void test_complex_island_stitching() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);
    
    heman_image* tiles[4];
    tiles[0] = make_island(1000, grad);
    tiles[1] = make_island(1001, grad);
    tiles[2] = make_island(1002, grad);
    tiles[3] = make_island(1003, grad);
    
    heman_image* rows[2];
    rows[0] = heman_ops_stitch_horizontal(tiles, 2);
    rows[1] = heman_ops_stitch_horizontal(tiles + 2, 2);
    assert(rows[0] != NULL);
    assert(rows[1] != NULL);
    
    heman_image* islands = heman_ops_stitch_vertical(rows, 2);
    assert(islands != NULL);
    
    heman_image_destroy(tiles[0]);
    heman_image_destroy(tiles[1]);
    heman_image_destroy(tiles[2]);
    heman_image_destroy(tiles[3]);
    heman_image_destroy(rows[0]);
    heman_image_destroy(rows[1]);
    heman_image_destroy(islands);
    heman_image_destroy(grad);
}

void test_final_composition() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);

    // Create planets section
    heman_image* planet_tiles[2];
    planet_tiles[0] = make_planet(1000, grad);
    planet_tiles[1] = make_planet(1001, grad);
    heman_image* planets = heman_ops_stitch_vertical(planet_tiles, 2);
    heman_image_destroy(planet_tiles[0]);
    heman_image_destroy(planet_tiles[1]);

    // Create islands section
    heman_image* island_tiles[4];
    island_tiles[0] = make_island(1000, grad);
    island_tiles[1] = make_island(1001, grad);
    island_tiles[2] = make_island(1002, grad);
    island_tiles[3] = make_island(1003, grad);
    heman_image* rows[2];
    rows[0] = heman_ops_stitch_horizontal(island_tiles, 2);
    rows[1] = heman_ops_stitch_horizontal(island_tiles + 2, 2);
    heman_image* islands = heman_ops_stitch_vertical(rows, 2);
    heman_image_destroy(island_tiles[0]);
    heman_image_destroy(island_tiles[1]);
    heman_image_destroy(island_tiles[2]);
    heman_image_destroy(island_tiles[3]);
    heman_image_destroy(rows[0]);
    heman_image_destroy(rows[1]);

    // Final composition
    heman_image* final_tiles[2];
    final_tiles[0] = planets;
    final_tiles[1] = islands;
    heman_image* final = heman_ops_stitch_horizontal(final_tiles, 2);
    assert(final != NULL);
    
    heman_image_destroy(planets);
    heman_image_destroy(islands);
    heman_image_destroy(final);
    heman_image_destroy(grad);
}

void test_image_output() {
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(CP_COLORS), CP_LOCATIONS, CP_COLORS);

    // Create a simple composition for output test
    heman_image* planet = make_planet(1000, grad);
    hut_write_image(OUTFOLDER "test_planet.png", planet, 0, 1);
    
    heman_image_destroy(planet);
    heman_image_destroy(grad);
}

/*************************************************************************************/

int main(int argc, char** argv)
{
    puts("\nStarting the heman planet unit/regression tests...\n");
    
    test_gradient_creation();
    
    test_planet_heightmap_generation();
    
    test_island_heightmap_generation();
    
    test_multiple_planet_generation();
    
    test_multiple_island_generation();
    
    test_vertical_stitching();
    
    test_horizontal_stitching();
    
    test_complex_island_stitching();
    
    test_final_composition();
    
    test_image_output();
    
    puts("\nAll heman planet tests pass! :)\n");
    return 0;
}