// This is a private header.  Clients should not include it.

#pragma once
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// An "image" encapsulates three integers (width, height, number of bands)
// and an array of (w * h * nbands) floats, in scanline order.  For simplicity
// the API disallows struct definitions, so this is just an opaque handle.
typedef struct heman_image_s heman_image;

// Point lists are actually one-dimensional images in disguise, usually with
// two bands (X and Y coordinates).
typedef struct heman_image_s heman_points;

// Image values in heman are always floating point, but clients may
// choose either 32-bit floats or 64-bit floats at compile time.
#ifdef USE_DOUBLE_PRECISION
#define HEMAN_FLOAT double
#else
#define HEMAN_FLOAT float
#endif

// Occasionally the heman API accepts four-byte color for convenience.  For now
// we're only using the lower three bytes (XRGB).
typedef unsigned int heman_color;
typedef unsigned char heman_byte;

// Allocate a floating-point image with dimensions width x height x nbands.
heman_image* heman_image_create(int width, int height, int nbands);

// Obtain image properties.
void heman_image_info(heman_image*, int* width, int* height, int* nbands);

// Peek at the stored texel values.
HEMAN_FLOAT* heman_image_data(heman_image*);

// Peek at the stored texel values in a SWIG-amenable way.
void heman_image_array(heman_image* img, HEMAN_FLOAT** outview, int* n);

// Peek at the given texel value.
HEMAN_FLOAT* heman_image_texel(heman_image*, int x, int y);

// Find a reasonable value for the given normalized texture coord.
void heman_image_sample(heman_image*, float u, float v, HEMAN_FLOAT* result);

// Set every band of every texel to the given value.
void heman_image_clear(heman_image*, HEMAN_FLOAT value);

// Free memory for a image.
void heman_image_destroy(heman_image*);

// Create a one-band image from a four-band image by extracting the 4th channel.
heman_image* heman_image_extract_alpha(heman_image*);

// Create a three-band image from a four-band image by extracting first 3 bands.
heman_image* heman_image_extract_rgb(heman_image*);

// Create a 1-pixel tall, 3-band image representing a color gradient that lerps
// the given control points, in a gamma correct way.  Each control point is
// defined by an X location (one integer each) and an RGB value (one 32-bit
// word for each color).
heman_image* heman_color_create_gradient(int width, int num_colors,
    const int* cp_locations, const heman_color* cp_colors);

// This sets some global state that affects lighting and color interpolation.
// The default value is 2.2.
void heman_color_set_gamma(float f);

// Create a 3-band image with the same dimensions as the given heightmap by
// making lookups from a 1-pixel tall color gradient.  The heightmap values
// are normalized using the given minval, maxval range.
heman_image* heman_color_apply_gradient(heman_image* heightmap,
    HEMAN_FLOAT minheight, HEMAN_FLOAT maxheight, heman_image* gradient);

// Convert a single-channel image into a 3-channel image via duplication.
heman_image* heman_color_from_grayscale(heman_image* gray);

// Convert 3-channel image into 1-channel image based on perceptive luminance.
heman_image* heman_color_to_grayscale(heman_image* colorimg);

// Dereference a coordinate field (see heman_distance_create_cpcf) by making
// lookups into a color texture.  Useful for creating Voronoi diagrams.
heman_image* heman_color_from_cpcf(heman_image* cfield, heman_image* texture);

// High-level function that uses several octaves of simplex noise and a signed
// distance field to generate an interesting height map.
heman_image* heman_generate_island_heightmap(int width, int height, int seed);

// High-level function that deforms a hemisphere with simplex noise.
heman_image* heman_generate_rock_heightmap(int width, int height, int seed);

// High-level function that uses several octaves of OpenSimplex noise over a 3D
// domain to generate an interesting lat-long height map.
heman_image* heman_generate_planet_heightmap(int width, int height, int seed);

// Similar to generate_island, but takes a two-band (X Y) list of centers.
// 0.3 is a good choice for the noiseamt, but 0 is useful for diagnostics.
// Points can be 3-tuples, in which case the 3rd component represents the
// strength of the seed point.
heman_image* heman_generate_archipelago_heightmap(
    int width, int height, heman_points* points, float noiseamt, int seed);

// Similar to generate_archipelago_heightmap, but generates a "political"
// RGB image in addition to the heightmap.  If the elevation mode is 0,
// purely political boundaries are ignored when generating the finalized
// height map.
void heman_generate_archipelago_political(int width, int height,
    heman_points* points, const heman_color* colors, heman_color ocean,
    int seed, heman_image** elevation, heman_image** political,
    int elevation_mode);

// High-level function that sums up a number of noise octaves, also known as
// Fractional Brownian Motion.  Taken alone, Perlin / Simplex noise are not
// fractals; this makes them more fractal-like. A good starting point is to use
// a lacunarity of 2.0 and a gain of 0.5, with only 2 or 3 octaves.
heman_image* heman_generate_simplex_fbm(int width, int height, float frequency,
    float amplitude, int octaves, float lacunarity, float gain, int seed);

// Apply ambient occlusion and diffuse lighting to the given heightmap.
heman_image* heman_lighting_apply(heman_image* heightmap,
    heman_image* colorbuffer, float occlusion, float diffuse,
    float diffuse_softening, const float* light_position);

// Given a 1-band heightmap image, create a 3-band image with surface normals,
// using simple forward differencing and OpenMP.
heman_image* heman_lighting_compute_normals(heman_image* heightmap);

// Compute occlusion values for the given heightmap, as described at
// http://nothings.org/gamedev/horizon/.
heman_image* heman_lighting_compute_occlusion(heman_image* heightmap);

// Sets some global state that affects ambient occlusion computations.
void heman_lighting_set_occlusion_scale(float s);

// Create a one-band "signed distance field" based on the given input, using
// the fast algorithm described in Felzenszwalb 2012.
heman_image* heman_distance_create_sdf(heman_image* monochrome);

// Create a one-band unsigned distance field based on the given input, using
// the fast algorithm described in Felzenszwalb 2012.
heman_image* heman_distance_create_df(heman_image* monochrome);

// Create a two-band "closest point coordinate field" containing the
// non-normalized texture coordinates of the nearest seed.  The result is
// related to the distance field but has a greater amount of information.
heman_image* heman_distance_create_cpcf(heman_image* seed);

// Convert a two-band coordinate field into an unsigned distance field.
heman_image* heman_distance_from_cpcf(heman_image* cf);

// Create a two-band CPCF where each texel contains its own coordinate.
heman_image* heman_distance_identity_cpcf(int width, int height);

// Create a single-channel floating point point image from bytes, such that
// [0, 255] map to the given [minval, maxval] range.
heman_image* heman_import_u8(int width, int height, int nbands,
    const heman_byte* source, HEMAN_FLOAT minval, HEMAN_FLOAT maxval);

// Create a mesh with (width - 1) x (height - 1) quads.
void heman_export_ply(heman_image*, const char* filename);

// Create a mesh with (width - 1) x (height - 1) quads and per-vertex colors.
void heman_export_with_colors_ply(
    heman_image* heightmap, heman_image* colors, const char* filename);

// Transform texel values so that [minval, maxval] map to [0, 255], and write
// the result to "dest".  Values outside the range are clamped.
void heman_export_u8(
    heman_image* source, HEMAN_FLOAT minv, HEMAN_FLOAT maxv, heman_byte* outp);

// Given a set of same-sized images, copy them into a horizontal filmstrip.
heman_image* heman_ops_stitch_horizontal(heman_image** images, int count);

// Given a set of same-sized images, copy them into a vertical filmstrip.
heman_image* heman_ops_stitch_vertical(heman_image** images, int count);

// Transform texel values so that [minval, maxval] map to [0, 1] and return the
// result.  Values outside the range are clamped.  The source image is
// untouched.
heman_image* heman_ops_normalize_f32(
    heman_image* source, HEMAN_FLOAT minval, HEMAN_FLOAT maxval);

// Compute the maximum value between two height maps.
heman_image* heman_ops_max(heman_image* imga, heman_image* imgb);

// Generate a monochrome image by applying a step function.
heman_image* heman_ops_step(heman_image* image, HEMAN_FLOAT threshold);

// Takes a 1-band elevation image and makes it tiered (scalloped).
// Optionally takes a color mask, and applies the step operator only
// in the regions with the given mask color.
heman_image* heman_ops_stairstep(heman_image* image, int nsteps,
    heman_image* mask, heman_color mask_color, int invert_mask,
    HEMAN_FLOAT offset);

// Similar to stairstep, but tries to guarantee that every tier
// has the same total land area.
heman_image* heman_ops_percentiles(heman_image* image, int nsteps,
    heman_image* mask, heman_color mask_color, int invert_mask,
    HEMAN_FLOAT offset);

// Generate a height x 1 x 1 image by averaging the values across each row.
heman_image* heman_ops_sweep(heman_image* image);

// Provide a cheap way of measuring "curvature" that doesn't work well
// at saddle points.  Returns a single-band image.
heman_image* heman_ops_laplacian(heman_image* heightmap);

// Highlight edges using the Sobel operator
heman_image* heman_ops_sobel(heman_image* dst, heman_color edge_color);

// Add the values of src into dst.
void heman_ops_accumulate(heman_image* dst, heman_image* src);

// Use FBM and Perlin noise to warp the given image.
heman_image* heman_ops_warp(heman_image* src, int seed, int octaves);

// Same as ops_warp, but alos applies the warping operation to a point list.
heman_image* heman_ops_warp_points(heman_image* src, int seed, int octaves,
    heman_points* pts);

// Consume a 3-band image and a color of interest; produce a 1-band image.
heman_image* heman_ops_extract_mask(heman_image* src, heman_color color, int invert);

// Replace a region of solid color with texture.
heman_image* heman_ops_replace_color(
    heman_image* src, heman_color color, heman_image* texture);

// Create a 4-band image by merging a 3-band political image with
// a 1-band elevation image.
heman_image* heman_ops_merge_political(
    heman_image* elevation, heman_image* political, heman_color ocean_color);

// Add coarse-grain noise to ocean and fine-grain noise to land.
heman_image* heman_ops_emboss(heman_image* elevation, int mode);

// Create a point list.
heman_image* heman_points_create(HEMAN_FLOAT* xy, int npoints, int nbands);

// Free memory for a point list.
void heman_points_destroy(heman_points*);

// Perform simple stratified sampling over a grid.
// Creates a two-band point list of X Y coordinates.
heman_points* heman_points_from_grid(HEMAN_FLOAT width, HEMAN_FLOAT height,
    HEMAN_FLOAT cellsize, HEMAN_FLOAT jitter);

// Perform Bridson's algorithm for Fast Poisson Disk sampling.
// Creates a two-band point list of X Y coordinates.
heman_points* heman_points_from_poisson(
    HEMAN_FLOAT width, HEMAN_FLOAT height, HEMAN_FLOAT mindist);

// Perform Bridson's sampling algorithm, modulated by a density field.
// Creates a two-band point list, sorted from high-density (low radius) to
// low-density (high radius).
heman_points* heman_points_from_density(
    heman_image* density, HEMAN_FLOAT mindist, HEMAN_FLOAT maxdist);

// Set the given list of texels to the given value.
void heman_draw_points(heman_image* target, heman_points* pts, HEMAN_FLOAT val);

// Set the given list of texels to the given list of colors.
void heman_draw_colored_points(
    heman_image* target, heman_points* coords, const heman_color* colors);

// Draw colored circles into the given render target.
void heman_draw_colored_circles(heman_image* target, heman_points* pts,
    int radius, const heman_color* colors);

// Draw a Gaussian splat at each given point.
// The blend_mode parameter is ignored for now (it's always ADD).
void heman_draw_splats(
    heman_image* target, heman_points* pts, int radius, int blend_mode);

// Treats a set of points like blobs and draws a contour around them.
// Points can be 2-tuples (X Y) or 3-tuples (X Y Radius).
void heman_draw_contour_from_points(heman_image* target, heman_points* coords,
    heman_color color, float mind, float maxd, int filterd);

// This returns omp_get_max_threads() for diagnostic purposes.
int heman_get_num_threads();

#ifdef __cplusplus
}
#endif

struct heman_image_s {
    int width;
    int height;
    int nbands;
    HEMAN_FLOAT* data;
};

extern float _gamma;

#define MIN(a, b) (a > b ? b : a)
#define MAX(a, b) (a > b ? a : b)
#define CLAMP(v, lo, hi) MAX(lo, MIN(hi, v))
#define CLAMP01(v) CLAMP(v, 0.0f, 1.0f)
#define SGN(x) ((x > 0) - (x < 0))
#define EDGE(value, upper) MAX(0, MIN(upper - 1, value))
#define TWO_OVER_PI (0.63661977236)
#define PI (3.1415926535)
#define SQR(x) ((x) * (x))
#define SWAP(type,a,b) {type _=a;a=b;b=_;}

inline HEMAN_FLOAT smoothstep(
    HEMAN_FLOAT edge0, HEMAN_FLOAT edge1, HEMAN_FLOAT x)
{
    HEMAN_FLOAT t;
    t = CLAMP01((x - edge0) / (edge1 - edge0));
    return t * t * (3.0 - 2.0 * t);
}

void generate_gaussian_row(int* target, int fwidth);
void generate_gaussian_splat(HEMAN_FLOAT* target, int fwidth);
#ifndef OPEN_SIMPLEX_NOISE_H__
#define OPEN_SIMPLEX_NOISE_H__

/*
 * OpenSimplex (Simplectic) Noise in C.
 * Ported to C from Kurt Spencer's java implementation by Stephen M. Cameron
 *
 * v1.1 (October 6, 2014)
 * - Ported to C
 *
 * v1.1 (October 5, 2014)
 * - Added 2D and 4D implementations.
 * - Proper gradient sets for all dimensions, from a
 *   dimensionally-generalizable scheme with an actual
 *   rhyme and reason behind it.
 * - Removed default permutation array in favor of
 *   default seed.
 * - Changed seed-based constructor to be independent
 *   of any particular randomization library, so results
 *   will be the same when ported to other languages.
 */
#include <stdint.h>

struct osn_context;

int open_simplex_noise(int64_t seed, struct osn_context** ctx);
void open_simplex_noise_free(struct osn_context* ctx);
int open_simplex_noise_init_perm(
    struct osn_context* ctx, int16_t p[], int nelements);
double open_simplex_noise2(struct osn_context* ctx, double x, double y);
double open_simplex_noise3(
    struct osn_context* ctx, double x, double y, double z);
double open_simplex_noise4(
    struct osn_context* ctx, double x, double y, double z, double w);

#endif
#include <assert.h>
/*
Copyright (c) 2008, Luke Benstead.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#ifndef VEC3_H_INCLUDED
#define VEC3_H_INCLUDED

#include <assert.h>
/*
Copyright (c) 2008, Luke Benstead.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#ifndef UTILITY_H_INCLUDED
#define UTILITY_H_INCLUDED

#include <math.h>

#ifndef kmScalar
#ifdef USE_DOUBLE_PRECISION
#define kmScalar double
#else
#define kmScalar float
#endif

#endif

#ifndef kmBool
#define kmBool unsigned char
#endif

#ifndef kmUchar
#define kmUchar unsigned char
#endif

#ifndef kmEnum
#define kmEnum unsigned int
#endif

#ifndef kmUint
#define kmUint unsigned int
#endif

#ifndef kmInt
#define kmInt int
#endif

#ifndef KM_FALSE
#define KM_FALSE 0
#endif

#ifndef KM_TRUE
#define KM_TRUE 1
#endif

#define kmPI 3.14159265358979323846f
#define kmPIOver180  (kmPI / 180.0f)
#define kmPIUnder180 (180.0 / kmPI)
#define kmEpsilon 0.0001

#define KM_CONTAINS_NONE (kmEnum)0
#define KM_CONTAINS_PARTIAL (kmEnum)1
#define KM_CONTAINS_ALL (kmEnum)2

#ifdef __cplusplus
extern "C" {
#endif

extern kmScalar kmSQR(kmScalar s);
extern kmScalar kmDegreesToRadians(kmScalar degrees);
extern kmScalar kmRadiansToDegrees(kmScalar radians);

extern kmScalar kmMin(kmScalar lhs, kmScalar rhs);
extern kmScalar kmMax(kmScalar lhs, kmScalar rhs);
extern kmBool kmAlmostEqual(kmScalar lhs, kmScalar rhs);

extern kmScalar kmClamp(kmScalar x, kmScalar min, kmScalar max);
extern kmScalar kmLerp(kmScalar x, kmScalar y, kmScalar factor);

#ifdef __cplusplus
}
#endif

#endif /* UTILITY_H_INCLUDED */

struct kmMat4;
struct kmMat3;
struct kmPlane;

typedef struct kmVec3 {
	kmScalar x;
	kmScalar y;
	kmScalar z;
} kmVec3;

#ifdef __cplusplus
extern "C" {
#endif

kmVec3* kmVec3Fill(kmVec3* pOut, kmScalar x, kmScalar y, kmScalar z);
kmScalar kmVec3Length(const kmVec3* pIn); /** Returns the length of the vector */
kmScalar kmVec3LengthSq(const kmVec3* pIn); /** Returns the square of the length of the vector */
kmVec3* kmVec3Lerp(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2, kmScalar t);
kmVec3* kmVec3Normalize(kmVec3* pOut, const kmVec3* pIn); /** Returns the vector passed in set to unit length */
kmVec3* kmVec3Cross(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2); /** Returns a vector perpendicular to 2 other vectors */
kmScalar kmVec3Dot(const kmVec3* pV1, const kmVec3* pV2); /** Returns the cosine of the angle between 2 vectors */
kmVec3* kmVec3Add(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2); /** Adds 2 vectors and returns the result */
kmVec3* kmVec3Subtract(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2); /** Subtracts 2 vectors and returns the result */
kmVec3* kmVec3Mul( kmVec3* pOut,const kmVec3* pV1, const kmVec3* pV2 ); 
kmVec3* kmVec3Div( kmVec3* pOut,const kmVec3* pV1, const kmVec3* pV2 );

kmVec3* kmVec3MultiplyMat3(kmVec3 *pOut, const kmVec3 *pV, const struct kmMat3* pM);
kmVec3* kmVec3MultiplyMat4(kmVec3* pOut, const kmVec3* pV, const struct kmMat4* pM);

kmVec3* kmVec3Transform(kmVec3* pOut, const kmVec3* pV1, const struct kmMat4* pM); /** Transforms a vector (assuming w=1) by a given matrix */
kmVec3* kmVec3TransformNormal(kmVec3* pOut, const kmVec3* pV, const struct kmMat4* pM);/**Transforms a 3D normal by a given matrix */
kmVec3* kmVec3TransformCoord(kmVec3* pOut, const kmVec3* pV, const struct kmMat4* pM); /**Transforms a 3D vector by a given matrix, projecting the result back into w = 1. */

kmVec3* kmVec3Scale(kmVec3* pOut, const kmVec3* pIn, const kmScalar s); /** Scales a vector to length s */
int 	kmVec3AreEqual(const kmVec3* p1, const kmVec3* p2);
kmVec3* kmVec3InverseTransform(kmVec3* pOut, const kmVec3* pV, const struct kmMat4* pM);
kmVec3* kmVec3InverseTransformNormal(kmVec3* pOut, const kmVec3* pVect, const struct kmMat4* pM);
kmVec3* kmVec3Assign(kmVec3* pOut, const kmVec3* pIn);
kmVec3* kmVec3Zero(kmVec3* pOut);
kmVec3* kmVec3GetHorizontalAngle(kmVec3* pOut, const kmVec3 *pIn); /** Get the rotations that would make a (0,0,1) direction vector point in the same direction as this direction vector. */
kmVec3* kmVec3RotationToDirection(kmVec3* pOut, const kmVec3* pIn, const kmVec3* forwards); /** Builds a direction vector from input vector. */

kmVec3* kmVec3ProjectOnToPlane(kmVec3* pOut, const kmVec3* point, const struct kmPlane* plane);

kmVec3* kmVec3Reflect(kmVec3* pOut, const kmVec3* pIn, const kmVec3* normal); /**< Reflects a vector about a given surface normal. The surface normal is assumed to be of unit length. */

extern const kmVec3 KM_VEC3_NEG_Z;
extern const kmVec3 KM_VEC3_POS_Z;
extern const kmVec3 KM_VEC3_POS_Y;
extern const kmVec3 KM_VEC3_NEG_Y;
extern const kmVec3 KM_VEC3_NEG_X;
extern const kmVec3 KM_VEC3_POS_X;
extern const kmVec3 KM_VEC3_ZERO;

#ifdef __cplusplus
}
#endif
#endif /* VEC3_H_INCLUDED */
#include <memory.h>
#include <omp.h>
#include <stdlib.h>

#define NOISEX(U, V, A, F) (A * open_simplex_noise2(ctx, U * F, V * F))

#define NOISEY(U, V, A, F) (A * open_simplex_noise2(ctx, U * F + 0.5, V * F))

int heman_get_num_threads() { return omp_get_max_threads(); }

heman_image* heman_ops_step(heman_image* hmap, HEMAN_FLOAT threshold)
{
    assert(hmap->nbands == 1);
    heman_image* result = heman_image_create(hmap->width, hmap->height, 1);
    int size = hmap->height * hmap->width;
    HEMAN_FLOAT* src = hmap->data;
    HEMAN_FLOAT* dst = result->data;
    for (int i = 0; i < size; ++i) {
        *dst++ = (*src++) >= threshold ? 1 : 0;
    }
    return result;
}

heman_image* heman_ops_max(heman_image* imga, heman_image* imgb)
{
    assert(imga->width == imgb->width);
    assert(imga->height == imgb->height);
    assert(imga->nbands == imgb->nbands);
    heman_image* result =
        heman_image_create(imga->width, imga->height, imga->nbands);
    int size = imga->height * imga->width * imga->nbands;
    HEMAN_FLOAT* srca = imga->data;
    HEMAN_FLOAT* srcb = imgb->data;
    HEMAN_FLOAT* dst = result->data;
    for (int i = 0; i < size; ++i, ++dst, ++srca, ++srcb) {
        *dst = MAX(*srca, *srcb);
    }
    return result;
}

heman_image* heman_ops_sweep(heman_image* hmap)
{
    assert(hmap->nbands == 1);
    heman_image* result = heman_image_create(hmap->height, 1, 1);
    HEMAN_FLOAT* dst = result->data;
    const HEMAN_FLOAT* src = hmap->data;
    HEMAN_FLOAT invw = 1.0f / hmap->width;
    for (int y = 0; y < hmap->height; y++) {
        HEMAN_FLOAT acc = 0;
        for (int x = 0; x < hmap->width; x++) {
            acc += *src++;
        }
        *dst++ = (acc * invw);
    }
    return result;
}

static void copy_row(heman_image* src, heman_image* dst, int dstx, int y)
{
    int width = src->width;
    if (src->nbands == 1) {
        for (int x = 0; x < width; x++) {
            HEMAN_FLOAT* srcp = heman_image_texel(src, x, y);
            HEMAN_FLOAT* dstp = heman_image_texel(dst, dstx + x, y);
            *dstp = *srcp;
        }
        return;
    }
    for (int x = 0; x < width; x++) {
        HEMAN_FLOAT* srcp = heman_image_texel(src, x, y);
        HEMAN_FLOAT* dstp = heman_image_texel(dst, dstx + x, y);
        int nbands = src->nbands;
        while (nbands--) {
            *dstp++ = *srcp++;
        }
    }
}

heman_image* heman_ops_stitch_horizontal(heman_image** images, int count)
{
    assert(count > 0);
    int width = images[0]->width;
    int height = images[0]->height;
    int nbands = images[0]->nbands;
    for (int i = 1; i < count; i++) {
        assert(images[i]->width == width);
        assert(images[i]->height == height);
        assert(images[i]->nbands == nbands);
    }
    heman_image* result = heman_image_create(width * count, height, nbands);

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        for (int tile = 0; tile < count; tile++) {
            copy_row(images[tile], result, tile * width, y);
        }
    }

    return result;
}

heman_image* heman_ops_stitch_vertical(heman_image** images, int count)
{
    assert(count > 0);
    int width = images[0]->width;
    int height = images[0]->height;
    int nbands = images[0]->nbands;
    for (int i = 1; i < count; i++) {
        assert(images[i]->width == width);
        assert(images[i]->height == height);
        assert(images[i]->nbands == nbands);
    }
    heman_image* result = heman_image_create(width, height * count, nbands);
    int size = width * height * nbands;
    HEMAN_FLOAT* dst = result->data;
    for (int tile = 0; tile < count; tile++) {
        memcpy(dst, images[tile]->data, size * sizeof(float));
        dst += size;
    }
    return result;
}

heman_image* heman_ops_normalize_f32(
    heman_image* source, HEMAN_FLOAT minv, HEMAN_FLOAT maxv)
{
    heman_image* result =
        heman_image_create(source->width, source->height, source->nbands);
    HEMAN_FLOAT* src = source->data;
    HEMAN_FLOAT* dst = result->data;
    HEMAN_FLOAT scale = 1.0f / (maxv - minv);
    int size = source->height * source->width * source->nbands;
    for (int i = 0; i < size; ++i) {
        HEMAN_FLOAT v = (*src++ - minv) * scale;
        *dst++ = CLAMP(v, 0, 1);
    }
    return result;
}

heman_image* heman_ops_laplacian(heman_image* heightmap)
{
    assert(heightmap->nbands == 1);
    int width = heightmap->width;
    int height = heightmap->height;
    heman_image* result = heman_image_create(width, height, 1);
    int maxx = width - 1;
    int maxy = height - 1;

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        int y1 = MIN(y + 1, maxy);
        HEMAN_FLOAT* dst = result->data + y * width;
        for (int x = 0; x < width; x++) {
            int x1 = MIN(x + 1, maxx);
            HEMAN_FLOAT p = *heman_image_texel(heightmap, x, y);
            HEMAN_FLOAT px = *heman_image_texel(heightmap, x1, y);
            HEMAN_FLOAT py = *heman_image_texel(heightmap, x, y1);
            *dst++ = (p - px) * (p - px) + (p - py) * (p - py);
        }
    }

    return result;
}

void heman_ops_accumulate(heman_image* dst, heman_image* src)
{
    assert(dst->nbands == src->nbands);
    assert(dst->width == src->width);
    assert(dst->height == src->height);
    int size = dst->height * dst->width;
    HEMAN_FLOAT* sdata = src->data;
    HEMAN_FLOAT* ddata = dst->data;
    for (int i = 0; i < size; ++i) {
        *ddata++ += (*sdata++);
    }
}

heman_image* heman_ops_sobel(heman_image* img, heman_color rgb)
{
    int width = img->width;
    int height = img->height;
    assert(img->nbands == 3);
    heman_image* result = heman_image_create(width, height, 3);
    heman_image* gray = heman_color_to_grayscale(img);
    HEMAN_FLOAT inv = 1.0f / 255.0f;

    kmVec3 edge_rgb;
    edge_rgb.x = (HEMAN_FLOAT)(rgb >> 16) * inv;
    edge_rgb.y = (HEMAN_FLOAT)((rgb >> 8) & 0xff) * inv;
    edge_rgb.z = (HEMAN_FLOAT)(rgb & 0xff) * inv;

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        kmVec3* dst = (kmVec3*) result->data + y * width;
        const kmVec3* src = (kmVec3*) img->data + y * width;
        for (int x = 0; x < width; x++) {
            int xm1 = MAX(x - 1, 0);
            int xp1 = MIN(x + 1, width - 1);
            int ym1 = MAX(y - 1, 0);
            int yp1 = MIN(y + 1, height - 1);
            HEMAN_FLOAT t00 = *heman_image_texel(gray, xm1, ym1);
            HEMAN_FLOAT t10 = *heman_image_texel(gray, x, ym1);
            HEMAN_FLOAT t20 = *heman_image_texel(gray, xp1, ym1);
            HEMAN_FLOAT t01 = *heman_image_texel(gray, xm1, 0);
            HEMAN_FLOAT t21 = *heman_image_texel(gray, xp1, 0);
            HEMAN_FLOAT t02 = *heman_image_texel(gray, xm1, yp1);
            HEMAN_FLOAT t12 = *heman_image_texel(gray, x, yp1);
            HEMAN_FLOAT t22 = *heman_image_texel(gray, xp1, yp1);
            HEMAN_FLOAT gx = t00 + 2.0 * t01 + t02 - t20 - 2.0 * t21 - t22;
            HEMAN_FLOAT gy = t00 + 2.0 * t10 + t20 - t02 - 2.0 * t12 - t22;
            HEMAN_FLOAT is_edge = gx * gx + gy * gy > 1e-5;
            kmVec3Lerp(dst++, src++, &edge_rgb, is_edge);
        }
    }

    heman_image_destroy(gray);
    return result;
}

heman_image* heman_ops_warp_core(
    heman_image* img, heman_image* secondary, int seed, int octaves)
{
    struct osn_context* ctx;
    open_simplex_noise(seed, &ctx);
    int width = img->width;
    int height = img->height;
    int nbands = img->nbands;
    heman_image* result = heman_image_create(width, height, nbands);
    heman_image* result2 =
        secondary ? heman_image_create(width, height, secondary->nbands) : 0;
    HEMAN_FLOAT invw = 1.0 / width;
    HEMAN_FLOAT invh = 1.0 / height;
    HEMAN_FLOAT inv = MIN(invw, invh);
    HEMAN_FLOAT aspect = (float) width / height;
    float gain = 0.6;
    float lacunarity = 2.0;
    float initial_amplitude = 0.05;
    float initial_frequency = 8.0;

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        HEMAN_FLOAT* dst = result->data + y * width * nbands;
        for (int x = 0; x < width; x++) {
            float a = initial_amplitude;
            float f = initial_frequency;

            HEMAN_FLOAT* src;

            // This is a little hack that modulates noise according to
            // elevation, to prevent "swimming" at high elevations.
            if (nbands == 4) {
                src = heman_image_texel(img, x, y);
                HEMAN_FLOAT elev = 1 - src[3];
                a *= pow(elev, 4);
            }

            float s = x * inv;
            float t = y * inv;
            float u = x * invw;
            float v = y * invh;
            for (int i = 0; i < octaves; i++) {
                u += NOISEX(s, t, a, f);
                v += aspect * NOISEY(s, t, a, f);
                a *= gain;
                f *= lacunarity;
            }
            int i = CLAMP(u * width, 0, width - 1);
            int j = CLAMP(v * height, 0, height - 1);
            src = heman_image_texel(img, i, j);
            for (int n = 0; n < nbands; n++) {
                *dst++ = *src++;
            }
            if (secondary) {
                src = heman_image_texel(secondary, x, y);
                HEMAN_FLOAT* dst2 = heman_image_texel(result2, i, j);
                for (int n = 0; n < secondary->nbands; n++) {
                    *dst2++ = *src++;
                }
            }
        }
    }
    open_simplex_noise_free(ctx);
    if (secondary) {
        free(secondary->data);
        secondary->data = result2->data;
        free(result2);
    }
    return result;
}

heman_image* heman_ops_warp_points(
    heman_image* img, int seed, int octaves, heman_points* pts)
{
    int width = img->width;
    int height = img->height;
    heman_image* mapping = heman_distance_identity_cpcf(width, height);
    heman_image* retval = heman_ops_warp_core(img, mapping, seed, octaves);
    HEMAN_FLOAT* src = pts->data;
    for (int k = 0; k < pts->width; k++, src += pts->nbands) {
        HEMAN_FLOAT x = src[0];
        HEMAN_FLOAT y = src[1];
        int i = x * mapping->width;
        int j = y * mapping->height;
        if (i < 0 || i >= mapping->width || j < 0 || j >= mapping->height) {
            continue;
        }
        HEMAN_FLOAT* texel = heman_image_texel(mapping, i, j);
        src[0] = texel[0] / mapping->width;
        src[1] = texel[1] / mapping->height;
    }
    heman_image_destroy(mapping);
    return retval;
}

heman_image* heman_ops_warp(heman_image* img, int seed, int octaves)
{
    return heman_ops_warp_core(img, 0, seed, octaves);
}

heman_image* heman_ops_extract_mask(
    heman_image* source, heman_color color, int invert)
{
    assert(source->nbands == 3);
    HEMAN_FLOAT inv = 1.0f / 255.0f;
    HEMAN_FLOAT r = (HEMAN_FLOAT)(color >> 16) * inv;
    HEMAN_FLOAT g = (HEMAN_FLOAT)((color >> 8) & 0xff) * inv;
    HEMAN_FLOAT b = (HEMAN_FLOAT)(color & 0xff) * inv;
    int height = source->height;
    int width = source->width;
    heman_image* result = heman_image_create(width, height, 1);

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        HEMAN_FLOAT* dst = result->data + y * width;
        HEMAN_FLOAT* src = source->data + y * width * 3;
        for (int x = 0; x < width; x++, src += 3) {
            HEMAN_FLOAT val = ((src[0] == r) && (src[1] == g) && (src[2] == b));
            if (!invert) {
                val = 1 - val;
            }
            *dst++ = val;
        }
    }

    return result;
}

heman_image* heman_ops_replace_color(
    heman_image* source, heman_color color, heman_image* texture)
{
    assert(source->nbands == 3);
    assert(texture->nbands == 3);
    int height = source->height;
    int width = source->width;
    assert(texture->width == width);
    assert(texture->height == height);
    HEMAN_FLOAT inv = 1.0f / 255.0f;
    HEMAN_FLOAT r = (HEMAN_FLOAT)(color >> 16) * inv;
    HEMAN_FLOAT g = (HEMAN_FLOAT)((color >> 8) & 0xff) * inv;
    HEMAN_FLOAT b = (HEMAN_FLOAT)(color & 0xff) * inv;
    heman_image* result = heman_image_create(width, height, 3);

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        HEMAN_FLOAT* dst = result->data + y * width * 3;
        HEMAN_FLOAT* src = source->data + y * width * 3;
        HEMAN_FLOAT* tex = texture->data + y * width * 3;
        for (int x = 0; x < width; x++, src += 3, dst += 3, tex += 3) {
            if ((src[0] == r) && (src[1] == g) && (src[2] == b)) {
                dst[0] = tex[0];
                dst[1] = tex[1];
                dst[2] = tex[2];
            } else {
                dst[0] = src[0];
                dst[1] = src[1];
                dst[2] = src[2];
            }
        }
    }

    return result;
}

static int _match(
    heman_image* mask, heman_color mask_color, int invert_mask, int pixel_index)
{
    HEMAN_FLOAT* mcolor = mask->data + pixel_index * 3;
    unsigned char r1 = mcolor[0] * 255;
    unsigned char g1 = mcolor[1] * 255;
    unsigned char b1 = mcolor[2] * 255;
    unsigned char r2 = mask_color >> 16;
    unsigned char g2 = (mask_color >> 8) & 0xff;
    unsigned char b2 = (mask_color & 0xff);
    int retval = r1 == r2 && g1 == g2 && b1 == b2;
    return invert_mask ? (1 - retval) : retval;
}

static float qselect(float* v, int len, int k)
{
    int i, st;
    for (st = i = 0; i < len - 1; i++) {
        if (v[i] > v[len - 1]) {
            continue;
        }
        SWAP(float, v[i], v[st]);
        st++;
    }
    SWAP(float, v[len - 1], v[st]);
    return k == st  ? v[st]
           : st > k ? qselect(v, st, k)
                    : qselect(v + st, len - st, k - st);
}

heman_image* heman_ops_percentiles(heman_image* hmap, int nsteps,
    heman_image* mask, heman_color mask_color, int invert_mask,
    HEMAN_FLOAT offset)
{
    assert(hmap->nbands == 1);
    assert(!mask || mask->nbands == 3);
    int size = hmap->height * hmap->width;
    HEMAN_FLOAT* src = hmap->data;
    HEMAN_FLOAT minv = 1000;
    HEMAN_FLOAT maxv = -1000;
    int npixels = 0;
    for (int i = 0; i < size; ++i) {
        if (!mask || _match(mask, mask_color, invert_mask, i)) {
            minv = MIN(minv, src[i]);
            maxv = MAX(maxv, src[i]);
            npixels++;
        }
    }

    HEMAN_FLOAT* vals = malloc(sizeof(HEMAN_FLOAT) * npixels);
    npixels = 0;
    for (int i = 0; i < size; ++i) {
        if (!mask || _match(mask, mask_color, invert_mask, i)) {
            vals[npixels++] = src[i];
        }
    }
    HEMAN_FLOAT* percentiles = malloc(sizeof(HEMAN_FLOAT) * nsteps);
    for (int tier = 0; tier < nsteps; tier++) {
        float height = qselect(vals, npixels, tier * npixels / nsteps);
        percentiles[tier] = height;
    }
    free(vals);

    for (int i = 0; i < size; ++i) {
        HEMAN_FLOAT e = *src;
        if (!mask || _match(mask, mask_color, invert_mask, i)) {
            for (int tier = nsteps - 1; tier >= 0; tier--) {
                if (e > percentiles[tier]) {
                    e = percentiles[tier];
                    break;
                }
            }
        }
        *src++ = e + offset;
    }
    free(percentiles);

    return hmap;
}

heman_image* heman_ops_stairstep(heman_image* hmap, int nsteps,
    heman_image* mask, heman_color mask_color, int invert_mask,
    HEMAN_FLOAT offset)
{
    assert(hmap->nbands == 1);
    assert(!mask || mask->nbands == 3);
    int size = hmap->height * hmap->width;
    HEMAN_FLOAT* src = hmap->data;
    HEMAN_FLOAT minv = 1000;
    HEMAN_FLOAT maxv = -1000;
    for (int i = 0; i < size; ++i) {
        if (!mask || _match(mask, mask_color, invert_mask, i)) {
            minv = MIN(minv, src[i]);
            maxv = MAX(maxv, src[i]);
        }
    }
    HEMAN_FLOAT range = maxv - minv;
    for (int i = 0; i < size; ++i) {
        HEMAN_FLOAT e = *src;
        if (!mask || _match(mask, mask_color, invert_mask, i)) {
            e = e - minv;
            e /= range;
            e = floor(e * nsteps) / nsteps;
            e = e * range + minv;
        }
        *src++ = e + offset;
    }
    return hmap;
}

heman_image* heman_ops_merge_political(
    heman_image* hmap, heman_image* cmap, heman_color ocean)
{
    assert(hmap->nbands == 1);
    assert(cmap->nbands == 3);
    heman_image* result = heman_image_create(hmap->width, hmap->height, 4);
    HEMAN_FLOAT* pheight = hmap->data;
    HEMAN_FLOAT* pcolour = cmap->data;
    HEMAN_FLOAT* pmerged = result->data;
    HEMAN_FLOAT inv = 1.0f / 255.0f;
    HEMAN_FLOAT oceanr = (HEMAN_FLOAT)(ocean >> 16) * inv;
    HEMAN_FLOAT oceang = (HEMAN_FLOAT)((ocean >> 8) & 0xff) * inv;
    HEMAN_FLOAT oceanb = (HEMAN_FLOAT)(ocean & 0xff) * inv;
    int size = hmap->height * hmap->width;
    float minh = 1000;
    float maxh = -1000;
    for (int i = 0; i < size; ++i) {
        minh = MIN(minh, pheight[i]);
        maxh = MIN(maxh, pheight[i]);
    }
    for (int i = 0; i < size; ++i) {
        HEMAN_FLOAT h = *pheight++;
        if (h < 0) {
            *pmerged++ = oceanr;
            *pmerged++ = oceang;
            *pmerged++ = oceanb;
            pcolour += 3;
        } else {
            *pmerged++ = *pcolour++;
            *pmerged++ = *pcolour++;
            *pmerged++ = *pcolour++;
        }
        *pmerged++ = (h - minh) / (maxh - minh);
    }
    return result;
}

heman_image* heman_ops_emboss(heman_image* img, int mode)
{
    int seed = 1;
    int octaves = 4;

    struct osn_context* ctx;
    open_simplex_noise(seed, &ctx);
    int width = img->width;
    int height = img->height;
    assert(img->nbands == 1);
    heman_image* result = heman_image_create(width, height, 1);
    HEMAN_FLOAT invw = 1.0 / width;
    HEMAN_FLOAT invh = 1.0 / height;
    HEMAN_FLOAT inv = MIN(invw, invh);
    float gain = 0.6;
    float lacunarity = 2.0;
    float land_amplitude = 0.0005;
    float land_frequency = 256.0;
    float ocean_amplitude = 0.5;
    float ocean_frequency = 1.0;

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        HEMAN_FLOAT* dst = result->data + y * width;
        for (int x = 0; x < width; x++) {
            HEMAN_FLOAT z = *heman_image_texel(img, x, y);
            if (z > 0 && mode == 1) {
                float s = x * inv;
                float t = y * inv;
                float a = land_amplitude;
                float f = land_frequency;
                for (int i = 0; i < octaves; i++) {
                    z += NOISEX(s, t, a, f);
                    a *= gain;
                    f *= lacunarity;
                }
            } else if (z <= 0 && mode == -1) {
                z = MAX(z, -0.1);
                float soften = fabsf(z);
                float s = x * inv;
                float t = y * inv;
                float a = ocean_amplitude;
                float f = ocean_frequency;
                for (int i = 0; i < octaves; i++) {
                    z += soften * NOISEX(s, t, a, f);
                    a *= gain;
                    f *= lacunarity;
                }
            }
            *dst++ = z;
        }
    }

    open_simplex_noise_free(ctx);
    return result;
}
