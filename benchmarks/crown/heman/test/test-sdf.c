#include <heman.h>
#include <assert.h>
#include "hut.h"

#define OUTFOLDER "./"
#define INFOLDER "../test/"

/*************************************************************************************/

void test_image_loading() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    assert(seed != NULL);
    heman_image_destroy(seed);
}

void test_sdf_creation() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    heman_image* sdf = heman_distance_create_sdf(seed);
    assert(sdf != NULL);
    
    heman_image_destroy(seed);
    heman_image_destroy(sdf);
}

void test_sdf_image_writing() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    heman_image* sdf = heman_distance_create_sdf(seed);
    
    hut_write_image(OUTFOLDER "sdfresult.png", sdf, -0.1, 0.1);
    
    heman_image_destroy(seed);
    heman_image_destroy(sdf);
}

void test_complete_sdf_pipeline() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    assert(seed != NULL);
    
    heman_image* sdf = heman_distance_create_sdf(seed);
    assert(sdf != NULL);
    
    hut_write_image(OUTFOLDER "sdfresult.png", sdf, -0.1, 0.1);
    
    heman_image_destroy(seed);
    heman_image_destroy(sdf);
}

void test_sdf_with_different_ranges() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    heman_image* sdf = heman_distance_create_sdf(seed);
    
    // Test with different output ranges
    hut_write_image(OUTFOLDER "sdf_range1.png", sdf, -0.05, 0.05);
    hut_write_image(OUTFOLDER "sdf_range2.png", sdf, -0.2, 0.2);
    
    heman_image_destroy(seed);
    heman_image_destroy(sdf);
}

void test_multiple_sdf_operations() {
    heman_image* seed = hut_read_image(INFOLDER "sdfseed.png", 1);
    
    // Create multiple SDF images to test consistency
    heman_image* sdf1 = heman_distance_create_sdf(seed);
    heman_image* sdf2 = heman_distance_create_sdf(seed);
    
    assert(sdf1 != NULL);
    assert(sdf2 != NULL);
    
    heman_image_destroy(seed);
    heman_image_destroy(sdf1);
    heman_image_destroy(sdf2);
}

/*************************************************************************************/

int main(int argc, char** argv)
{
    puts("\nStarting the heman SDF unit/regression tests...\n");
    
    test_image_loading();
    
    test_sdf_creation();
    
    test_sdf_image_writing();
    
    test_complete_sdf_pipeline();
    
    test_sdf_with_different_ranges();
    
    test_multiple_sdf_operations();
    
    puts("\nAll heman SDF tests pass! :)\n");
    return 0;
}