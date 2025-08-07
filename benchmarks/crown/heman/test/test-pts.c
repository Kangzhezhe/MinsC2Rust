#include <heman.h>
#include <omp.h>
#include <time.h>
#include <assert.h>
#include <kazmath/vec2.h>
#include <kazmath/vec3.h>
#include "hut.h"

static const int SIZE = 512;

#define COUNT(a) (sizeof(a) / sizeof(a[0]))
#define OUTFOLDER "build/"

/*************************************************************************************/

void test_openmp_threads() {
    int max_threads = omp_get_max_threads();
    assert(max_threads > 0);
    printf("%d threads available.\n", max_threads);
}

void test_points_creation() {
    const int npts = 5;
    heman_points* pts = heman_image_create(npts, 1, 3);
    assert(pts != NULL);
    
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    assert(coords != NULL);
    
    heman_image_destroy(pts);
}

void test_points_coordinate_assignment() {
    const int npts = 5;
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    // Verify coordinates were set correctly
    assert(coords[0].x == 0.3f && coords[0].y == 0.4f && coords[0].z == 0.1f);
    assert(coords[4].x == 0.5f && coords[4].y == 0.5f && coords[4].z == 0.2f);
    
    heman_image_destroy(pts);
}

void test_contour_image_creation() {
    const int res = 4096;
    heman_image* contour = heman_image_create(res, res / 2, 3);
    assert(contour != NULL);
    
    heman_image_clear(contour, 0);
    
    heman_image_destroy(contour);
}

void test_contour_drawing() {
    const int npts = 5;
    const int res = 4096;
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
}

void test_colored_circles_drawing() {
    const int npts = 5;
    const int res = 4096;
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
}

void test_cpcf_creation() {
    const int npts = 5;
    const int res = 4096;
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);
    
    heman_image* cpcf = heman_distance_create_cpcf(contour);
    assert(cpcf != NULL);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
    heman_image_destroy(cpcf);
}

void test_image_warping() {
    const int npts = 5;
    const int res = 4096;
    const int seed = 1;
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);
    
    heman_image* cpcf = heman_distance_create_cpcf(contour);
    heman_image* warped = heman_ops_warp(cpcf, seed, 10);
    assert(warped != NULL);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
    heman_image_destroy(cpcf);
    heman_image_destroy(warped);
}

void test_voronoi_coloring() {
    const int npts = 5;
    const int res = 4096;
    const int seed = 1;
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);
    
    heman_image* cpcf = heman_distance_create_cpcf(contour);
    heman_image* warped = heman_ops_warp(cpcf, seed, 10);
    heman_image* voronoi = heman_color_from_cpcf(warped, contour);
    assert(voronoi != NULL);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
    heman_image_destroy(cpcf);
    heman_image_destroy(warped);
    heman_image_destroy(voronoi);
}

void test_sobel_effect() {
    const int npts = 5;
    const int res = 4096;
    const int seed = 1;
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);
    
    heman_image* cpcf = heman_distance_create_cpcf(contour);
    heman_image* warped = heman_ops_warp(cpcf, seed, 10);
    heman_image* voronoi = heman_color_from_cpcf(warped, contour);
    heman_image* toon = heman_ops_sobel(voronoi, 0x303030);
    assert(toon != NULL);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
    heman_image_destroy(cpcf);
    heman_image_destroy(warped);
    heman_image_destroy(voronoi);
    heman_image_destroy(toon);
}

void test_complete_terrain_generation() {
    const int seed = 1;
    const int npts = 5;
    const int res = 4096;

    heman_points* pts = heman_image_create(npts, 1, 3);
    kmVec3* coords = (kmVec3*) heman_image_data(pts);
    coords[0] = (kmVec3){0.3, 0.4, 0.1};
    coords[1] = (kmVec3){0.2, 0.5, 0.1};
    coords[2] = (kmVec3){0.8, 0.7, 0.1};
    coords[3] = (kmVec3){0.8, 0.5, 0.1};
    coords[4] = (kmVec3){0.5, 0.5, 0.2};
    heman_color colors[5] = {0xC8758A, 0xDE935A, 0xE0BB5E, 0xE0BB5E, 0x8EC85D};
    heman_color ocean = 0x83B2B2;
    
    heman_image* contour = heman_image_create(res, res / 2, 3);
    heman_image_clear(contour, 0);
    heman_draw_contour_from_points(contour, pts, ocean, 0.3, 0.45, 1);
    heman_draw_colored_circles(contour, pts, 20, colors);

    heman_image* cpcf = heman_distance_create_cpcf(contour);
    heman_image* warped = heman_ops_warp(cpcf, seed, 10);
    heman_image* voronoi = heman_color_from_cpcf(warped, contour);
    heman_image* toon = heman_ops_sobel(voronoi, 0x303030);
    
    assert(voronoi != NULL);
    assert(toon != NULL);
    
    hut_write_image(OUTFOLDER "terrainpts.png", voronoi, 0, 1);
    hut_write_image(OUTFOLDER "terrainpts_toon.png", toon, 0, 1);
    
    heman_image_destroy(pts);
    heman_image_destroy(contour);
    heman_image_destroy(cpcf);
    heman_image_destroy(warped);
    heman_image_destroy(voronoi);
    heman_image_destroy(toon);
}

/*************************************************************************************/

int main(int argc, char** argv)
{
    puts("\nStarting the heman points unit/regression tests...\n");
    
    test_openmp_threads();
    
    test_points_creation();
    
    test_points_coordinate_assignment();
    
    test_contour_image_creation();
    
    test_contour_drawing();
    
    test_colored_circles_drawing();
    
    test_cpcf_creation();
    
    test_image_warping();
    
    test_voronoi_coloring();
    
    test_sobel_effect();
    
    test_complete_terrain_generation();
    
    puts("\nAll heman points tests pass! :)\n");
    return 0;
}