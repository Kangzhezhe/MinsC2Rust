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
#include <stdlib.h>
#include <assert.h>
#include <memory.h>
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

static float _occlusion_scale = 1.0f;

void heman_lighting_set_occlusion_scale(float s)
{
    _occlusion_scale = s;
}

heman_image* heman_lighting_compute_normals(heman_image* heightmap)
{
    assert(heightmap->nbands == 1);
    int width = heightmap->width;
    int height = heightmap->height;
    heman_image* result = heman_image_create(width, height, 3);
    HEMAN_FLOAT invh = 1.0f / height;
    HEMAN_FLOAT invw = 1.0f / width;
    int maxx = width - 1;
    int maxy = height - 1;
    kmVec3* normals = (kmVec3*) result->data;
    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        HEMAN_FLOAT v = y * invh;
        int y1 = MIN(y + 1, maxy);
        kmVec3 p;
        kmVec3 px;
        kmVec3 py;
        kmVec3* n = normals + y * width;
        for (int x = 0; x < width; x++, n++) {
            HEMAN_FLOAT u = x * invw;
            int x1 = MIN(x + 1, maxx);
            p.x = u;
            p.y = v;
            p.z = *heman_image_texel(heightmap, x, y);
            px.x = u + invw;
            px.y = v;
            px.z = *heman_image_texel(heightmap, x1, y);
            py.x = u;
            py.y = v + invh;
            py.z = *heman_image_texel(heightmap, x, y1);
            kmVec3Subtract(&px, &px, &p);
            kmVec3Subtract(&py, &py, &p);
            kmVec3Cross(n, &px, &py);
            kmVec3Normalize(n, n);
            n->y *= -1;
        }
    }

    return result;
}

heman_image* heman_lighting_apply(heman_image* heightmap, heman_image* albedo,
    float occlusion, float diffuse, float diffuse_softening,
    const float* light_position)
{
    assert(heightmap->nbands == 1);
    int width = heightmap->width;
    int height = heightmap->height;
    heman_image* final = heman_image_create(width, height, 3);
    heman_image* normals = heman_lighting_compute_normals(heightmap);
    heman_image* occ = heman_lighting_compute_occlusion(heightmap);

    if (albedo) {
        assert(albedo->nbands == 3);
        assert(albedo->width == width);
        assert(albedo->height == height);
    }

    static float default_pos[] = {-0.5f, 0.5f, 1.0f};
    if (!light_position) {
        light_position = default_pos;
    }

    kmVec3* colors = (kmVec3*) final->data;
    HEMAN_FLOAT invgamma = 1.0f / _gamma;

    kmVec3 L;
    L.x = light_position[0];
    L.y = light_position[1];
    L.z = light_position[2];
    kmVec3Normalize(&L, &L);

    int y;
#pragma omp parallel for
    for (y = 0; y < height; y++) {
        kmVec3* color = colors + y * width;
        for (int x = 0; x < width; x++, color++) {
            kmVec3* N = (kmVec3*) heman_image_texel(normals, x, y);
            kmVec3Lerp(N, N, &KM_VEC3_POS_Z, diffuse_softening);
            HEMAN_FLOAT df =
                1 - diffuse * (1 - kmClamp(kmVec3Dot(N, &L), 0, 1));
            HEMAN_FLOAT of =
                1 - occlusion * (1 - *heman_image_texel(occ, x, y));
            if (albedo) {
                *color = *((kmVec3*) heman_image_texel(albedo, x, y));
            } else {
                color->x = color->y = color->z = 1;
            }
            color->x = pow(color->x, _gamma);
            color->y = pow(color->y, _gamma);
            color->z = pow(color->z, _gamma);
            kmVec3Scale(color, color, df * of);
            color->x = pow(color->x, invgamma);
            color->y = pow(color->y, invgamma);
            color->z = pow(color->z, invgamma);
        }
    }

    heman_image_destroy(normals);
    heman_image_destroy(occ);
    return final;
}

#define NUM_SCANS (16)
#define INV_SCANS (1.0f / 16.0f)

static HEMAN_FLOAT azimuth_slope(kmVec3 a, kmVec3 b)
{
    kmVec3 d;
    kmVec3Subtract(&d, &a, &b);
    HEMAN_FLOAT x = kmVec3Length(&d);
    HEMAN_FLOAT y = b.z - a.z;
    return y / x;
}

static HEMAN_FLOAT compute_occlusion(kmVec3 thispt, kmVec3 horizonpt)
{
    kmVec3 direction;
    kmVec3Subtract(&direction, &horizonpt, &thispt);
    kmVec3Normalize(&direction, &direction);
    HEMAN_FLOAT dot = kmVec3Dot(&direction, &KM_VEC3_POS_Z);
    return atan(MAX(dot, 0.0f)) * TWO_OVER_PI;
}

static void horizon_scan(
    heman_image* heightmap, heman_image* result, int* startpts, int dx, int dy)
{
    int w = heightmap->width, h = heightmap->height;
    int sx = SGN(dx), sy = SGN(dy);
    int ax = abs(dx), ay = abs(dy);

    // Generate the start positions for each sweep line.  The start positions
    // occur just outside the image boundary.
    int nsweeps = ay * w + ax * h - (ax + ay - 1);
    int* p = startpts;
    for (int x = -ax; x < w - ax; x++) {
        for (int y = -ay; y < h - ay; y++) {
            if (x >= 0 && x < w && y >= 0 && y < h) {
                continue;
            }
            *p++ = (sx < 0) ? (w - x - 1) : x;
            *p++ = (sy < 0) ? (h - y - 1) : y;
        }
    }
    assert(nsweeps == (p - startpts) / 2);

    // Compute the number of steps by doing a mock sweep.
    int pathlen = 0;
    int i = startpts[0], j = startpts[1];
    do {
        i += dx;
        j += dy;
        ++pathlen;
    } while (i >= 0 && i < w && j >= 0 && j < h);

    // Each cell in the grid has a certain width and height.  These can be
    // multiplied by row / column indices to get world-space X / Y values,
    // which are in the same coordinate system as the height values.
    HEMAN_FLOAT cellw = _occlusion_scale / MAX(w, h);
    HEMAN_FLOAT cellh = _occlusion_scale / MAX(w, h);

    // Initialize a stack of candidate horizon points, one for each sweep.  In a
    // serial implementation we wouldn't need to allocate this much memory, but
    // we're trying to make life easy for multithreading.
    kmVec3* hull_buffer = malloc(sizeof(kmVec3) * pathlen * nsweeps);

// Finally, perform the actual sweeps. We're careful to touch each pixel
// exactly once, which makes this embarassingly threadable.
    int sweep;

#pragma omp parallel for
    for (sweep = 0; sweep < nsweeps; sweep++) {
        kmVec3* convex_hull = hull_buffer + sweep * pathlen;
        int* p = startpts + sweep * 2;
        int i = p[0];
        int j = p[1];
        kmVec3 thispt, horizonpt;
        thispt.x = i * cellw;
        thispt.y = j * cellh;
        thispt.z = *heman_image_texel(heightmap, EDGE(i, w), EDGE(j, h));
        int stack_top = 0;
        convex_hull[0] = thispt;
        i += dx, j += dy;
        while (i >= 0 && i < w && j >= 0 && j < h) {
            thispt.x = i * cellw;
            thispt.y = j * cellh;
            thispt.z = *heman_image_texel(heightmap, i, j);
            while (stack_top > 0) {
                HEMAN_FLOAT s1 = azimuth_slope(thispt, convex_hull[stack_top]);
                HEMAN_FLOAT s2 =
                    azimuth_slope(thispt, convex_hull[stack_top - 1]);
                if (s1 >= s2) {
                    break;
                }
                stack_top--;
            }
            horizonpt = convex_hull[stack_top++];
            assert(stack_top < pathlen);
            convex_hull[stack_top] = thispt;
            HEMAN_FLOAT occlusion = compute_occlusion(thispt, horizonpt);
            *heman_image_texel(result, i, j) += INV_SCANS * occlusion;
            i += dx;
            j += dy;
        }
    }

    free(hull_buffer);
}

heman_image* heman_lighting_compute_occlusion(heman_image* heightmap)
{
    assert(heightmap->nbands == 1);
    int width = heightmap->width;
    int height = heightmap->height;
    heman_image* result = heman_image_create(width, height, 1);
    memset(result->data, 0, sizeof(HEMAN_FLOAT) * width * height);

    // Define sixteen 2D vectors, used for the sweep directions.
    const int scans[NUM_SCANS * 2] = {
        1, 0, 0, 1, -1, 0, 0, -1,                               // Rook
        1, 1, -1, -1, 1, -1, -1, 1,                             // Bishop
        2, 1, 2, -1, -2, 1, -2, -1, 1, 2, 1, -2, -1, 2, -1, -2  // Knight
    };

    // Allocate memory that will store the starting positions of each sweep.
    int* startpts = malloc(sizeof(int) * 2 * 3 * kmMax(width, height));

    // Make each sweep serially, accumulating the result.
    for (int i = 0; i < NUM_SCANS; i++) {
        int dx = scans[i * 2];
        int dy = scans[i * 2 + 1];
        horizon_scan(heightmap, result, startpts, dx, dy);
    }

    // Invert the occlusion values and make sure they are valid.
    for (int i = 0; i < width * height; i++) {
        result->data[i] = 1.0f - result->data[i];
        assert(result->data[i] >= 0.0 && result->data[i] <= 1.0f);
    }

    free(startpts);
    return result;
}
