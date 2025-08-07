#include <heman.h>
#include <time.h>
#include <omp.h>
#include <assert.h>
#include "hut.h"

#define COUNT(a) (sizeof(a) / sizeof(a[0]))
#define OUTFOLDER "./"
#define INFOLDER "../test/"

/*************************************************************************************/

void test_color_gradient_creation() {
    int cp_locations[] = {
        000, 155, 156, 200, 255,
    };
    heman_color cp_colors[] = {
        0x001070,  // Dark Blue
        0x2C5A7C,  // Light Blue
        0x5D943C,  // Dark Green
        0x606011,  // Brown
        0xFFFFFF,  // White
    };
    assert(COUNT(cp_locations) == COUNT(cp_colors));
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(cp_colors), cp_locations, cp_colors);
    
    assert(grad != NULL);
    heman_image_destroy(grad);
}

void test_image_loading() {
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    assert(hmap != NULL);
    heman_image_destroy(hmap);
}

void test_color_gradient_application() {
    int cp_locations[] = {
        000, 155, 156, 200, 255,
    };
    heman_color cp_colors[] = {
        0x001070,  // Dark Blue
        0x2C5A7C,  // Light Blue
        0x5D943C,  // Dark Green
        0x606011,  // Brown
        0xFFFFFF,  // White
    };
    
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(cp_colors), cp_locations, cp_colors);
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    
    heman_image* colorized = heman_color_apply_gradient(hmap, 0, 1, grad);
    assert(colorized != NULL);
    
    heman_image_destroy(grad);
    heman_image_destroy(hmap);
    heman_image_destroy(colorized);
}

void test_image_writing() {
    int cp_locations[] = {
        000, 155, 156, 200, 255,
    };
    heman_color cp_colors[] = {
        0x001070,  // Dark Blue
        0x2C5A7C,  // Light Blue
        0x5D943C,  // Dark Green
        0x606011,  // Brown
        0xFFFFFF,  // White
    };
    
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(cp_colors), cp_locations, cp_colors);
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    heman_image* colorized = heman_color_apply_gradient(hmap, 0, 1, grad);
    
    hut_write_image(OUTFOLDER "colorized.png", colorized, 0, 1);
    
    heman_image_destroy(grad);
    heman_image_destroy(hmap);
    heman_image_destroy(colorized);
}

void test_lighting_application() {
    int cp_locations[] = {
        000, 155, 156, 200, 255,
    };
    heman_color cp_colors[] = {
        0x001070,  // Dark Blue
        0x2C5A7C,  // Light Blue
        0x5D943C,  // Dark Green
        0x606011,  // Brown
        0xFFFFFF,  // White
    };
    
    heman_image* grad = heman_color_create_gradient(
        256, COUNT(cp_colors), cp_locations, cp_colors);
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    heman_image* colorized = heman_color_apply_gradient(hmap, 0, 1, grad);
    
    float lightpos[] = {-0.5f, 0.5f, 1.0f};
    heman_image* litearth = heman_lighting_apply(hmap, colorized, 1, 0.5, 0.5, lightpos);
    assert(litearth != NULL);
    
    hut_write_image(OUTFOLDER "litearth.png", litearth, 0, 1);
    
    heman_image_destroy(grad);
    heman_image_destroy(hmap);
    heman_image_destroy(colorized);
    heman_image_destroy(litearth);
}

void test_step_operation() {
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    heman_image* masked = heman_ops_step(hmap, 0.61);
    assert(masked != NULL);
    
    hut_write_image(OUTFOLDER "masked.png", masked, 0, 1);
    
    heman_image_destroy(hmap);
    heman_image_destroy(masked);
}

void test_sweep_operation() {
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    heman_image* masked = heman_ops_step(hmap, 0.61);
    heman_image* sweep = heman_ops_sweep(masked);
    assert(sweep != NULL);
    
    hut_write_image(OUTFOLDER "sweep.png", sweep, 0, 1);
    
    heman_image_destroy(hmap);
    heman_image_destroy(masked);
    heman_image_destroy(sweep);
}
void test_openmp_threads() {
    int max_threads = omp_get_max_threads();
    assert(max_threads > 0);
    printf("%d threads available.\n", max_threads);
}

void test_timing_operations() {
    double begin = omp_get_wtime();
    
    // Perform a simple operation to test timing
    heman_image* hmap = hut_read_image(INFOLDER "earth2048.png", 1);
    assert(hmap != NULL);
    heman_image_destroy(hmap);
    
    double duration = omp_get_wtime() - begin;
    assert(duration >= 0.0);
    printf("Simple operation completed in %.3f seconds.\n", duration);
}

/*************************************************************************************/

int main(int argc, char** argv) {
    puts("\nStarting the heman unit/regression tests...\n");
    
    test_openmp_threads();
    
    test_color_gradient_creation();
    
    test_image_loading();
    
    test_color_gradient_application();
    
    test_image_writing();
    
    test_lighting_application();
    
    test_step_operation();
    
    test_sweep_operation();
    
    test_timing_operations();
    
    puts("\nAll heman tests pass! :)\n");
    return 0;
}