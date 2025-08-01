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
#include <omp.h>
#include <time.h>
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

#ifndef VEC2_H_INCLUDED
#define VEC2_H_INCLUDED

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

struct kmMat3;

#pragma pack(push)  /* push current alignment to stack */
#pragma pack(1)     /* set alignment to 1 byte boundary */
typedef struct kmVec2 {
    kmScalar x;
    kmScalar y;
} kmVec2;

#pragma pack(pop)

#ifdef __cplusplus
extern "C" {
#endif

kmVec2* kmVec2Fill(kmVec2* pOut, kmScalar x, kmScalar y);
kmScalar kmVec2Length(const kmVec2* pIn); /**< Returns the length of the vector*/
kmScalar kmVec2LengthSq(const kmVec2* pIn); /**< Returns the square of the length of the vector*/
kmVec2* kmVec2Normalize(kmVec2* pOut, const kmVec2* pIn); /**< Returns the vector passed in set to unit length*/
kmVec2* kmVec2Lerp(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2, kmScalar t);
kmVec2* kmVec2Add(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2); /**< Adds 2 vectors and returns the result*/
kmScalar kmVec2Dot(const kmVec2* pV1, const kmVec2* pV2); /** Returns the Dot product which is the cosine of the angle between the two vectors multiplied by their lengths */
kmScalar kmVec2Cross(const kmVec2* pV1, const kmVec2* pV2);
kmVec2* kmVec2Subtract(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2); /**< Subtracts 2 vectors and returns the result*/
kmVec2* kmVec2Mul( kmVec2* pOut,const kmVec2* pV1, const kmVec2* pV2 ); /**< Component-wise multiplication */
kmVec2* kmVec2Div( kmVec2* pOut,const kmVec2* pV1, const kmVec2* pV2 ); /**< Component-wise division*/
kmVec2* kmVec2Transform(kmVec2* pOut, const kmVec2* pV1, const struct kmMat3* pM); /** Transform the Vector */
kmVec2* kmVec2TransformCoord(kmVec2* pOut, const kmVec2* pV, const struct kmMat3* pM); /**<Transforms a 2D vector by a given matrix, projecting the result back into w = 1.*/
kmVec2* kmVec2Scale(kmVec2* pOut, const kmVec2* pIn, const kmScalar s); /**< Scales a vector to length s*/
int	kmVec2AreEqual(const kmVec2* p1, const kmVec2* p2); /**< Returns 1 if both vectors are equal*/
kmVec2* kmVec2Assign(kmVec2* pOut, const kmVec2* pIn);
kmVec2* kmVec2RotateBy(kmVec2* pOut, const kmVec2* pIn, const kmScalar degrees, const kmVec2* center); /**<Rotates the point anticlockwise around a center by an amount of degrees.*/
kmScalar kmVec2DegreesBetween(const kmVec2* v1, const kmVec2* v2);
kmScalar kmVec2DistanceBetween(const kmVec2* v1, const kmVec2* v2);
kmVec2* kmVec2MidPointBetween(kmVec2* pOut, const kmVec2* v1, const kmVec2* v2);
kmVec2* kmVec2Reflect(kmVec2* pOut, const kmVec2* pIn, const kmVec2* normal); /**< Reflects a vector about a given surface normal. The surface normal is assumed to be of unit length. */

extern const kmVec2 KM_VEC2_POS_Y;
extern const kmVec2 KM_VEC2_NEG_Y;
extern const kmVec2 KM_VEC2_NEG_X;
extern const kmVec2 KM_VEC2_POS_X;
extern const kmVec2 KM_VEC2_ZERO;

#ifdef __cplusplus
}
#endif


#endif /* VEC2_H_INCLUDED */
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
// Heman utilities.  This is part of the test suite, not the core library.

#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STB_IMAGE_RESIZE_IMPLEMENTATION
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#pragma GCC diagnostic ignored "-Wunused-value"
#pragma GCC diagnostic ignored "-Wpointer-sign"
#pragma GCC diagnostic ignored "-Wunknown-pragmas"
#pragma GCC diagnostic ignored "-Wmaybe-uninitialized"
/* stb_image_write - v0.98 - public domain - http://nothings.org/stb/stb_image_write.h
   writes out PNG/BMP/TGA images to C stdio - Sean Barrett 2010
                            no warranty implied; use at your own risk


   Before #including,

       #define STB_IMAGE_WRITE_IMPLEMENTATION

   in the file that you want to have the implementation.

   Will probably not work correctly with strict-aliasing optimizations.

ABOUT:

   This header file is a library for writing images to C stdio. It could be
   adapted to write to memory or a general streaming interface; let me know.

   The PNG output is not optimal; it is 20-50% larger than the file
   written by a decent optimizing implementation. This library is designed
   for source code compactness and simplicitly, not optimal image file size
   or run-time performance.

BUILDING:

   You can #define STBIW_ASSERT(x) before the #include to avoid using assert.h.
   You can #define STBIW_MALLOC(), STBIW_REALLOC(), and STBIW_FREE() to replace
   malloc,realloc,free.
   You can define STBIW_MEMMOVE() to replace memmove()

USAGE:

   There are four functions, one for each image file format:

     int stbi_write_png(char const *filename, int w, int h, int comp, const void *data, int stride_in_bytes);
     int stbi_write_bmp(char const *filename, int w, int h, int comp, const void *data);
     int stbi_write_tga(char const *filename, int w, int h, int comp, const void *data);
     int stbi_write_hdr(char const *filename, int w, int h, int comp, const void *data);

   Each function returns 0 on failure and non-0 on success.

   The functions create an image file defined by the parameters. The image
   is a rectangle of pixels stored from left-to-right, top-to-bottom.
   Each pixel contains 'comp' channels of data stored interleaved with 8-bits
   per channel, in the following order: 1=Y, 2=YA, 3=RGB, 4=RGBA. (Y is
   monochrome color.) The rectangle is 'w' pixels wide and 'h' pixels tall.
   The *data pointer points to the first byte of the top-left-most pixel.
   For PNG, "stride_in_bytes" is the distance in bytes from the first byte of
   a row of pixels to the first byte of the next row of pixels.

   PNG creates output files with the same number of components as the input.
   The BMP format expands Y to RGB in the file format and does not
   output alpha.

   PNG supports writing rectangles of data even when the bytes storing rows of
   data are not consecutive in memory (e.g. sub-rectangles of a larger image),
   by supplying the stride between the beginning of adjacent rows. The other
   formats do not. (Thus you cannot write a native-format BMP through the BMP
   writer, both because it is in BGR order and because it may have padding
   at the end of the line.)

   HDR expects linear float data. Since the format is always 32-bit rgb(e)
   data, alpha (if provided) is discarded, and for monochrome data it is
   replicated across all three channels.

CREDITS:

   PNG/BMP/TGA
      Sean Barrett
   HDR
      Baldur Karlsson
   TGA monochrome:
      Jean-Sebastien Guay
   misc enhancements:
      Tim Kelsey
   bugfixes:
      github:Chribba
*/

#ifndef INCLUDE_STB_IMAGE_WRITE_H
#define INCLUDE_STB_IMAGE_WRITE_H

#ifdef __cplusplus
extern "C" {
#endif

extern int stbi_write_png(char const *filename, int w, int h, int comp, const void  *data, int stride_in_bytes);
extern int stbi_write_bmp(char const *filename, int w, int h, int comp, const void  *data);
extern int stbi_write_tga(char const *filename, int w, int h, int comp, const void  *data);
extern int stbi_write_hdr(char const *filename, int w, int h, int comp, const float *data);

#ifdef __cplusplus
}
#endif

#endif//INCLUDE_STB_IMAGE_WRITE_H

#ifdef STB_IMAGE_WRITE_IMPLEMENTATION

#include <stdarg.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#if defined(STBIW_MALLOC) && defined(STBIW_FREE) && defined(STBIW_REALLOC)
// ok
#elif !defined(STBIW_MALLOC) && !defined(STBIW_FREE) && !defined(STBIW_REALLOC)
// ok
#else
#error "Must define all or none of STBIW_MALLOC, STBIW_FREE, and STBIW_REALLOC."
#endif

#ifndef STBIW_MALLOC
#define STBIW_MALLOC(sz)    malloc(sz)
#define STBIW_REALLOC(p,sz) realloc(p,sz)
#define STBIW_FREE(p)       free(p)
#endif
#ifndef STBIW_MEMMOVE
#define STBIW_MEMMOVE(a,b,sz) memmove(a,b,sz)
#endif


#ifndef STBIW_ASSERT
#include <assert.h>
#define STBIW_ASSERT(x) assert(x)
#endif

typedef unsigned int stbiw_uint32;
typedef int stb_image_write_test[sizeof(stbiw_uint32)==4 ? 1 : -1];

static void writefv(FILE *f, const char *fmt, va_list v)
{
   while (*fmt) {
      switch (*fmt++) {
         case ' ': break;
         case '1': { unsigned char x = (unsigned char) va_arg(v, int); fputc(x,f); break; }
         case '2': { int x = va_arg(v,int); unsigned char b[2];
                     b[0] = (unsigned char) x; b[1] = (unsigned char) (x>>8);
                     fwrite(b,2,1,f); break; }
         case '4': { stbiw_uint32 x = va_arg(v,int); unsigned char b[4];
                     b[0]=(unsigned char)x; b[1]=(unsigned char)(x>>8);
                     b[2]=(unsigned char)(x>>16); b[3]=(unsigned char)(x>>24);
                     fwrite(b,4,1,f); break; }
         default:
            STBIW_ASSERT(0);
            return;
      }
   }
}

static void write3(FILE *f, unsigned char a, unsigned char b, unsigned char c)
{
   unsigned char arr[3];
   arr[0] = a, arr[1] = b, arr[2] = c;
   fwrite(arr, 3, 1, f);
}

static void write_pixels(FILE *f, int rgb_dir, int vdir, int x, int y, int comp, void *data, int write_alpha, int scanline_pad, int expand_mono)
{
   unsigned char bg[3] = { 255, 0, 255}, px[3];
   stbiw_uint32 zero = 0;
   int i,j,k, j_end;

   if (y <= 0)
      return;

   if (vdir < 0)
      j_end = -1, j = y-1;
   else
      j_end =  y, j = 0;

   for (; j != j_end; j += vdir) {
      for (i=0; i < x; ++i) {
         unsigned char *d = (unsigned char *) data + (j*x+i)*comp;
         if (write_alpha < 0)
            fwrite(&d[comp-1], 1, 1, f);
         switch (comp) {
            case 1: fwrite(d, 1, 1, f);
                    break;
            case 2: if (expand_mono)
                       write3(f, d[0],d[0],d[0]); // monochrome bmp
                    else
                       fwrite(d, 1, 1, f);  // monochrome TGA
                    break;
            case 4:
               if (!write_alpha) {
                  // composite against pink background
                  for (k=0; k < 3; ++k)
                     px[k] = bg[k] + ((d[k] - bg[k]) * d[3])/255;
                  write3(f, px[1-rgb_dir],px[1],px[1+rgb_dir]);
                  break;
               }
               /* FALLTHROUGH */
            case 3:
               write3(f, d[1-rgb_dir],d[1],d[1+rgb_dir]);
               break;
         }
         if (write_alpha > 0)
            fwrite(&d[comp-1], 1, 1, f);
      }
      fwrite(&zero,scanline_pad,1,f);
   }
}

static int outfile(char const *filename, int rgb_dir, int vdir, int x, int y, int comp, int expand_mono, void *data, int alpha, int pad, const char *fmt, ...)
{
   FILE *f;
   if (y < 0 || x < 0) return 0;
   f = fopen(filename, "wb");
   if (f) {
      va_list v;
      va_start(v, fmt);
      writefv(f, fmt, v);
      va_end(v);
      write_pixels(f,rgb_dir,vdir,x,y,comp,data,alpha,pad,expand_mono);
      fclose(f);
   }
   return f != NULL;
}

int stbi_write_bmp(char const *filename, int x, int y, int comp, const void *data)
{
   int pad = (-x*3) & 3;
   return outfile(filename,-1,-1,x,y,comp,1,(void *) data,0,pad,
           "11 4 22 4" "4 44 22 444444",
           'B', 'M', 14+40+(x*3+pad)*y, 0,0, 14+40,  // file header
            40, x,y, 1,24, 0,0,0,0,0,0);             // bitmap header
}

int stbi_write_tga(char const *filename, int x, int y, int comp, const void *data)
{
   int has_alpha = (comp == 2 || comp == 4);
   int colorbytes = has_alpha ? comp-1 : comp;
   int format = colorbytes < 2 ? 3 : 2; // 3 color channels (RGB/RGBA) = 2, 1 color channel (Y/YA) = 3
   return outfile(filename, -1,-1, x, y, comp, 0, (void *) data, has_alpha, 0,
                  "111 221 2222 11", 0,0,format, 0,0,0, 0,0,x,y, (colorbytes+has_alpha)*8, has_alpha*8);
}

// *************************************************************************************************
// Radiance RGBE HDR writer
// by Baldur Karlsson
#define stbiw__max(a, b)  ((a) > (b) ? (a) : (b))

void stbiw__linear_to_rgbe(unsigned char *rgbe, float *linear)
{
   int exponent;
   float maxcomp = stbiw__max(linear[0], stbiw__max(linear[1], linear[2]));

   if (maxcomp < 1e-32) {
      rgbe[0] = rgbe[1] = rgbe[2] = rgbe[3] = 0;
   } else {
      float normalize = (float) frexp(maxcomp, &exponent) * 256.0f/maxcomp;

      rgbe[0] = (unsigned char)(linear[0] * normalize);
      rgbe[1] = (unsigned char)(linear[1] * normalize);
      rgbe[2] = (unsigned char)(linear[2] * normalize);
      rgbe[3] = (unsigned char)(exponent + 128);
   }
}

void stbiw__write_run_data(FILE *f, int length, unsigned char databyte)
{
   unsigned char lengthbyte = (unsigned char) (length+128);
   STBIW_ASSERT(length+128 <= 255);
   fwrite(&lengthbyte, 1, 1, f);
   fwrite(&databyte, 1, 1, f);
}

void stbiw__write_dump_data(FILE *f, int length, unsigned char *data)
{
   unsigned char lengthbyte = (unsigned char )(length & 0xff);
   STBIW_ASSERT(length <= 128); // inconsistent with spec but consistent with official code
   fwrite(&lengthbyte, 1, 1, f);
   fwrite(data, length, 1, f);
}

void stbiw__write_hdr_scanline(FILE *f, int width, int comp, unsigned char *scratch, const float *scanline)
{
   unsigned char scanlineheader[4] = { 2, 2, 0, 0 };
   unsigned char rgbe[4];
   float linear[3];
   int x;

   scanlineheader[2] = (width&0xff00)>>8;
   scanlineheader[3] = (width&0x00ff);

   /* skip RLE for images too small or large */
   if (width < 8 || width >= 32768) {
      for (x=0; x < width; x++) {
         switch (comp) {
            case 4: /* fallthrough */
            case 3: linear[2] = scanline[x*comp + 2];
                    linear[1] = scanline[x*comp + 1];
                    linear[0] = scanline[x*comp + 0];
                    break;
            case 2: /* fallthrough */
            case 1: linear[0] = linear[1] = linear[2] = scanline[x*comp + 0];
                    break;
         }
         stbiw__linear_to_rgbe(rgbe, linear);
         fwrite(rgbe, 4, 1, f);
      }
   } else {
      int c,r;
      /* encode into scratch buffer */
      for (x=0; x < width; x++) {
         switch(comp) {
            case 4: /* fallthrough */
            case 3: linear[2] = scanline[x*comp + 2];
                    linear[1] = scanline[x*comp + 1];
                    linear[0] = scanline[x*comp + 0];
                    break;
            case 2: /* fallthrough */
            case 1: linear[0] = linear[1] = linear[2] = scanline[x*comp + 0];
                    break;
         }
         stbiw__linear_to_rgbe(rgbe, linear);
         scratch[x + width*0] = rgbe[0];
         scratch[x + width*1] = rgbe[1];
         scratch[x + width*2] = rgbe[2];
         scratch[x + width*3] = rgbe[3];
      }

      fwrite(scanlineheader, 4, 1, f);

      /* RLE each component separately */
      for (c=0; c < 4; c++) {
         unsigned char *comp = &scratch[width*c];

         x = 0;
         while (x < width) {
            // find first run
            r = x;
            while (r+2 < width) {
               if (comp[r] == comp[r+1] && comp[r] == comp[r+2])
                  break;
               ++r;
            }
            if (r+2 >= width)
               r = width;
            // dump up to first run
            while (x < r) {
               int len = r-x;
               if (len > 128) len = 128;
               stbiw__write_dump_data(f, len, &comp[x]);
               x += len;
            }
            // if there's a run, output it
            if (r+2 < width) { // same test as what we break out of in search loop, so only true if we break'd
               // find next byte after run
               while (r < width && comp[r] == comp[x])
                  ++r;
               // output run up to r
               while (x < r) {
                  int len = r-x;
                  if (len > 127) len = 127;
                  stbiw__write_run_data(f, len, comp[x]);
                  x += len;
               }
            }
         }
      }
   }
}

int stbi_write_hdr(char const *filename, int x, int y, int comp, const float *data)
{
   int i;
   FILE *f;
   if (y <= 0 || x <= 0 || data == NULL) return 0;
   f = fopen(filename, "wb");
   if (f) {
      /* Each component is stored separately. Allocate scratch space for full output scanline. */
      unsigned char *scratch = (unsigned char *) STBIW_MALLOC(x*4);
      fprintf(f, "#?RADIANCE\n# Written by stb_image_write.h\nFORMAT=32-bit_rle_rgbe\n"      );
      fprintf(f, "EXPOSURE=          1.0000000000000\n\n-Y %d +X %d\n"                 , y, x);
      for(i=0; i < y; i++)
         stbiw__write_hdr_scanline(f, x, comp, scratch, data + comp*i*x);
      STBIW_FREE(scratch);
      fclose(f);
   }
   return f != NULL;
}

/////////////////////////////////////////////////////////
// PNG

// stretchy buffer; stbiw__sbpush() == vector<>::push_back() -- stbiw__sbcount() == vector<>::size()
#define stbiw__sbraw(a) ((int *) (a) - 2)
#define stbiw__sbm(a)   stbiw__sbraw(a)[0]
#define stbiw__sbn(a)   stbiw__sbraw(a)[1]

#define stbiw__sbneedgrow(a,n)  ((a)==0 || stbiw__sbn(a)+n >= stbiw__sbm(a))
#define stbiw__sbmaybegrow(a,n) (stbiw__sbneedgrow(a,(n)) ? stbiw__sbgrow(a,n) : 0)
#define stbiw__sbgrow(a,n)  stbiw__sbgrowf((void **) &(a), (n), sizeof(*(a)))

#define stbiw__sbpush(a, v)      (stbiw__sbmaybegrow(a,1), (a)[stbiw__sbn(a)++] = (v))
#define stbiw__sbcount(a)        ((a) ? stbiw__sbn(a) : 0)
#define stbiw__sbfree(a)         ((a) ? STBIW_FREE(stbiw__sbraw(a)),0 : 0)

static void *stbiw__sbgrowf(void **arr, int increment, int itemsize)
{
   int m = *arr ? 2*stbiw__sbm(*arr)+increment : increment+1;
   void *p = STBIW_REALLOC(*arr ? stbiw__sbraw(*arr) : 0, itemsize * m + sizeof(int)*2);
   STBIW_ASSERT(p);
   if (p) {
      if (!*arr) ((int *) p)[1] = 0;
      *arr = (void *) ((int *) p + 2);
      stbiw__sbm(*arr) = m;
   }
   return *arr;
}

static unsigned char *stbiw__zlib_flushf(unsigned char *data, unsigned int *bitbuffer, int *bitcount)
{
   while (*bitcount >= 8) {
      stbiw__sbpush(data, (unsigned char) *bitbuffer);
      *bitbuffer >>= 8;
      *bitcount -= 8;
   }
   return data;
}

static int stbiw__zlib_bitrev(int code, int codebits)
{
   int res=0;
   while (codebits--) {
      res = (res << 1) | (code & 1);
      code >>= 1;
   }
   return res;
}

static unsigned int stbiw__zlib_countm(unsigned char *a, unsigned char *b, int limit)
{
   int i;
   for (i=0; i < limit && i < 258; ++i)
      if (a[i] != b[i]) break;
   return i;
}

static unsigned int stbiw__zhash(unsigned char *data)
{
   stbiw_uint32 hash = data[0] + (data[1] << 8) + (data[2] << 16);
   hash ^= hash << 3;
   hash += hash >> 5;
   hash ^= hash << 4;
   hash += hash >> 17;
   hash ^= hash << 25;
   hash += hash >> 6;
   return hash;
}

#define stbiw__zlib_flush() (out = stbiw__zlib_flushf(out, &bitbuf, &bitcount))
#define stbiw__zlib_add(code,codebits) \
      (bitbuf |= (code) << bitcount, bitcount += (codebits), stbiw__zlib_flush())
#define stbiw__zlib_huffa(b,c)  stbiw__zlib_add(stbiw__zlib_bitrev(b,c),c)
// default huffman tables
#define stbiw__zlib_huff1(n)  stbiw__zlib_huffa(0x30 + (n), 8)
#define stbiw__zlib_huff2(n)  stbiw__zlib_huffa(0x190 + (n)-144, 9)
#define stbiw__zlib_huff3(n)  stbiw__zlib_huffa(0 + (n)-256,7)
#define stbiw__zlib_huff4(n)  stbiw__zlib_huffa(0xc0 + (n)-280,8)
#define stbiw__zlib_huff(n)  ((n) <= 143 ? stbiw__zlib_huff1(n) : (n) <= 255 ? stbiw__zlib_huff2(n) : (n) <= 279 ? stbiw__zlib_huff3(n) : stbiw__zlib_huff4(n))
#define stbiw__zlib_huffb(n) ((n) <= 143 ? stbiw__zlib_huff1(n) : stbiw__zlib_huff2(n))

#define stbiw__ZHASH   16384

unsigned char * stbi_zlib_compress(unsigned char *data, int data_len, int *out_len, int quality)
{
   static unsigned short lengthc[] = { 3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258, 259 };
   static unsigned char  lengtheb[]= { 0,0,0,0,0,0,0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4,  4,  5,  5,  5,  5,  0 };
   static unsigned short distc[]   = { 1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577, 32768 };
   static unsigned char  disteb[]  = { 0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13 };
   unsigned int bitbuf=0;
   int i,j, bitcount=0;
   unsigned char *out = NULL;
   unsigned char **hash_table[stbiw__ZHASH]; // 64KB on the stack!
   if (quality < 5) quality = 5;

   stbiw__sbpush(out, 0x78);   // DEFLATE 32K window
   stbiw__sbpush(out, 0x5e);   // FLEVEL = 1
   stbiw__zlib_add(1,1);  // BFINAL = 1
   stbiw__zlib_add(1,2);  // BTYPE = 1 -- fixed huffman

   for (i=0; i < stbiw__ZHASH; ++i)
      hash_table[i] = NULL;

   i=0;
   while (i < data_len-3) {
      // hash next 3 bytes of data to be compressed
      int h = stbiw__zhash(data+i)&(stbiw__ZHASH-1), best=3;
      unsigned char *bestloc = 0;
      unsigned char **hlist = hash_table[h];
      int n = stbiw__sbcount(hlist);
      for (j=0; j < n; ++j) {
         if (hlist[j]-data > i-32768) { // if entry lies within window
            int d = stbiw__zlib_countm(hlist[j], data+i, data_len-i);
            if (d >= best) best=d,bestloc=hlist[j];
         }
      }
      // when hash table entry is too long, delete half the entries
      if (hash_table[h] && stbiw__sbn(hash_table[h]) == 2*quality) {
         STBIW_MEMMOVE(hash_table[h], hash_table[h]+quality, sizeof(hash_table[h][0])*quality);
         stbiw__sbn(hash_table[h]) = quality;
      }
      stbiw__sbpush(hash_table[h],data+i);

      if (bestloc) {
         // "lazy matching" - check match at *next* byte, and if it's better, do cur byte as literal
         h = stbiw__zhash(data+i+1)&(stbiw__ZHASH-1);
         hlist = hash_table[h];
         n = stbiw__sbcount(hlist);
         for (j=0; j < n; ++j) {
            if (hlist[j]-data > i-32767) {
               int e = stbiw__zlib_countm(hlist[j], data+i+1, data_len-i-1);
               if (e > best) { // if next match is better, bail on current match
                  bestloc = NULL;
                  break;
               }
            }
         }
      }

      if (bestloc) {
         int d = (int) (data+i - bestloc); // distance back
         STBIW_ASSERT(d <= 32767 && best <= 258);
         for (j=0; best > lengthc[j+1]-1; ++j);
         stbiw__zlib_huff(j+257);
         if (lengtheb[j]) stbiw__zlib_add(best - lengthc[j], lengtheb[j]);
         for (j=0; d > distc[j+1]-1; ++j);
         stbiw__zlib_add(stbiw__zlib_bitrev(j,5),5);
         if (disteb[j]) stbiw__zlib_add(d - distc[j], disteb[j]);
         i += best;
      } else {
         stbiw__zlib_huffb(data[i]);
         ++i;
      }
   }
   // write out final bytes
   for (;i < data_len; ++i)
      stbiw__zlib_huffb(data[i]);
   stbiw__zlib_huff(256); // end of block
   // pad with 0 bits to byte boundary
   while (bitcount)
      stbiw__zlib_add(0,1);

   for (i=0; i < stbiw__ZHASH; ++i)
      (void) stbiw__sbfree(hash_table[i]);

   {
      // compute adler32 on input
      unsigned int i=0, s1=1, s2=0, blocklen = data_len % 5552;
      int j=0;
      while (j < data_len) {
         for (i=0; i < blocklen; ++i) s1 += data[j+i], s2 += s1;
         s1 %= 65521, s2 %= 65521;
         j += blocklen;
         blocklen = 5552;
      }
      stbiw__sbpush(out, (unsigned char) (s2 >> 8));
      stbiw__sbpush(out, (unsigned char) s2);
      stbiw__sbpush(out, (unsigned char) (s1 >> 8));
      stbiw__sbpush(out, (unsigned char) s1);
   }
   *out_len = stbiw__sbn(out);
   // make returned pointer freeable
   STBIW_MEMMOVE(stbiw__sbraw(out), out, *out_len);
   return (unsigned char *) stbiw__sbraw(out);
}

unsigned int stbiw__crc32(unsigned char *buffer, int len)
{
   static unsigned int crc_table[256];
   unsigned int crc = ~0u;
   int i,j;
   if (crc_table[1] == 0)
      for(i=0; i < 256; i++)
         for (crc_table[i]=i, j=0; j < 8; ++j)
            crc_table[i] = (crc_table[i] >> 1) ^ (crc_table[i] & 1 ? 0xedb88320 : 0);
   for (i=0; i < len; ++i)
      crc = (crc >> 8) ^ crc_table[buffer[i] ^ (crc & 0xff)];
   return ~crc;
}

#define stbiw__wpng4(o,a,b,c,d) ((o)[0]=(unsigned char)(a),(o)[1]=(unsigned char)(b),(o)[2]=(unsigned char)(c),(o)[3]=(unsigned char)(d),(o)+=4)
#define stbiw__wp32(data,v) stbiw__wpng4(data, (v)>>24,(v)>>16,(v)>>8,(v));
#define stbiw__wptag(data,s) stbiw__wpng4(data, s[0],s[1],s[2],s[3])

static void stbiw__wpcrc(unsigned char **data, int len)
{
   unsigned int crc = stbiw__crc32(*data - len - 4, len+4);
   stbiw__wp32(*data, crc);
}

static unsigned char stbiw__paeth(int a, int b, int c)
{
   int p = a + b - c, pa = abs(p-a), pb = abs(p-b), pc = abs(p-c);
   if (pa <= pb && pa <= pc) return (unsigned char) a;
   if (pb <= pc) return (unsigned char) b;
   return (unsigned char) c;
}

unsigned char *stbi_write_png_to_mem(unsigned char *pixels, int stride_bytes, int x, int y, int n, int *out_len)
{
   int ctype[5] = { -1, 0, 4, 2, 6 };
   unsigned char sig[8] = { 137,80,78,71,13,10,26,10 };
   unsigned char *out,*o, *filt, *zlib;
   signed char *line_buffer;
   int i,j,k,p,zlen;

   if (stride_bytes == 0)
      stride_bytes = x * n;

   filt = (unsigned char *) STBIW_MALLOC((x*n+1) * y); if (!filt) return 0;
   line_buffer = (signed char *) STBIW_MALLOC(x * n); if (!line_buffer) { STBIW_FREE(filt); return 0; }
   for (j=0; j < y; ++j) {
      static int mapping[] = { 0,1,2,3,4 };
      static int firstmap[] = { 0,1,0,5,6 };
      int *mymap = j ? mapping : firstmap;
      int best = 0, bestval = 0x7fffffff;
      for (p=0; p < 2; ++p) {
         for (k= p?best:0; k < 5; ++k) {
            int type = mymap[k],est=0;
            unsigned char *z = pixels + stride_bytes*j;
            for (i=0; i < n; ++i)
               switch (type) {
                  case 0: line_buffer[i] = z[i]; break;
                  case 1: line_buffer[i] = z[i]; break;
                  case 2: line_buffer[i] = z[i] - z[i-stride_bytes]; break;
                  case 3: line_buffer[i] = z[i] - (z[i-stride_bytes]>>1); break;
                  case 4: line_buffer[i] = (signed char) (z[i] - stbiw__paeth(0,z[i-stride_bytes],0)); break;
                  case 5: line_buffer[i] = z[i]; break;
                  case 6: line_buffer[i] = z[i]; break;
               }
            for (i=n; i < x*n; ++i) {
               switch (type) {
                  case 0: line_buffer[i] = z[i]; break;
                  case 1: line_buffer[i] = z[i] - z[i-n]; break;
                  case 2: line_buffer[i] = z[i] - z[i-stride_bytes]; break;
                  case 3: line_buffer[i] = z[i] - ((z[i-n] + z[i-stride_bytes])>>1); break;
                  case 4: line_buffer[i] = z[i] - stbiw__paeth(z[i-n], z[i-stride_bytes], z[i-stride_bytes-n]); break;
                  case 5: line_buffer[i] = z[i] - (z[i-n]>>1); break;
                  case 6: line_buffer[i] = z[i] - stbiw__paeth(z[i-n], 0,0); break;
               }
            }
            if (p) break;
            for (i=0; i < x*n; ++i)
               est += abs((signed char) line_buffer[i]);
            if (est < bestval) { bestval = est; best = k; }
         }
      }
      // when we get here, best contains the filter type, and line_buffer contains the data
      filt[j*(x*n+1)] = (unsigned char) best;
      STBIW_MEMMOVE(filt+j*(x*n+1)+1, line_buffer, x*n);
   }
   STBIW_FREE(line_buffer);
   zlib = stbi_zlib_compress(filt, y*( x*n+1), &zlen, 8); // increase 8 to get smaller but use more memory
   STBIW_FREE(filt);
   if (!zlib) return 0;

   // each tag requires 12 bytes of overhead
   out = (unsigned char *) STBIW_MALLOC(8 + 12+13 + 12+zlen + 12);
   if (!out) return 0;
   *out_len = 8 + 12+13 + 12+zlen + 12;

   o=out;
   STBIW_MEMMOVE(o,sig,8); o+= 8;
   stbiw__wp32(o, 13); // header length
   stbiw__wptag(o, "IHDR");
   stbiw__wp32(o, x);
   stbiw__wp32(o, y);
   *o++ = 8;
   *o++ = (unsigned char) ctype[n];
   *o++ = 0;
   *o++ = 0;
   *o++ = 0;
   stbiw__wpcrc(&o,13);

   stbiw__wp32(o, zlen);
   stbiw__wptag(o, "IDAT");
   STBIW_MEMMOVE(o, zlib, zlen);
   o += zlen;
   STBIW_FREE(zlib);
   stbiw__wpcrc(&o, zlen);

   stbiw__wp32(o,0);
   stbiw__wptag(o, "IEND");
   stbiw__wpcrc(&o,0);

   STBIW_ASSERT(o == out + *out_len);

   return out;
}

int stbi_write_png(char const *filename, int x, int y, int comp, const void *data, int stride_bytes)
{
   FILE *f;
   int len;
   unsigned char *png = stbi_write_png_to_mem((unsigned char *) data, stride_bytes, x, y, comp, &len);
   if (!png) return 0;
   f = fopen(filename, "wb");
   if (!f) { STBIW_FREE(png); return 0; }
   fwrite(png, 1, len, f);
   fclose(f);
   STBIW_FREE(png);
   return 1;
}
#endif // STB_IMAGE_WRITE_IMPLEMENTATION

/* Revision history
      0.98 (2015-04-08)
             added STBIW_MALLOC, STBIW_ASSERT etc
      0.97 (2015-01-18)
             fixed HDR asserts, rewrote HDR rle logic
      0.96 (2015-01-17)
             add HDR output
             fix monochrome BMP
      0.95 (2014-08-17)
		       add monochrome TGA output
      0.94 (2014-05-31)
             rename private functions to avoid conflicts with stb_image.h
      0.93 (2014-05-27)
             warning fixes
      0.92 (2010-08-01)
             casts to unsigned char to fix warnings
      0.91 (2010-07-17)
             first public release
      0.90   first internal release
*/
/* stb_image_resize - v0.90 - public domain image resizing
   by Jorge L Rodriguez (@VinoBS) - 2014
   http://github.com/nothings/stb

   Written with emphasis on usability, portability, and efficiency. (No
   SIMD or threads, so it be easily outperformed by libs that use those.)
   Only scaling and translation is supported, no rotations or shears.
   Easy API downsamples w/Mitchell filter, upsamples w/cubic interpolation.

   COMPILING & LINKING
      In one C/C++ file that #includes this file, do this:
         #define STB_IMAGE_RESIZE_IMPLEMENTATION
      before the #include. That will create the implementation in that file.

   QUICKSTART
      stbir_resize_uint8(      input_pixels , in_w , in_h , 0,
                               output_pixels, out_w, out_h, 0, num_channels)
      stbir_resize_float(...)
      stbir_resize_uint8_srgb( input_pixels , in_w , in_h , 0,
                               output_pixels, out_w, out_h, 0,
                               num_channels , alpha_chan  , 0)
      stbir_resize_uint8_srgb_edgemode(
                               input_pixels , in_w , in_h , 0, 
                               output_pixels, out_w, out_h, 0, 
                               num_channels , alpha_chan  , 0, STBIR_EDGE_CLAMP)
                                                            // WRAP/REFLECT/ZERO

   FULL API
      See the "header file" section of the source for API documentation.

   ADDITIONAL DOCUMENTATION

      SRGB & FLOATING POINT REPRESENTATION
         The sRGB functions presume IEEE floating point. If you do not have
         IEEE floating point, define STBIR_NON_IEEE_FLOAT. This will use
         a slower implementation.

      MEMORY ALLOCATION
         The resize functions here perform a single memory allocation using
         malloc. To control the memory allocation, before the #include that
         triggers the implementation, do:

            #define STBIR_MALLOC(size,context) ...
            #define STBIR_FREE(ptr,context)   ...

         Each resize function makes exactly one call to malloc/free, so to use
         temp memory, store the temp memory in the context and return that.

      ASSERT
         Define STBIR_ASSERT(boolval) to override assert() and not use assert.h

      OPTIMIZATION
         Define STBIR_SATURATE_INT to compute clamp values in-range using
         integer operations instead of float operations. This may be faster
         on some platforms.

      DEFAULT FILTERS
         For functions which don't provide explicit control over what filters
         to use, you can change the compile-time defaults with

            #define STBIR_DEFAULT_FILTER_UPSAMPLE     STBIR_FILTER_something
            #define STBIR_DEFAULT_FILTER_DOWNSAMPLE   STBIR_FILTER_something

         See stbir_filter in the header-file section for the list of filters.

      NEW FILTERS
         A number of 1D filter kernels are used. For a list of
         supported filters see the stbir_filter enum. To add a new filter,
         write a filter function and add it to stbir__filter_info_table.

      PROGRESS
         For interactive use with slow resize operations, you can install
         a progress-report callback:

            #define STBIR_PROGRESS_REPORT(val)   some_func(val)

         The parameter val is a float which goes from 0 to 1 as progress is made.

         For example:

            static void my_progress_report(float progress);
            #define STBIR_PROGRESS_REPORT(val) my_progress_report(val)

            #define STB_IMAGE_RESIZE_IMPLEMENTATION
            #include "stb_image_resize.h"

            static void my_progress_report(float progress)
            {
               printf("Progress: %f%%\n", progress*100);
            }

      MAX CHANNELS
         If your image has more than 64 channels, define STBIR_MAX_CHANNELS
         to the max you'll have.

      ALPHA CHANNEL
         Most of the resizing functions provide the ability to control how
         the alpha channel of an image is processed. The important things
         to know about this:

         1. The best mathematically-behaved version of alpha to use is
         called "premultiplied alpha", in which the other color channels
         have had the alpha value multiplied in. If you use premultiplied
         alpha, linear filtering (such as image resampling done by this
         library, or performed in texture units on GPUs) does the "right
         thing". While premultiplied alpha is standard in the movie CGI
         industry, it is still uncommon in the videogame/real-time world.

         If you linearly filter non-premultiplied alpha, strange effects
         occur. (For example, the average of 1% opaque bright green
         and 99% opaque black produces 50% transparent dark green when
         non-premultiplied, whereas premultiplied it produces 50%
         transparent near-black. The former introduces green energy
         that doesn't exist in the source image.)

         2. Artists should not edit premultiplied-alpha images; artists
         want non-premultiplied alpha images. Thus, art tools generally output
         non-premultiplied alpha images.

         3. You will get best results in most cases by converting images
         to premultiplied alpha before processing them mathematically.

         4. If you pass the flag STBIR_FLAG_ALPHA_PREMULTIPLIED, the
         resizer does not do anything special for the alpha channel;
         it is resampled identically to other channels. This produces
         the correct results for premultiplied-alpha images, but produces
         less-than-ideal results for non-premultiplied-alpha images.

         5. If you do not pass the flag STBIR_FLAG_ALPHA_PREMULTIPLIED,
         then the resizer weights the contribution of input pixels
         based on their alpha values, or, equivalently, it multiplies
         the alpha value into the color channels, resamples, then divides
         by the resultant alpha value. Input pixels which have alpha=0 do
         not contribute at all to output pixels unless _all_ of the input
         pixels affecting that output pixel have alpha=0, in which case
         the result for that pixel is the same as it would be without
         STBIR_FLAG_ALPHA_PREMULTIPLIED. However, this is only true for
         input images in integer formats. For input images in float format,
         input pixels with alpha=0 have no effect, and output pixels
         which have alpha=0 will be 0 in all channels. (For float images,
         you can manually achieve the same result by adding a tiny epsilon
         value to the alpha channel of every image, and then subtracting
         or clamping it at the end.)

         6. You can suppress the behavior described in #5 and make
         all-0-alpha pixels have 0 in all channels by #defining
         STBIR_NO_ALPHA_EPSILON.

         7. You can separately control whether the alpha channel is
         interpreted as linear or affected by the colorspace. By default
         it is linear; you almost never want to apply the colorspace.
         (For example, graphics hardware does not apply sRGB conversion
         to the alpha channel.)

   ADDITIONAL CONTRIBUTORS
      Sean Barrett: API design, optimizations
         
   REVISIONS
      0.90 (2014-09-17) first released version

   LICENSE
      This software is in the public domain. Where that dedication is not
      recognized, you are granted a perpetual, irrevocable license to copy
      and modify this file as you see fit.

   TODO
      Don't decode all of the image data when only processing a partial tile
      Don't use full-width decode buffers when only processing a partial tile
      When processing wide images, break processing into tiles so data fits in L1 cache
      Installable filters?
      Resize that respects alpha test coverage
         (Reference code: FloatImage::alphaTestCoverage and FloatImage::scaleAlphaToCoverage:
         https://code.google.com/p/nvidia-texture-tools/source/browse/trunk/src/nvimage/FloatImage.cpp )
*/

#ifndef STBIR_INCLUDE_STB_IMAGE_RESIZE_H
#define STBIR_INCLUDE_STB_IMAGE_RESIZE_H

#ifdef _MSC_VER
typedef unsigned char  stbir_uint8;
typedef unsigned short stbir_uint16;
typedef unsigned int   stbir_uint32;
#else
#include <stdint.h>
typedef uint8_t  stbir_uint8;
typedef uint16_t stbir_uint16;
typedef uint32_t stbir_uint32;
#endif

#ifdef STB_IMAGE_RESIZE_STATIC
#define STBIRDEF static
#else
#ifdef __cplusplus
#define STBIRDEF extern "C"
#else
#define STBIRDEF extern
#endif
#endif


//////////////////////////////////////////////////////////////////////////////
//
// Easy-to-use API:
//
//     * "input pixels" points to an array of image data with 'num_channels' channels (e.g. RGB=3, RGBA=4)
//     * input_w is input image width (x-axis), input_h is input image height (y-axis)
//     * stride is the offset between successive rows of image data in memory, in bytes. you can
//       specify 0 to mean packed continuously in memory
//     * alpha channel is treated identically to other channels.
//     * colorspace is linear or sRGB as specified by function name
//     * returned result is 1 for success or 0 in case of an error.
//       #define STBIR_ASSERT() to trigger an assert on parameter validation errors.
//     * Memory required grows approximately linearly with input and output size, but with
//       discontinuities at input_w == output_w and input_h == output_h.
//     * These functions use a "default" resampling filter defined at compile time. To change the filter,
//       you can change the compile-time defaults by #defining STBIR_DEFAULT_FILTER_UPSAMPLE
//       and STBIR_DEFAULT_FILTER_DOWNSAMPLE, or you can use the medium-complexity API.

STBIRDEF int stbir_resize_uint8(     const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels);

STBIRDEF int stbir_resize_float(     const float *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           float *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels);


// The following functions interpret image data as gamma-corrected sRGB. 
// Specify STBIR_ALPHA_CHANNEL_NONE if you have no alpha channel,
// or otherwise provide the index of the alpha channel. Flags value
// of 0 will probably do the right thing if you're not sure what
// the flags mean.

#define STBIR_ALPHA_CHANNEL_NONE       -1

// Set this flag if your texture has premultiplied alpha. Otherwise, stbir will
// use alpha-weighted resampling (effectively premultiplying, resampling,
// then unpremultiplying).
#define STBIR_FLAG_ALPHA_PREMULTIPLIED    (1 << 0)
// The specified alpha channel should be handled as gamma-corrected value even
// when doing sRGB operations.
#define STBIR_FLAG_ALPHA_USES_COLORSPACE  (1 << 1)

STBIRDEF int stbir_resize_uint8_srgb(const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels, int alpha_channel, int flags);


typedef enum
{
    STBIR_EDGE_CLAMP   = 1,
    STBIR_EDGE_REFLECT = 2,
    STBIR_EDGE_WRAP    = 3,
    STBIR_EDGE_ZERO    = 4,
} stbir_edge;

// This function adds the ability to specify how requests to sample off the edge of the image are handled.
STBIRDEF int stbir_resize_uint8_srgb_edgemode(const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                                    unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                              int num_channels, int alpha_channel, int flags,
                                              stbir_edge edge_wrap_mode);

//////////////////////////////////////////////////////////////////////////////
//
// Medium-complexity API
//
// This extends the easy-to-use API as follows:
//
//     * Alpha-channel can be processed separately
//       * If alpha_channel is not STBIR_ALPHA_CHANNEL_NONE
//         * Alpha channel will not be gamma corrected (unless flags&STBIR_FLAG_GAMMA_CORRECT)
//         * Filters will be weighted by alpha channel (unless flags&STBIR_FLAG_ALPHA_PREMULTIPLIED)
//     * Filter can be selected explicitly
//     * uint16 image type
//     * sRGB colorspace available for all types
//     * context parameter for passing to STBIR_MALLOC

typedef enum
{
    STBIR_FILTER_DEFAULT      = 0,  // use same filter type that easy-to-use API chooses
    STBIR_FILTER_BOX          = 1,  // A trapezoid w/1-pixel wide ramps, same result as box for integer scale ratios
    STBIR_FILTER_TRIANGLE     = 2,  // On upsampling, produces same results as bilinear texture filtering
    STBIR_FILTER_CUBICBSPLINE = 3,  // The cubic b-spline (aka Mitchell-Netrevalli with B=1,C=0), gaussian-esque
    STBIR_FILTER_CATMULLROM   = 4,  // An interpolating cubic spline
    STBIR_FILTER_MITCHELL     = 5,  // Mitchell-Netrevalli filter with B=1/3, C=1/3
} stbir_filter;

typedef enum
{
    STBIR_COLORSPACE_LINEAR,
    STBIR_COLORSPACE_SRGB,

    STBIR_MAX_COLORSPACES,
} stbir_colorspace;

// The following functions are all identical except for the type of the image data

STBIRDEF int stbir_resize_uint8_generic( const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                               unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context);

STBIRDEF int stbir_resize_uint16_generic(const stbir_uint16 *input_pixels  , int input_w , int input_h , int input_stride_in_bytes,
                                               stbir_uint16 *output_pixels , int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context);

STBIRDEF int stbir_resize_float_generic( const float *input_pixels         , int input_w , int input_h , int input_stride_in_bytes,
                                               float *output_pixels        , int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context);



//////////////////////////////////////////////////////////////////////////////
//
// Full-complexity API
//
// This extends the medium API as follows:
//
//       * uint32 image type
//     * not typesafe
//     * separate filter types for each axis
//     * separate edge modes for each axis
//     * can specify scale explicitly for subpixel correctness
//     * can specify image source tile using texture coordinates

typedef enum
{
    STBIR_TYPE_UINT8 ,
    STBIR_TYPE_UINT16,
    STBIR_TYPE_UINT32,
    STBIR_TYPE_FLOAT ,

    STBIR_MAX_TYPES
} stbir_datatype;

STBIRDEF int stbir_resize(         const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context);

STBIRDEF int stbir_resize_subpixel(const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context,
                                   float x_scale, float y_scale,
                                   float x_offset, float y_offset);

STBIRDEF int stbir_resize_region(  const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context,
                                   float s0, float t0, float s1, float t1);
// (s0, t0) & (s1, t1) are the top-left and bottom right corner (uv addressing style: [0, 1]x[0, 1]) of a region of the input image to use.

//
//
////   end header file   /////////////////////////////////////////////////////
#endif // STBIR_INCLUDE_STB_IMAGE_RESIZE_H





#ifdef STB_IMAGE_RESIZE_IMPLEMENTATION

#ifndef STBIR_ASSERT
#include <assert.h>
#define STBIR_ASSERT(x) assert(x)
#endif

#ifdef STBIR_DEBUG
#define STBIR__DEBUG_ASSERT STBIR_ASSERT
#else
#define STBIR__DEBUG_ASSERT
#endif

// If you hit this it means I haven't done it yet.
#define STBIR__UNIMPLEMENTED(x) STBIR_ASSERT(!(x))

// For memset
#include <string.h>

#include <math.h>

#ifndef STBIR_MALLOC
#include <stdlib.h>
#define STBIR_MALLOC(size,c) malloc(size)
#define STBIR_FREE(ptr,c)    free(ptr)
#endif

#ifndef _MSC_VER
#ifdef __cplusplus
#define stbir__inline inline
#else
#define stbir__inline
#endif
#else
#define stbir__inline __forceinline
#endif


// should produce compiler error if size is wrong
typedef unsigned char stbir__validate_uint32[sizeof(stbir_uint32) == 4 ? 1 : -1];

#ifdef _MSC_VER
#define STBIR__NOTUSED(v)  (void)(v)
#else
#define STBIR__NOTUSED(v)  (void)sizeof(v)
#endif

#define STBIR__ARRAY_SIZE(a) (sizeof((a))/sizeof((a)[0]))

#ifndef STBIR_DEFAULT_FILTER_UPSAMPLE
#define STBIR_DEFAULT_FILTER_UPSAMPLE    STBIR_FILTER_CATMULLROM
#endif

#ifndef STBIR_DEFAULT_FILTER_DOWNSAMPLE
#define STBIR_DEFAULT_FILTER_DOWNSAMPLE  STBIR_FILTER_MITCHELL
#endif

#ifndef STBIR_PROGRESS_REPORT
#define STBIR_PROGRESS_REPORT(float_0_to_1)
#endif

#ifndef STBIR_MAX_CHANNELS
#define STBIR_MAX_CHANNELS 64
#endif

#if STBIR_MAX_CHANNELS > 65536
#error "Too many channels; STBIR_MAX_CHANNELS must be no more than 65536."
// because we store the indices in 16-bit variables
#endif

// This value is added to alpha just before premultiplication to avoid
// zeroing out color values. It is equivalent to 2^-80. If you don't want
// that behavior (it may interfere if you have floating point images with
// very small alpha values) then you can define STBIR_NO_ALPHA_EPSILON to
// disable it.
#ifndef STBIR_ALPHA_EPSILON
#define STBIR_ALPHA_EPSILON ((float)1 / (1 << 20) / (1 << 20) / (1 << 20) / (1 << 20))
#endif



#ifdef _MSC_VER
#define STBIR__UNUSED_PARAM(v)  (void)(v)
#else
#define STBIR__UNUSED_PARAM(v)  (void)sizeof(v)
#endif

// must match stbir_datatype
static unsigned char stbir__type_size[] = {
    1, // STBIR_TYPE_UINT8
    2, // STBIR_TYPE_UINT16
    4, // STBIR_TYPE_UINT32
    4, // STBIR_TYPE_FLOAT
};

// Kernel function centered at 0
typedef float (stbir__kernel_fn)(float x, float scale);
typedef float (stbir__support_fn)(float scale);

typedef struct
{
    stbir__kernel_fn* kernel;
    stbir__support_fn* support;
} stbir__filter_info;

// When upsampling, the contributors are which source pixels contribute.
// When downsampling, the contributors are which destination pixels are contributed to.
typedef struct
{
    int n0; // First contributing pixel
    int n1; // Last contributing pixel
} stbir__contributors;

typedef struct
{
    const void* input_data;
    int input_w;
    int input_h;
    int input_stride_bytes;

    void* output_data;
    int output_w;
    int output_h;
    int output_stride_bytes;

    float s0, t0, s1, t1;

    float horizontal_shift; // Units: output pixels
    float vertical_shift;   // Units: output pixels
    float horizontal_scale;
    float vertical_scale;

    int channels;
    int alpha_channel;
    stbir_uint32 flags;
    stbir_datatype type;
    stbir_filter horizontal_filter;
    stbir_filter vertical_filter;
    stbir_edge edge_horizontal;
    stbir_edge edge_vertical;
    stbir_colorspace colorspace;

    stbir__contributors* horizontal_contributors;
    float* horizontal_coefficients;

    stbir__contributors* vertical_contributors;
    float* vertical_coefficients;

    int decode_buffer_pixels;
    float* decode_buffer;

    float* horizontal_buffer;

    // cache these because ceil/floor are inexplicably showing up in profile
    int horizontal_coefficient_width;
    int vertical_coefficient_width;
    int horizontal_filter_pixel_width;
    int vertical_filter_pixel_width;
    int horizontal_filter_pixel_margin;
    int vertical_filter_pixel_margin;
    int horizontal_num_contributors;
    int vertical_num_contributors;

    int ring_buffer_length_bytes; // The length of an individual entry in the ring buffer. The total number of ring buffers is stbir__get_filter_pixel_width(filter)
    int ring_buffer_first_scanline;
    int ring_buffer_last_scanline;
    int ring_buffer_begin_index;
    float* ring_buffer;

    float* encode_buffer; // A temporary buffer to store floats so we don't lose precision while we do multiply-adds.

    int horizontal_contributors_size;
    int horizontal_coefficients_size;
    int vertical_contributors_size;
    int vertical_coefficients_size;
    int decode_buffer_size;
    int horizontal_buffer_size;
    int ring_buffer_size;
    int encode_buffer_size;
} stbir__info;

static stbir__inline int stbir__min(int a, int b)
{
    return a < b ? a : b;
}

static stbir__inline float stbir__saturate(float x)
{
    if (x < 0)
        return 0;

    if (x > 1)
        return 1;

    return x;
}

#ifdef STBIR_SATURATE_INT
static stbir__inline stbir_uint8 stbir__saturate8(int x)
{
    if ((unsigned int) x <= 255)
        return x;

    if (x < 0)
        return 0;

    return 255;
}

static stbir__inline stbir_uint16 stbir__saturate16(int x)
{
    if ((unsigned int) x <= 65535)
        return x;

    if (x < 0)
        return 0;

    return 65535;
}
#endif

static float stbir__srgb_uchar_to_linear_float[256] = {
    0.000000f, 0.000304f, 0.000607f, 0.000911f, 0.001214f, 0.001518f, 0.001821f, 0.002125f, 0.002428f, 0.002732f, 0.003035f,
    0.003347f, 0.003677f, 0.004025f, 0.004391f, 0.004777f, 0.005182f, 0.005605f, 0.006049f, 0.006512f, 0.006995f, 0.007499f,
    0.008023f, 0.008568f, 0.009134f, 0.009721f, 0.010330f, 0.010960f, 0.011612f, 0.012286f, 0.012983f, 0.013702f, 0.014444f,
    0.015209f, 0.015996f, 0.016807f, 0.017642f, 0.018500f, 0.019382f, 0.020289f, 0.021219f, 0.022174f, 0.023153f, 0.024158f,
    0.025187f, 0.026241f, 0.027321f, 0.028426f, 0.029557f, 0.030713f, 0.031896f, 0.033105f, 0.034340f, 0.035601f, 0.036889f,
    0.038204f, 0.039546f, 0.040915f, 0.042311f, 0.043735f, 0.045186f, 0.046665f, 0.048172f, 0.049707f, 0.051269f, 0.052861f,
    0.054480f, 0.056128f, 0.057805f, 0.059511f, 0.061246f, 0.063010f, 0.064803f, 0.066626f, 0.068478f, 0.070360f, 0.072272f,
    0.074214f, 0.076185f, 0.078187f, 0.080220f, 0.082283f, 0.084376f, 0.086500f, 0.088656f, 0.090842f, 0.093059f, 0.095307f,
    0.097587f, 0.099899f, 0.102242f, 0.104616f, 0.107023f, 0.109462f, 0.111932f, 0.114435f, 0.116971f, 0.119538f, 0.122139f,
    0.124772f, 0.127438f, 0.130136f, 0.132868f, 0.135633f, 0.138432f, 0.141263f, 0.144128f, 0.147027f, 0.149960f, 0.152926f,
    0.155926f, 0.158961f, 0.162029f, 0.165132f, 0.168269f, 0.171441f, 0.174647f, 0.177888f, 0.181164f, 0.184475f, 0.187821f,
    0.191202f, 0.194618f, 0.198069f, 0.201556f, 0.205079f, 0.208637f, 0.212231f, 0.215861f, 0.219526f, 0.223228f, 0.226966f,
    0.230740f, 0.234551f, 0.238398f, 0.242281f, 0.246201f, 0.250158f, 0.254152f, 0.258183f, 0.262251f, 0.266356f, 0.270498f,
    0.274677f, 0.278894f, 0.283149f, 0.287441f, 0.291771f, 0.296138f, 0.300544f, 0.304987f, 0.309469f, 0.313989f, 0.318547f,
    0.323143f, 0.327778f, 0.332452f, 0.337164f, 0.341914f, 0.346704f, 0.351533f, 0.356400f, 0.361307f, 0.366253f, 0.371238f,
    0.376262f, 0.381326f, 0.386430f, 0.391573f, 0.396755f, 0.401978f, 0.407240f, 0.412543f, 0.417885f, 0.423268f, 0.428691f,
    0.434154f, 0.439657f, 0.445201f, 0.450786f, 0.456411f, 0.462077f, 0.467784f, 0.473532f, 0.479320f, 0.485150f, 0.491021f,
    0.496933f, 0.502887f, 0.508881f, 0.514918f, 0.520996f, 0.527115f, 0.533276f, 0.539480f, 0.545725f, 0.552011f, 0.558340f,
    0.564712f, 0.571125f, 0.577581f, 0.584078f, 0.590619f, 0.597202f, 0.603827f, 0.610496f, 0.617207f, 0.623960f, 0.630757f,
    0.637597f, 0.644480f, 0.651406f, 0.658375f, 0.665387f, 0.672443f, 0.679543f, 0.686685f, 0.693872f, 0.701102f, 0.708376f,
    0.715694f, 0.723055f, 0.730461f, 0.737911f, 0.745404f, 0.752942f, 0.760525f, 0.768151f, 0.775822f, 0.783538f, 0.791298f,
    0.799103f, 0.806952f, 0.814847f, 0.822786f, 0.830770f, 0.838799f, 0.846873f, 0.854993f, 0.863157f, 0.871367f, 0.879622f,
    0.887923f, 0.896269f, 0.904661f, 0.913099f, 0.921582f, 0.930111f, 0.938686f, 0.947307f, 0.955974f, 0.964686f, 0.973445f,
    0.982251f, 0.991102f, 1.0f
};

static float stbir__srgb_to_linear(float f)
{
    if (f <= 0.04045f)
        return f / 12.92f;
    else
        return (float)pow((f + 0.055f) / 1.055f, 2.4f);
}

static float stbir__linear_to_srgb(float f)
{
    if (f <= 0.0031308f)
        return f * 12.92f;
    else
        return 1.055f * (float)pow(f, 1 / 2.4f) - 0.055f;
}

#ifndef STBIR_NON_IEEE_FLOAT
// From https://gist.github.com/rygorous/2203834

typedef union
{
    stbir_uint32 u;
    float f;
} stbir__FP32;

static const stbir_uint32 fp32_to_srgb8_tab4[104] = {
    0x0073000d, 0x007a000d, 0x0080000d, 0x0087000d, 0x008d000d, 0x0094000d, 0x009a000d, 0x00a1000d,
    0x00a7001a, 0x00b4001a, 0x00c1001a, 0x00ce001a, 0x00da001a, 0x00e7001a, 0x00f4001a, 0x0101001a,
    0x010e0033, 0x01280033, 0x01410033, 0x015b0033, 0x01750033, 0x018f0033, 0x01a80033, 0x01c20033,
    0x01dc0067, 0x020f0067, 0x02430067, 0x02760067, 0x02aa0067, 0x02dd0067, 0x03110067, 0x03440067,
    0x037800ce, 0x03df00ce, 0x044600ce, 0x04ad00ce, 0x051400ce, 0x057b00c5, 0x05dd00bc, 0x063b00b5,
    0x06970158, 0x07420142, 0x07e30130, 0x087b0120, 0x090b0112, 0x09940106, 0x0a1700fc, 0x0a9500f2,
    0x0b0f01cb, 0x0bf401ae, 0x0ccb0195, 0x0d950180, 0x0e56016e, 0x0f0d015e, 0x0fbc0150, 0x10630143,
    0x11070264, 0x1238023e, 0x1357021d, 0x14660201, 0x156601e9, 0x165a01d3, 0x174401c0, 0x182401af,
    0x18fe0331, 0x1a9602fe, 0x1c1502d2, 0x1d7e02ad, 0x1ed4028d, 0x201a0270, 0x21520256, 0x227d0240,
    0x239f0443, 0x25c003fe, 0x27bf03c4, 0x29a10392, 0x2b6a0367, 0x2d1d0341, 0x2ebe031f, 0x304d0300,
    0x31d105b0, 0x34a80555, 0x37520507, 0x39d504c5, 0x3c37048b, 0x3e7c0458, 0x40a8042a, 0x42bd0401,
    0x44c20798, 0x488e071e, 0x4c1c06b6, 0x4f76065d, 0x52a50610, 0x55ac05cc, 0x5892058f, 0x5b590559,
    0x5e0c0a23, 0x631c0980, 0x67db08f6, 0x6c55087f, 0x70940818, 0x74a007bd, 0x787d076c, 0x7c330723,
};
 
static stbir_uint8 stbir__linear_to_srgb_uchar(float in)
{
    static const stbir__FP32 almostone = { 0x3f7fffff }; // 1-eps
    static const stbir__FP32 minval = { (127-13) << 23 };
    stbir_uint32 tab,bias,scale,t;
    stbir__FP32 f;
 
    // Clamp to [2^(-13), 1-eps]; these two values map to 0 and 1, respectively.
    // The tests are carefully written so that NaNs map to 0, same as in the reference
    // implementation.
    if (!(in > minval.f)) // written this way to catch NaNs
        in = minval.f;
    if (in > almostone.f)
        in = almostone.f;
 
    // Do the table lookup and unpack bias, scale
    f.f = in;
    tab = fp32_to_srgb8_tab4[(f.u - minval.u) >> 20];
    bias = (tab >> 16) << 9;
    scale = tab & 0xffff;
 
    // Grab next-highest mantissa bits and perform linear interpolation
    t = (f.u >> 12) & 0xff;
    return (unsigned char) ((bias + scale*t) >> 16);
}

#else
// sRGB transition values, scaled by 1<<28
static int stbir__srgb_offset_to_linear_scaled[256] =
{
            0,     40738,    122216,    203693,    285170,    366648,    448125,    529603,
       611080,    692557,    774035,    855852,    942009,   1033024,   1128971,   1229926,
      1335959,   1447142,   1563542,   1685229,   1812268,   1944725,   2082664,   2226148,
      2375238,   2529996,   2690481,   2856753,   3028870,   3206888,   3390865,   3580856,
      3776916,   3979100,   4187460,   4402049,   4622919,   4850123,   5083710,   5323731,
      5570236,   5823273,   6082892,   6349140,   6622065,   6901714,   7188133,   7481369,
      7781466,   8088471,   8402427,   8723380,   9051372,   9386448,   9728650,  10078021,
     10434603,  10798439,  11169569,  11548036,  11933879,  12327139,  12727857,  13136073,
     13551826,  13975156,  14406100,  14844697,  15290987,  15745007,  16206795,  16676389,
     17153826,  17639142,  18132374,  18633560,  19142734,  19659934,  20185196,  20718552,
     21260042,  21809696,  22367554,  22933648,  23508010,  24090680,  24681686,  25281066,
     25888850,  26505076,  27129772,  27762974,  28404716,  29055026,  29713942,  30381490,
     31057708,  31742624,  32436272,  33138682,  33849884,  34569912,  35298800,  36036568,
     36783260,  37538896,  38303512,  39077136,  39859796,  40651528,  41452360,  42262316,
     43081432,  43909732,  44747252,  45594016,  46450052,  47315392,  48190064,  49074096,
     49967516,  50870356,  51782636,  52704392,  53635648,  54576432,  55526772,  56486700,
     57456236,  58435408,  59424248,  60422780,  61431036,  62449032,  63476804,  64514376,
     65561776,  66619028,  67686160,  68763192,  69850160,  70947088,  72053992,  73170912,
     74297864,  75434880,  76581976,  77739184,  78906536,  80084040,  81271736,  82469648,
     83677792,  84896192,  86124888,  87363888,  88613232,  89872928,  91143016,  92423512,
     93714432,  95015816,  96327688,  97650056,  98982952, 100326408, 101680440, 103045072,
    104420320, 105806224, 107202800, 108610064, 110028048, 111456776, 112896264, 114346544,
    115807632, 117279552, 118762328, 120255976, 121760536, 123276016, 124802440, 126339832,
    127888216, 129447616, 131018048, 132599544, 134192112, 135795792, 137410592, 139036528,
    140673648, 142321952, 143981456, 145652208, 147334208, 149027488, 150732064, 152447968,
    154175200, 155913792, 157663776, 159425168, 161197984, 162982240, 164777968, 166585184,
    168403904, 170234160, 172075968, 173929344, 175794320, 177670896, 179559120, 181458992,
    183370528, 185293776, 187228736, 189175424, 191133888, 193104112, 195086128, 197079968,
    199085648, 201103184, 203132592, 205173888, 207227120, 209292272, 211369392, 213458480,
    215559568, 217672656, 219797792, 221934976, 224084240, 226245600, 228419056, 230604656,
    232802400, 235012320, 237234432, 239468736, 241715280, 243974080, 246245120, 248528464,
    250824112, 253132064, 255452368, 257785040, 260130080, 262487520, 264857376, 267239664,
};

static stbir_uint8 stbir__linear_to_srgb_uchar(float f)
{
    int x = (int) (f * (1 << 28)); // has headroom so you don't need to clamp
    int v = 0;
    int i;

    // Refine the guess with a short binary search.
    i = v + 128; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +  64; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +  32; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +  16; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +   8; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +   4; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +   2; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;
    i = v +   1; if (x >= stbir__srgb_offset_to_linear_scaled[i]) v = i;

    return (stbir_uint8) v;
}
#endif

static float stbir__filter_trapezoid(float x, float scale)
{
    float halfscale = scale / 2;
    float t = 0.5f + halfscale;
    STBIR__DEBUG_ASSERT(scale <= 1);

    x = (float)fabs(x);

    if (x >= t)
        return 0;
    else
    {
        float r = 0.5f - halfscale;
        if (x <= r)
            return 1;
        else
            return (t - x) / scale;
    }
}

static float stbir__support_trapezoid(float scale)
{
    STBIR__DEBUG_ASSERT(scale <= 1);
    return 0.5f + scale / 2;
}

static float stbir__filter_triangle(float x, float s)
{
    STBIR__UNUSED_PARAM(s);

    x = (float)fabs(x);

    if (x <= 1.0f)
        return 1 - x;
    else
        return 0;
}

static float stbir__filter_cubic(float x, float s)
{
    STBIR__UNUSED_PARAM(s);

    x = (float)fabs(x);

    if (x < 1.0f)
        return (4 + x*x*(3*x - 6))/6;
    else if (x < 2.0f)
        return (8 + x*(-12 + x*(6 - x)))/6;

    return (0.0f);
}

static float stbir__filter_catmullrom(float x, float s)
{
    STBIR__UNUSED_PARAM(s);

    x = (float)fabs(x);

    if (x < 1.0f)
        return 1 - x*x*(2.5f - 1.5f*x);
    else if (x < 2.0f)
        return 2 - x*(4 + x*(0.5f*x - 2.5f));

    return (0.0f);
}

static float stbir__filter_mitchell(float x, float s)
{
    STBIR__UNUSED_PARAM(s);

    x = (float)fabs(x);

    if (x < 1.0f)
        return (16 + x*x*(21 * x - 36))/18;
    else if (x < 2.0f)
        return (32 + x*(-60 + x*(36 - 7*x)))/18;

    return (0.0f);
}

static float stbir__support_zero(float s)
{
    STBIR__UNUSED_PARAM(s);
    return 0;
}

static float stbir__support_one(float s)
{
    STBIR__UNUSED_PARAM(s);
    return 1;
}

static float stbir__support_two(float s)
{
    STBIR__UNUSED_PARAM(s);
    return 2;
}

static stbir__filter_info stbir__filter_info_table[] = {
        { NULL,                     stbir__support_zero },
        { stbir__filter_trapezoid,  stbir__support_trapezoid },
        { stbir__filter_triangle,   stbir__support_one },
        { stbir__filter_cubic,      stbir__support_two },
        { stbir__filter_catmullrom, stbir__support_two },
        { stbir__filter_mitchell,   stbir__support_two },
};

stbir__inline static int stbir__use_upsampling(float ratio)
{
    return ratio > 1;
}

stbir__inline static int stbir__use_width_upsampling(stbir__info* stbir_info)
{
    return stbir__use_upsampling(stbir_info->horizontal_scale);
}

stbir__inline static int stbir__use_height_upsampling(stbir__info* stbir_info)
{
    return stbir__use_upsampling(stbir_info->vertical_scale);
}

// This is the maximum number of input samples that can affect an output sample
// with the given filter
static int stbir__get_filter_pixel_width(stbir_filter filter, float scale)
{
    STBIR_ASSERT(filter != 0);
    STBIR_ASSERT(filter < STBIR__ARRAY_SIZE(stbir__filter_info_table));

    if (stbir__use_upsampling(scale))
        return (int)ceil(stbir__filter_info_table[filter].support(1/scale) * 2);
    else
        return (int)ceil(stbir__filter_info_table[filter].support(scale) * 2 / scale);
}

// This is how much to expand buffers to account for filters seeking outside
// the image boundaries.
static int stbir__get_filter_pixel_margin(stbir_filter filter, float scale)
{
    return stbir__get_filter_pixel_width(filter, scale) / 2;
}

static int stbir__get_coefficient_width(stbir_filter filter, float scale)
{
    if (stbir__use_upsampling(scale))
        return (int)ceil(stbir__filter_info_table[filter].support(1 / scale) * 2);
    else
        return (int)ceil(stbir__filter_info_table[filter].support(scale) * 2);
}

static int stbir__get_contributors(float scale, stbir_filter filter, int input_size, int output_size)
{
    if (stbir__use_upsampling(scale))
        return output_size;
    else
        return (input_size + stbir__get_filter_pixel_margin(filter, scale) * 2);
}

static int stbir__get_total_horizontal_coefficients(stbir__info* info)
{
    return info->horizontal_num_contributors
         * stbir__get_coefficient_width      (info->horizontal_filter, info->horizontal_scale);
}

static int stbir__get_total_vertical_coefficients(stbir__info* info)
{
    return info->vertical_num_contributors
         * stbir__get_coefficient_width      (info->vertical_filter, info->vertical_scale);
}

static stbir__contributors* stbir__get_contributor(stbir__contributors* contributors, int n)
{
    return &contributors[n];
}

// For perf reasons this code is duplicated in stbir__resample_horizontal_upsample/downsample,
// if you change it here change it there too.
static float* stbir__get_coefficient(float* coefficients, stbir_filter filter, float scale, int n, int c)
{
    int width = stbir__get_coefficient_width(filter, scale);
    return &coefficients[width*n + c];
}

static int stbir__edge_wrap_slow(stbir_edge edge, int n, int max)
{
    switch (edge)
    {
    case STBIR_EDGE_ZERO:
        return 0; // we'll decode the wrong pixel here, and then overwrite with 0s later

    case STBIR_EDGE_CLAMP:
        if (n < 0)
            return 0;

        if (n >= max)
            return max - 1;

        return n; // NOTREACHED

    case STBIR_EDGE_REFLECT:
    {
        if (n < 0)
        {
            if (n < max)
                return -n;
            else
                return max - 1;
        }

        if (n >= max)
        {
            int max2 = max * 2;
            if (n >= max2)
                return 0;
            else
                return max2 - n - 1;
        }

        return n; // NOTREACHED
    }

    case STBIR_EDGE_WRAP:
        if (n >= 0)
            return (n % max);
        else
        {
            int m = (-n) % max;

            if (m != 0)
                m = max - m;

            return (m);
        }
        return n;  // NOTREACHED

    default:
        STBIR__UNIMPLEMENTED("Unimplemented edge type");
        return 0;
    }
}

stbir__inline static int stbir__edge_wrap(stbir_edge edge, int n, int max)
{
    // avoid per-pixel switch
    if (n >= 0 && n < max)
        return n;
    return stbir__edge_wrap_slow(edge, n, max);
}

// What input pixels contribute to this output pixel?
static void stbir__calculate_sample_range_upsample(int n, float out_filter_radius, float scale_ratio, float out_shift, int* in_first_pixel, int* in_last_pixel, float* in_center_of_out)
{
    float out_pixel_center = (float)n + 0.5f;
    float out_pixel_influence_lowerbound = out_pixel_center - out_filter_radius;
    float out_pixel_influence_upperbound = out_pixel_center + out_filter_radius;

    float in_pixel_influence_lowerbound = (out_pixel_influence_lowerbound + out_shift) / scale_ratio;
    float in_pixel_influence_upperbound = (out_pixel_influence_upperbound + out_shift) / scale_ratio;

    *in_center_of_out = (out_pixel_center + out_shift) / scale_ratio;
    *in_first_pixel = (int)(floor(in_pixel_influence_lowerbound + 0.5));
    *in_last_pixel = (int)(floor(in_pixel_influence_upperbound - 0.5));
}

// What output pixels does this input pixel contribute to?
static void stbir__calculate_sample_range_downsample(int n, float in_pixels_radius, float scale_ratio, float out_shift, int* out_first_pixel, int* out_last_pixel, float* out_center_of_in)
{
    float in_pixel_center = (float)n + 0.5f;
    float in_pixel_influence_lowerbound = in_pixel_center - in_pixels_radius;
    float in_pixel_influence_upperbound = in_pixel_center + in_pixels_radius;

    float out_pixel_influence_lowerbound = in_pixel_influence_lowerbound * scale_ratio - out_shift;
    float out_pixel_influence_upperbound = in_pixel_influence_upperbound * scale_ratio - out_shift;

    *out_center_of_in = in_pixel_center * scale_ratio - out_shift;
    *out_first_pixel = (int)(floor(out_pixel_influence_lowerbound + 0.5));
    *out_last_pixel = (int)(floor(out_pixel_influence_upperbound - 0.5));
}

static void stbir__calculate_coefficients_upsample(stbir__info* stbir_info, stbir_filter filter, float scale, int in_first_pixel, int in_last_pixel, float in_center_of_out, stbir__contributors* contributor, float* coefficient_group)
{
    int i;
    float total_filter = 0;
    float filter_scale;

    STBIR__DEBUG_ASSERT(in_last_pixel - in_first_pixel <= (int)ceil(stbir__filter_info_table[filter].support(1/scale) * 2)); // Taken directly from stbir__get_coefficient_width() which we can't call because we don't know if we're horizontal or vertical.

    contributor->n0 = in_first_pixel;
    contributor->n1 = in_last_pixel;

    STBIR__DEBUG_ASSERT(contributor->n1 >= contributor->n0);

    for (i = 0; i <= in_last_pixel - in_first_pixel; i++)
    {
        float in_pixel_center = (float)(i + in_first_pixel) + 0.5f;
        coefficient_group[i] = stbir__filter_info_table[filter].kernel(in_center_of_out - in_pixel_center, 1 / scale);

        // If the coefficient is zero, skip it. (Don't do the <0 check here, we want the influence of those outside pixels.)
        if (i == 0 && !coefficient_group[i])
        {
            contributor->n0 = ++in_first_pixel;
            i--;
            continue;
        }

        total_filter += coefficient_group[i];
    }

    STBIR__DEBUG_ASSERT(stbir__filter_info_table[filter].kernel((float)(in_last_pixel + 1) + 0.5f - in_center_of_out, 1/scale) == 0);

    STBIR__DEBUG_ASSERT(total_filter > 0.9);
    STBIR__DEBUG_ASSERT(total_filter < 1.1f); // Make sure it's not way off.

    // Make sure the sum of all coefficients is 1.
    filter_scale = 1 / total_filter;

    for (i = 0; i <= in_last_pixel - in_first_pixel; i++)
        coefficient_group[i] *= filter_scale;

    for (i = in_last_pixel - in_first_pixel; i >= 0; i--)
    {
        if (coefficient_group[i])
            break;

        // This line has no weight. We can skip it.
        contributor->n1 = contributor->n0 + i - 1;
    }
}

static void stbir__calculate_coefficients_downsample(stbir__info* stbir_info, stbir_filter filter, float scale_ratio, int out_first_pixel, int out_last_pixel, float out_center_of_in, stbir__contributors* contributor, float* coefficient_group)
{
    int i;

     STBIR__DEBUG_ASSERT(out_last_pixel - out_first_pixel <= (int)ceil(stbir__filter_info_table[filter].support(scale_ratio) * 2)); // Taken directly from stbir__get_coefficient_width() which we can't call because we don't know if we're horizontal or vertical.

    contributor->n0 = out_first_pixel;
    contributor->n1 = out_last_pixel;

    STBIR__DEBUG_ASSERT(contributor->n1 >= contributor->n0);

    for (i = 0; i <= out_last_pixel - out_first_pixel; i++)
    {
        float out_pixel_center = (float)(i + out_first_pixel) + 0.5f;
        float x = out_pixel_center - out_center_of_in;
        coefficient_group[i] = stbir__filter_info_table[filter].kernel(x, scale_ratio) * scale_ratio;
    }

    STBIR__DEBUG_ASSERT(stbir__filter_info_table[filter].kernel((float)(out_last_pixel + 1) + 0.5f - out_center_of_in, scale_ratio) == 0);

    for (i = out_last_pixel - out_first_pixel; i >= 0; i--)
    {
        if (coefficient_group[i])
            break;

        // This line has no weight. We can skip it.
        contributor->n1 = contributor->n0 + i - 1;
    }
}

static void stbir__normalize_downsample_coefficients(stbir__info* stbir_info, stbir__contributors* contributors, float* coefficients, stbir_filter filter, float scale_ratio, float shift, int input_size, int output_size)
{
    int num_contributors = stbir__get_contributors(scale_ratio, filter, input_size, output_size);
    int num_coefficients = stbir__get_coefficient_width(filter, scale_ratio);
    int i, j;
    int skip;

    for (i = 0; i < output_size; i++)
    {
        float scale;
        float total = 0;

        for (j = 0; j < num_contributors; j++)
        {
            if (i >= contributors[j].n0 && i <= contributors[j].n1)
            {
                float coefficient = *stbir__get_coefficient(coefficients, filter, scale_ratio, j, i - contributors[j].n0);
                total += coefficient;
            }
            else if (i < contributors[j].n0)
                break;
        }

        STBIR__DEBUG_ASSERT(total > 0.9f);
        STBIR__DEBUG_ASSERT(total < 1.1f);

        scale = 1 / total;

        for (j = 0; j < num_contributors; j++)
        {
            if (i >= contributors[j].n0 && i <= contributors[j].n1)
                *stbir__get_coefficient(coefficients, filter, scale_ratio, j, i - contributors[j].n0) *= scale;
            else if (i < contributors[j].n0)
                break;
        }
    }

    // Optimize: Skip zero coefficients and contributions outside of image bounds.
    // Do this after normalizing because normalization depends on the n0/n1 values.
    for (j = 0; j < num_contributors; j++)
    {
        int range, max, width;

        skip = 0;
        while (*stbir__get_coefficient(coefficients, filter, scale_ratio, j, skip) == 0)
            skip++;

        contributors[j].n0 += skip;

        while (contributors[j].n0 < 0)
        {
            contributors[j].n0++;
            skip++;
        }

        range = contributors[j].n1 - contributors[j].n0 + 1;
        max = stbir__min(num_coefficients, range);

        width = stbir__get_coefficient_width(filter, scale_ratio);
        for (i = 0; i < max; i++)
        {
            if (i + skip >= width)
                break;

            *stbir__get_coefficient(coefficients, filter, scale_ratio, j, i) = *stbir__get_coefficient(coefficients, filter, scale_ratio, j, i + skip);
        }

        continue;
    }

    // Using min to avoid writing into invalid pixels.
    for (i = 0; i < num_contributors; i++)
        contributors[i].n1 = stbir__min(contributors[i].n1, output_size - 1);
}

// Each scan line uses the same kernel values so we should calculate the kernel
// values once and then we can use them for every scan line.
static void stbir__calculate_filters(stbir__info* stbir_info, stbir__contributors* contributors, float* coefficients, stbir_filter filter, float scale_ratio, float shift, int input_size, int output_size)
{
    int n;
    int total_contributors = stbir__get_contributors(scale_ratio, filter, input_size, output_size);

    if (stbir__use_upsampling(scale_ratio))
    {
        float out_pixels_radius = stbir__filter_info_table[filter].support(1 / scale_ratio) * scale_ratio;

        // Looping through out pixels
        for (n = 0; n < total_contributors; n++)
        {
            float in_center_of_out; // Center of the current out pixel in the in pixel space
            int in_first_pixel, in_last_pixel;

            stbir__calculate_sample_range_upsample(n, out_pixels_radius, scale_ratio, shift, &in_first_pixel, &in_last_pixel, &in_center_of_out);

            stbir__calculate_coefficients_upsample(stbir_info, filter, scale_ratio, in_first_pixel, in_last_pixel, in_center_of_out, stbir__get_contributor(contributors, n), stbir__get_coefficient(coefficients, filter, scale_ratio, n, 0));
        }
    }
    else
    {
        float in_pixels_radius = stbir__filter_info_table[filter].support(scale_ratio) / scale_ratio;

        // Looping through in pixels
        for (n = 0; n < total_contributors; n++)
        {
            float out_center_of_in; // Center of the current out pixel in the in pixel space
            int out_first_pixel, out_last_pixel;
            int n_adjusted = n - stbir__get_filter_pixel_margin(filter, scale_ratio);

            stbir__calculate_sample_range_downsample(n_adjusted, in_pixels_radius, scale_ratio, shift, &out_first_pixel, &out_last_pixel, &out_center_of_in);

            stbir__calculate_coefficients_downsample(stbir_info, filter, scale_ratio, out_first_pixel, out_last_pixel, out_center_of_in, stbir__get_contributor(contributors, n), stbir__get_coefficient(coefficients, filter, scale_ratio, n, 0));
        }

        stbir__normalize_downsample_coefficients(stbir_info, contributors, coefficients, filter, scale_ratio, shift, input_size, output_size);
    }
}

static float* stbir__get_decode_buffer(stbir__info* stbir_info)
{
    // The 0 index of the decode buffer starts after the margin. This makes
    // it okay to use negative indexes on the decode buffer.
    return &stbir_info->decode_buffer[stbir_info->horizontal_filter_pixel_margin * stbir_info->channels];
}

#define STBIR__DECODE(type, colorspace) ((type) * (STBIR_MAX_COLORSPACES) + (colorspace))

static void stbir__decode_scanline(stbir__info* stbir_info, int n)
{
    int c;
    int channels = stbir_info->channels;
    int alpha_channel = stbir_info->alpha_channel;
    int type = stbir_info->type;
    int colorspace = stbir_info->colorspace;
    int input_w = stbir_info->input_w;
    int input_stride_bytes = stbir_info->input_stride_bytes;
    float* decode_buffer = stbir__get_decode_buffer(stbir_info);
    stbir_edge edge_horizontal = stbir_info->edge_horizontal;
    stbir_edge edge_vertical = stbir_info->edge_vertical;
    int in_buffer_row_offset = stbir__edge_wrap(edge_vertical, n, stbir_info->input_h) * input_stride_bytes;
    const void* input_data = (char *) stbir_info->input_data + in_buffer_row_offset;
    int max_x = input_w + stbir_info->horizontal_filter_pixel_margin;
    int decode = STBIR__DECODE(type, colorspace);

    int x = -stbir_info->horizontal_filter_pixel_margin;

    // special handling for STBIR_EDGE_ZERO because it needs to return an item that doesn't appear in the input,
    // and we want to avoid paying overhead on every pixel if not STBIR_EDGE_ZERO
    if (edge_vertical == STBIR_EDGE_ZERO && (n < 0 || n >= stbir_info->input_h))
    {
        for (; x < max_x; x++)
            for (c = 0; c < channels; c++)
                decode_buffer[x*channels + c] = 0;
        return;
    }

    switch (decode)
    {
    case STBIR__DECODE(STBIR_TYPE_UINT8, STBIR_COLORSPACE_LINEAR):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = ((float)((const unsigned char*)input_data)[input_pixel_index + c]) / 255;
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_UINT8, STBIR_COLORSPACE_SRGB):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = stbir__srgb_uchar_to_linear_float[((const unsigned char*)input_data)[input_pixel_index + c]];

            if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                decode_buffer[decode_pixel_index + alpha_channel] = ((float)((const unsigned char*)input_data)[input_pixel_index + alpha_channel]) / 255;
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_UINT16, STBIR_COLORSPACE_LINEAR):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = ((float)((const unsigned short*)input_data)[input_pixel_index + c]) / 65535;
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_UINT16, STBIR_COLORSPACE_SRGB):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = stbir__srgb_to_linear(((float)((const unsigned short*)input_data)[input_pixel_index + c]) / 65535);

            if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                decode_buffer[decode_pixel_index + alpha_channel] = ((float)((const unsigned short*)input_data)[input_pixel_index + alpha_channel]) / 65535;
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_UINT32, STBIR_COLORSPACE_LINEAR):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = (float)(((double)((const unsigned int*)input_data)[input_pixel_index + c]) / 4294967295);
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_UINT32, STBIR_COLORSPACE_SRGB):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = stbir__srgb_to_linear((float)(((double)((const unsigned int*)input_data)[input_pixel_index + c]) / 4294967295));

            if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                decode_buffer[decode_pixel_index + alpha_channel] = (float)(((double)((const unsigned int*)input_data)[input_pixel_index + alpha_channel]) / 4294967295);
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_FLOAT, STBIR_COLORSPACE_LINEAR):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = ((const float*)input_data)[input_pixel_index + c];
        }
        break;

    case STBIR__DECODE(STBIR_TYPE_FLOAT, STBIR_COLORSPACE_SRGB):
        for (; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;
            int input_pixel_index = stbir__edge_wrap(edge_horizontal, x, input_w) * channels;
            for (c = 0; c < channels; c++)
                decode_buffer[decode_pixel_index + c] = stbir__srgb_to_linear(((const float*)input_data)[input_pixel_index + c]);

            if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                decode_buffer[decode_pixel_index + alpha_channel] = ((const float*)input_data)[input_pixel_index + alpha_channel];
        }

        break;

    default:
        STBIR__UNIMPLEMENTED("Unknown type/colorspace/channels combination.");
        break;
    }

    if (!(stbir_info->flags & STBIR_FLAG_ALPHA_PREMULTIPLIED))
    {
        for (x = -stbir_info->horizontal_filter_pixel_margin; x < max_x; x++)
        {
            int decode_pixel_index = x * channels;

            // If the alpha value is 0 it will clobber the color values. Make sure it's not.
            float alpha = decode_buffer[decode_pixel_index + alpha_channel];
#ifndef STBIR_NO_ALPHA_EPSILON
            if (stbir_info->type != STBIR_TYPE_FLOAT) {
                alpha += STBIR_ALPHA_EPSILON;
                decode_buffer[decode_pixel_index + alpha_channel] = alpha;
            }
#endif
            for (c = 0; c < channels; c++)
            {
                if (c == alpha_channel)
                    continue;

                decode_buffer[decode_pixel_index + c] *= alpha;
            }
        }
    }

    if (edge_horizontal == STBIR_EDGE_ZERO)
    {
        for (x = -stbir_info->horizontal_filter_pixel_margin; x < 0; x++)
        {
            for (c = 0; c < channels; c++)
                decode_buffer[x*channels + c] = 0;
        }
        for (x = input_w; x < max_x; x++)
        {
            for (c = 0; c < channels; c++)
                decode_buffer[x*channels + c] = 0;
        }
    }
}

static float* stbir__get_ring_buffer_entry(float* ring_buffer, int index, int ring_buffer_length)
{
    return &ring_buffer[index * ring_buffer_length];
}

static float* stbir__add_empty_ring_buffer_entry(stbir__info* stbir_info, int n)
{
    int ring_buffer_index;
    float* ring_buffer;

    if (stbir_info->ring_buffer_begin_index < 0)
    {
        ring_buffer_index = stbir_info->ring_buffer_begin_index = 0;
        stbir_info->ring_buffer_first_scanline = n;
    }
    else
    {
        ring_buffer_index = (stbir_info->ring_buffer_begin_index + (stbir_info->ring_buffer_last_scanline - stbir_info->ring_buffer_first_scanline) + 1) % stbir_info->vertical_filter_pixel_width;
        STBIR__DEBUG_ASSERT(ring_buffer_index != stbir_info->ring_buffer_begin_index);
    }

    ring_buffer = stbir__get_ring_buffer_entry(stbir_info->ring_buffer, ring_buffer_index, stbir_info->ring_buffer_length_bytes / sizeof(float));
    memset(ring_buffer, 0, stbir_info->ring_buffer_length_bytes);

    stbir_info->ring_buffer_last_scanline = n;

    return ring_buffer;
}


static void stbir__resample_horizontal_upsample(stbir__info* stbir_info, int n, float* output_buffer)
{
    int x, k;
    int output_w = stbir_info->output_w;
    int kernel_pixel_width = stbir_info->horizontal_filter_pixel_width;
    int channels = stbir_info->channels;
    float* decode_buffer = stbir__get_decode_buffer(stbir_info);
    stbir__contributors* horizontal_contributors = stbir_info->horizontal_contributors;
    float* horizontal_coefficients = stbir_info->horizontal_coefficients;
    int coefficient_width = stbir_info->horizontal_coefficient_width;

    for (x = 0; x < output_w; x++)
    {
        int n0 = horizontal_contributors[x].n0;
        int n1 = horizontal_contributors[x].n1;

        int out_pixel_index = x * channels;
        int coefficient_group = coefficient_width * x;
        int coefficient_counter = 0;

        STBIR__DEBUG_ASSERT(n1 >= n0);
        STBIR__DEBUG_ASSERT(n0 >= -stbir_info->horizontal_filter_pixel_margin);
        STBIR__DEBUG_ASSERT(n1 >= -stbir_info->horizontal_filter_pixel_margin);
        STBIR__DEBUG_ASSERT(n0 < stbir_info->input_w + stbir_info->horizontal_filter_pixel_margin);
        STBIR__DEBUG_ASSERT(n1 < stbir_info->input_w + stbir_info->horizontal_filter_pixel_margin);

        switch (channels) {
            case 1:
                for (k = n0; k <= n1; k++)
                {
                    int in_pixel_index = k * 1;
                    float coefficient = horizontal_coefficients[coefficient_group + coefficient_counter++];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                }
                break;
            case 2:
                for (k = n0; k <= n1; k++)
                {
                    int in_pixel_index = k * 2;
                    float coefficient = horizontal_coefficients[coefficient_group + coefficient_counter++];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                }
                break;
            case 3:
                for (k = n0; k <= n1; k++)
                {
                    int in_pixel_index = k * 3;
                    float coefficient = horizontal_coefficients[coefficient_group + coefficient_counter++];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                    output_buffer[out_pixel_index + 2] += decode_buffer[in_pixel_index + 2] * coefficient;
                }
                break;
            case 4:
                for (k = n0; k <= n1; k++)
                {
                    int in_pixel_index = k * 4;
                    float coefficient = horizontal_coefficients[coefficient_group + coefficient_counter++];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                    output_buffer[out_pixel_index + 2] += decode_buffer[in_pixel_index + 2] * coefficient;
                    output_buffer[out_pixel_index + 3] += decode_buffer[in_pixel_index + 3] * coefficient;
                }
                break;
            default:
                for (k = n0; k <= n1; k++)
                {
                    int in_pixel_index = k * channels;
                    float coefficient = horizontal_coefficients[coefficient_group + coefficient_counter++];
                    int c;
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    for (c = 0; c < channels; c++)
                        output_buffer[out_pixel_index + c] += decode_buffer[in_pixel_index + c] * coefficient;
                }
                break;
        }
    }
}

static void stbir__resample_horizontal_downsample(stbir__info* stbir_info, int n, float* output_buffer)
{
    int x, k;
    int input_w = stbir_info->input_w;
    int output_w = stbir_info->output_w;
    int kernel_pixel_width = stbir_info->horizontal_filter_pixel_width;
    int channels = stbir_info->channels;
    float* decode_buffer = stbir__get_decode_buffer(stbir_info);
    stbir__contributors* horizontal_contributors = stbir_info->horizontal_contributors;
    float* horizontal_coefficients = stbir_info->horizontal_coefficients;
    int coefficient_width = stbir_info->horizontal_coefficient_width;
    int filter_pixel_margin = stbir_info->horizontal_filter_pixel_margin;
    int max_x = input_w + filter_pixel_margin * 2;

    STBIR__DEBUG_ASSERT(!stbir__use_width_upsampling(stbir_info));

    switch (channels) {
        case 1:
            for (x = 0; x < max_x; x++)
            {
                int n0 = horizontal_contributors[x].n0;
                int n1 = horizontal_contributors[x].n1;

                int in_x = x - filter_pixel_margin;
                int in_pixel_index = in_x * 1;
                int max_n = n1;
                int coefficient_group = coefficient_width * x;

                for (k = n0; k <= max_n; k++)
                {
                    int out_pixel_index = k * 1;
                    float coefficient = horizontal_coefficients[coefficient_group + k - n0];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                }
            }
            break;

        case 2:
            for (x = 0; x < max_x; x++)
            {
                int n0 = horizontal_contributors[x].n0;
                int n1 = horizontal_contributors[x].n1;

                int in_x = x - filter_pixel_margin;
                int in_pixel_index = in_x * 2;
                int max_n = n1;
                int coefficient_group = coefficient_width * x;

                for (k = n0; k <= max_n; k++)
                {
                    int out_pixel_index = k * 2;
                    float coefficient = horizontal_coefficients[coefficient_group + k - n0];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                }
            }
            break;

        case 3:
            for (x = 0; x < max_x; x++)
            {
                int n0 = horizontal_contributors[x].n0;
                int n1 = horizontal_contributors[x].n1;

                int in_x = x - filter_pixel_margin;
                int in_pixel_index = in_x * 3;
                int max_n = n1;
                int coefficient_group = coefficient_width * x;

                for (k = n0; k <= max_n; k++)
                {
                    int out_pixel_index = k * 3;
                    float coefficient = horizontal_coefficients[coefficient_group + k - n0];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                    output_buffer[out_pixel_index + 2] += decode_buffer[in_pixel_index + 2] * coefficient;
                }
            }
            break;

        case 4:
            for (x = 0; x < max_x; x++)
            {
                int n0 = horizontal_contributors[x].n0;
                int n1 = horizontal_contributors[x].n1;

                int in_x = x - filter_pixel_margin;
                int in_pixel_index = in_x * 4;
                int max_n = n1;
                int coefficient_group = coefficient_width * x;

                for (k = n0; k <= max_n; k++)
                {
                    int out_pixel_index = k * 4;
                    float coefficient = horizontal_coefficients[coefficient_group + k - n0];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    output_buffer[out_pixel_index + 0] += decode_buffer[in_pixel_index + 0] * coefficient;
                    output_buffer[out_pixel_index + 1] += decode_buffer[in_pixel_index + 1] * coefficient;
                    output_buffer[out_pixel_index + 2] += decode_buffer[in_pixel_index + 2] * coefficient;
                    output_buffer[out_pixel_index + 3] += decode_buffer[in_pixel_index + 3] * coefficient;
                }
            }
            break;

        default:
            for (x = 0; x < max_x; x++)
            {
                int n0 = horizontal_contributors[x].n0;
                int n1 = horizontal_contributors[x].n1;

                int in_x = x - filter_pixel_margin;
                int in_pixel_index = in_x * channels;
                int max_n = n1;
                int coefficient_group = coefficient_width * x;

                for (k = n0; k <= max_n; k++)
                {
                    int c;
                    int out_pixel_index = k * channels;
                    float coefficient = horizontal_coefficients[coefficient_group + k - n0];
                    STBIR__DEBUG_ASSERT(coefficient != 0);
                    for (c = 0; c < channels; c++)
                        output_buffer[out_pixel_index + c] += decode_buffer[in_pixel_index + c] * coefficient;
                }
            }
            break;
    }
}

static void stbir__decode_and_resample_upsample(stbir__info* stbir_info, int n)
{
    // Decode the nth scanline from the source image into the decode buffer.
    stbir__decode_scanline(stbir_info, n);

    // Now resample it into the ring buffer.
    if (stbir__use_width_upsampling(stbir_info))
        stbir__resample_horizontal_upsample(stbir_info, n, stbir__add_empty_ring_buffer_entry(stbir_info, n));
    else
        stbir__resample_horizontal_downsample(stbir_info, n, stbir__add_empty_ring_buffer_entry(stbir_info, n));

    // Now it's sitting in the ring buffer ready to be used as source for the vertical sampling.
}

static void stbir__decode_and_resample_downsample(stbir__info* stbir_info, int n)
{
    // Decode the nth scanline from the source image into the decode buffer.
    stbir__decode_scanline(stbir_info, n);

    memset(stbir_info->horizontal_buffer, 0, stbir_info->output_w * stbir_info->channels * sizeof(float));

    // Now resample it into the horizontal buffer.
    if (stbir__use_width_upsampling(stbir_info))
        stbir__resample_horizontal_upsample(stbir_info, n, stbir_info->horizontal_buffer);
    else
        stbir__resample_horizontal_downsample(stbir_info, n, stbir_info->horizontal_buffer);

    // Now it's sitting in the horizontal buffer ready to be distributed into the ring buffers.
}

// Get the specified scan line from the ring buffer.
static float* stbir__get_ring_buffer_scanline(int get_scanline, float* ring_buffer, int begin_index, int first_scanline, int ring_buffer_size, int ring_buffer_length)
{
    int ring_buffer_index = (begin_index + (get_scanline - first_scanline)) % ring_buffer_size;
    return stbir__get_ring_buffer_entry(ring_buffer, ring_buffer_index, ring_buffer_length);
}


static void stbir__encode_scanline(stbir__info* stbir_info, int num_pixels, void *output_buffer, float *encode_buffer, int channels, int alpha_channel, int decode)
{
    int x;
    int n;
    int num_nonalpha;
    stbir_uint16 nonalpha[STBIR_MAX_CHANNELS];

    if (!(stbir_info->flags&STBIR_FLAG_ALPHA_PREMULTIPLIED))
    {
        for (x=0; x < num_pixels; ++x)
        {
            int pixel_index = x*channels;

            float alpha = encode_buffer[pixel_index + alpha_channel];
            float reciprocal_alpha = alpha ? 1.0f / alpha : 0;

            // unrolling this produced a 1% slowdown upscaling a large RGBA linear-space image on my machine - stb
            for (n = 0; n < channels; n++)
                if (n != alpha_channel)
                    encode_buffer[pixel_index + n] *= reciprocal_alpha;

            // We added in a small epsilon to prevent the color channel from being deleted with zero alpha.
            // Because we only add it for integer types, it will automatically be discarded on integer
            // conversion, so we don't need to subtract it back out (which would be problematic for
            // numeric precision reasons).
        }
    }

    // build a table of all channels that need colorspace correction, so
    // we don't perform colorspace correction on channels that don't need it.
    for (x=0, num_nonalpha=0; x < channels; ++x)
        if (x != alpha_channel || (stbir_info->flags & STBIR_FLAG_ALPHA_USES_COLORSPACE))
            nonalpha[num_nonalpha++] = x;

    #define STBIR__ROUND_INT(f)    ((int)          ((f)+0.5))
    #define STBIR__ROUND_UINT(f)   ((stbir_uint32) ((f)+0.5))

    #ifdef STBIR__SATURATE_INT
    #define STBIR__ENCODE_LINEAR8(f)   stbir__saturate8 (STBIR__ROUND_INT((f) * 255  ))
    #define STBIR__ENCODE_LINEAR16(f)  stbir__saturate16(STBIR__ROUND_INT((f) * 65535))
    #else
    #define STBIR__ENCODE_LINEAR8(f)   (unsigned char ) STBIR__ROUND_INT(stbir__saturate(f) * 255  )
    #define STBIR__ENCODE_LINEAR16(f)  (unsigned short) STBIR__ROUND_INT(stbir__saturate(f) * 65535)
    #endif

    switch (decode)
    {
        case STBIR__DECODE(STBIR_TYPE_UINT8, STBIR_COLORSPACE_LINEAR):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < channels; n++)
                {
                    int index = pixel_index + n;
                    ((unsigned char*)output_buffer)[index] = STBIR__ENCODE_LINEAR8(encode_buffer[index]);
                }
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_UINT8, STBIR_COLORSPACE_SRGB):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < num_nonalpha; n++)
                {
                    int index = pixel_index + nonalpha[n];
                    ((unsigned char*)output_buffer)[index] = stbir__linear_to_srgb_uchar(encode_buffer[index]);
                }

                if (!(stbir_info->flags & STBIR_FLAG_ALPHA_USES_COLORSPACE))
                    ((unsigned char *)output_buffer)[pixel_index + alpha_channel] = STBIR__ENCODE_LINEAR8(encode_buffer[pixel_index+alpha_channel]);
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_UINT16, STBIR_COLORSPACE_LINEAR):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < channels; n++)
                {
                    int index = pixel_index + n;
                    ((unsigned short*)output_buffer)[index] = STBIR__ENCODE_LINEAR16(encode_buffer[index]);
                }
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_UINT16, STBIR_COLORSPACE_SRGB):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < num_nonalpha; n++)
                {
                    int index = pixel_index + nonalpha[n];
                    ((unsigned short*)output_buffer)[index] = (unsigned short)STBIR__ROUND_INT(stbir__linear_to_srgb(stbir__saturate(encode_buffer[index])) * 65535);
                }

                if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                    ((unsigned short*)output_buffer)[pixel_index + alpha_channel] = STBIR__ENCODE_LINEAR16(encode_buffer[pixel_index + alpha_channel]);
            }

            break;

        case STBIR__DECODE(STBIR_TYPE_UINT32, STBIR_COLORSPACE_LINEAR):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < channels; n++)
                {
                    int index = pixel_index + n;
                    ((unsigned int*)output_buffer)[index] = (unsigned int)STBIR__ROUND_UINT(((double)stbir__saturate(encode_buffer[index])) * 4294967295);
                }
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_UINT32, STBIR_COLORSPACE_SRGB):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < num_nonalpha; n++)
                {
                    int index = pixel_index + nonalpha[n];
                    ((unsigned int*)output_buffer)[index] = (unsigned int)STBIR__ROUND_UINT(((double)stbir__linear_to_srgb(stbir__saturate(encode_buffer[index]))) * 4294967295);
                }

                if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                    ((unsigned int*)output_buffer)[pixel_index + alpha_channel] = (unsigned int)STBIR__ROUND_INT(((double)stbir__saturate(encode_buffer[pixel_index + alpha_channel])) * 4294967295);
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_FLOAT, STBIR_COLORSPACE_LINEAR):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < channels; n++)
                {
                    int index = pixel_index + n;
                    ((float*)output_buffer)[index] = encode_buffer[index];
                }
            }
            break;

        case STBIR__DECODE(STBIR_TYPE_FLOAT, STBIR_COLORSPACE_SRGB):
            for (x=0; x < num_pixels; ++x)
            {
                int pixel_index = x*channels;

                for (n = 0; n < num_nonalpha; n++)
                {
                    int index = pixel_index + nonalpha[n];
                    ((float*)output_buffer)[index] = stbir__linear_to_srgb(encode_buffer[index]);
                }

                if (!(stbir_info->flags&STBIR_FLAG_ALPHA_USES_COLORSPACE))
                    ((float*)output_buffer)[pixel_index + alpha_channel] = encode_buffer[pixel_index + alpha_channel];
            }
            break;

        default:
            STBIR__UNIMPLEMENTED("Unknown type/colorspace/channels combination.");
            break;
    }
}

static void stbir__resample_vertical_upsample(stbir__info* stbir_info, int n, int in_first_scanline, int in_last_scanline, float in_center_of_out)
{
    int x, k;
    int output_w = stbir_info->output_w;
    stbir__contributors* vertical_contributors = stbir_info->vertical_contributors;
    float* vertical_coefficients = stbir_info->vertical_coefficients;
    int channels = stbir_info->channels;
    int alpha_channel = stbir_info->alpha_channel;
    int type = stbir_info->type;
    int colorspace = stbir_info->colorspace;
    int kernel_pixel_width = stbir_info->vertical_filter_pixel_width;
    void* output_data = stbir_info->output_data;
    float* encode_buffer = stbir_info->encode_buffer;
    int decode = STBIR__DECODE(type, colorspace);
    int coefficient_width = stbir_info->vertical_coefficient_width;
    int coefficient_counter;
    int contributor = n;

    float* ring_buffer = stbir_info->ring_buffer;
    int ring_buffer_begin_index = stbir_info->ring_buffer_begin_index;
    int ring_buffer_first_scanline = stbir_info->ring_buffer_first_scanline;
    int ring_buffer_last_scanline = stbir_info->ring_buffer_last_scanline;
    int ring_buffer_length = stbir_info->ring_buffer_length_bytes/sizeof(float);

    int n0,n1, output_row_start;
    int coefficient_group = coefficient_width * contributor;

    n0 = vertical_contributors[contributor].n0;
    n1 = vertical_contributors[contributor].n1;

    output_row_start = n * stbir_info->output_stride_bytes;

    STBIR__DEBUG_ASSERT(stbir__use_height_upsampling(stbir_info));

    memset(encode_buffer, 0, output_w * sizeof(float) * channels);

    // I tried reblocking this for better cache usage of encode_buffer
    // (using x_outer, k, x_inner), but it lost speed. -- stb

    coefficient_counter = 0;
    switch (channels) {
        case 1:
            for (k = n0; k <= n1; k++)
            {
                int coefficient_index = coefficient_counter++;
                float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);
                float coefficient = vertical_coefficients[coefficient_group + coefficient_index];
                for (x = 0; x < output_w; ++x)
                {
                    int in_pixel_index = x * 1;
                    encode_buffer[in_pixel_index + 0] += ring_buffer_entry[in_pixel_index + 0] * coefficient;
                }
            }
            break;
        case 2:
            for (k = n0; k <= n1; k++)
            {
                int coefficient_index = coefficient_counter++;
                float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);
                float coefficient = vertical_coefficients[coefficient_group + coefficient_index];
                for (x = 0; x < output_w; ++x)
                {
                    int in_pixel_index = x * 2;
                    encode_buffer[in_pixel_index + 0] += ring_buffer_entry[in_pixel_index + 0] * coefficient;
                    encode_buffer[in_pixel_index + 1] += ring_buffer_entry[in_pixel_index + 1] * coefficient;
                }
            }
            break;
        case 3:
            for (k = n0; k <= n1; k++)
            {
                int coefficient_index = coefficient_counter++;
                float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);
                float coefficient = vertical_coefficients[coefficient_group + coefficient_index];
                for (x = 0; x < output_w; ++x)
                {
                    int in_pixel_index = x * 3;
                    encode_buffer[in_pixel_index + 0] += ring_buffer_entry[in_pixel_index + 0] * coefficient;
                    encode_buffer[in_pixel_index + 1] += ring_buffer_entry[in_pixel_index + 1] * coefficient;
                    encode_buffer[in_pixel_index + 2] += ring_buffer_entry[in_pixel_index + 2] * coefficient;
                }
            }
            break;
        case 4:
            for (k = n0; k <= n1; k++)
            {
                int coefficient_index = coefficient_counter++;
                float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);
                float coefficient = vertical_coefficients[coefficient_group + coefficient_index];
                for (x = 0; x < output_w; ++x)
                {
                    int in_pixel_index = x * 4;
                    encode_buffer[in_pixel_index + 0] += ring_buffer_entry[in_pixel_index + 0] * coefficient;
                    encode_buffer[in_pixel_index + 1] += ring_buffer_entry[in_pixel_index + 1] * coefficient;
                    encode_buffer[in_pixel_index + 2] += ring_buffer_entry[in_pixel_index + 2] * coefficient;
                    encode_buffer[in_pixel_index + 3] += ring_buffer_entry[in_pixel_index + 3] * coefficient;
                }
            }
            break;
        default:
            for (k = n0; k <= n1; k++)
            {
                int coefficient_index = coefficient_counter++;
                float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);
                float coefficient = vertical_coefficients[coefficient_group + coefficient_index];
                for (x = 0; x < output_w; ++x)
                {
                    int in_pixel_index = x * channels;
                    int c;
                    for (c = 0; c < channels; c++)
                        encode_buffer[in_pixel_index + c] += ring_buffer_entry[in_pixel_index + c] * coefficient;
                }
            }
            break;
    }
    stbir__encode_scanline(stbir_info, output_w, (char *) output_data + output_row_start, encode_buffer, channels, alpha_channel, decode);
}

static void stbir__resample_vertical_downsample(stbir__info* stbir_info, int n, int in_first_scanline, int in_last_scanline, float in_center_of_out)
{
    int x, k;
    int output_w = stbir_info->output_w;
    int output_h = stbir_info->output_h;
    stbir__contributors* vertical_contributors = stbir_info->vertical_contributors;
    float* vertical_coefficients = stbir_info->vertical_coefficients;
    int channels = stbir_info->channels;
    int kernel_pixel_width = stbir_info->vertical_filter_pixel_width;
    void* output_data = stbir_info->output_data;
    float* horizontal_buffer = stbir_info->horizontal_buffer;
    int coefficient_width = stbir_info->vertical_coefficient_width;
    int contributor = n + stbir_info->vertical_filter_pixel_margin;

    float* ring_buffer = stbir_info->ring_buffer;
    int ring_buffer_begin_index = stbir_info->ring_buffer_begin_index;
    int ring_buffer_first_scanline = stbir_info->ring_buffer_first_scanline;
    int ring_buffer_last_scanline = stbir_info->ring_buffer_last_scanline;
    int ring_buffer_length = stbir_info->ring_buffer_length_bytes/sizeof(float);
    int n0,n1;

    n0 = vertical_contributors[contributor].n0;
    n1 = vertical_contributors[contributor].n1;

    STBIR__DEBUG_ASSERT(!stbir__use_height_upsampling(stbir_info));

    for (k = n0; k <= n1; k++)
    {
        int coefficient_index = k - n0;
        int coefficient_group = coefficient_width * contributor;
        float coefficient = vertical_coefficients[coefficient_group + coefficient_index];

        float* ring_buffer_entry = stbir__get_ring_buffer_scanline(k, ring_buffer, ring_buffer_begin_index, ring_buffer_first_scanline, kernel_pixel_width, ring_buffer_length);

        switch (channels) {
            case 1:
                for (x = 0; x < output_w; x++)
                {
                    int in_pixel_index = x * 1;
                    ring_buffer_entry[in_pixel_index + 0] += horizontal_buffer[in_pixel_index + 0] * coefficient;
                }
                break;
            case 2:
                for (x = 0; x < output_w; x++)
                {
                    int in_pixel_index = x * 2;
                    ring_buffer_entry[in_pixel_index + 0] += horizontal_buffer[in_pixel_index + 0] * coefficient;
                    ring_buffer_entry[in_pixel_index + 1] += horizontal_buffer[in_pixel_index + 1] * coefficient;
                }
                break;
            case 3:
                for (x = 0; x < output_w; x++)
                {
                    int in_pixel_index = x * 3;
                    ring_buffer_entry[in_pixel_index + 0] += horizontal_buffer[in_pixel_index + 0] * coefficient;
                    ring_buffer_entry[in_pixel_index + 1] += horizontal_buffer[in_pixel_index + 1] * coefficient;
                    ring_buffer_entry[in_pixel_index + 2] += horizontal_buffer[in_pixel_index + 2] * coefficient;
                }
                break;
            case 4:
                for (x = 0; x < output_w; x++)
                {
                    int in_pixel_index = x * 4;
                    ring_buffer_entry[in_pixel_index + 0] += horizontal_buffer[in_pixel_index + 0] * coefficient;
                    ring_buffer_entry[in_pixel_index + 1] += horizontal_buffer[in_pixel_index + 1] * coefficient;
                    ring_buffer_entry[in_pixel_index + 2] += horizontal_buffer[in_pixel_index + 2] * coefficient;
                    ring_buffer_entry[in_pixel_index + 3] += horizontal_buffer[in_pixel_index + 3] * coefficient;
                }
                break;
            default:
                for (x = 0; x < output_w; x++)
                {
                    int in_pixel_index = x * channels;

                    int c;
                    for (c = 0; c < channels; c++)
                        ring_buffer_entry[in_pixel_index + c] += horizontal_buffer[in_pixel_index + c] * coefficient;
                }
                break;
        }
    }
}

static void stbir__buffer_loop_upsample(stbir__info* stbir_info)
{
    int y;
    float scale_ratio = stbir_info->vertical_scale;
    float out_scanlines_radius = stbir__filter_info_table[stbir_info->vertical_filter].support(1/scale_ratio) * scale_ratio;

    STBIR__DEBUG_ASSERT(stbir__use_height_upsampling(stbir_info));

    for (y = 0; y < stbir_info->output_h; y++)
    {
        float in_center_of_out = 0; // Center of the current out scanline in the in scanline space
        int in_first_scanline = 0, in_last_scanline = 0;

        stbir__calculate_sample_range_upsample(y, out_scanlines_radius, scale_ratio, stbir_info->vertical_shift, &in_first_scanline, &in_last_scanline, &in_center_of_out);

        STBIR__DEBUG_ASSERT(in_last_scanline - in_first_scanline <= stbir_info->vertical_filter_pixel_width);

        if (stbir_info->ring_buffer_begin_index >= 0)
        {
            // Get rid of whatever we don't need anymore.
            while (in_first_scanline > stbir_info->ring_buffer_first_scanline)
            {
                if (stbir_info->ring_buffer_first_scanline == stbir_info->ring_buffer_last_scanline)
                {
                    // We just popped the last scanline off the ring buffer.
                    // Reset it to the empty state.
                    stbir_info->ring_buffer_begin_index = -1;
                    stbir_info->ring_buffer_first_scanline = 0;
                    stbir_info->ring_buffer_last_scanline = 0;
                    break;
                }
                else
                {
                    stbir_info->ring_buffer_first_scanline++;
                    stbir_info->ring_buffer_begin_index = (stbir_info->ring_buffer_begin_index + 1) % stbir_info->vertical_filter_pixel_width;
                }
            }
        }

        // Load in new ones.
        if (stbir_info->ring_buffer_begin_index < 0)
            stbir__decode_and_resample_upsample(stbir_info, in_first_scanline);

        while (in_last_scanline > stbir_info->ring_buffer_last_scanline)
            stbir__decode_and_resample_upsample(stbir_info, stbir_info->ring_buffer_last_scanline + 1);

        // Now all buffers should be ready to write a row of vertical sampling.
        stbir__resample_vertical_upsample(stbir_info, y, in_first_scanline, in_last_scanline, in_center_of_out);

        STBIR_PROGRESS_REPORT((float)y / stbir_info->output_h);
    }
}

static void stbir__empty_ring_buffer(stbir__info* stbir_info, int first_necessary_scanline)
{
    int output_stride_bytes = stbir_info->output_stride_bytes;
    int channels = stbir_info->channels;
    int alpha_channel = stbir_info->alpha_channel;
    int type = stbir_info->type;
    int colorspace = stbir_info->colorspace;
    int output_w = stbir_info->output_w;
    void* output_data = stbir_info->output_data;
    int decode = STBIR__DECODE(type, colorspace);

    float* ring_buffer = stbir_info->ring_buffer;
    int ring_buffer_length = stbir_info->ring_buffer_length_bytes/sizeof(float);

    if (stbir_info->ring_buffer_begin_index >= 0)
    {
        // Get rid of whatever we don't need anymore.
        while (first_necessary_scanline > stbir_info->ring_buffer_first_scanline)
        {
            if (stbir_info->ring_buffer_first_scanline >= 0 && stbir_info->ring_buffer_first_scanline < stbir_info->output_h)
            {
                int output_row_start = stbir_info->ring_buffer_first_scanline * output_stride_bytes;
                float* ring_buffer_entry = stbir__get_ring_buffer_entry(ring_buffer, stbir_info->ring_buffer_begin_index, ring_buffer_length);
                stbir__encode_scanline(stbir_info, output_w, (char *) output_data + output_row_start, ring_buffer_entry, channels, alpha_channel, decode);
                STBIR_PROGRESS_REPORT((float)stbir_info->ring_buffer_first_scanline / stbir_info->output_h);
            }

            if (stbir_info->ring_buffer_first_scanline == stbir_info->ring_buffer_last_scanline)
            {
                // We just popped the last scanline off the ring buffer.
                // Reset it to the empty state.
                stbir_info->ring_buffer_begin_index = -1;
                stbir_info->ring_buffer_first_scanline = 0;
                stbir_info->ring_buffer_last_scanline = 0;
                break;
            }
            else
            {
                stbir_info->ring_buffer_first_scanline++;
                stbir_info->ring_buffer_begin_index = (stbir_info->ring_buffer_begin_index + 1) % stbir_info->vertical_filter_pixel_width;
            }
        }
    }
}

static void stbir__buffer_loop_downsample(stbir__info* stbir_info)
{
    int y;
    float scale_ratio = stbir_info->vertical_scale;
    int output_h = stbir_info->output_h;
    float in_pixels_radius = stbir__filter_info_table[stbir_info->vertical_filter].support(scale_ratio) / scale_ratio;
    int pixel_margin = stbir_info->vertical_filter_pixel_margin;
    int max_y = stbir_info->input_h + pixel_margin;

    STBIR__DEBUG_ASSERT(!stbir__use_height_upsampling(stbir_info));

    for (y = -pixel_margin; y < max_y; y++)
    {
        float out_center_of_in; // Center of the current out scanline in the in scanline space
        int out_first_scanline, out_last_scanline;

        stbir__calculate_sample_range_downsample(y, in_pixels_radius, scale_ratio, stbir_info->vertical_shift, &out_first_scanline, &out_last_scanline, &out_center_of_in);

        STBIR__DEBUG_ASSERT(out_last_scanline - out_first_scanline <= stbir_info->vertical_filter_pixel_width);

        if (out_last_scanline < 0 || out_first_scanline >= output_h)
            continue;

        stbir__empty_ring_buffer(stbir_info, out_first_scanline);

        stbir__decode_and_resample_downsample(stbir_info, y);

        // Load in new ones.
        if (stbir_info->ring_buffer_begin_index < 0)
            stbir__add_empty_ring_buffer_entry(stbir_info, out_first_scanline);

        while (out_last_scanline > stbir_info->ring_buffer_last_scanline)
            stbir__add_empty_ring_buffer_entry(stbir_info, stbir_info->ring_buffer_last_scanline + 1);

        // Now the horizontal buffer is ready to write to all ring buffer rows.
        stbir__resample_vertical_downsample(stbir_info, y, out_first_scanline, out_last_scanline, out_center_of_in);
    }

    stbir__empty_ring_buffer(stbir_info, stbir_info->output_h);
}

static void stbir__setup(stbir__info *info, int input_w, int input_h, int output_w, int output_h, int channels)
{
    info->input_w = input_w;
    info->input_h = input_h;
    info->output_w = output_w;
    info->output_h = output_h;
    info->channels = channels;
}

static void stbir__calculate_transform(stbir__info *info, float s0, float t0, float s1, float t1, float *transform)
{
    info->s0 = s0;
    info->t0 = t0;
    info->s1 = s1;
    info->t1 = t1;

    if (transform)
    {
        info->horizontal_scale = transform[0];
        info->vertical_scale   = transform[1];
        info->horizontal_shift = transform[2];
        info->vertical_shift   = transform[3];
    }
    else
    {
        info->horizontal_scale = ((float)info->output_w / info->input_w) / (s1 - s0);
        info->vertical_scale = ((float)info->output_h / info->input_h) / (t1 - t0);

        info->horizontal_shift = s0 * info->input_w / (s1 - s0);
        info->vertical_shift = t0 * info->input_h / (t1 - t0);
    }
}

static void stbir__choose_filter(stbir__info *info, stbir_filter h_filter, stbir_filter v_filter)
{
    if (h_filter == 0)
        h_filter = stbir__use_upsampling(info->horizontal_scale) ? STBIR_DEFAULT_FILTER_UPSAMPLE : STBIR_DEFAULT_FILTER_DOWNSAMPLE;
    if (v_filter == 0)
        v_filter = stbir__use_upsampling(info->vertical_scale)   ? STBIR_DEFAULT_FILTER_UPSAMPLE : STBIR_DEFAULT_FILTER_DOWNSAMPLE;
    info->horizontal_filter = h_filter;
    info->vertical_filter = v_filter;
}

static stbir_uint32 stbir__calculate_memory(stbir__info *info)
{
    int pixel_margin = stbir__get_filter_pixel_margin(info->horizontal_filter, info->horizontal_scale);
    int filter_height = stbir__get_filter_pixel_width(info->vertical_filter, info->vertical_scale);

    info->horizontal_num_contributors = stbir__get_contributors(info->horizontal_scale, info->horizontal_filter, info->input_w, info->output_w);
    info->vertical_num_contributors   = stbir__get_contributors(info->vertical_scale  , info->vertical_filter  , info->input_h, info->output_h);

    info->horizontal_contributors_size = info->horizontal_num_contributors * sizeof(stbir__contributors);
    info->horizontal_coefficients_size = stbir__get_total_horizontal_coefficients(info) * sizeof(float);
    info->vertical_contributors_size = info->vertical_num_contributors * sizeof(stbir__contributors);
    info->vertical_coefficients_size = stbir__get_total_vertical_coefficients(info) * sizeof(float);
    info->decode_buffer_size = (info->input_w + pixel_margin * 2) * info->channels * sizeof(float);
    info->horizontal_buffer_size = info->output_w * info->channels * sizeof(float);
    info->ring_buffer_size = info->output_w * info->channels * filter_height * sizeof(float);
    info->encode_buffer_size = info->output_w * info->channels * sizeof(float);

    STBIR_ASSERT(info->horizontal_filter != 0);
    STBIR_ASSERT(info->horizontal_filter < STBIR__ARRAY_SIZE(stbir__filter_info_table)); // this now happens too late
    STBIR_ASSERT(info->vertical_filter != 0);
    STBIR_ASSERT(info->vertical_filter < STBIR__ARRAY_SIZE(stbir__filter_info_table)); // this now happens too late

    if (stbir__use_height_upsampling(info))
        // The horizontal buffer is for when we're downsampling the height and we
        // can't output the result of sampling the decode buffer directly into the
        // ring buffers.
        info->horizontal_buffer_size = 0;
    else
        // The encode buffer is to retain precision in the height upsampling method
        // and isn't used when height downsampling.
        info->encode_buffer_size = 0;

    return info->horizontal_contributors_size + info->horizontal_coefficients_size
        + info->vertical_contributors_size + info->vertical_coefficients_size
        + info->decode_buffer_size + info->horizontal_buffer_size
        + info->ring_buffer_size + info->encode_buffer_size;
}

static int stbir__resize_allocated(stbir__info *info,
    const void* input_data, int input_stride_in_bytes,
    void* output_data, int output_stride_in_bytes,
    int alpha_channel, stbir_uint32 flags, stbir_datatype type,
    stbir_edge edge_horizontal, stbir_edge edge_vertical, stbir_colorspace colorspace,
    void* tempmem, size_t tempmem_size_in_bytes)
{
    size_t memory_required = stbir__calculate_memory(info);

    int width_stride_input = input_stride_in_bytes ? input_stride_in_bytes : info->channels * info->input_w * stbir__type_size[type];
    int width_stride_output = output_stride_in_bytes ? output_stride_in_bytes : info->channels * info->output_w * stbir__type_size[type];

#ifdef STBIR_DEBUG_OVERWRITE_TEST
#define OVERWRITE_ARRAY_SIZE 8
    unsigned char overwrite_output_before_pre[OVERWRITE_ARRAY_SIZE];
    unsigned char overwrite_tempmem_before_pre[OVERWRITE_ARRAY_SIZE];
    unsigned char overwrite_output_after_pre[OVERWRITE_ARRAY_SIZE];
    unsigned char overwrite_tempmem_after_pre[OVERWRITE_ARRAY_SIZE];

    size_t begin_forbidden = width_stride_output * (info->output_h - 1) + info->output_w * info->channels * stbir__type_size[type];
    memcpy(overwrite_output_before_pre, &((unsigned char*)output_data)[-OVERWRITE_ARRAY_SIZE], OVERWRITE_ARRAY_SIZE);
    memcpy(overwrite_output_after_pre, &((unsigned char*)output_data)[begin_forbidden], OVERWRITE_ARRAY_SIZE);
    memcpy(overwrite_tempmem_before_pre, &((unsigned char*)tempmem)[-OVERWRITE_ARRAY_SIZE], OVERWRITE_ARRAY_SIZE);
    memcpy(overwrite_tempmem_after_pre, &((unsigned char*)tempmem)[tempmem_size_in_bytes], OVERWRITE_ARRAY_SIZE);
#endif

    STBIR_ASSERT(info->channels >= 0);
    STBIR_ASSERT(info->channels <= STBIR_MAX_CHANNELS);

    if (info->channels < 0 || info->channels > STBIR_MAX_CHANNELS)
        return 0;

    STBIR_ASSERT(info->horizontal_filter < STBIR__ARRAY_SIZE(stbir__filter_info_table));
    STBIR_ASSERT(info->vertical_filter < STBIR__ARRAY_SIZE(stbir__filter_info_table));

    if (info->horizontal_filter >= STBIR__ARRAY_SIZE(stbir__filter_info_table))
        return 0;
    if (info->vertical_filter >= STBIR__ARRAY_SIZE(stbir__filter_info_table))
        return 0;

    if (alpha_channel < 0)
        flags |= STBIR_FLAG_ALPHA_USES_COLORSPACE | STBIR_FLAG_ALPHA_PREMULTIPLIED;

    if (!(flags&STBIR_FLAG_ALPHA_USES_COLORSPACE) || !(flags&STBIR_FLAG_ALPHA_PREMULTIPLIED))
        STBIR_ASSERT(alpha_channel >= 0 && alpha_channel < info->channels);

    if (alpha_channel >= info->channels)
        return 0;

    STBIR_ASSERT(tempmem);

    if (!tempmem)
        return 0;

    STBIR_ASSERT(tempmem_size_in_bytes >= memory_required);

    if (tempmem_size_in_bytes < memory_required)
        return 0;

    memset(tempmem, 0, tempmem_size_in_bytes);

    info->input_data = input_data;
    info->input_stride_bytes = width_stride_input;

    info->output_data = output_data;
    info->output_stride_bytes = width_stride_output;

    info->alpha_channel = alpha_channel;
    info->flags = flags;
    info->type = type;
    info->edge_horizontal = edge_horizontal;
    info->edge_vertical = edge_vertical;
    info->colorspace = colorspace;

    info->horizontal_coefficient_width   = stbir__get_coefficient_width  (info->horizontal_filter, info->horizontal_scale);
    info->vertical_coefficient_width     = stbir__get_coefficient_width  (info->vertical_filter  , info->vertical_scale  );
    info->horizontal_filter_pixel_width  = stbir__get_filter_pixel_width (info->horizontal_filter, info->horizontal_scale);
    info->vertical_filter_pixel_width    = stbir__get_filter_pixel_width (info->vertical_filter  , info->vertical_scale  );
    info->horizontal_filter_pixel_margin = stbir__get_filter_pixel_margin(info->horizontal_filter, info->horizontal_scale);
    info->vertical_filter_pixel_margin   = stbir__get_filter_pixel_margin(info->vertical_filter  , info->vertical_scale  );

    info->ring_buffer_length_bytes = info->output_w * info->channels * sizeof(float);
    info->decode_buffer_pixels = info->input_w + info->horizontal_filter_pixel_margin * 2;

#define STBIR__NEXT_MEMPTR(current, newtype) (newtype*)(((unsigned char*)current) + current##_size)

    info->horizontal_contributors = (stbir__contributors *) tempmem;
    info->horizontal_coefficients = STBIR__NEXT_MEMPTR(info->horizontal_contributors, float);
    info->vertical_contributors = STBIR__NEXT_MEMPTR(info->horizontal_coefficients, stbir__contributors);
    info->vertical_coefficients = STBIR__NEXT_MEMPTR(info->vertical_contributors, float);
    info->decode_buffer = STBIR__NEXT_MEMPTR(info->vertical_coefficients, float);

    if (stbir__use_height_upsampling(info))
    {
        info->horizontal_buffer = NULL;
        info->ring_buffer = STBIR__NEXT_MEMPTR(info->decode_buffer, float);
        info->encode_buffer = STBIR__NEXT_MEMPTR(info->ring_buffer, float);

        STBIR__DEBUG_ASSERT((size_t)STBIR__NEXT_MEMPTR(info->encode_buffer, unsigned char) == (size_t)tempmem + tempmem_size_in_bytes);
    }
    else
    {
        info->horizontal_buffer = STBIR__NEXT_MEMPTR(info->decode_buffer, float);
        info->ring_buffer = STBIR__NEXT_MEMPTR(info->horizontal_buffer, float);
        info->encode_buffer = NULL;

        STBIR__DEBUG_ASSERT((size_t)STBIR__NEXT_MEMPTR(info->ring_buffer, unsigned char) == (size_t)tempmem + tempmem_size_in_bytes);
    }

#undef STBIR__NEXT_MEMPTR

    // This signals that the ring buffer is empty
    info->ring_buffer_begin_index = -1;

    stbir__calculate_filters(info, info->horizontal_contributors, info->horizontal_coefficients, info->horizontal_filter, info->horizontal_scale, info->horizontal_shift, info->input_w, info->output_w);
    stbir__calculate_filters(info, info->vertical_contributors, info->vertical_coefficients, info->vertical_filter, info->vertical_scale, info->vertical_shift, info->input_h, info->output_h);

    STBIR_PROGRESS_REPORT(0);

    if (stbir__use_height_upsampling(info))
        stbir__buffer_loop_upsample(info);
    else
        stbir__buffer_loop_downsample(info);

    STBIR_PROGRESS_REPORT(1);

#ifdef STBIR_DEBUG_OVERWRITE_TEST
    STBIR__DEBUG_ASSERT(memcmp(overwrite_output_before_pre, &((unsigned char*)output_data)[-OVERWRITE_ARRAY_SIZE], OVERWRITE_ARRAY_SIZE) == 0);
    STBIR__DEBUG_ASSERT(memcmp(overwrite_output_after_pre, &((unsigned char*)output_data)[begin_forbidden], OVERWRITE_ARRAY_SIZE) == 0);
    STBIR__DEBUG_ASSERT(memcmp(overwrite_tempmem_before_pre, &((unsigned char*)tempmem)[-OVERWRITE_ARRAY_SIZE], OVERWRITE_ARRAY_SIZE) == 0);
    STBIR__DEBUG_ASSERT(memcmp(overwrite_tempmem_after_pre, &((unsigned char*)tempmem)[tempmem_size_in_bytes], OVERWRITE_ARRAY_SIZE) == 0);
#endif

    return 1;
}


static int stbir__resize_arbitrary(
    void *alloc_context,
    const void* input_data, int input_w, int input_h, int input_stride_in_bytes,
    void* output_data, int output_w, int output_h, int output_stride_in_bytes,
    float s0, float t0, float s1, float t1, float *transform,
    int channels, int alpha_channel, stbir_uint32 flags, stbir_datatype type,
    stbir_filter h_filter, stbir_filter v_filter,
    stbir_edge edge_horizontal, stbir_edge edge_vertical, stbir_colorspace colorspace)
{
    stbir__info info;
    int result;
    size_t memory_required;
    void* extra_memory;

    stbir__setup(&info, input_w, input_h, output_w, output_h, channels);
    stbir__calculate_transform(&info, s0,t0,s1,t1,transform);
    stbir__choose_filter(&info, h_filter, v_filter);
    memory_required = stbir__calculate_memory(&info);
    extra_memory = STBIR_MALLOC(memory_required, alloc_context);

    if (!extra_memory)
        return 0;

    result = stbir__resize_allocated(&info, input_data, input_stride_in_bytes,
                                            output_data, output_stride_in_bytes, 
                                            alpha_channel, flags, type,
                                            edge_horizontal, edge_vertical,
                                            colorspace, extra_memory, memory_required);

    STBIR_FREE(extra_memory, alloc_context);

    return result;
}

STBIRDEF int stbir_resize_uint8(     const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels)
{
    return stbir__resize_arbitrary(NULL, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,-1,0, STBIR_TYPE_UINT8, STBIR_FILTER_DEFAULT, STBIR_FILTER_DEFAULT,
        STBIR_EDGE_CLAMP, STBIR_EDGE_CLAMP, STBIR_COLORSPACE_LINEAR);
}

STBIRDEF int stbir_resize_float(     const float *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           float *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels)
{
    return stbir__resize_arbitrary(NULL, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,-1,0, STBIR_TYPE_FLOAT, STBIR_FILTER_DEFAULT, STBIR_FILTER_DEFAULT,
        STBIR_EDGE_CLAMP, STBIR_EDGE_CLAMP, STBIR_COLORSPACE_LINEAR);
}

STBIRDEF int stbir_resize_uint8_srgb(const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                           unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                     int num_channels, int alpha_channel, int flags)
{
    return stbir__resize_arbitrary(NULL, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, STBIR_TYPE_UINT8, STBIR_FILTER_DEFAULT, STBIR_FILTER_DEFAULT,
        STBIR_EDGE_CLAMP, STBIR_EDGE_CLAMP, STBIR_COLORSPACE_SRGB);
}

STBIRDEF int stbir_resize_uint8_srgb_edgemode(const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                                    unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                              int num_channels, int alpha_channel, int flags,
                                              stbir_edge edge_wrap_mode)
{
    return stbir__resize_arbitrary(NULL, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, STBIR_TYPE_UINT8, STBIR_FILTER_DEFAULT, STBIR_FILTER_DEFAULT,
        edge_wrap_mode, edge_wrap_mode, STBIR_COLORSPACE_SRGB);
}

STBIRDEF int stbir_resize_uint8_generic( const unsigned char *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                               unsigned char *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context)
{
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, STBIR_TYPE_UINT8, filter, filter,
        edge_wrap_mode, edge_wrap_mode, space);
}

STBIRDEF int stbir_resize_uint16_generic(const stbir_uint16 *input_pixels  , int input_w , int input_h , int input_stride_in_bytes,
                                               stbir_uint16 *output_pixels , int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context)
{
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, STBIR_TYPE_UINT16, filter, filter,
        edge_wrap_mode, edge_wrap_mode, space);
}


STBIRDEF int stbir_resize_float_generic( const float *input_pixels         , int input_w , int input_h , int input_stride_in_bytes,
                                               float *output_pixels        , int output_w, int output_h, int output_stride_in_bytes,
                                         int num_channels, int alpha_channel, int flags,
                                         stbir_edge edge_wrap_mode, stbir_filter filter, stbir_colorspace space, 
                                         void *alloc_context)
{
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, STBIR_TYPE_FLOAT, filter, filter,
        edge_wrap_mode, edge_wrap_mode, space);
}


STBIRDEF int stbir_resize(         const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context)
{
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,NULL,num_channels,alpha_channel,flags, datatype, filter_horizontal, filter_vertical,
        edge_mode_horizontal, edge_mode_vertical, space);
}


STBIRDEF int stbir_resize_subpixel(const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context,
                                   float x_scale, float y_scale,
                                   float x_offset, float y_offset)
{
    float transform[4];
    transform[0] = x_scale;
    transform[1] = y_scale;
    transform[2] = x_offset;
    transform[3] = y_offset;
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        0,0,1,1,transform,num_channels,alpha_channel,flags, datatype, filter_horizontal, filter_vertical,
        edge_mode_horizontal, edge_mode_vertical, space);
}

STBIRDEF int stbir_resize_region(  const void *input_pixels , int input_w , int input_h , int input_stride_in_bytes,
                                         void *output_pixels, int output_w, int output_h, int output_stride_in_bytes,
                                   stbir_datatype datatype,
                                   int num_channels, int alpha_channel, int flags,
                                   stbir_edge edge_mode_horizontal, stbir_edge edge_mode_vertical, 
                                   stbir_filter filter_horizontal,  stbir_filter filter_vertical,
                                   stbir_colorspace space, void *alloc_context,
                                   float s0, float t0, float s1, float t1)
{
    return stbir__resize_arbitrary(alloc_context, input_pixels, input_w, input_h, input_stride_in_bytes,
        output_pixels, output_w, output_h, output_stride_in_bytes,
        s0,t0,s1,t1,NULL,num_channels,alpha_channel,flags, datatype, filter_horizontal, filter_vertical,
        edge_mode_horizontal, edge_mode_vertical, space);
}

#endif // STB_IMAGE_RESIZE_IMPLEMENTATION
/* stb_image - v1.46 - public domain JPEG/PNG reader - http://nothings.org/stb_image.c
   when you control the images you're loading
                                     no warranty implied; use at your own risk

   Do this:
      #define STB_IMAGE_IMPLEMENTATION
   before you include this file in *one* C or C++ file to create the implementation.

   #define STBI_ASSERT(x) to avoid using assert.h.

   QUICK NOTES:
      Primarily of interest to game developers and other people who can
          avoid problematic images and only need the trivial interface

      JPEG baseline (no JPEG progressive)
      PNG 8-bit-per-channel only

      TGA (not sure what subset, if a subset)
      BMP non-1bpp, non-RLE
      PSD (composited view only, no extra channels)

      GIF (*comp always reports as 4-channel)
      HDR (radiance rgbE format)
      PIC (Softimage PIC)

      - decode from memory or through FILE (define STBI_NO_STDIO to remove code)
      - decode from arbitrary I/O callbacks
      - overridable dequantizing-IDCT, YCbCr-to-RGB conversion (define STBI_SIMD)

   Latest revisions:
      1.46 (2014-08-26) fix broken tRNS chunk in non-paletted PNG
      1.45 (2014-08-16) workaround MSVC-ARM internal compiler error by wrapping malloc
      1.44 (2014-08-07) warnings
      1.43 (2014-07-15) fix MSVC-only bug in 1.42
      1.42 (2014-07-09) no _CRT_SECURE_NO_WARNINGS; error-path fixes; STBI_ASSERT
      1.41 (2014-06-25) fix search&replace that messed up comments/error messages
      1.40 (2014-06-22) gcc warning
      1.39 (2014-06-15) TGA optimization bugfix, multiple BMP fixes
      1.38 (2014-06-06) suppress MSVC run-time warnings, fix accidental rename of 'skip'
      1.37 (2014-06-04) remove duplicate typedef
      1.36 (2014-06-03) converted to header file, allow reading incorrect iphoned-images without iphone flag
      1.35 (2014-05-27) warnings, bugfixes, TGA optimization, etc

   See end of file for full revision history.

   TODO:
      stbi_info support for BMP,PSD,HDR,PIC


 ============================    Contributors    =========================
              
 Image formats                                Bug fixes & warning fixes
    Sean Barrett (jpeg, png, bmp)                Marc LeBlanc
    Nicolas Schulz (hdr, psd)                    Christpher Lloyd
    Jonathan Dummer (tga)                        Dave Moore
    Jean-Marc Lienher (gif)                      Won Chun
    Tom Seddon (pic)                             the Horde3D community
    Thatcher Ulrich (psd)                        Janez Zemva
                                                 Jonathan Blow
                                                 Laurent Gomila
 Extensions, features                            Aruelien Pocheville
    Jetro Lauha (stbi_info)                      Ryamond Barbiero
    James "moose2000" Brown (iPhone PNG)         David Woo
    Ben "Disch" Wenger (io callbacks)            Roy Eltham
    Martin "SpartanJ" Golini                     Luke Graham
                                                 Thomas Ruf
                                                 John Bartholomew
 Optimizations & bugfixes                        Ken Hamada
    Fabian "ryg" Giesen                          Cort Stratton
    Arseny Kapoulkine                            Blazej Dariusz Roszkowski
                                                 Thibault Reuille
                                                 Paul Du Bois
                                                 Guillaume George
                                                 Jerry Jansson
  If your name should be here but                Hayaki Saito
  isn't, let Sean know.                          Johan Duparc
                                                 Ronny Chevalier
                                                 Michal Cichon
*/

#ifndef STBI_INCLUDE_STB_IMAGE_H
#define STBI_INCLUDE_STB_IMAGE_H

// Limitations:
//    - no jpeg progressive support
//    - non-HDR formats support 8-bit samples only (jpeg, png)
//    - no delayed line count (jpeg) -- IJG doesn't support either
//    - no 1-bit BMP
//    - GIF always returns *comp=4
//
// Basic usage (see HDR discussion below):
//    int x,y,n;
//    unsigned char *data = stbi_load(filename, &x, &y, &n, 0);
//    // ... process data if not NULL ... 
//    // ... x = width, y = height, n = # 8-bit components per pixel ...
//    // ... replace '0' with '1'..'4' to force that many components per pixel
//    // ... but 'n' will always be the number that it would have been if you said 0
//    stbi_image_freea(data)
//
// Standard parameters:
//    int *x       -- outputs image width in pixels
//    int *y       -- outputs image height in pixels
//    int *comp    -- outputs # of image components in image file
//    int req_comp -- if non-zero, # of image components requested in result
//
// The return value from an image loader is an 'unsigned char *' which points
// to the pixel data. The pixel data consists of *y scanlines of *x pixels,
// with each pixel consisting of N interleaved 8-bit components; the first
// pixel pointed to is top-left-most in the image. There is no padding between
// image scanlines or between pixels, regardless of format. The number of
// components N is 'req_comp' if req_comp is non-zero, or *comp otherwise.
// If req_comp is non-zero, *comp has the number of components that _would_
// have been output otherwise. E.g. if you set req_comp to 4, you will always
// get RGBA output, but you can check *comp to easily see if it's opaque.
//
// An output image with N components has the following components interleaved
// in this order in each pixel:
//
//     N=#comp     components
//       1           grey
//       2           grey, alpha
//       3           red, green, blue
//       4           red, green, blue, alpha
//
// If image loading fails for any reason, the return value will be NULL,
// and *x, *y, *comp will be unchanged. The function stbi_failure_reason()
// can be queried for an extremely brief, end-user unfriendly explanation
// of why the load failed. Define STBI_NO_FAILURE_STRINGS to avoid
// compiling these strings at all, and STBI_FAILURE_USERMSG to get slightly
// more user-friendly ones.
//
// Paletted PNG, BMP, GIF, and PIC images are automatically depalettized.
//
// ===========================================================================
//
// iPhone PNG support:
//
// By default we convert iphone-formatted PNGs back to RGB; nominally they
// would silently load as BGR, except the existing code should have just
// failed on such iPhone PNGs. But you can disable this conversion by
// by calling stbi_convert_iphone_png_to_rgb(0), in which case
// you will always just get the native iphone "format" through.
//
// Call stbi_set_unpremultiply_on_load(1) as well to force a divide per
// pixel to remove any premultiplied alpha *only* if the image file explicitly
// says there's premultiplied data (currently only happens in iPhone images,
// and only if iPhone convert-to-rgb processing is on).
//
// ===========================================================================
//
// HDR image support   (disable by defining STBI_NO_HDR)
//
// stb_image now supports loading HDR images in general, and currently
// the Radiance .HDR file format, although the support is provided
// generically. You can still load any file through the existing interface;
// if you attempt to load an HDR file, it will be automatically remapped to
// LDR, assuming gamma 2.2 and an arbitrary scale factor defaulting to 1;
// both of these constants can be reconfigured through this interface:
//
//     stbi_hdr_to_ldr_gamma(2.2f);
//     stbi_hdr_to_ldr_scale(1.0f);
//
// (note, do not use _inverse_ constants; stbi_image will invert them
// appropriately).
//
// Additionally, there is a new, parallel interface for loading files as
// (linear) floats to preserve the full dynamic range:
//
//    float *data = stbi_loadf(filename, &x, &y, &n, 0);
// 
// If you load LDR images through this interface, those images will
// be promoted to floating point values, run through the inverse of
// constants corresponding to the above:
//
//     stbi_ldr_to_hdr_scale(1.0f);
//     stbi_ldr_to_hdr_gamma(2.2f);
//
// Finally, given a filename (or an open file or memory block--see header
// file for details) containing image data, you can query for the "most
// appropriate" interface to use (that is, whether the image is HDR or
// not), using:
//
//     stbi_is_hdr(char *filename);
//
// ===========================================================================
//
// I/O callbacks
//
// I/O callbacks allow you to read from arbitrary sources, like packaged
// files or some other source. Data read from callbacks are processed
// through a small internal buffer (currently 128 bytes) to try to reduce
// overhead. 
//
// The three functions you must define are "read" (reads some bytes of data),
// "skip" (skips some bytes of data), "eof" (reports if the stream is at the end).


#ifndef STBI_NO_STDIO
#include <stdio.h>
#endif // STBI_NO_STDIO

#define STBI_VERSION 1

enum
{
   STBI_default = 0, // only used for req_comp

   STBI_grey       = 1,
   STBI_grey_alpha = 2,
   STBI_rgb        = 3,
   STBI_rgb_alpha  = 4
};

typedef unsigned char stbi_uc;

#ifdef __cplusplus
extern "C" {
#endif

#ifdef STB_IMAGE_STATIC
#define STBIDEF static
#else
#define STBIDEF extern
#endif

//////////////////////////////////////////////////////////////////////////////
//
// PRIMARY API - works on images of any type
//

//
// load image by filename, open file, or memory buffer
//

STBIDEF stbi_uc *stbi_load_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp, int req_comp);

#ifndef STBI_NO_STDIO
STBIDEF stbi_uc *stbi_load            (char const *filename,     int *x, int *y, int *comp, int req_comp);
STBIDEF stbi_uc *stbi_load_from_file  (FILE *f,                  int *x, int *y, int *comp, int req_comp);
// for stbi_load_from_file, file pointer is left pointing immediately after image
#endif

typedef struct
{
   int      (*read)  (void *user,char *data,int size);   // fill 'data' with 'size' bytes.  return number of bytes actually read 
   void     (*skip)  (void *user,int n);                 // skip the next 'n' bytes, or 'unget' the last -n bytes if negative
   int      (*eof)   (void *user);                       // returns nonzero if we are at end of file/data
} stbi_io_callbacks;

STBIDEF stbi_uc *stbi_load_from_callbacks  (stbi_io_callbacks const *clbk, void *user, int *x, int *y, int *comp, int req_comp);

#ifndef STBI_NO_HDR
   STBIDEF float *stbi_loadf_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp, int req_comp);

   #ifndef STBI_NO_STDIO
   STBIDEF float *stbi_loadf            (char const *filename,   int *x, int *y, int *comp, int req_comp);
   STBIDEF float *stbi_loadf_from_file  (FILE *f,                int *x, int *y, int *comp, int req_comp);
   #endif
   
   STBIDEF float *stbi_loadf_from_callbacks  (stbi_io_callbacks const *clbk, void *user, int *x, int *y, int *comp, int req_comp);

   STBIDEF void   stbi_hdr_to_ldr_gamma(float gamma);
   STBIDEF void   stbi_hdr_to_ldr_scale(float scale);

   STBIDEF void   stbi_ldr_to_hdr_gamma(float gamma);
   STBIDEF void   stbi_ldr_to_hdr_scale(float scale);
#endif // STBI_NO_HDR

// stbi_is_hdr is always defined
STBIDEF int    stbi_is_hdr_from_callbacks(stbi_io_callbacks const *clbk, void *user);
STBIDEF int    stbi_is_hdr_from_memory(stbi_uc const *buffer, int len);
#ifndef STBI_NO_STDIO
STBIDEF int      stbi_is_hdr          (char const *filename);
STBIDEF int      stbi_is_hdr_from_file(FILE *f);
#endif // STBI_NO_STDIO


// get a VERY brief reason for failure
// NOT THREADSAFE
STBIDEF const char *stbi_failure_reason  (void); 

// free the loaded image -- this is just free()
STBIDEF void     stbi_image_free      (void *retval_from_stbi_load);

// get image dimensions & components without fully decoding
STBIDEF int      stbi_info_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp);
STBIDEF int      stbi_info_from_callbacks(stbi_io_callbacks const *clbk, void *user, int *x, int *y, int *comp);

#ifndef STBI_NO_STDIO
STBIDEF int      stbi_info            (char const *filename,     int *x, int *y, int *comp);
STBIDEF int      stbi_info_from_file  (FILE *f,                  int *x, int *y, int *comp);

#endif



// for image formats that explicitly notate that they have premultiplied alpha,
// we just return the colors as stored in the file. set this flag to force
// unpremultiplication. results are undefined if the unpremultiply overflow.
STBIDEF void stbi_set_unpremultiply_on_load(int flag_true_if_should_unpremultiply);

// indicate whether we should process iphone images back to canonical format,
// or just pass them through "as-is"
STBIDEF void stbi_convert_iphone_png_to_rgb(int flag_true_if_should_convert);


// ZLIB client - used by PNG, available for other purposes

STBIDEF char *stbi_zlib_decode_malloc_guesssize(const char *buffer, int len, int initial_size, int *outlen);
STBIDEF char *stbi_zlib_decode_malloc_guesssize_headerflag(const char *buffer, int len, int initial_size, int *outlen, int parse_header);
STBIDEF char *stbi_zlib_decode_malloc(const char *buffer, int len, int *outlen);
STBIDEF int   stbi_zlib_decode_buffer(char *obuffer, int olen, const char *ibuffer, int ilen);

STBIDEF char *stbi_zlib_decode_noheader_malloc(const char *buffer, int len, int *outlen);
STBIDEF int   stbi_zlib_decode_noheader_buffer(char *obuffer, int olen, const char *ibuffer, int ilen);


// define faster low-level operations (typically SIMD support)
#ifdef STBI_SIMD
typedef void (*stbi_idct_8x8)(stbi_uc *out, int out_stride, short data[64], unsigned short *dequantize);
// compute an integer IDCT on "input"
//     input[x] = data[x] * dequantize[x]
//     write results to 'out': 64 samples, each run of 8 spaced by 'out_stride'
//                             CLAMP results to 0..255
typedef void (*stbi_YCbCr_to_RGB_run)(stbi_uc *output, stbi_uc const  *y, stbi_uc const *cb, stbi_uc const *cr, int count, int step);
// compute a conversion from YCbCr to RGB
//     'count' pixels
//     write pixels to 'output'; each pixel is 'step' bytes (either 3 or 4; if 4, write '255' as 4th), order R,G,B
//     y: Y input channel
//     cb: Cb input channel; scale/biased to be 0..255
//     cr: Cr input channel; scale/biased to be 0..255

STBIDEF void stbi_install_idct(stbi_idct_8x8 func);
STBIDEF void stbi_install_YCbCr_to_RGB(stbi_YCbCr_to_RGB_run func);
#endif // STBI_SIMD


#ifdef __cplusplus
}
#endif

//
//
////   end header file   /////////////////////////////////////////////////////
#endif // STBI_INCLUDE_STB_IMAGE_H

#ifdef STB_IMAGE_IMPLEMENTATION

#ifndef STBI_NO_HDR
#include <math.h>  // ldexp
#include <string.h> // strcmp, strtok
#endif

#ifndef STBI_NO_STDIO
#include <stdio.h>
#endif
#include <stdlib.h>
#include <string.h>
#ifndef STBI_ASSERT
#include <assert.h>
#define STBI_ASSERT(x) assert(x)
#endif
#include <stdarg.h>
#include <stddef.h> // ptrdiff_t on osx

#ifndef _MSC_VER
   #ifdef __cplusplus
   #define stbi_inline inline
   #else
   #define stbi_inline
   #endif
#else
   #define stbi_inline __forceinline
#endif


#ifdef _MSC_VER
typedef unsigned short stbi__uint16;
typedef   signed short stbi__int16;
typedef unsigned int   stbi__uint32;
typedef   signed int   stbi__int32;
#else
#include <stdint.h>
typedef uint16_t stbi__uint16;
typedef int16_t  stbi__int16;
typedef uint32_t stbi__uint32;
typedef int32_t  stbi__int32;
#endif

// should produce compiler error if size is wrong
typedef unsigned char validate_uint32[sizeof(stbi__uint32)==4 ? 1 : -1];

#ifdef _MSC_VER
#define STBI_NOTUSED(v)  (void)(v)
#else
#define STBI_NOTUSED(v)  (void)sizeof(v)
#endif

#ifdef _MSC_VER
#define STBI_HAS_LROTL
#endif

#ifdef STBI_HAS_LROTL
   #define stbi_lrot(x,y)  _lrotl(x,y)
#else
   #define stbi_lrot(x,y)  (((x) << (y)) | ((x) >> (32 - (y))))
#endif

///////////////////////////////////////////////
//
//  stbi__context struct and start_xxx functions

// stbi__context structure is our basic context used by all images, so it
// contains all the IO context, plus some basic image information
typedef struct
{
   stbi__uint32 img_x, img_y;
   int img_n, img_out_n;
   
   stbi_io_callbacks io;
   void *io_user_data;

   int read_from_callbacks;
   int buflen;
   stbi_uc buffer_start[128];

   stbi_uc *img_buffer, *img_buffer_end;
   stbi_uc *img_buffer_original;
} stbi__context;


static void stbi__refill_buffer(stbi__context *s);

// initialize a memory-decode context
static void stbi__start_mem(stbi__context *s, stbi_uc const *buffer, int len)
{
   s->io.read = NULL;
   s->read_from_callbacks = 0;
   s->img_buffer = s->img_buffer_original = (stbi_uc *) buffer;
   s->img_buffer_end = (stbi_uc *) buffer+len;
}

// initialize a callback-based context
static void stbi__start_callbacks(stbi__context *s, stbi_io_callbacks *c, void *user)
{
   s->io = *c;
   s->io_user_data = user;
   s->buflen = sizeof(s->buffer_start);
   s->read_from_callbacks = 1;
   s->img_buffer_original = s->buffer_start;
   stbi__refill_buffer(s);
}

#ifndef STBI_NO_STDIO

static int stbi__stdio_read(void *user, char *data, int size)
{
   return (int) fread(data,1,size,(FILE*) user);
}

static void stbi__stdio_skip(void *user, int n)
{
   fseek((FILE*) user, n, SEEK_CUR);
}

static int stbi__stdio_eof(void *user)
{
   return feof((FILE*) user);
}

static stbi_io_callbacks stbi__stdio_callbacks =
{
   stbi__stdio_read,
   stbi__stdio_skip,
   stbi__stdio_eof,
};

static void stbi__start_file(stbi__context *s, FILE *f)
{
   stbi__start_callbacks(s, &stbi__stdio_callbacks, (void *) f);
}

//static void stop_file(stbi__context *s) { }

#endif // !STBI_NO_STDIO

static void stbi__rewind(stbi__context *s)
{
   // conceptually rewind SHOULD rewind to the beginning of the stream,
   // but we just rewind to the beginning of the initial buffer, because
   // we only use it after doing 'test', which only ever looks at at most 92 bytes
   s->img_buffer = s->img_buffer_original;
}

static int      stbi__jpeg_test(stbi__context *s);
static stbi_uc *stbi__jpeg_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__jpeg_info(stbi__context *s, int *x, int *y, int *comp);
static int      stbi__png_test(stbi__context *s);
static stbi_uc *stbi__png_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__png_info(stbi__context *s, int *x, int *y, int *comp);
static int      stbi__bmp_test(stbi__context *s);
static stbi_uc *stbi__bmp_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__tga_test(stbi__context *s);
static stbi_uc *stbi__tga_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__tga_info(stbi__context *s, int *x, int *y, int *comp);
static int      stbi__psd_test(stbi__context *s);
static stbi_uc *stbi__psd_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
#ifndef STBI_NO_HDR
static int      stbi__hdr_test(stbi__context *s);
static float   *stbi__hdr_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
#endif
static int      stbi__pic_test(stbi__context *s);
static stbi_uc *stbi__pic_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__gif_test(stbi__context *s);
static stbi_uc *stbi__gif_load(stbi__context *s, int *x, int *y, int *comp, int req_comp);
static int      stbi__gif_info(stbi__context *s, int *x, int *y, int *comp);


// this is not threadsafe
static const char *stbi__g_failure_reason;

STBIDEF const char *stbi_failure_reason(void)
{
   return stbi__g_failure_reason;
}

static int stbi__err(const char *str)
{
   stbi__g_failure_reason = str;
   return 0;
}

static void *stbi__malloc(size_t size)
{
    return malloc(size);
}

// stbi__err - error
// stbi__errpf - error returning pointer to float
// stbi__errpuc - error returning pointer to unsigned char

#ifdef STBI_NO_FAILURE_STRINGS
   #define stbi__err(x,y)  0
#elif defined(STBI_FAILURE_USERMSG)
   #define stbi__err(x,y)  stbi__err(y)
#else
   #define stbi__err(x,y)  stbi__err(x)
#endif

#define stbi__errpf(x,y)   ((float *) (stbi__err(x,y)?NULL:NULL))
#define stbi__errpuc(x,y)  ((unsigned char *) (stbi__err(x,y)?NULL:NULL))

STBIDEF void stbi_image_free(void *retval_from_stbi_load)
{
   free(retval_from_stbi_load);
}

#ifndef STBI_NO_HDR
static float   *stbi__ldr_to_hdr(stbi_uc *data, int x, int y, int comp);
static stbi_uc *stbi__hdr_to_ldr(float   *data, int x, int y, int comp);
#endif

static unsigned char *stbi_load_main(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   if (stbi__jpeg_test(s)) return stbi__jpeg_load(s,x,y,comp,req_comp);
   if (stbi__png_test(s))  return stbi__png_load(s,x,y,comp,req_comp);
   if (stbi__bmp_test(s))  return stbi__bmp_load(s,x,y,comp,req_comp);
   if (stbi__gif_test(s))  return stbi__gif_load(s,x,y,comp,req_comp);
   if (stbi__psd_test(s))  return stbi__psd_load(s,x,y,comp,req_comp);
   if (stbi__pic_test(s))  return stbi__pic_load(s,x,y,comp,req_comp);

   #ifndef STBI_NO_HDR
   if (stbi__hdr_test(s)) {
      float *hdr = stbi__hdr_load(s, x,y,comp,req_comp);
      return stbi__hdr_to_ldr(hdr, *x, *y, req_comp ? req_comp : *comp);
   }
   #endif

   // test tga last because it's a crappy test!
   if (stbi__tga_test(s))
      return stbi__tga_load(s,x,y,comp,req_comp);
   return stbi__errpuc("unknown image type", "Image not of any known type, or corrupt");
}

#ifndef STBI_NO_STDIO

FILE *stbi__fopen(char const *filename, char const *mode)
{
   FILE *f;
#if defined(_MSC_VER) && _MSC_VER >= 1400
   if (0 != fopen_s(&f, filename, mode))
      f=0;
#else
   f = fopen(filename, mode);
#endif
   return f;
}


STBIDEF unsigned char *stbi_load(char const *filename, int *x, int *y, int *comp, int req_comp)
{
   FILE *f = stbi__fopen(filename, "rb");
   unsigned char *result;
   if (!f) return stbi__errpuc("can't fopen", "Unable to open file");
   result = stbi_load_from_file(f,x,y,comp,req_comp);
   fclose(f);
   return result;
}

STBIDEF unsigned char *stbi_load_from_file(FILE *f, int *x, int *y, int *comp, int req_comp)
{
   unsigned char *result;
   stbi__context s;
   stbi__start_file(&s,f);
   result = stbi_load_main(&s,x,y,comp,req_comp);
   if (result) {
      // need to 'unget' all the characters in the IO buffer
      fseek(f, - (int) (s.img_buffer_end - s.img_buffer), SEEK_CUR);
   }
   return result;
}
#endif //!STBI_NO_STDIO

STBIDEF unsigned char *stbi_load_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp, int req_comp)
{
   stbi__context s;
   stbi__start_mem(&s,buffer,len);
   return stbi_load_main(&s,x,y,comp,req_comp);
}

unsigned char *stbi_load_from_callbacks(stbi_io_callbacks const *clbk, void *user, int *x, int *y, int *comp, int req_comp)
{
   stbi__context s;
   stbi__start_callbacks(&s, (stbi_io_callbacks *) clbk, user);
   return stbi_load_main(&s,x,y,comp,req_comp);
}

#ifndef STBI_NO_HDR

float *stbi_loadf_main(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   unsigned char *data;
   #ifndef STBI_NO_HDR
   if (stbi__hdr_test(s))
      return stbi__hdr_load(s,x,y,comp,req_comp);
   #endif
   data = stbi_load_main(s, x, y, comp, req_comp);
   if (data)
      return stbi__ldr_to_hdr(data, *x, *y, req_comp ? req_comp : *comp);
   return stbi__errpf("unknown image type", "Image not of any known type, or corrupt");
}

float *stbi_loadf_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp, int req_comp)
{
   stbi__context s;
   stbi__start_mem(&s,buffer,len);
   return stbi_loadf_main(&s,x,y,comp,req_comp);
}

float *stbi_loadf_from_callbacks(stbi_io_callbacks const *clbk, void *user, int *x, int *y, int *comp, int req_comp)
{
   stbi__context s;
   stbi__start_callbacks(&s, (stbi_io_callbacks *) clbk, user);
   return stbi_loadf_main(&s,x,y,comp,req_comp);
}

#ifndef STBI_NO_STDIO
float *stbi_loadf(char const *filename, int *x, int *y, int *comp, int req_comp)
{
   float *result;
   FILE *f = stbi__fopen(filename, "rb");
   if (!f) return stbi__errpf("can't fopen", "Unable to open file");
   result = stbi_loadf_from_file(f,x,y,comp,req_comp);
   fclose(f);
   return result;
}

float *stbi_loadf_from_file(FILE *f, int *x, int *y, int *comp, int req_comp)
{
   stbi__context s;
   stbi__start_file(&s,f);
   return stbi_loadf_main(&s,x,y,comp,req_comp);
}
#endif // !STBI_NO_STDIO

#endif // !STBI_NO_HDR

// these is-hdr-or-not is defined independent of whether STBI_NO_HDR is
// defined, for API simplicity; if STBI_NO_HDR is defined, it always
// reports false!

int stbi_is_hdr_from_memory(stbi_uc const *buffer, int len)
{
   #ifndef STBI_NO_HDR
   stbi__context s;
   stbi__start_mem(&s,buffer,len);
   return stbi__hdr_test(&s);
   #else
   STBI_NOTUSED(buffer);
   STBI_NOTUSED(len);
   return 0;
   #endif
}

#ifndef STBI_NO_STDIO
STBIDEF int      stbi_is_hdr          (char const *filename)
{
   FILE *f = stbi__fopen(filename, "rb");
   int result=0;
   if (f) {
      result = stbi_is_hdr_from_file(f);
      fclose(f);
   }
   return result;
}

STBIDEF int      stbi_is_hdr_from_file(FILE *f)
{
   #ifndef STBI_NO_HDR
   stbi__context s;
   stbi__start_file(&s,f);
   return stbi__hdr_test(&s);
   #else
   return 0;
   #endif
}
#endif // !STBI_NO_STDIO

STBIDEF int      stbi_is_hdr_from_callbacks(stbi_io_callbacks const *clbk, void *user)
{
   #ifndef STBI_NO_HDR
   stbi__context s;
   stbi__start_callbacks(&s, (stbi_io_callbacks *) clbk, user);
   return stbi__hdr_test(&s);
   #else
   return 0;
   #endif
}

#ifndef STBI_NO_HDR
static float stbi__h2l_gamma_i=1.0f/2.2f, stbi__h2l_scale_i=1.0f;
static float stbi__l2h_gamma=2.2f, stbi__l2h_scale=1.0f;

void   stbi_hdr_to_ldr_gamma(float gamma) { stbi__h2l_gamma_i = 1/gamma; }
void   stbi_hdr_to_ldr_scale(float scale) { stbi__h2l_scale_i = 1/scale; }

void   stbi_ldr_to_hdr_gamma(float gamma) { stbi__l2h_gamma = gamma; }
void   stbi_ldr_to_hdr_scale(float scale) { stbi__l2h_scale = scale; }
#endif


//////////////////////////////////////////////////////////////////////////////
//
// Common code used by all image loaders
//

enum
{
   SCAN_load=0,
   SCAN_type,
   SCAN_header
};

static void stbi__refill_buffer(stbi__context *s)
{
   int n = (s->io.read)(s->io_user_data,(char*)s->buffer_start,s->buflen);
   if (n == 0) {
      // at end of file, treat same as if from memory, but need to handle case
      // where s->img_buffer isn't pointing to safe memory, e.g. 0-byte file
      s->read_from_callbacks = 0;
      s->img_buffer = s->buffer_start;
      s->img_buffer_end = s->buffer_start+1;
      *s->img_buffer = 0;
   } else {
      s->img_buffer = s->buffer_start;
      s->img_buffer_end = s->buffer_start + n;
   }
}

stbi_inline static stbi_uc stbi__get8(stbi__context *s)
{
   if (s->img_buffer < s->img_buffer_end)
      return *s->img_buffer++;
   if (s->read_from_callbacks) {
      stbi__refill_buffer(s);
      return *s->img_buffer++;
   }
   return 0;
}

stbi_inline static int stbi__at_eof(stbi__context *s)
{
   if (s->io.read) {
      if (!(s->io.eof)(s->io_user_data)) return 0;
      // if feof() is true, check if buffer = end
      // special case: we've only got the special 0 character at the end
      if (s->read_from_callbacks == 0) return 1;
   }

   return s->img_buffer >= s->img_buffer_end;   
}

static void stbi__skip(stbi__context *s, int n)
{
   if (s->io.read) {
      int blen = (int) (s->img_buffer_end - s->img_buffer);
      if (blen < n) {
         s->img_buffer = s->img_buffer_end;
         (s->io.skip)(s->io_user_data, n - blen);
         return;
      }
   }
   s->img_buffer += n;
}

static int stbi__getn(stbi__context *s, stbi_uc *buffer, int n)
{
   if (s->io.read) {
      int blen = (int) (s->img_buffer_end - s->img_buffer);
      if (blen < n) {
         int res, count;

         memcpy(buffer, s->img_buffer, blen);
         
         count = (s->io.read)(s->io_user_data, (char*) buffer + blen, n - blen);
         res = (count == (n-blen));
         s->img_buffer = s->img_buffer_end;
         return res;
      }
   }

   if (s->img_buffer+n <= s->img_buffer_end) {
      memcpy(buffer, s->img_buffer, n);
      s->img_buffer += n;
      return 1;
   } else
      return 0;
}

static int stbi__get16be(stbi__context *s)
{
   int z = stbi__get8(s);
   return (z << 8) + stbi__get8(s);
}

static stbi__uint32 stbi__get32be(stbi__context *s)
{
   stbi__uint32 z = stbi__get16be(s);
   return (z << 16) + stbi__get16be(s);
}

static int stbi__get16le(stbi__context *s)
{
   int z = stbi__get8(s);
   return z + (stbi__get8(s) << 8);
}

static stbi__uint32 stbi__get32le(stbi__context *s)
{
   stbi__uint32 z = stbi__get16le(s);
   return z + (stbi__get16le(s) << 16);
}

//////////////////////////////////////////////////////////////////////////////
//
//  generic converter from built-in img_n to req_comp
//    individual types do this automatically as much as possible (e.g. jpeg
//    does all cases internally since it needs to colorspace convert anyway,
//    and it never has alpha, so very few cases ). png can automatically
//    interleave an alpha=255 channel, but falls back to this for other cases
//
//  assume data buffer is malloced, so malloc a new one and free that one
//  only failure mode is malloc failing

static stbi_uc stbi__compute_y(int r, int g, int b)
{
   return (stbi_uc) (((r*77) + (g*150) +  (29*b)) >> 8);
}

static unsigned char *stbi__convert_format(unsigned char *data, int img_n, int req_comp, unsigned int x, unsigned int y)
{
   int i,j;
   unsigned char *good;

   if (req_comp == img_n) return data;
   STBI_ASSERT(req_comp >= 1 && req_comp <= 4);

   good = (unsigned char *) stbi__malloc(req_comp * x * y);
   if (good == NULL) {
      free(data);
      return stbi__errpuc("outofmem", "Out of memory");
   }

   for (j=0; j < (int) y; ++j) {
      unsigned char *src  = data + j * x * img_n   ;
      unsigned char *dest = good + j * x * req_comp;

      #define COMBO(a,b)  ((a)*8+(b))
      #define CASE(a,b)   case COMBO(a,b): for(i=x-1; i >= 0; --i, src += a, dest += b)
      // convert source image with img_n components to one with req_comp components;
      // avoid switch per pixel, so use switch per scanline and massive macros
      switch (COMBO(img_n, req_comp)) {
         CASE(1,2) dest[0]=src[0], dest[1]=255; break;
         CASE(1,3) dest[0]=dest[1]=dest[2]=src[0]; break;
         CASE(1,4) dest[0]=dest[1]=dest[2]=src[0], dest[3]=255; break;
         CASE(2,1) dest[0]=src[0]; break;
         CASE(2,3) dest[0]=dest[1]=dest[2]=src[0]; break;
         CASE(2,4) dest[0]=dest[1]=dest[2]=src[0], dest[3]=src[1]; break;
         CASE(3,4) dest[0]=src[0],dest[1]=src[1],dest[2]=src[2],dest[3]=255; break;
         CASE(3,1) dest[0]=stbi__compute_y(src[0],src[1],src[2]); break;
         CASE(3,2) dest[0]=stbi__compute_y(src[0],src[1],src[2]), dest[1] = 255; break;
         CASE(4,1) dest[0]=stbi__compute_y(src[0],src[1],src[2]); break;
         CASE(4,2) dest[0]=stbi__compute_y(src[0],src[1],src[2]), dest[1] = src[3]; break;
         CASE(4,3) dest[0]=src[0],dest[1]=src[1],dest[2]=src[2]; break;
         default: STBI_ASSERT(0);
      }
      #undef CASE
   }

   free(data);
   return good;
}

#ifndef STBI_NO_HDR
static float   *stbi__ldr_to_hdr(stbi_uc *data, int x, int y, int comp)
{
   int i,k,n;
   float *output = (float *) stbi__malloc(x * y * comp * sizeof(float));
   if (output == NULL) { free(data); return stbi__errpf("outofmem", "Out of memory"); }
   // compute number of non-alpha components
   if (comp & 1) n = comp; else n = comp-1;
   for (i=0; i < x*y; ++i) {
      for (k=0; k < n; ++k) {
         output[i*comp + k] = (float) (pow(data[i*comp+k]/255.0f, stbi__l2h_gamma) * stbi__l2h_scale);
      }
      if (k < comp) output[i*comp + k] = data[i*comp+k]/255.0f;
   }
   free(data);
   return output;
}

#define stbi__float2int(x)   ((int) (x))
static stbi_uc *stbi__hdr_to_ldr(float   *data, int x, int y, int comp)
{
   int i,k,n;
   stbi_uc *output = (stbi_uc *) stbi__malloc(x * y * comp);
   if (output == NULL) { free(data); return stbi__errpuc("outofmem", "Out of memory"); }
   // compute number of non-alpha components
   if (comp & 1) n = comp; else n = comp-1;
   for (i=0; i < x*y; ++i) {
      for (k=0; k < n; ++k) {
         float z = (float) pow(data[i*comp+k]*stbi__h2l_scale_i, stbi__h2l_gamma_i) * 255 + 0.5f;
         if (z < 0) z = 0;
         if (z > 255) z = 255;
         output[i*comp + k] = (stbi_uc) stbi__float2int(z);
      }
      if (k < comp) {
         float z = data[i*comp+k] * 255 + 0.5f;
         if (z < 0) z = 0;
         if (z > 255) z = 255;
         output[i*comp + k] = (stbi_uc) stbi__float2int(z);
      }
   }
   free(data);
   return output;
}
#endif

//////////////////////////////////////////////////////////////////////////////
//
//  "baseline" JPEG/JFIF decoder (not actually fully baseline implementation)
//
//    simple implementation
//      - channel subsampling of at most 2 in each dimension
//      - doesn't support delayed output of y-dimension
//      - simple interface (only one output format: 8-bit interleaved RGB)
//      - doesn't try to recover corrupt jpegs
//      - doesn't allow partial loading, loading multiple at once
//      - still fast on x86 (copying globals into locals doesn't help x86)
//      - allocates lots of intermediate memory (full size of all components)
//        - non-interleaved case requires this anyway
//        - allows good upsampling (see next)
//    high-quality
//      - upsampled channels are bilinearly interpolated, even across blocks
//      - quality integer IDCT derived from IJG's 'slow'
//    performance
//      - fast huffman; reasonable integer IDCT
//      - uses a lot of intermediate memory, could cache poorly
//      - load http://nothings.org/remote/anemones.jpg 3 times on 2.8Ghz P4
//          stb_jpeg:   1.34 seconds (MSVC6, default release build)
//          stb_jpeg:   1.06 seconds (MSVC6, processor = Pentium Pro)
//          IJL11.dll:  1.08 seconds (compiled by intel)
//          IJG 1998:   0.98 seconds (MSVC6, makefile provided by IJG)
//          IJG 1998:   0.95 seconds (MSVC6, makefile + proc=PPro)

// huffman decoding acceleration
#define FAST_BITS   9  // larger handles more cases; smaller stomps less cache

typedef struct
{
   stbi_uc  fast[1 << FAST_BITS];
   // weirdly, repacking this into AoS is a 10% speed loss, instead of a win
   stbi__uint16 code[256];
   stbi_uc  values[256];
   stbi_uc  size[257];
   unsigned int maxcode[18];
   int    delta[17];   // old 'firstsymbol' - old 'firstcode'
} stbi__huffman;

typedef struct
{
   #ifdef STBI_SIMD
   unsigned short dequant2[4][64];
   #endif
   stbi__context *s;
   stbi__huffman huff_dc[4];
   stbi__huffman huff_ac[4];
   stbi_uc dequant[4][64];

// sizes for components, interleaved MCUs
   int img_h_max, img_v_max;
   int img_mcu_x, img_mcu_y;
   int img_mcu_w, img_mcu_h;

// definition of jpeg image component
   struct
   {
      int id;
      int h,v;
      int tq;
      int hd,ha;
      int dc_pred;

      int x,y,w2,h2;
      stbi_uc *data;
      void *raw_data;
      stbi_uc *linebuf;
   } img_comp[4];

   stbi__uint32         code_buffer; // jpeg entropy-coded buffer
   int            code_bits;   // number of valid bits
   unsigned char  marker;      // marker seen while filling entropy buffer
   int            nomore;      // flag if we saw a marker so must stop

   int scan_n, order[4];
   int restart_interval, todo;
} stbi__jpeg;

static int stbi__build_huffman(stbi__huffman *h, int *count)
{
   int i,j,k=0,code;
   // build size list for each symbol (from JPEG spec)
   for (i=0; i < 16; ++i)
      for (j=0; j < count[i]; ++j)
         h->size[k++] = (stbi_uc) (i+1);
   h->size[k] = 0;

   // compute actual symbols (from jpeg spec)
   code = 0;
   k = 0;
   for(j=1; j <= 16; ++j) {
      // compute delta to add to code to compute symbol id
      h->delta[j] = k - code;
      if (h->size[k] == j) {
         while (h->size[k] == j)
            h->code[k++] = (stbi__uint16) (code++);
         if (code-1 >= (1 << j)) return stbi__err("bad code lengths","Corrupt JPEG");
      }
      // compute largest code + 1 for this size, preshifted as needed later
      h->maxcode[j] = code << (16-j);
      code <<= 1;
   }
   h->maxcode[j] = 0xffffffff;

   // build non-spec acceleration table; 255 is flag for not-accelerated
   memset(h->fast, 255, 1 << FAST_BITS);
   for (i=0; i < k; ++i) {
      int s = h->size[i];
      if (s <= FAST_BITS) {
         int c = h->code[i] << (FAST_BITS-s);
         int m = 1 << (FAST_BITS-s);
         for (j=0; j < m; ++j) {
            h->fast[c+j] = (stbi_uc) i;
         }
      }
   }
   return 1;
}

static void stbi__grow_buffer_unsafe(stbi__jpeg *j)
{
   do {
      int b = j->nomore ? 0 : stbi__get8(j->s);
      if (b == 0xff) {
         int c = stbi__get8(j->s);
         if (c != 0) {
            j->marker = (unsigned char) c;
            j->nomore = 1;
            return;
         }
      }
      j->code_buffer |= b << (24 - j->code_bits);
      j->code_bits += 8;
   } while (j->code_bits <= 24);
}

// (1 << n) - 1
static stbi__uint32 stbi__bmask[17]={0,1,3,7,15,31,63,127,255,511,1023,2047,4095,8191,16383,32767,65535};

// decode a jpeg huffman value from the bitstream
stbi_inline static int stbi__jpeg_huff_decode(stbi__jpeg *j, stbi__huffman *h)
{
   unsigned int temp;
   int c,k;

   if (j->code_bits < 16) stbi__grow_buffer_unsafe(j);

   // look at the top FAST_BITS and determine what symbol ID it is,
   // if the code is <= FAST_BITS
   c = (j->code_buffer >> (32 - FAST_BITS)) & ((1 << FAST_BITS)-1);
   k = h->fast[c];
   if (k < 255) {
      int s = h->size[k];
      if (s > j->code_bits)
         return -1;
      j->code_buffer <<= s;
      j->code_bits -= s;
      return h->values[k];
   }

   // naive test is to shift the code_buffer down so k bits are
   // valid, then test against maxcode. To speed this up, we've
   // preshifted maxcode left so that it has (16-k) 0s at the
   // end; in other words, regardless of the number of bits, it
   // wants to be compared against something shifted to have 16;
   // that way we don't need to shift inside the loop.
   temp = j->code_buffer >> 16;
   for (k=FAST_BITS+1 ; ; ++k)
      if (temp < h->maxcode[k])
         break;
   if (k == 17) {
      // error! code not found
      j->code_bits -= 16;
      return -1;
   }

   if (k > j->code_bits)
      return -1;

   // convert the huffman code to the symbol id
   c = ((j->code_buffer >> (32 - k)) & stbi__bmask[k]) + h->delta[k];
   STBI_ASSERT((((j->code_buffer) >> (32 - h->size[c])) & stbi__bmask[h->size[c]]) == h->code[c]);

   // convert the id to a symbol
   j->code_bits -= k;
   j->code_buffer <<= k;
   return h->values[c];
}

// combined JPEG 'receive' and JPEG 'extend', since baseline
// always extends everything it receives.
stbi_inline static int stbi__extend_receive(stbi__jpeg *j, int n)
{
   unsigned int m = 1 << (n-1);
   unsigned int k;
   if (j->code_bits < n) stbi__grow_buffer_unsafe(j);

   #if 1
   k = stbi_lrot(j->code_buffer, n);
   j->code_buffer = k & ~stbi__bmask[n];
   k &= stbi__bmask[n];
   j->code_bits -= n;
   #else
   k = (j->code_buffer >> (32 - n)) & stbi__bmask[n];
   j->code_bits -= n;
   j->code_buffer <<= n;
   #endif
   // the following test is probably a random branch that won't
   // predict well. I tried to table accelerate it but failed.
   // maybe it's compiling as a conditional move?
   if (k < m)
      return (-1 << n) + k + 1;
   else
      return k;
}

// given a value that's at position X in the zigzag stream,
// where does it appear in the 8x8 matrix coded as row-major?
static stbi_uc stbi__jpeg_dezigzag[64+15] =
{
    0,  1,  8, 16,  9,  2,  3, 10,
   17, 24, 32, 25, 18, 11,  4,  5,
   12, 19, 26, 33, 40, 48, 41, 34,
   27, 20, 13,  6,  7, 14, 21, 28,
   35, 42, 49, 56, 57, 50, 43, 36,
   29, 22, 15, 23, 30, 37, 44, 51,
   58, 59, 52, 45, 38, 31, 39, 46,
   53, 60, 61, 54, 47, 55, 62, 63,
   // let corrupt input sample past end
   63, 63, 63, 63, 63, 63, 63, 63,
   63, 63, 63, 63, 63, 63, 63
};

// decode one 64-entry block--
static int stbi__jpeg_decode_block(stbi__jpeg *j, short data[64], stbi__huffman *hdc, stbi__huffman *hac, int b)
{
   int diff,dc,k;
   int t = stbi__jpeg_huff_decode(j, hdc);
   if (t < 0) return stbi__err("bad huffman code","Corrupt JPEG");

   // 0 all the ac values now so we can do it 32-bits at a time
   memset(data,0,64*sizeof(data[0]));

   diff = t ? stbi__extend_receive(j, t) : 0;
   dc = j->img_comp[b].dc_pred + diff;
   j->img_comp[b].dc_pred = dc;
   data[0] = (short) dc;

   // decode AC components, see JPEG spec
   k = 1;
   do {
      int r,s;
      int rs = stbi__jpeg_huff_decode(j, hac);
      if (rs < 0) return stbi__err("bad huffman code","Corrupt JPEG");
      s = rs & 15;
      r = rs >> 4;
      if (s == 0) {
         if (rs != 0xf0) break; // end block
         k += 16;
      } else {
         k += r;
         // decode into unzigzag'd location
         data[stbi__jpeg_dezigzag[k++]] = (short) stbi__extend_receive(j,s);
      }
   } while (k < 64);
   return 1;
}

// take a -128..127 value and stbi__clamp it and convert to 0..255
stbi_inline static stbi_uc stbi__clamp(int x)
{
   // trick to use a single test to catch both cases
   if ((unsigned int) x > 255) {
      if (x < 0) return 0;
      if (x > 255) return 255;
   }
   return (stbi_uc) x;
}

#define stbi__f2f(x)  (int) (((x) * 4096 + 0.5))
#define stbi__fsh(x)  ((x) << 12)

// derived from jidctint -- DCT_ISLOW
#define STBI__IDCT_1D(s0,s1,s2,s3,s4,s5,s6,s7)       \
   int t0,t1,t2,t3,p1,p2,p3,p4,p5,x0,x1,x2,x3; \
   p2 = s2;                                    \
   p3 = s6;                                    \
   p1 = (p2+p3) * stbi__f2f(0.5411961f);             \
   t2 = p1 + p3*stbi__f2f(-1.847759065f);            \
   t3 = p1 + p2*stbi__f2f( 0.765366865f);            \
   p2 = s0;                                    \
   p3 = s4;                                    \
   t0 = stbi__fsh(p2+p3);                            \
   t1 = stbi__fsh(p2-p3);                            \
   x0 = t0+t3;                                 \
   x3 = t0-t3;                                 \
   x1 = t1+t2;                                 \
   x2 = t1-t2;                                 \
   t0 = s7;                                    \
   t1 = s5;                                    \
   t2 = s3;                                    \
   t3 = s1;                                    \
   p3 = t0+t2;                                 \
   p4 = t1+t3;                                 \
   p1 = t0+t3;                                 \
   p2 = t1+t2;                                 \
   p5 = (p3+p4)*stbi__f2f( 1.175875602f);            \
   t0 = t0*stbi__f2f( 0.298631336f);                 \
   t1 = t1*stbi__f2f( 2.053119869f);                 \
   t2 = t2*stbi__f2f( 3.072711026f);                 \
   t3 = t3*stbi__f2f( 1.501321110f);                 \
   p1 = p5 + p1*stbi__f2f(-0.899976223f);            \
   p2 = p5 + p2*stbi__f2f(-2.562915447f);            \
   p3 = p3*stbi__f2f(-1.961570560f);                 \
   p4 = p4*stbi__f2f(-0.390180644f);                 \
   t3 += p1+p4;                                \
   t2 += p2+p3;                                \
   t1 += p2+p4;                                \
   t0 += p1+p3;

#ifdef STBI_SIMD
typedef unsigned short stbi_dequantize_t;
#else
typedef stbi_uc stbi_dequantize_t;
#endif

// .344 seconds on 3*anemones.jpg
static void stbi__idct_block(stbi_uc *out, int out_stride, short data[64], stbi_dequantize_t *dequantize)
{
   int i,val[64],*v=val;
   stbi_dequantize_t *dq = dequantize;
   stbi_uc *o;
   short *d = data;

   // columns
   for (i=0; i < 8; ++i,++d,++dq, ++v) {
      // if all zeroes, shortcut -- this avoids dequantizing 0s and IDCTing
      if (d[ 8]==0 && d[16]==0 && d[24]==0 && d[32]==0
           && d[40]==0 && d[48]==0 && d[56]==0) {
         //    no shortcut                 0     seconds
         //    (1|2|3|4|5|6|7)==0          0     seconds
         //    all separate               -0.047 seconds
         //    1 && 2|3 && 4|5 && 6|7:    -0.047 seconds
         int dcterm = d[0] * dq[0] << 2;
         v[0] = v[8] = v[16] = v[24] = v[32] = v[40] = v[48] = v[56] = dcterm;
      } else {
         STBI__IDCT_1D(d[ 0]*dq[ 0],d[ 8]*dq[ 8],d[16]*dq[16],d[24]*dq[24],
                 d[32]*dq[32],d[40]*dq[40],d[48]*dq[48],d[56]*dq[56])
         // constants scaled things up by 1<<12; let's bring them back
         // down, but keep 2 extra bits of precision
         x0 += 512; x1 += 512; x2 += 512; x3 += 512;
         v[ 0] = (x0+t3) >> 10;
         v[56] = (x0-t3) >> 10;
         v[ 8] = (x1+t2) >> 10;
         v[48] = (x1-t2) >> 10;
         v[16] = (x2+t1) >> 10;
         v[40] = (x2-t1) >> 10;
         v[24] = (x3+t0) >> 10;
         v[32] = (x3-t0) >> 10;
      }
   }

   for (i=0, v=val, o=out; i < 8; ++i,v+=8,o+=out_stride) {
      // no fast case since the first 1D IDCT spread components out
      STBI__IDCT_1D(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7])
      // constants scaled things up by 1<<12, plus we had 1<<2 from first
      // loop, plus horizontal and vertical each scale by sqrt(8) so together
      // we've got an extra 1<<3, so 1<<17 total we need to remove.
      // so we want to round that, which means adding 0.5 * 1<<17,
      // aka 65536. Also, we'll end up with -128 to 127 that we want
      // to encode as 0..255 by adding 128, so we'll add that before the shift
      x0 += 65536 + (128<<17);
      x1 += 65536 + (128<<17);
      x2 += 65536 + (128<<17);
      x3 += 65536 + (128<<17);
      // tried computing the shifts into temps, or'ing the temps to see
      // if any were out of range, but that was slower
      o[0] = stbi__clamp((x0+t3) >> 17);
      o[7] = stbi__clamp((x0-t3) >> 17);
      o[1] = stbi__clamp((x1+t2) >> 17);
      o[6] = stbi__clamp((x1-t2) >> 17);
      o[2] = stbi__clamp((x2+t1) >> 17);
      o[5] = stbi__clamp((x2-t1) >> 17);
      o[3] = stbi__clamp((x3+t0) >> 17);
      o[4] = stbi__clamp((x3-t0) >> 17);
   }
}

#ifdef STBI_SIMD
static stbi_idct_8x8 stbi__idct_installed = stbi__idct_block;

STBIDEF void stbi_install_idct(stbi_idct_8x8 func)
{
   stbi__idct_installed = func;
}
#endif

#define STBI__MARKER_none  0xff
// if there's a pending marker from the entropy stream, return that
// otherwise, fetch from the stream and get a marker. if there's no
// marker, return 0xff, which is never a valid marker value
static stbi_uc stbi__get_marker(stbi__jpeg *j)
{
   stbi_uc x;
   if (j->marker != STBI__MARKER_none) { x = j->marker; j->marker = STBI__MARKER_none; return x; }
   x = stbi__get8(j->s);
   if (x != 0xff) return STBI__MARKER_none;
   while (x == 0xff)
      x = stbi__get8(j->s);
   return x;
}

// in each scan, we'll have scan_n components, and the order
// of the components is specified by order[]
#define STBI__RESTART(x)     ((x) >= 0xd0 && (x) <= 0xd7)

// after a restart interval, stbi__jpeg_reset the entropy decoder and
// the dc prediction
static void stbi__jpeg_reset(stbi__jpeg *j)
{
   j->code_bits = 0;
   j->code_buffer = 0;
   j->nomore = 0;
   j->img_comp[0].dc_pred = j->img_comp[1].dc_pred = j->img_comp[2].dc_pred = 0;
   j->marker = STBI__MARKER_none;
   j->todo = j->restart_interval ? j->restart_interval : 0x7fffffff;
   // no more than 1<<31 MCUs if no restart_interal? that's plenty safe,
   // since we don't even allow 1<<30 pixels
}

static int stbi__parse_entropy_coded_data(stbi__jpeg *z)
{
   stbi__jpeg_reset(z);
   if (z->scan_n == 1) {
      int i,j;
      #ifdef STBI_SIMD
      __declspec(align(16))
      #endif
      short data[64];
      int n = z->order[0];
      // non-interleaved data, we just need to process one block at a time,
      // in trivial scanline order
      // number of blocks to do just depends on how many actual "pixels" this
      // component has, independent of interleaved MCU blocking and such
      int w = (z->img_comp[n].x+7) >> 3;
      int h = (z->img_comp[n].y+7) >> 3;
      for (j=0; j < h; ++j) {
         for (i=0; i < w; ++i) {
            if (!stbi__jpeg_decode_block(z, data, z->huff_dc+z->img_comp[n].hd, z->huff_ac+z->img_comp[n].ha, n)) return 0;
            #ifdef STBI_SIMD
            stbi__idct_installed(z->img_comp[n].data+z->img_comp[n].w2*j*8+i*8, z->img_comp[n].w2, data, z->dequant2[z->img_comp[n].tq]);
            #else
            stbi__idct_block(z->img_comp[n].data+z->img_comp[n].w2*j*8+i*8, z->img_comp[n].w2, data, z->dequant[z->img_comp[n].tq]);
            #endif
            // every data block is an MCU, so countdown the restart interval
            if (--z->todo <= 0) {
               if (z->code_bits < 24) stbi__grow_buffer_unsafe(z);
               // if it's NOT a restart, then just bail, so we get corrupt data
               // rather than no data
               if (!STBI__RESTART(z->marker)) return 1;
               stbi__jpeg_reset(z);
            }
         }
      }
   } else { // interleaved!
      int i,j,k,x,y;
      short data[64];
      for (j=0; j < z->img_mcu_y; ++j) {
         for (i=0; i < z->img_mcu_x; ++i) {
            // scan an interleaved mcu... process scan_n components in order
            for (k=0; k < z->scan_n; ++k) {
               int n = z->order[k];
               // scan out an mcu's worth of this component; that's just determined
               // by the basic H and V specified for the component
               for (y=0; y < z->img_comp[n].v; ++y) {
                  for (x=0; x < z->img_comp[n].h; ++x) {
                     int x2 = (i*z->img_comp[n].h + x)*8;
                     int y2 = (j*z->img_comp[n].v + y)*8;
                     if (!stbi__jpeg_decode_block(z, data, z->huff_dc+z->img_comp[n].hd, z->huff_ac+z->img_comp[n].ha, n)) return 0;
                     #ifdef STBI_SIMD
                     stbi__idct_installed(z->img_comp[n].data+z->img_comp[n].w2*y2+x2, z->img_comp[n].w2, data, z->dequant2[z->img_comp[n].tq]);
                     #else
                     stbi__idct_block(z->img_comp[n].data+z->img_comp[n].w2*y2+x2, z->img_comp[n].w2, data, z->dequant[z->img_comp[n].tq]);
                     #endif
                  }
               }
            }
            // after all interleaved components, that's an interleaved MCU,
            // so now count down the restart interval
            if (--z->todo <= 0) {
               if (z->code_bits < 24) stbi__grow_buffer_unsafe(z);
               // if it's NOT a restart, then just bail, so we get corrupt data
               // rather than no data
               if (!STBI__RESTART(z->marker)) return 1;
               stbi__jpeg_reset(z);
            }
         }
      }
   }
   return 1;
}

static int stbi__process_marker(stbi__jpeg *z, int m)
{
   int L;
   switch (m) {
      case STBI__MARKER_none: // no marker found
         return stbi__err("expected marker","Corrupt JPEG");

      case 0xC2: // stbi__SOF - progressive
         return stbi__err("progressive jpeg","JPEG format not supported (progressive)");

      case 0xDD: // DRI - specify restart interval
         if (stbi__get16be(z->s) != 4) return stbi__err("bad DRI len","Corrupt JPEG");
         z->restart_interval = stbi__get16be(z->s);
         return 1;

      case 0xDB: // DQT - define quantization table
         L = stbi__get16be(z->s)-2;
         while (L > 0) {
            int q = stbi__get8(z->s);
            int p = q >> 4;
            int t = q & 15,i;
            if (p != 0) return stbi__err("bad DQT type","Corrupt JPEG");
            if (t > 3) return stbi__err("bad DQT table","Corrupt JPEG");
            for (i=0; i < 64; ++i)
               z->dequant[t][stbi__jpeg_dezigzag[i]] = stbi__get8(z->s);
            #ifdef STBI_SIMD
            for (i=0; i < 64; ++i)
               z->dequant2[t][i] = z->dequant[t][i];
            #endif
            L -= 65;
         }
         return L==0;

      case 0xC4: // DHT - define huffman table
         L = stbi__get16be(z->s)-2;
         while (L > 0) {
            stbi_uc *v;
            int sizes[16],i,n=0;
            int q = stbi__get8(z->s);
            int tc = q >> 4;
            int th = q & 15;
            if (tc > 1 || th > 3) return stbi__err("bad DHT header","Corrupt JPEG");
            for (i=0; i < 16; ++i) {
               sizes[i] = stbi__get8(z->s);
               n += sizes[i];
            }
            L -= 17;
            if (tc == 0) {
               if (!stbi__build_huffman(z->huff_dc+th, sizes)) return 0;
               v = z->huff_dc[th].values;
            } else {
               if (!stbi__build_huffman(z->huff_ac+th, sizes)) return 0;
               v = z->huff_ac[th].values;
            }
            for (i=0; i < n; ++i)
               v[i] = stbi__get8(z->s);
            L -= n;
         }
         return L==0;
   }
   // check for comment block or APP blocks
   if ((m >= 0xE0 && m <= 0xEF) || m == 0xFE) {
      stbi__skip(z->s, stbi__get16be(z->s)-2);
      return 1;
   }
   return 0;
}

// after we see stbi__SOS
static int stbi__process_scan_header(stbi__jpeg *z)
{
   int i;
   int Ls = stbi__get16be(z->s);
   z->scan_n = stbi__get8(z->s);
   if (z->scan_n < 1 || z->scan_n > 4 || z->scan_n > (int) z->s->img_n) return stbi__err("bad stbi__SOS component count","Corrupt JPEG");
   if (Ls != 6+2*z->scan_n) return stbi__err("bad stbi__SOS len","Corrupt JPEG");
   for (i=0; i < z->scan_n; ++i) {
      int id = stbi__get8(z->s), which;
      int q = stbi__get8(z->s);
      for (which = 0; which < z->s->img_n; ++which)
         if (z->img_comp[which].id == id)
            break;
      if (which == z->s->img_n) return 0;
      z->img_comp[which].hd = q >> 4;   if (z->img_comp[which].hd > 3) return stbi__err("bad DC huff","Corrupt JPEG");
      z->img_comp[which].ha = q & 15;   if (z->img_comp[which].ha > 3) return stbi__err("bad AC huff","Corrupt JPEG");
      z->order[i] = which;
   }
   if (stbi__get8(z->s) != 0) return stbi__err("bad stbi__SOS","Corrupt JPEG");
   stbi__get8(z->s); // should be 63, but might be 0
   if (stbi__get8(z->s) != 0) return stbi__err("bad stbi__SOS","Corrupt JPEG");

   return 1;
}

static int stbi__process_frame_header(stbi__jpeg *z, int scan)
{
   stbi__context *s = z->s;
   int Lf,p,i,q, h_max=1,v_max=1,c;
   Lf = stbi__get16be(s);         if (Lf < 11) return stbi__err("bad stbi__SOF len","Corrupt JPEG"); // JPEG
   p  = stbi__get8(s);          if (p != 8) return stbi__err("only 8-bit","JPEG format not supported: 8-bit only"); // JPEG baseline
   s->img_y = stbi__get16be(s);   if (s->img_y == 0) return stbi__err("no header height", "JPEG format not supported: delayed height"); // Legal, but we don't handle it--but neither does IJG
   s->img_x = stbi__get16be(s);   if (s->img_x == 0) return stbi__err("0 width","Corrupt JPEG"); // JPEG requires
   c = stbi__get8(s);
   if (c != 3 && c != 1) return stbi__err("bad component count","Corrupt JPEG");    // JFIF requires
   s->img_n = c;
   for (i=0; i < c; ++i) {
      z->img_comp[i].data = NULL;
      z->img_comp[i].linebuf = NULL;
   }

   if (Lf != 8+3*s->img_n) return stbi__err("bad stbi__SOF len","Corrupt JPEG");

   for (i=0; i < s->img_n; ++i) {
      z->img_comp[i].id = stbi__get8(s);
      if (z->img_comp[i].id != i+1)   // JFIF requires
         if (z->img_comp[i].id != i)  // some version of jpegtran outputs non-JFIF-compliant files!
            return stbi__err("bad component ID","Corrupt JPEG");
      q = stbi__get8(s);
      z->img_comp[i].h = (q >> 4);  if (!z->img_comp[i].h || z->img_comp[i].h > 4) return stbi__err("bad H","Corrupt JPEG");
      z->img_comp[i].v = q & 15;    if (!z->img_comp[i].v || z->img_comp[i].v > 4) return stbi__err("bad V","Corrupt JPEG");
      z->img_comp[i].tq = stbi__get8(s);  if (z->img_comp[i].tq > 3) return stbi__err("bad TQ","Corrupt JPEG");
   }

   if (scan != SCAN_load) return 1;

   if ((1 << 30) / s->img_x / s->img_n < s->img_y) return stbi__err("too large", "Image too large to decode");

   for (i=0; i < s->img_n; ++i) {
      if (z->img_comp[i].h > h_max) h_max = z->img_comp[i].h;
      if (z->img_comp[i].v > v_max) v_max = z->img_comp[i].v;
   }

   // compute interleaved mcu info
   z->img_h_max = h_max;
   z->img_v_max = v_max;
   z->img_mcu_w = h_max * 8;
   z->img_mcu_h = v_max * 8;
   z->img_mcu_x = (s->img_x + z->img_mcu_w-1) / z->img_mcu_w;
   z->img_mcu_y = (s->img_y + z->img_mcu_h-1) / z->img_mcu_h;

   for (i=0; i < s->img_n; ++i) {
      // number of effective pixels (e.g. for non-interleaved MCU)
      z->img_comp[i].x = (s->img_x * z->img_comp[i].h + h_max-1) / h_max;
      z->img_comp[i].y = (s->img_y * z->img_comp[i].v + v_max-1) / v_max;
      // to simplify generation, we'll allocate enough memory to decode
      // the bogus oversized data from using interleaved MCUs and their
      // big blocks (e.g. a 16x16 iMCU on an image of width 33); we won't
      // discard the extra data until colorspace conversion
      z->img_comp[i].w2 = z->img_mcu_x * z->img_comp[i].h * 8;
      z->img_comp[i].h2 = z->img_mcu_y * z->img_comp[i].v * 8;
      z->img_comp[i].raw_data = stbi__malloc(z->img_comp[i].w2 * z->img_comp[i].h2+15);
      if (z->img_comp[i].raw_data == NULL) {
         for(--i; i >= 0; --i) {
            free(z->img_comp[i].raw_data);
            z->img_comp[i].data = NULL;
         }
         return stbi__err("outofmem", "Out of memory");
      }
      // align blocks for installable-idct using mmx/sse
      z->img_comp[i].data = (stbi_uc*) (((size_t) z->img_comp[i].raw_data + 15) & ~15);
      z->img_comp[i].linebuf = NULL;
   }

   return 1;
}

// use comparisons since in some cases we handle more than one case (e.g. stbi__SOF)
#define stbi__DNL(x)         ((x) == 0xdc)
#define stbi__SOI(x)         ((x) == 0xd8)
#define stbi__EOI(x)         ((x) == 0xd9)
#define stbi__SOF(x)         ((x) == 0xc0 || (x) == 0xc1)
#define stbi__SOS(x)         ((x) == 0xda)

static int decode_jpeg_header(stbi__jpeg *z, int scan)
{
   int m;
   z->marker = STBI__MARKER_none; // initialize cached marker to empty
   m = stbi__get_marker(z);
   if (!stbi__SOI(m)) return stbi__err("no stbi__SOI","Corrupt JPEG");
   if (scan == SCAN_type) return 1;
   m = stbi__get_marker(z);
   while (!stbi__SOF(m)) {
      if (!stbi__process_marker(z,m)) return 0;
      m = stbi__get_marker(z);
      while (m == STBI__MARKER_none) {
         // some files have extra padding after their blocks, so ok, we'll scan
         if (stbi__at_eof(z->s)) return stbi__err("no stbi__SOF", "Corrupt JPEG");
         m = stbi__get_marker(z);
      }
   }
   if (!stbi__process_frame_header(z, scan)) return 0;
   return 1;
}

static int decode_jpeg_image(stbi__jpeg *j)
{
   int m;
   j->restart_interval = 0;
   if (!decode_jpeg_header(j, SCAN_load)) return 0;
   m = stbi__get_marker(j);
   while (!stbi__EOI(m)) {
      if (stbi__SOS(m)) {
         if (!stbi__process_scan_header(j)) return 0;
         if (!stbi__parse_entropy_coded_data(j)) return 0;
         if (j->marker == STBI__MARKER_none ) {
            // handle 0s at the end of image data from IP Kamera 9060
            while (!stbi__at_eof(j->s)) {
               int x = stbi__get8(j->s);
               if (x == 255) {
                  j->marker = stbi__get8(j->s);
                  break;
               } else if (x != 0) {
                  return 0;
               }
            }
            // if we reach eof without hitting a marker, stbi__get_marker() below will fail and we'll eventually return 0
         }
      } else {
         if (!stbi__process_marker(j, m)) return 0;
      }
      m = stbi__get_marker(j);
   }
   return 1;
}

// static jfif-centered resampling (across block boundaries)

typedef stbi_uc *(*resample_row_func)(stbi_uc *out, stbi_uc *in0, stbi_uc *in1,
                                    int w, int hs);

#define stbi__div4(x) ((stbi_uc) ((x) >> 2))

static stbi_uc *resample_row_1(stbi_uc *out, stbi_uc *in_near, stbi_uc *in_far, int w, int hs)
{
   STBI_NOTUSED(out);
   STBI_NOTUSED(in_far);
   STBI_NOTUSED(w);
   STBI_NOTUSED(hs);
   return in_near;
}

static stbi_uc* stbi__resample_row_v_2(stbi_uc *out, stbi_uc *in_near, stbi_uc *in_far, int w, int hs)
{
   // need to generate two samples vertically for every one in input
   int i;
   STBI_NOTUSED(hs);
   for (i=0; i < w; ++i)
      out[i] = stbi__div4(3*in_near[i] + in_far[i] + 2);
   return out;
}

static stbi_uc*  stbi__resample_row_h_2(stbi_uc *out, stbi_uc *in_near, stbi_uc *in_far, int w, int hs)
{
   // need to generate two samples horizontally for every one in input
   int i;
   stbi_uc *input = in_near;

   if (w == 1) {
      // if only one sample, can't do any interpolation
      out[0] = out[1] = input[0];
      return out;
   }

   out[0] = input[0];
   out[1] = stbi__div4(input[0]*3 + input[1] + 2);
   for (i=1; i < w-1; ++i) {
      int n = 3*input[i]+2;
      out[i*2+0] = stbi__div4(n+input[i-1]);
      out[i*2+1] = stbi__div4(n+input[i+1]);
   }
   out[i*2+0] = stbi__div4(input[w-2]*3 + input[w-1] + 2);
   out[i*2+1] = input[w-1];

   STBI_NOTUSED(in_far);
   STBI_NOTUSED(hs);

   return out;
}

#define stbi__div16(x) ((stbi_uc) ((x) >> 4))

static stbi_uc *stbi__resample_row_hv_2(stbi_uc *out, stbi_uc *in_near, stbi_uc *in_far, int w, int hs)
{
   // need to generate 2x2 samples for every one in input
   int i,t0,t1;
   if (w == 1) {
      out[0] = out[1] = stbi__div4(3*in_near[0] + in_far[0] + 2);
      return out;
   }

   t1 = 3*in_near[0] + in_far[0];
   out[0] = stbi__div4(t1+2);
   for (i=1; i < w; ++i) {
      t0 = t1;
      t1 = 3*in_near[i]+in_far[i];
      out[i*2-1] = stbi__div16(3*t0 + t1 + 8);
      out[i*2  ] = stbi__div16(3*t1 + t0 + 8);
   }
   out[w*2-1] = stbi__div4(t1+2);

   STBI_NOTUSED(hs);

   return out;
}

static stbi_uc *stbi__resample_row_generic(stbi_uc *out, stbi_uc *in_near, stbi_uc *in_far, int w, int hs)
{
   // resample with nearest-neighbor
   int i,j;
   STBI_NOTUSED(in_far);
   for (i=0; i < w; ++i)
      for (j=0; j < hs; ++j)
         out[i*hs+j] = in_near[i];
   return out;
}

#define float2fixed(x)  ((int) ((x) * 65536 + 0.5))

// 0.38 seconds on 3*anemones.jpg   (0.25 with processor = Pro)
// VC6 without processor=Pro is generating multiple LEAs per multiply!
static void stbi__YCbCr_to_RGB_row(stbi_uc *out, const stbi_uc *y, const stbi_uc *pcb, const stbi_uc *pcr, int count, int step)
{
   int i;
   for (i=0; i < count; ++i) {
      int y_fixed = (y[i] << 16) + 32768; // rounding
      int r,g,b;
      int cr = pcr[i] - 128;
      int cb = pcb[i] - 128;
      r = y_fixed + cr*float2fixed(1.40200f);
      g = y_fixed - cr*float2fixed(0.71414f) - cb*float2fixed(0.34414f);
      b = y_fixed                            + cb*float2fixed(1.77200f);
      r >>= 16;
      g >>= 16;
      b >>= 16;
      if ((unsigned) r > 255) { if (r < 0) r = 0; else r = 255; }
      if ((unsigned) g > 255) { if (g < 0) g = 0; else g = 255; }
      if ((unsigned) b > 255) { if (b < 0) b = 0; else b = 255; }
      out[0] = (stbi_uc)r;
      out[1] = (stbi_uc)g;
      out[2] = (stbi_uc)b;
      out[3] = 255;
      out += step;
   }
}

#ifdef STBI_SIMD
static stbi_YCbCr_to_RGB_run stbi__YCbCr_installed = stbi__YCbCr_to_RGB_row;

STBIDEF void stbi_install_YCbCr_to_RGB(stbi_YCbCr_to_RGB_run func)
{
   stbi__YCbCr_installed = func;
}
#endif


// clean up the temporary component buffers
static void stbi__cleanup_jpeg(stbi__jpeg *j)
{
   int i;
   for (i=0; i < j->s->img_n; ++i) {
      if (j->img_comp[i].raw_data) {
         free(j->img_comp[i].raw_data);
         j->img_comp[i].raw_data = NULL;
         j->img_comp[i].data = NULL;
      }
      if (j->img_comp[i].linebuf) {
         free(j->img_comp[i].linebuf);
         j->img_comp[i].linebuf = NULL;
      }
   }
}

typedef struct
{
   resample_row_func resample;
   stbi_uc *line0,*line1;
   int hs,vs;   // expansion factor in each axis
   int w_lores; // horizontal pixels pre-expansion 
   int ystep;   // how far through vertical expansion we are
   int ypos;    // which pre-expansion row we're on
} stbi__resample;

static stbi_uc *load_jpeg_image(stbi__jpeg *z, int *out_x, int *out_y, int *comp, int req_comp)
{
   int n, decode_n;
   z->s->img_n = 0; // make stbi__cleanup_jpeg safe

   // validate req_comp
   if (req_comp < 0 || req_comp > 4) return stbi__errpuc("bad req_comp", "Internal error");

   // load a jpeg image from whichever source
   if (!decode_jpeg_image(z)) { stbi__cleanup_jpeg(z); return NULL; }

   // determine actual number of components to generate
   n = req_comp ? req_comp : z->s->img_n;

   if (z->s->img_n == 3 && n < 3)
      decode_n = 1;
   else
      decode_n = z->s->img_n;

   // resample and color-convert
   {
      int k;
      unsigned int i,j;
      stbi_uc *output;
      stbi_uc *coutput[4];

      stbi__resample res_comp[4];

      for (k=0; k < decode_n; ++k) {
         stbi__resample *r = &res_comp[k];

         // allocate line buffer big enough for upsampling off the edges
         // with upsample factor of 4
         z->img_comp[k].linebuf = (stbi_uc *) stbi__malloc(z->s->img_x + 3);
         if (!z->img_comp[k].linebuf) { stbi__cleanup_jpeg(z); return stbi__errpuc("outofmem", "Out of memory"); }

         r->hs      = z->img_h_max / z->img_comp[k].h;
         r->vs      = z->img_v_max / z->img_comp[k].v;
         r->ystep   = r->vs >> 1;
         r->w_lores = (z->s->img_x + r->hs-1) / r->hs;
         r->ypos    = 0;
         r->line0   = r->line1 = z->img_comp[k].data;

         if      (r->hs == 1 && r->vs == 1) r->resample = resample_row_1;
         else if (r->hs == 1 && r->vs == 2) r->resample = stbi__resample_row_v_2;
         else if (r->hs == 2 && r->vs == 1) r->resample = stbi__resample_row_h_2;
         else if (r->hs == 2 && r->vs == 2) r->resample = stbi__resample_row_hv_2;
         else                               r->resample = stbi__resample_row_generic;
      }

      // can't error after this so, this is safe
      output = (stbi_uc *) stbi__malloc(n * z->s->img_x * z->s->img_y + 1);
      if (!output) { stbi__cleanup_jpeg(z); return stbi__errpuc("outofmem", "Out of memory"); }

      // now go ahead and resample
      for (j=0; j < z->s->img_y; ++j) {
         stbi_uc *out = output + n * z->s->img_x * j;
         for (k=0; k < decode_n; ++k) {
            stbi__resample *r = &res_comp[k];
            int y_bot = r->ystep >= (r->vs >> 1);
            coutput[k] = r->resample(z->img_comp[k].linebuf,
                                     y_bot ? r->line1 : r->line0,
                                     y_bot ? r->line0 : r->line1,
                                     r->w_lores, r->hs);
            if (++r->ystep >= r->vs) {
               r->ystep = 0;
               r->line0 = r->line1;
               if (++r->ypos < z->img_comp[k].y)
                  r->line1 += z->img_comp[k].w2;
            }
         }
         if (n >= 3) {
            stbi_uc *y = coutput[0];
            if (z->s->img_n == 3) {
               #ifdef STBI_SIMD
               stbi__YCbCr_installed(out, y, coutput[1], coutput[2], z->s->img_x, n);
               #else
               stbi__YCbCr_to_RGB_row(out, y, coutput[1], coutput[2], z->s->img_x, n);
               #endif
            } else
               for (i=0; i < z->s->img_x; ++i) {
                  out[0] = out[1] = out[2] = y[i];
                  out[3] = 255; // not used if n==3
                  out += n;
               }
         } else {
            stbi_uc *y = coutput[0];
            if (n == 1)
               for (i=0; i < z->s->img_x; ++i) out[i] = y[i];
            else
               for (i=0; i < z->s->img_x; ++i) *out++ = y[i], *out++ = 255;
         }
      }
      stbi__cleanup_jpeg(z);
      *out_x = z->s->img_x;
      *out_y = z->s->img_y;
      if (comp) *comp  = z->s->img_n; // report original components, not output
      return output;
   }
}

static unsigned char *stbi__jpeg_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   stbi__jpeg j;
   j.s = s;
   return load_jpeg_image(&j, x,y,comp,req_comp);
}

static int stbi__jpeg_test(stbi__context *s)
{
   int r;
   stbi__jpeg j;
   j.s = s;
   r = decode_jpeg_header(&j, SCAN_type);
   stbi__rewind(s);
   return r;
}

static int stbi__jpeg_info_raw(stbi__jpeg *j, int *x, int *y, int *comp)
{
   if (!decode_jpeg_header(j, SCAN_header)) {
      stbi__rewind( j->s );
      return 0;
   }
   if (x) *x = j->s->img_x;
   if (y) *y = j->s->img_y;
   if (comp) *comp = j->s->img_n;
   return 1;
}

static int stbi__jpeg_info(stbi__context *s, int *x, int *y, int *comp)
{
   stbi__jpeg j;
   j.s = s;
   return stbi__jpeg_info_raw(&j, x, y, comp);
}

// public domain zlib decode    v0.2  Sean Barrett 2006-11-18
//    simple implementation
//      - all input must be provided in an upfront buffer
//      - all output is written to a single output buffer (can malloc/realloc)
//    performance
//      - fast huffman

// fast-way is faster to check than jpeg huffman, but slow way is slower
#define STBI__ZFAST_BITS  9 // accelerate all cases in default tables
#define STBI__ZFAST_MASK  ((1 << STBI__ZFAST_BITS) - 1)

// zlib-style huffman encoding
// (jpegs packs from left, zlib from right, so can't share code)
typedef struct
{
   stbi__uint16 fast[1 << STBI__ZFAST_BITS];
   stbi__uint16 firstcode[16];
   int maxcode[17];
   stbi__uint16 firstsymbol[16];
   stbi_uc  size[288];
   stbi__uint16 value[288]; 
} stbi__zhuffman;

stbi_inline static int stbi__bitreverse16(int n)
{
  n = ((n & 0xAAAA) >>  1) | ((n & 0x5555) << 1);
  n = ((n & 0xCCCC) >>  2) | ((n & 0x3333) << 2);
  n = ((n & 0xF0F0) >>  4) | ((n & 0x0F0F) << 4);
  n = ((n & 0xFF00) >>  8) | ((n & 0x00FF) << 8);
  return n;
}

stbi_inline static int stbi__bit_reverse(int v, int bits)
{
   STBI_ASSERT(bits <= 16);
   // to bit reverse n bits, reverse 16 and shift
   // e.g. 11 bits, bit reverse and shift away 5
   return stbi__bitreverse16(v) >> (16-bits);
}

static int stbi__zbuild_huffman(stbi__zhuffman *z, stbi_uc *sizelist, int num)
{
   int i,k=0;
   int code, next_code[16], sizes[17];

   // DEFLATE spec for generating codes
   memset(sizes, 0, sizeof(sizes));
   memset(z->fast, 255, sizeof(z->fast));
   for (i=0; i < num; ++i) 
      ++sizes[sizelist[i]];
   sizes[0] = 0;
   for (i=1; i < 16; ++i)
      STBI_ASSERT(sizes[i] <= (1 << i));
   code = 0;
   for (i=1; i < 16; ++i) {
      next_code[i] = code;
      z->firstcode[i] = (stbi__uint16) code;
      z->firstsymbol[i] = (stbi__uint16) k;
      code = (code + sizes[i]);
      if (sizes[i])
         if (code-1 >= (1 << i)) return stbi__err("bad codelengths","Corrupt JPEG");
      z->maxcode[i] = code << (16-i); // preshift for inner loop
      code <<= 1;
      k += sizes[i];
   }
   z->maxcode[16] = 0x10000; // sentinel
   for (i=0; i < num; ++i) {
      int s = sizelist[i];
      if (s) {
         int c = next_code[s] - z->firstcode[s] + z->firstsymbol[s];
         z->size [c] = (stbi_uc     ) s;
         z->value[c] = (stbi__uint16) i;
         if (s <= STBI__ZFAST_BITS) {
            int k = stbi__bit_reverse(next_code[s],s);
            while (k < (1 << STBI__ZFAST_BITS)) {
               z->fast[k] = (stbi__uint16) c;
               k += (1 << s);
            }
         }
         ++next_code[s];
      }
   }
   return 1;
}

// zlib-from-memory implementation for PNG reading
//    because PNG allows splitting the zlib stream arbitrarily,
//    and it's annoying structurally to have PNG call ZLIB call PNG,
//    we require PNG read all the IDATs and combine them into a single
//    memory buffer

typedef struct
{
   stbi_uc *zbuffer, *zbuffer_end;
   int num_bits;
   stbi__uint32 code_buffer;

   char *zout;
   char *zout_start;
   char *zout_end;
   int   z_expandable;

   stbi__zhuffman z_length, z_distance;
} stbi__zbuf;

stbi_inline static stbi_uc stbi__zget8(stbi__zbuf *z)
{
   if (z->zbuffer >= z->zbuffer_end) return 0;
   return *z->zbuffer++;
}

static void stbi__fill_bits(stbi__zbuf *z)
{
   do {
      STBI_ASSERT(z->code_buffer < (1U << z->num_bits));
      z->code_buffer |= stbi__zget8(z) << z->num_bits;
      z->num_bits += 8;
   } while (z->num_bits <= 24);
}

stbi_inline static unsigned int stbi__zreceive(stbi__zbuf *z, int n)
{
   unsigned int k;
   if (z->num_bits < n) stbi__fill_bits(z);
   k = z->code_buffer & ((1 << n) - 1);
   z->code_buffer >>= n;
   z->num_bits -= n;
   return k;   
}

stbi_inline static int stbi__zhuffman_decode(stbi__zbuf *a, stbi__zhuffman *z)
{
   int b,s,k;
   if (a->num_bits < 16) stbi__fill_bits(a);
   b = z->fast[a->code_buffer & STBI__ZFAST_MASK];
   if (b < 0xffff) {
      s = z->size[b];
      a->code_buffer >>= s;
      a->num_bits -= s;
      return z->value[b];
   }

   // not resolved by fast table, so compute it the slow way
   // use jpeg approach, which requires MSbits at top
   k = stbi__bit_reverse(a->code_buffer, 16);
   for (s=STBI__ZFAST_BITS+1; ; ++s)
      if (k < z->maxcode[s])
         break;
   if (s == 16) return -1; // invalid code!
   // code size is s, so:
   b = (k >> (16-s)) - z->firstcode[s] + z->firstsymbol[s];
   STBI_ASSERT(z->size[b] == s);
   a->code_buffer >>= s;
   a->num_bits -= s;
   return z->value[b];
}

static int stbi__zexpand(stbi__zbuf *z, int n)  // need to make room for n bytes
{
   char *q;
   int cur, limit;
   if (!z->z_expandable) return stbi__err("output buffer limit","Corrupt PNG");
   cur   = (int) (z->zout     - z->zout_start);
   limit = (int) (z->zout_end - z->zout_start);
   while (cur + n > limit)
      limit *= 2;
   q = (char *) realloc(z->zout_start, limit);
   if (q == NULL) return stbi__err("outofmem", "Out of memory");
   z->zout_start = q;
   z->zout       = q + cur;
   z->zout_end   = q + limit;
   return 1;
}

static int stbi__zlength_base[31] = {
   3,4,5,6,7,8,9,10,11,13,
   15,17,19,23,27,31,35,43,51,59,
   67,83,99,115,131,163,195,227,258,0,0 };

static int stbi__zlength_extra[31]= 
{ 0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0 };

static int stbi__zdist_base[32] = { 1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,
257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577,0,0};

static int stbi__zdist_extra[32] =
{ 0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13};

static int stbi__parse_huffman_block(stbi__zbuf *a)
{
   for(;;) {
      int z = stbi__zhuffman_decode(a, &a->z_length);
      if (z < 256) {
         if (z < 0) return stbi__err("bad huffman code","Corrupt PNG"); // error in huffman codes
         if (a->zout >= a->zout_end) if (!stbi__zexpand(a, 1)) return 0;
         *a->zout++ = (char) z;
      } else {
         stbi_uc *p;
         int len,dist;
         if (z == 256) return 1;
         z -= 257;
         len = stbi__zlength_base[z];
         if (stbi__zlength_extra[z]) len += stbi__zreceive(a, stbi__zlength_extra[z]);
         z = stbi__zhuffman_decode(a, &a->z_distance);
         if (z < 0) return stbi__err("bad huffman code","Corrupt PNG");
         dist = stbi__zdist_base[z];
         if (stbi__zdist_extra[z]) dist += stbi__zreceive(a, stbi__zdist_extra[z]);
         if (a->zout - a->zout_start < dist) return stbi__err("bad dist","Corrupt PNG");
         if (a->zout + len > a->zout_end) if (!stbi__zexpand(a, len)) return 0;
         p = (stbi_uc *) (a->zout - dist);
         while (len--)
            *a->zout++ = *p++;
      }
   }
}

static int stbi__compute_huffman_codes(stbi__zbuf *a)
{
   static stbi_uc length_dezigzag[19] = { 16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15 };
   stbi__zhuffman z_codelength;
   stbi_uc lencodes[286+32+137];//padding for maximum single op
   stbi_uc codelength_sizes[19];
   int i,n;

   int hlit  = stbi__zreceive(a,5) + 257;
   int hdist = stbi__zreceive(a,5) + 1;
   int hclen = stbi__zreceive(a,4) + 4;

   memset(codelength_sizes, 0, sizeof(codelength_sizes));
   for (i=0; i < hclen; ++i) {
      int s = stbi__zreceive(a,3);
      codelength_sizes[length_dezigzag[i]] = (stbi_uc) s;
   }
   if (!stbi__zbuild_huffman(&z_codelength, codelength_sizes, 19)) return 0;

   n = 0;
   while (n < hlit + hdist) {
      int c = stbi__zhuffman_decode(a, &z_codelength);
      STBI_ASSERT(c >= 0 && c < 19);
      if (c < 16)
         lencodes[n++] = (stbi_uc) c;
      else if (c == 16) {
         c = stbi__zreceive(a,2)+3;
         memset(lencodes+n, lencodes[n-1], c);
         n += c;
      } else if (c == 17) {
         c = stbi__zreceive(a,3)+3;
         memset(lencodes+n, 0, c);
         n += c;
      } else {
         STBI_ASSERT(c == 18);
         c = stbi__zreceive(a,7)+11;
         memset(lencodes+n, 0, c);
         n += c;
      }
   }
   if (n != hlit+hdist) return stbi__err("bad codelengths","Corrupt PNG");
   if (!stbi__zbuild_huffman(&a->z_length, lencodes, hlit)) return 0;
   if (!stbi__zbuild_huffman(&a->z_distance, lencodes+hlit, hdist)) return 0;
   return 1;
}

static int stbi__parse_uncomperssed_block(stbi__zbuf *a)
{
   stbi_uc header[4];
   int len,nlen,k;
   if (a->num_bits & 7)
      stbi__zreceive(a, a->num_bits & 7); // discard
   // drain the bit-packed data into header
   k = 0;
   while (a->num_bits > 0) {
      header[k++] = (stbi_uc) (a->code_buffer & 255); // suppress MSVC run-time check
      a->code_buffer >>= 8;
      a->num_bits -= 8;
   }
   STBI_ASSERT(a->num_bits == 0);
   // now fill header the normal way
   while (k < 4)
      header[k++] = stbi__zget8(a);
   len  = header[1] * 256 + header[0];
   nlen = header[3] * 256 + header[2];
   if (nlen != (len ^ 0xffff)) return stbi__err("zlib corrupt","Corrupt PNG");
   if (a->zbuffer + len > a->zbuffer_end) return stbi__err("read past buffer","Corrupt PNG");
   if (a->zout + len > a->zout_end)
      if (!stbi__zexpand(a, len)) return 0;
   memcpy(a->zout, a->zbuffer, len);
   a->zbuffer += len;
   a->zout += len;
   return 1;
}

static int stbi__parse_zlib_header(stbi__zbuf *a)
{
   int cmf   = stbi__zget8(a);
   int cm    = cmf & 15;
   /* int cinfo = cmf >> 4; */
   int flg   = stbi__zget8(a);
   if ((cmf*256+flg) % 31 != 0) return stbi__err("bad zlib header","Corrupt PNG"); // zlib spec
   if (flg & 32) return stbi__err("no preset dict","Corrupt PNG"); // preset dictionary not allowed in png
   if (cm != 8) return stbi__err("bad compression","Corrupt PNG"); // DEFLATE required for png
   // window = 1 << (8 + cinfo)... but who cares, we fully buffer output
   return 1;
}

// @TODO: should statically initialize these for optimal thread safety
static stbi_uc stbi__zdefault_length[288], stbi__zdefault_distance[32];
static void stbi__init_zdefaults(void)
{
   int i;   // use <= to match clearly with spec
   for (i=0; i <= 143; ++i)     stbi__zdefault_length[i]   = 8;
   for (   ; i <= 255; ++i)     stbi__zdefault_length[i]   = 9;
   for (   ; i <= 279; ++i)     stbi__zdefault_length[i]   = 7;
   for (   ; i <= 287; ++i)     stbi__zdefault_length[i]   = 8;

   for (i=0; i <=  31; ++i)     stbi__zdefault_distance[i] = 5;
}

static int stbi__parse_zlib(stbi__zbuf *a, int parse_header)
{
   int final, type;
   if (parse_header)
      if (!stbi__parse_zlib_header(a)) return 0;
   a->num_bits = 0;
   a->code_buffer = 0;
   do {
      final = stbi__zreceive(a,1);
      type = stbi__zreceive(a,2);
      if (type == 0) {
         if (!stbi__parse_uncomperssed_block(a)) return 0;
      } else if (type == 3) {
         return 0;
      } else {
         if (type == 1) {
            // use fixed code lengths
            if (!stbi__zdefault_distance[31]) stbi__init_zdefaults();
            if (!stbi__zbuild_huffman(&a->z_length  , stbi__zdefault_length  , 288)) return 0;
            if (!stbi__zbuild_huffman(&a->z_distance, stbi__zdefault_distance,  32)) return 0;
         } else {
            if (!stbi__compute_huffman_codes(a)) return 0;
         }
         if (!stbi__parse_huffman_block(a)) return 0;
      }
   } while (!final);
   return 1;
}

static int stbi__do_zlib(stbi__zbuf *a, char *obuf, int olen, int exp, int parse_header)
{
   a->zout_start = obuf;
   a->zout       = obuf;
   a->zout_end   = obuf + olen;
   a->z_expandable = exp;

   return stbi__parse_zlib(a, parse_header);
}

STBIDEF char *stbi_zlib_decode_malloc_guesssize(const char *buffer, int len, int initial_size, int *outlen)
{
   stbi__zbuf a;
   char *p = (char *) stbi__malloc(initial_size);
   if (p == NULL) return NULL;
   a.zbuffer = (stbi_uc *) buffer;
   a.zbuffer_end = (stbi_uc *) buffer + len;
   if (stbi__do_zlib(&a, p, initial_size, 1, 1)) {
      if (outlen) *outlen = (int) (a.zout - a.zout_start);
      return a.zout_start;
   } else {
      free(a.zout_start);
      return NULL;
   }
}

STBIDEF char *stbi_zlib_decode_malloc(char const *buffer, int len, int *outlen)
{
   return stbi_zlib_decode_malloc_guesssize(buffer, len, 16384, outlen);
}

STBIDEF char *stbi_zlib_decode_malloc_guesssize_headerflag(const char *buffer, int len, int initial_size, int *outlen, int parse_header)
{
   stbi__zbuf a;
   char *p = (char *) stbi__malloc(initial_size);
   if (p == NULL) return NULL;
   a.zbuffer = (stbi_uc *) buffer;
   a.zbuffer_end = (stbi_uc *) buffer + len;
   if (stbi__do_zlib(&a, p, initial_size, 1, parse_header)) {
      if (outlen) *outlen = (int) (a.zout - a.zout_start);
      return a.zout_start;
   } else {
      free(a.zout_start);
      return NULL;
   }
}

STBIDEF int stbi_zlib_decode_buffer(char *obuffer, int olen, char const *ibuffer, int ilen)
{
   stbi__zbuf a;
   a.zbuffer = (stbi_uc *) ibuffer;
   a.zbuffer_end = (stbi_uc *) ibuffer + ilen;
   if (stbi__do_zlib(&a, obuffer, olen, 0, 1))
      return (int) (a.zout - a.zout_start);
   else
      return -1;
}

STBIDEF char *stbi_zlib_decode_noheader_malloc(char const *buffer, int len, int *outlen)
{
   stbi__zbuf a;
   char *p = (char *) stbi__malloc(16384);
   if (p == NULL) return NULL;
   a.zbuffer = (stbi_uc *) buffer;
   a.zbuffer_end = (stbi_uc *) buffer+len;
   if (stbi__do_zlib(&a, p, 16384, 1, 0)) {
      if (outlen) *outlen = (int) (a.zout - a.zout_start);
      return a.zout_start;
   } else {
      free(a.zout_start);
      return NULL;
   }
}

STBIDEF int stbi_zlib_decode_noheader_buffer(char *obuffer, int olen, const char *ibuffer, int ilen)
{
   stbi__zbuf a;
   a.zbuffer = (stbi_uc *) ibuffer;
   a.zbuffer_end = (stbi_uc *) ibuffer + ilen;
   if (stbi__do_zlib(&a, obuffer, olen, 0, 0))
      return (int) (a.zout - a.zout_start);
   else
      return -1;
}

// public domain "baseline" PNG decoder   v0.10  Sean Barrett 2006-11-18
//    simple implementation
//      - only 8-bit samples
//      - no CRC checking
//      - allocates lots of intermediate memory
//        - avoids problem of streaming data between subsystems
//        - avoids explicit window management
//    performance
//      - uses stb_zlib, a PD zlib implementation with fast huffman decoding


typedef struct
{
   stbi__uint32 length;
   stbi__uint32 type;
} stbi__pngchunk;

#define PNG_TYPE(a,b,c,d)  (((a) << 24) + ((b) << 16) + ((c) << 8) + (d))

static stbi__pngchunk stbi__get_chunk_header(stbi__context *s)
{
   stbi__pngchunk c;
   c.length = stbi__get32be(s);
   c.type   = stbi__get32be(s);
   return c;
}

static int stbi__check_png_header(stbi__context *s)
{
   static stbi_uc png_sig[8] = { 137,80,78,71,13,10,26,10 };
   int i;
   for (i=0; i < 8; ++i)
      if (stbi__get8(s) != png_sig[i]) return stbi__err("bad png sig","Not a PNG");
   return 1;
}

typedef struct
{
   stbi__context *s;
   stbi_uc *idata, *expanded, *out;
} stbi__png;


enum {
   STBI__F_none=0, STBI__F_sub=1, STBI__F_up=2, STBI__F_avg=3, STBI__F_paeth=4,
   STBI__F_avg_first, STBI__F_paeth_first
};

static stbi_uc first_row_filter[5] =
{
   STBI__F_none, STBI__F_sub, STBI__F_none, STBI__F_avg_first, STBI__F_paeth_first
};

static int stbi__paeth(int a, int b, int c)
{
   int p = a + b - c;
   int pa = abs(p-a);
   int pb = abs(p-b);
   int pc = abs(p-c);
   if (pa <= pb && pa <= pc) return a;
   if (pb <= pc) return b;
   return c;
}

#define STBI__BYTECAST(x)  ((stbi_uc) ((x) & 255))  // truncate int to byte without warnings

// create the png data from post-deflated data
static int stbi__create_png_image_raw(stbi__png *a, stbi_uc *raw, stbi__uint32 raw_len, int out_n, stbi__uint32 x, stbi__uint32 y)
{
   stbi__context *s = a->s;
   stbi__uint32 i,j,stride = x*out_n;
   int k;
   int img_n = s->img_n; // copy it into a local for later
   STBI_ASSERT(out_n == s->img_n || out_n == s->img_n+1);
   a->out = (stbi_uc *) stbi__malloc(x * y * out_n);
   if (!a->out) return stbi__err("outofmem", "Out of memory");
   if (s->img_x == x && s->img_y == y) {
      if (raw_len != (img_n * x + 1) * y) return stbi__err("not enough pixels","Corrupt PNG");
   } else { // interlaced:
      if (raw_len < (img_n * x + 1) * y) return stbi__err("not enough pixels","Corrupt PNG");
   }
   for (j=0; j < y; ++j) {
      stbi_uc *cur = a->out + stride*j;
      stbi_uc *prior = cur - stride;
      int filter = *raw++;
      if (filter > 4) return stbi__err("invalid filter","Corrupt PNG");
      // if first row, use special filter that doesn't sample previous row
      if (j == 0) filter = first_row_filter[filter];
      // handle first pixel explicitly
      for (k=0; k < img_n; ++k) {
         switch (filter) {
            case STBI__F_none       : cur[k] = raw[k]; break;
            case STBI__F_sub        : cur[k] = raw[k]; break;
            case STBI__F_up         : cur[k] = STBI__BYTECAST(raw[k] + prior[k]); break;
            case STBI__F_avg        : cur[k] = STBI__BYTECAST(raw[k] + (prior[k]>>1)); break;
            case STBI__F_paeth      : cur[k] = STBI__BYTECAST(raw[k] + stbi__paeth(0,prior[k],0)); break;
            case STBI__F_avg_first  : cur[k] = raw[k]; break;
            case STBI__F_paeth_first: cur[k] = raw[k]; break;
         }
      }
      if (img_n != out_n) cur[img_n] = 255;
      raw += img_n;
      cur += out_n;
      prior += out_n;
      // this is a little gross, so that we don't switch per-pixel or per-component
      if (img_n == out_n) {
         #define CASE(f) \
             case f:     \
                for (i=x-1; i >= 1; --i, raw+=img_n,cur+=img_n,prior+=img_n) \
                   for (k=0; k < img_n; ++k)
         switch (filter) {
            CASE(STBI__F_none)         cur[k] = raw[k]; break;
            CASE(STBI__F_sub)          cur[k] = STBI__BYTECAST(raw[k] + cur[k-img_n]); break;
            CASE(STBI__F_up)           cur[k] = STBI__BYTECAST(raw[k] + prior[k]); break;
            CASE(STBI__F_avg)          cur[k] = STBI__BYTECAST(raw[k] + ((prior[k] + cur[k-img_n])>>1)); break;
            CASE(STBI__F_paeth)        cur[k] = STBI__BYTECAST(raw[k] + stbi__paeth(cur[k-img_n],prior[k],prior[k-img_n])); break;
            CASE(STBI__F_avg_first)    cur[k] = STBI__BYTECAST(raw[k] + (cur[k-img_n] >> 1)); break;
            CASE(STBI__F_paeth_first)  cur[k] = STBI__BYTECAST(raw[k] + stbi__paeth(cur[k-img_n],0,0)); break;
         }
         #undef CASE
      } else {
         STBI_ASSERT(img_n+1 == out_n);
         #define CASE(f) \
             case f:     \
                for (i=x-1; i >= 1; --i, cur[img_n]=255,raw+=img_n,cur+=out_n,prior+=out_n) \
                   for (k=0; k < img_n; ++k)
         switch (filter) {
            CASE(STBI__F_none)         cur[k] = raw[k]; break;
            CASE(STBI__F_sub)          cur[k] = STBI__BYTECAST(raw[k] + cur[k-out_n]); break;
            CASE(STBI__F_up)           cur[k] = STBI__BYTECAST(raw[k] + prior[k]); break;
            CASE(STBI__F_avg)          cur[k] = STBI__BYTECAST(raw[k] + ((prior[k] + cur[k-out_n])>>1)); break;
            CASE(STBI__F_paeth)        cur[k] = STBI__BYTECAST(raw[k] + stbi__paeth(cur[k-out_n],prior[k],prior[k-out_n])); break;
            CASE(STBI__F_avg_first)    cur[k] = STBI__BYTECAST(raw[k] + (cur[k-out_n] >> 1)); break;
            CASE(STBI__F_paeth_first)  cur[k] = STBI__BYTECAST(raw[k] + stbi__paeth(cur[k-out_n],0,0)); break;
         }
         #undef CASE
      }
   }
   return 1;
}

static int stbi__create_png_image(stbi__png *a, stbi_uc *raw, stbi__uint32 raw_len, int out_n, int interlaced)
{
   stbi_uc *final;
   int p;
   if (!interlaced)
      return stbi__create_png_image_raw(a, raw, raw_len, out_n, a->s->img_x, a->s->img_y);

   // de-interlacing
   final = (stbi_uc *) stbi__malloc(a->s->img_x * a->s->img_y * out_n);
   for (p=0; p < 7; ++p) {
      int xorig[] = { 0,4,0,2,0,1,0 };
      int yorig[] = { 0,0,4,0,2,0,1 };
      int xspc[]  = { 8,8,4,4,2,2,1 };
      int yspc[]  = { 8,8,8,4,4,2,2 };
      int i,j,x,y;
      // pass1_x[4] = 0, pass1_x[5] = 1, pass1_x[12] = 1
      x = (a->s->img_x - xorig[p] + xspc[p]-1) / xspc[p];
      y = (a->s->img_y - yorig[p] + yspc[p]-1) / yspc[p];
      if (x && y) {
         if (!stbi__create_png_image_raw(a, raw, raw_len, out_n, x, y)) {
            free(final);
            return 0;
         }
         for (j=0; j < y; ++j)
            for (i=0; i < x; ++i)
               memcpy(final + (j*yspc[p]+yorig[p])*a->s->img_x*out_n + (i*xspc[p]+xorig[p])*out_n,
                      a->out + (j*x+i)*out_n, out_n);
         free(a->out);
         raw += (x*out_n+1)*y;
         raw_len -= (x*out_n+1)*y;
      }
   }
   a->out = final;

   return 1;
}

static int stbi__compute_transparency(stbi__png *z, stbi_uc tc[3], int out_n)
{
   stbi__context *s = z->s;
   stbi__uint32 i, pixel_count = s->img_x * s->img_y;
   stbi_uc *p = z->out;

   // compute color-based transparency, assuming we've
   // already got 255 as the alpha value in the output
   STBI_ASSERT(out_n == 2 || out_n == 4);

   if (out_n == 2) {
      for (i=0; i < pixel_count; ++i) {
         p[1] = (p[0] == tc[0] ? 0 : 255);
         p += 2;
      }
   } else {
      for (i=0; i < pixel_count; ++i) {
         if (p[0] == tc[0] && p[1] == tc[1] && p[2] == tc[2])
            p[3] = 0;
         p += 4;
      }
   }
   return 1;
}

static int stbi__expand_png_palette(stbi__png *a, stbi_uc *palette, int len, int pal_img_n)
{
   stbi__uint32 i, pixel_count = a->s->img_x * a->s->img_y;
   stbi_uc *p, *temp_out, *orig = a->out;

   p = (stbi_uc *) stbi__malloc(pixel_count * pal_img_n);
   if (p == NULL) return stbi__err("outofmem", "Out of memory");

   // between here and free(out) below, exitting would leak
   temp_out = p;

   if (pal_img_n == 3) {
      for (i=0; i < pixel_count; ++i) {
         int n = orig[i]*4;
         p[0] = palette[n  ];
         p[1] = palette[n+1];
         p[2] = palette[n+2];
         p += 3;
      }
   } else {
      for (i=0; i < pixel_count; ++i) {
         int n = orig[i]*4;
         p[0] = palette[n  ];
         p[1] = palette[n+1];
         p[2] = palette[n+2];
         p[3] = palette[n+3];
         p += 4;
      }
   }
   free(a->out);
   a->out = temp_out;

   STBI_NOTUSED(len);

   return 1;
}

static int stbi__unpremultiply_on_load = 0;
static int stbi__de_iphone_flag = 0;

STBIDEF void stbi_set_unpremultiply_on_load(int flag_true_if_should_unpremultiply)
{
   stbi__unpremultiply_on_load = flag_true_if_should_unpremultiply;
}

STBIDEF void stbi_convert_iphone_png_to_rgb(int flag_true_if_should_convert)
{
   stbi__de_iphone_flag = flag_true_if_should_convert;
}

static void stbi__de_iphone(stbi__png *z)
{
   stbi__context *s = z->s;
   stbi__uint32 i, pixel_count = s->img_x * s->img_y;
   stbi_uc *p = z->out;

   if (s->img_out_n == 3) {  // convert bgr to rgb
      for (i=0; i < pixel_count; ++i) {
         stbi_uc t = p[0];
         p[0] = p[2];
         p[2] = t;
         p += 3;
      }
   } else {
      STBI_ASSERT(s->img_out_n == 4);
      if (stbi__unpremultiply_on_load) {
         // convert bgr to rgb and unpremultiply
         for (i=0; i < pixel_count; ++i) {
            stbi_uc a = p[3];
            stbi_uc t = p[0];
            if (a) {
               p[0] = p[2] * 255 / a;
               p[1] = p[1] * 255 / a;
               p[2] =  t   * 255 / a;
            } else {
               p[0] = p[2];
               p[2] = t;
            } 
            p += 4;
         }
      } else {
         // convert bgr to rgb
         for (i=0; i < pixel_count; ++i) {
            stbi_uc t = p[0];
            p[0] = p[2];
            p[2] = t;
            p += 4;
         }
      }
   }
}

static int stbi__parse_png_file(stbi__png *z, int scan, int req_comp)
{
   stbi_uc palette[1024], pal_img_n=0;
   stbi_uc has_trans=0, tc[3];
   stbi__uint32 ioff=0, idata_limit=0, i, pal_len=0;
   int first=1,k,interlace=0, is_iphone=0;
   stbi__context *s = z->s;

   z->expanded = NULL;
   z->idata = NULL;
   z->out = NULL;

   if (!stbi__check_png_header(s)) return 0;

   if (scan == SCAN_type) return 1;

   for (;;) {
      stbi__pngchunk c = stbi__get_chunk_header(s);
      switch (c.type) {
         case PNG_TYPE('C','g','B','I'):
            is_iphone = 1;
            stbi__skip(s, c.length);
            break;
         case PNG_TYPE('I','H','D','R'): {
            int depth,color,comp,filter;
            if (!first) return stbi__err("multiple IHDR","Corrupt PNG");
            first = 0;
            if (c.length != 13) return stbi__err("bad IHDR len","Corrupt PNG");
            s->img_x = stbi__get32be(s); if (s->img_x > (1 << 24)) return stbi__err("too large","Very large image (corrupt?)");
            s->img_y = stbi__get32be(s); if (s->img_y > (1 << 24)) return stbi__err("too large","Very large image (corrupt?)");
            depth = stbi__get8(s);  if (depth != 8)        return stbi__err("8bit only","PNG not supported: 8-bit only");
            color = stbi__get8(s);  if (color > 6)         return stbi__err("bad ctype","Corrupt PNG");
            if (color == 3) pal_img_n = 3; else if (color & 1) return stbi__err("bad ctype","Corrupt PNG");
            comp  = stbi__get8(s);  if (comp) return stbi__err("bad comp method","Corrupt PNG");
            filter= stbi__get8(s);  if (filter) return stbi__err("bad filter method","Corrupt PNG");
            interlace = stbi__get8(s); if (interlace>1) return stbi__err("bad interlace method","Corrupt PNG");
            if (!s->img_x || !s->img_y) return stbi__err("0-pixel image","Corrupt PNG");
            if (!pal_img_n) {
               s->img_n = (color & 2 ? 3 : 1) + (color & 4 ? 1 : 0);
               if ((1 << 30) / s->img_x / s->img_n < s->img_y) return stbi__err("too large", "Image too large to decode");
               if (scan == SCAN_header) return 1;
            } else {
               // if paletted, then pal_n is our final components, and
               // img_n is # components to decompress/filter.
               s->img_n = 1;
               if ((1 << 30) / s->img_x / 4 < s->img_y) return stbi__err("too large","Corrupt PNG");
               // if SCAN_header, have to scan to see if we have a tRNS
            }
            break;
         }

         case PNG_TYPE('P','L','T','E'):  {
            if (first) return stbi__err("first not IHDR", "Corrupt PNG");
            if (c.length > 256*3) return stbi__err("invalid PLTE","Corrupt PNG");
            pal_len = c.length / 3;
            if (pal_len * 3 != c.length) return stbi__err("invalid PLTE","Corrupt PNG");
            for (i=0; i < pal_len; ++i) {
               palette[i*4+0] = stbi__get8(s);
               palette[i*4+1] = stbi__get8(s);
               palette[i*4+2] = stbi__get8(s);
               palette[i*4+3] = 255;
            }
            break;
         }

         case PNG_TYPE('t','R','N','S'): {
            if (first) return stbi__err("first not IHDR", "Corrupt PNG");
            if (z->idata) return stbi__err("tRNS after IDAT","Corrupt PNG");
            if (pal_img_n) {
               if (scan == SCAN_header) { s->img_n = 4; return 1; }
               if (pal_len == 0) return stbi__err("tRNS before PLTE","Corrupt PNG");
               if (c.length > pal_len) return stbi__err("bad tRNS len","Corrupt PNG");
               pal_img_n = 4;
               for (i=0; i < c.length; ++i)
                  palette[i*4+3] = stbi__get8(s);
            } else {
               if (!(s->img_n & 1)) return stbi__err("tRNS with alpha","Corrupt PNG");
               if (c.length != (stbi__uint32) s->img_n*2) return stbi__err("bad tRNS len","Corrupt PNG");
               has_trans = 1;
               for (k=0; k < s->img_n; ++k)
                  tc[k] = (stbi_uc) (stbi__get16be(s) & 255); // non 8-bit images will be larger
            }
            break;
         }

         case PNG_TYPE('I','D','A','T'): {
            if (first) return stbi__err("first not IHDR", "Corrupt PNG");
            if (pal_img_n && !pal_len) return stbi__err("no PLTE","Corrupt PNG");
            if (scan == SCAN_header) { s->img_n = pal_img_n; return 1; }
            if (ioff + c.length > idata_limit) {
               stbi_uc *p;
               if (idata_limit == 0) idata_limit = c.length > 4096 ? c.length : 4096;
               while (ioff + c.length > idata_limit)
                  idata_limit *= 2;
               p = (stbi_uc *) realloc(z->idata, idata_limit); if (p == NULL) return stbi__err("outofmem", "Out of memory");
               z->idata = p;
            }
            if (!stbi__getn(s, z->idata+ioff,c.length)) return stbi__err("outofdata","Corrupt PNG");
            ioff += c.length;
            break;
         }

         case PNG_TYPE('I','E','N','D'): {
            stbi__uint32 raw_len;
            if (first) return stbi__err("first not IHDR", "Corrupt PNG");
            if (scan != SCAN_load) return 1;
            if (z->idata == NULL) return stbi__err("no IDAT","Corrupt PNG");
            z->expanded = (stbi_uc *) stbi_zlib_decode_malloc_guesssize_headerflag((char *) z->idata, ioff, 16384, (int *) &raw_len, !is_iphone);
            if (z->expanded == NULL) return 0; // zlib should set error
            free(z->idata); z->idata = NULL;
            if ((req_comp == s->img_n+1 && req_comp != 3 && !pal_img_n) || has_trans)
               s->img_out_n = s->img_n+1;
            else
               s->img_out_n = s->img_n;
            if (!stbi__create_png_image(z, z->expanded, raw_len, s->img_out_n, interlace)) return 0;
            if (has_trans)
               if (!stbi__compute_transparency(z, tc, s->img_out_n)) return 0;
            if (is_iphone && stbi__de_iphone_flag && s->img_out_n > 2)
               stbi__de_iphone(z);
            if (pal_img_n) {
               // pal_img_n == 3 or 4
               s->img_n = pal_img_n; // record the actual colors we had
               s->img_out_n = pal_img_n;
               if (req_comp >= 3) s->img_out_n = req_comp;
               if (!stbi__expand_png_palette(z, palette, pal_len, s->img_out_n))
                  return 0;
            }
            free(z->expanded); z->expanded = NULL;
            return 1;
         }

         default:
            // if critical, fail
            if (first) return stbi__err("first not IHDR", "Corrupt PNG");
            if ((c.type & (1 << 29)) == 0) {
               #ifndef STBI_NO_FAILURE_STRINGS
               // not threadsafe
               static char invalid_chunk[] = "XXXX PNG chunk not known";
               invalid_chunk[0] = STBI__BYTECAST(c.type >> 24);
               invalid_chunk[1] = STBI__BYTECAST(c.type >> 16);
               invalid_chunk[2] = STBI__BYTECAST(c.type >>  8);
               invalid_chunk[3] = STBI__BYTECAST(c.type >>  0);
               #endif
               return stbi__err(invalid_chunk, "PNG not supported: unknown PNG chunk type");
            }
            stbi__skip(s, c.length);
            break;
      }
      // end of PNG chunk, read and skip CRC
      stbi__get32be(s);
   }
}

static unsigned char *stbi__do_png(stbi__png *p, int *x, int *y, int *n, int req_comp)
{
   unsigned char *result=NULL;
   if (req_comp < 0 || req_comp > 4) return stbi__errpuc("bad req_comp", "Internal error");
   if (stbi__parse_png_file(p, SCAN_load, req_comp)) {
      result = p->out;
      p->out = NULL;
      if (req_comp && req_comp != p->s->img_out_n) {
         result = stbi__convert_format(result, p->s->img_out_n, req_comp, p->s->img_x, p->s->img_y);
         p->s->img_out_n = req_comp;
         if (result == NULL) return result;
      }
      *x = p->s->img_x;
      *y = p->s->img_y;
      if (n) *n = p->s->img_out_n;
   }
   free(p->out);      p->out      = NULL;
   free(p->expanded); p->expanded = NULL;
   free(p->idata);    p->idata    = NULL;

   return result;
}

static unsigned char *stbi__png_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   stbi__png p;
   p.s = s;
   return stbi__do_png(&p, x,y,comp,req_comp);
}

static int stbi__png_test(stbi__context *s)
{
   int r;
   r = stbi__check_png_header(s);
   stbi__rewind(s);
   return r;
}

static int stbi__png_info_raw(stbi__png *p, int *x, int *y, int *comp)
{
   if (!stbi__parse_png_file(p, SCAN_header, 0)) {
      stbi__rewind( p->s );
      return 0;
   }
   if (x) *x = p->s->img_x;
   if (y) *y = p->s->img_y;
   if (comp) *comp = p->s->img_n;
   return 1;
}

static int stbi__png_info(stbi__context *s, int *x, int *y, int *comp)
{
   stbi__png p;
   p.s = s;
   return stbi__png_info_raw(&p, x, y, comp);
}

// Microsoft/Windows BMP image
static int stbi__bmp_test_raw(stbi__context *s)
{
   int r;
   int sz;
   if (stbi__get8(s) != 'B') return 0;
   if (stbi__get8(s) != 'M') return 0;
   stbi__get32le(s); // discard filesize
   stbi__get16le(s); // discard reserved
   stbi__get16le(s); // discard reserved
   stbi__get32le(s); // discard data offset
   sz = stbi__get32le(s);
   r = (sz == 12 || sz == 40 || sz == 56 || sz == 108 || sz == 124);
   return r;
}

static int stbi__bmp_test(stbi__context *s)
{
   int r = stbi__bmp_test_raw(s);
   stbi__rewind(s);
   return r;
}


// returns 0..31 for the highest set bit
static int stbi__high_bit(unsigned int z)
{
   int n=0;
   if (z == 0) return -1;
   if (z >= 0x10000) n += 16, z >>= 16;
   if (z >= 0x00100) n +=  8, z >>=  8;
   if (z >= 0x00010) n +=  4, z >>=  4;
   if (z >= 0x00004) n +=  2, z >>=  2;
   if (z >= 0x00002) n +=  1, z >>=  1;
   return n;
}

static int stbi__bitcount(unsigned int a)
{
   a = (a & 0x55555555) + ((a >>  1) & 0x55555555); // max 2
   a = (a & 0x33333333) + ((a >>  2) & 0x33333333); // max 4
   a = (a + (a >> 4)) & 0x0f0f0f0f; // max 8 per 4, now 8 bits
   a = (a + (a >> 8)); // max 16 per 8 bits
   a = (a + (a >> 16)); // max 32 per 8 bits
   return a & 0xff;
}

static int stbi__shiftsigned(int v, int shift, int bits)
{
   int result;
   int z=0;

   if (shift < 0) v <<= -shift;
   else v >>= shift;
   result = v;

   z = bits;
   while (z < 8) {
      result += v >> z;
      z += bits;
   }
   return result;
}

static stbi_uc *stbi__bmp_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   stbi_uc *out;
   unsigned int mr=0,mg=0,mb=0,ma=0, fake_a=0;
   stbi_uc pal[256][4];
   int psize=0,i,j,compress=0,width;
   int bpp, flip_vertically, pad, target, offset, hsz;
   if (stbi__get8(s) != 'B' || stbi__get8(s) != 'M') return stbi__errpuc("not BMP", "Corrupt BMP");
   stbi__get32le(s); // discard filesize
   stbi__get16le(s); // discard reserved
   stbi__get16le(s); // discard reserved
   offset = stbi__get32le(s);
   hsz = stbi__get32le(s);
   if (hsz != 12 && hsz != 40 && hsz != 56 && hsz != 108 && hsz != 124) return stbi__errpuc("unknown BMP", "BMP type not supported: unknown");
   if (hsz == 12) {
      s->img_x = stbi__get16le(s);
      s->img_y = stbi__get16le(s);
   } else {
      s->img_x = stbi__get32le(s);
      s->img_y = stbi__get32le(s);
   }
   if (stbi__get16le(s) != 1) return stbi__errpuc("bad BMP", "bad BMP");
   bpp = stbi__get16le(s);
   if (bpp == 1) return stbi__errpuc("monochrome", "BMP type not supported: 1-bit");
   flip_vertically = ((int) s->img_y) > 0;
   s->img_y = abs((int) s->img_y);
   if (hsz == 12) {
      if (bpp < 24)
         psize = (offset - 14 - 24) / 3;
   } else {
      compress = stbi__get32le(s);
      if (compress == 1 || compress == 2) return stbi__errpuc("BMP RLE", "BMP type not supported: RLE");
      stbi__get32le(s); // discard sizeof
      stbi__get32le(s); // discard hres
      stbi__get32le(s); // discard vres
      stbi__get32le(s); // discard colorsused
      stbi__get32le(s); // discard max important
      if (hsz == 40 || hsz == 56) {
         if (hsz == 56) {
            stbi__get32le(s);
            stbi__get32le(s);
            stbi__get32le(s);
            stbi__get32le(s);
         }
         if (bpp == 16 || bpp == 32) {
            mr = mg = mb = 0;
            if (compress == 0) {
               if (bpp == 32) {
                  mr = 0xffu << 16;
                  mg = 0xffu <<  8;
                  mb = 0xffu <<  0;
                  ma = 0xffu << 24;
                  fake_a = 1; // @TODO: check for cases like alpha value is all 0 and switch it to 255
                  STBI_NOTUSED(fake_a);
               } else {
                  mr = 31u << 10;
                  mg = 31u <<  5;
                  mb = 31u <<  0;
               }
            } else if (compress == 3) {
               mr = stbi__get32le(s);
               mg = stbi__get32le(s);
               mb = stbi__get32le(s);
               // not documented, but generated by photoshop and handled by mspaint
               if (mr == mg && mg == mb) {
                  // ?!?!?
                  return stbi__errpuc("bad BMP", "bad BMP");
               }
            } else
               return stbi__errpuc("bad BMP", "bad BMP");
         }
      } else {
         STBI_ASSERT(hsz == 108 || hsz == 124);
         mr = stbi__get32le(s);
         mg = stbi__get32le(s);
         mb = stbi__get32le(s);
         ma = stbi__get32le(s);
         stbi__get32le(s); // discard color space
         for (i=0; i < 12; ++i)
            stbi__get32le(s); // discard color space parameters
         if (hsz == 124) {
            stbi__get32le(s); // discard rendering intent
            stbi__get32le(s); // discard offset of profile data
            stbi__get32le(s); // discard size of profile data
            stbi__get32le(s); // discard reserved
         }
      }
      if (bpp < 16)
         psize = (offset - 14 - hsz) >> 2;
   }
   s->img_n = ma ? 4 : 3;
   if (req_comp && req_comp >= 3) // we can directly decode 3 or 4
      target = req_comp;
   else
      target = s->img_n; // if they want monochrome, we'll post-convert
   out = (stbi_uc *) stbi__malloc(target * s->img_x * s->img_y);
   if (!out) return stbi__errpuc("outofmem", "Out of memory");
   if (bpp < 16) {
      int z=0;
      if (psize == 0 || psize > 256) { free(out); return stbi__errpuc("invalid", "Corrupt BMP"); }
      for (i=0; i < psize; ++i) {
         pal[i][2] = stbi__get8(s);
         pal[i][1] = stbi__get8(s);
         pal[i][0] = stbi__get8(s);
         if (hsz != 12) stbi__get8(s);
         pal[i][3] = 255;
      }
      stbi__skip(s, offset - 14 - hsz - psize * (hsz == 12 ? 3 : 4));
      if (bpp == 4) width = (s->img_x + 1) >> 1;
      else if (bpp == 8) width = s->img_x;
      else { free(out); return stbi__errpuc("bad bpp", "Corrupt BMP"); }
      pad = (-width)&3;
      for (j=0; j < (int) s->img_y; ++j) {
         for (i=0; i < (int) s->img_x; i += 2) {
            int v=stbi__get8(s),v2=0;
            if (bpp == 4) {
               v2 = v & 15;
               v >>= 4;
            }
            out[z++] = pal[v][0];
            out[z++] = pal[v][1];
            out[z++] = pal[v][2];
            if (target == 4) out[z++] = 255;
            if (i+1 == (int) s->img_x) break;
            v = (bpp == 8) ? stbi__get8(s) : v2;
            out[z++] = pal[v][0];
            out[z++] = pal[v][1];
            out[z++] = pal[v][2];
            if (target == 4) out[z++] = 255;
         }
         stbi__skip(s, pad);
      }
   } else {
      int rshift=0,gshift=0,bshift=0,ashift=0,rcount=0,gcount=0,bcount=0,acount=0;
      int z = 0;
      int easy=0;
      stbi__skip(s, offset - 14 - hsz);
      if (bpp == 24) width = 3 * s->img_x;
      else if (bpp == 16) width = 2*s->img_x;
      else /* bpp = 32 and pad = 0 */ width=0;
      pad = (-width) & 3;
      if (bpp == 24) {
         easy = 1;
      } else if (bpp == 32) {
         if (mb == 0xff && mg == 0xff00 && mr == 0x00ff0000 && ma == 0xff000000)
            easy = 2;
      }
      if (!easy) {
         if (!mr || !mg || !mb) { free(out); return stbi__errpuc("bad masks", "Corrupt BMP"); }
         // right shift amt to put high bit in position #7
         rshift = stbi__high_bit(mr)-7; rcount = stbi__bitcount(mr);
         gshift = stbi__high_bit(mg)-7; gcount = stbi__bitcount(mg);
         bshift = stbi__high_bit(mb)-7; bcount = stbi__bitcount(mb);
         ashift = stbi__high_bit(ma)-7; acount = stbi__bitcount(ma);
      }
      for (j=0; j < (int) s->img_y; ++j) {
         if (easy) {
            for (i=0; i < (int) s->img_x; ++i) {
               unsigned char a;
               out[z+2] = stbi__get8(s);
               out[z+1] = stbi__get8(s);
               out[z+0] = stbi__get8(s);
               z += 3;
               a = (easy == 2 ? stbi__get8(s) : 255);
               if (target == 4) out[z++] = a;
            }
         } else {
            for (i=0; i < (int) s->img_x; ++i) {
               stbi__uint32 v = (stbi__uint32) (bpp == 16 ? stbi__get16le(s) : stbi__get32le(s));
               int a;
               out[z++] = STBI__BYTECAST(stbi__shiftsigned(v & mr, rshift, rcount));
               out[z++] = STBI__BYTECAST(stbi__shiftsigned(v & mg, gshift, gcount));
               out[z++] = STBI__BYTECAST(stbi__shiftsigned(v & mb, bshift, bcount));
               a = (ma ? stbi__shiftsigned(v & ma, ashift, acount) : 255);
               if (target == 4) out[z++] = STBI__BYTECAST(a); 
            }
         }
         stbi__skip(s, pad);
      }
   }
   if (flip_vertically) {
      stbi_uc t;
      for (j=0; j < (int) s->img_y>>1; ++j) {
         stbi_uc *p1 = out +      j     *s->img_x*target;
         stbi_uc *p2 = out + (s->img_y-1-j)*s->img_x*target;
         for (i=0; i < (int) s->img_x*target; ++i) {
            t = p1[i], p1[i] = p2[i], p2[i] = t;
         }
      }
   }

   if (req_comp && req_comp != target) {
      out = stbi__convert_format(out, target, req_comp, s->img_x, s->img_y);
      if (out == NULL) return out; // stbi__convert_format frees input on failure
   }

   *x = s->img_x;
   *y = s->img_y;
   if (comp) *comp = s->img_n;
   return out;
}

// Targa Truevision - TGA
// by Jonathan Dummer

static int stbi__tga_info(stbi__context *s, int *x, int *y, int *comp)
{
    int tga_w, tga_h, tga_comp;
    int sz;
    stbi__get8(s);                   // discard Offset
    sz = stbi__get8(s);              // color type
    if( sz > 1 ) {
        stbi__rewind(s);
        return 0;      // only RGB or indexed allowed
    }
    sz = stbi__get8(s);              // image type
    // only RGB or grey allowed, +/- RLE
    if ((sz != 1) && (sz != 2) && (sz != 3) && (sz != 9) && (sz != 10) && (sz != 11)) return 0;
    stbi__skip(s,9);
    tga_w = stbi__get16le(s);
    if( tga_w < 1 ) {
        stbi__rewind(s);
        return 0;   // test width
    }
    tga_h = stbi__get16le(s);
    if( tga_h < 1 ) {
        stbi__rewind(s);
        return 0;   // test height
    }
    sz = stbi__get8(s);               // bits per pixel
    // only RGB or RGBA or grey allowed
    if ((sz != 8) && (sz != 16) && (sz != 24) && (sz != 32)) {
        stbi__rewind(s);
        return 0;
    }
    tga_comp = sz;
    if (x) *x = tga_w;
    if (y) *y = tga_h;
    if (comp) *comp = tga_comp / 8;
    return 1;                   // seems to have passed everything
}

static int stbi__tga_test(stbi__context *s)
{
   int res;
   int sz;
   stbi__get8(s);      //   discard Offset
   sz = stbi__get8(s);   //   color type
   if ( sz > 1 ) return 0;   //   only RGB or indexed allowed
   sz = stbi__get8(s);   //   image type
   if ( (sz != 1) && (sz != 2) && (sz != 3) && (sz != 9) && (sz != 10) && (sz != 11) ) return 0;   //   only RGB or grey allowed, +/- RLE
   stbi__get16be(s);      //   discard palette start
   stbi__get16be(s);      //   discard palette length
   stbi__get8(s);         //   discard bits per palette color entry
   stbi__get16be(s);      //   discard x origin
   stbi__get16be(s);      //   discard y origin
   if ( stbi__get16be(s) < 1 ) return 0;      //   test width
   if ( stbi__get16be(s) < 1 ) return 0;      //   test height
   sz = stbi__get8(s);   //   bits per pixel
   if ( (sz != 8) && (sz != 16) && (sz != 24) && (sz != 32) )
      res = 0;
   else
      res = 1;
   stbi__rewind(s);
   return res;
}

static stbi_uc *stbi__tga_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   //   read in the TGA header stuff
   int tga_offset = stbi__get8(s);
   int tga_indexed = stbi__get8(s);
   int tga_image_type = stbi__get8(s);
   int tga_is_RLE = 0;
   int tga_palette_start = stbi__get16le(s);
   int tga_palette_len = stbi__get16le(s);
   int tga_palette_bits = stbi__get8(s);
   int tga_x_origin = stbi__get16le(s);
   int tga_y_origin = stbi__get16le(s);
   int tga_width = stbi__get16le(s);
   int tga_height = stbi__get16le(s);
   int tga_bits_per_pixel = stbi__get8(s);
   int tga_comp = tga_bits_per_pixel / 8;
   int tga_inverted = stbi__get8(s);
   //   image data
   unsigned char *tga_data;
   unsigned char *tga_palette = NULL;
   int i, j;
   unsigned char raw_data[4];
   int RLE_count = 0;
   int RLE_repeating = 0;
   int read_next_pixel = 1;

   //   do a tiny bit of precessing
   if ( tga_image_type >= 8 )
   {
      tga_image_type -= 8;
      tga_is_RLE = 1;
   }
   /* int tga_alpha_bits = tga_inverted & 15; */
   tga_inverted = 1 - ((tga_inverted >> 5) & 1);

   //   error check
   if ( //(tga_indexed) ||
      (tga_width < 1) || (tga_height < 1) ||
      (tga_image_type < 1) || (tga_image_type > 3) ||
      ((tga_bits_per_pixel != 8) && (tga_bits_per_pixel != 16) &&
      (tga_bits_per_pixel != 24) && (tga_bits_per_pixel != 32))
      )
   {
      return NULL; // we don't report this as a bad TGA because we don't even know if it's TGA
   }

   //   If I'm paletted, then I'll use the number of bits from the palette
   if ( tga_indexed )
   {
      tga_comp = tga_palette_bits / 8;
   }

   //   tga info
   *x = tga_width;
   *y = tga_height;
   if (comp) *comp = tga_comp;

   tga_data = (unsigned char*)stbi__malloc( tga_width * tga_height * tga_comp );
   if (!tga_data) return stbi__errpuc("outofmem", "Out of memory");

   // skip to the data's starting position (offset usually = 0)
   stbi__skip(s, tga_offset );

   if ( !tga_indexed && !tga_is_RLE) {
      for (i=0; i < tga_height; ++i) {
         int y = tga_inverted ? tga_height -i - 1 : i;
         stbi_uc *tga_row = tga_data + y*tga_width*tga_comp;
         stbi__getn(s, tga_row, tga_width * tga_comp);
      }
   } else  {
      //   do I need to load a palette?
      if ( tga_indexed)
      {
         //   any data to skip? (offset usually = 0)
         stbi__skip(s, tga_palette_start );
         //   load the palette
         tga_palette = (unsigned char*)stbi__malloc( tga_palette_len * tga_palette_bits / 8 );
         if (!tga_palette) {
            free(tga_data);
            return stbi__errpuc("outofmem", "Out of memory");
         }
         if (!stbi__getn(s, tga_palette, tga_palette_len * tga_palette_bits / 8 )) {
            free(tga_data);
            free(tga_palette);
            return stbi__errpuc("bad palette", "Corrupt TGA");
         }
      }
      //   load the data
      for (i=0; i < tga_width * tga_height; ++i)
      {
         //   if I'm in RLE mode, do I need to get a RLE stbi__pngchunk?
         if ( tga_is_RLE )
         {
            if ( RLE_count == 0 )
            {
               //   yep, get the next byte as a RLE command
               int RLE_cmd = stbi__get8(s);
               RLE_count = 1 + (RLE_cmd & 127);
               RLE_repeating = RLE_cmd >> 7;
               read_next_pixel = 1;
            } else if ( !RLE_repeating )
            {
               read_next_pixel = 1;
            }
         } else
         {
            read_next_pixel = 1;
         }
         //   OK, if I need to read a pixel, do it now
         if ( read_next_pixel )
         {
            //   load however much data we did have
            if ( tga_indexed )
            {
               //   read in 1 byte, then perform the lookup
               int pal_idx = stbi__get8(s);
               if ( pal_idx >= tga_palette_len )
               {
                  //   invalid index
                  pal_idx = 0;
               }
               pal_idx *= tga_bits_per_pixel / 8;
               for (j = 0; j*8 < tga_bits_per_pixel; ++j)
               {
                  raw_data[j] = tga_palette[pal_idx+j];
               }
            } else
            {
               //   read in the data raw
               for (j = 0; j*8 < tga_bits_per_pixel; ++j)
               {
                  raw_data[j] = stbi__get8(s);
               }
            }
            //   clear the reading flag for the next pixel
            read_next_pixel = 0;
         } // end of reading a pixel

         // copy data
         for (j = 0; j < tga_comp; ++j)
           tga_data[i*tga_comp+j] = raw_data[j];

         //   in case we're in RLE mode, keep counting down
         --RLE_count;
      }
      //   do I need to invert the image?
      if ( tga_inverted )
      {
         for (j = 0; j*2 < tga_height; ++j)
         {
            int index1 = j * tga_width * tga_comp;
            int index2 = (tga_height - 1 - j) * tga_width * tga_comp;
            for (i = tga_width * tga_comp; i > 0; --i)
            {
               unsigned char temp = tga_data[index1];
               tga_data[index1] = tga_data[index2];
               tga_data[index2] = temp;
               ++index1;
               ++index2;
            }
         }
      }
      //   clear my palette, if I had one
      if ( tga_palette != NULL )
      {
         free( tga_palette );
      }
   }

   // swap RGB
   if (tga_comp >= 3)
   {
      unsigned char* tga_pixel = tga_data;
      for (i=0; i < tga_width * tga_height; ++i)
      {
         unsigned char temp = tga_pixel[0];
         tga_pixel[0] = tga_pixel[2];
         tga_pixel[2] = temp;
         tga_pixel += tga_comp;
      }
   }

   // convert to target component count
   if (req_comp && req_comp != tga_comp)
      tga_data = stbi__convert_format(tga_data, tga_comp, req_comp, tga_width, tga_height);

   //   the things I do to get rid of an error message, and yet keep
   //   Microsoft's C compilers happy... [8^(
   tga_palette_start = tga_palette_len = tga_palette_bits =
         tga_x_origin = tga_y_origin = 0;
   //   OK, done
   return tga_data;
}

// *************************************************************************************************
// Photoshop PSD loader -- PD by Thatcher Ulrich, integration by Nicolas Schulz, tweaked by STB

static int stbi__psd_test(stbi__context *s)
{
   int r = (stbi__get32be(s) == 0x38425053);
   stbi__rewind(s);
   return r;
}

static stbi_uc *stbi__psd_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   int   pixelCount;
   int channelCount, compression;
   int channel, i, count, len;
   int w,h;
   stbi_uc *out;

   // Check identifier
   if (stbi__get32be(s) != 0x38425053)   // "8BPS"
      return stbi__errpuc("not PSD", "Corrupt PSD image");

   // Check file type version.
   if (stbi__get16be(s) != 1)
      return stbi__errpuc("wrong version", "Unsupported version of PSD image");

   // Skip 6 reserved bytes.
   stbi__skip(s, 6 );

   // Read the number of channels (R, G, B, A, etc).
   channelCount = stbi__get16be(s);
   if (channelCount < 0 || channelCount > 16)
      return stbi__errpuc("wrong channel count", "Unsupported number of channels in PSD image");

   // Read the rows and columns of the image.
   h = stbi__get32be(s);
   w = stbi__get32be(s);
   
   // Make sure the depth is 8 bits.
   if (stbi__get16be(s) != 8)
      return stbi__errpuc("unsupported bit depth", "PSD bit depth is not 8 bit");

   // Make sure the color mode is RGB.
   // Valid options are:
   //   0: Bitmap
   //   1: Grayscale
   //   2: Indexed color
   //   3: RGB color
   //   4: CMYK color
   //   7: Multichannel
   //   8: Duotone
   //   9: Lab color
   if (stbi__get16be(s) != 3)
      return stbi__errpuc("wrong color format", "PSD is not in RGB color format");

   // Skip the Mode Data.  (It's the palette for indexed color; other info for other modes.)
   stbi__skip(s,stbi__get32be(s) );

   // Skip the image resources.  (resolution, pen tool paths, etc)
   stbi__skip(s, stbi__get32be(s) );

   // Skip the reserved data.
   stbi__skip(s, stbi__get32be(s) );

   // Find out if the data is compressed.
   // Known values:
   //   0: no compression
   //   1: RLE compressed
   compression = stbi__get16be(s);
   if (compression > 1)
      return stbi__errpuc("bad compression", "PSD has an unknown compression format");

   // Create the destination image.
   out = (stbi_uc *) stbi__malloc(4 * w*h);
   if (!out) return stbi__errpuc("outofmem", "Out of memory");
   pixelCount = w*h;

   // Initialize the data to zero.
   //memset( out, 0, pixelCount * 4 );
   
   // Finally, the image data.
   if (compression) {
      // RLE as used by .PSD and .TIFF
      // Loop until you get the number of unpacked bytes you are expecting:
      //     Read the next source byte into n.
      //     If n is between 0 and 127 inclusive, copy the next n+1 bytes literally.
      //     Else if n is between -127 and -1 inclusive, copy the next byte -n+1 times.
      //     Else if n is 128, noop.
      // Endloop

      // The RLE-compressed data is preceeded by a 2-byte data count for each row in the data,
      // which we're going to just skip.
      stbi__skip(s, h * channelCount * 2 );

      // Read the RLE data by channel.
      for (channel = 0; channel < 4; channel++) {
         stbi_uc *p;
         
         p = out+channel;
         if (channel >= channelCount) {
            // Fill this channel with default data.
            for (i = 0; i < pixelCount; i++) *p = (channel == 3 ? 255 : 0), p += 4;
         } else {
            // Read the RLE data.
            count = 0;
            while (count < pixelCount) {
               len = stbi__get8(s);
               if (len == 128) {
                  // No-op.
               } else if (len < 128) {
                  // Copy next len+1 bytes literally.
                  len++;
                  count += len;
                  while (len) {
                     *p = stbi__get8(s);
                     p += 4;
                     len--;
                  }
               } else if (len > 128) {
                  stbi_uc   val;
                  // Next -len+1 bytes in the dest are replicated from next source byte.
                  // (Interpret len as a negative 8-bit int.)
                  len ^= 0x0FF;
                  len += 2;
                  val = stbi__get8(s);
                  count += len;
                  while (len) {
                     *p = val;
                     p += 4;
                     len--;
                  }
               }
            }
         }
      }
      
   } else {
      // We're at the raw image data.  It's each channel in order (Red, Green, Blue, Alpha, ...)
      // where each channel consists of an 8-bit value for each pixel in the image.
      
      // Read the data by channel.
      for (channel = 0; channel < 4; channel++) {
         stbi_uc *p;
         
         p = out + channel;
         if (channel > channelCount) {
            // Fill this channel with default data.
            for (i = 0; i < pixelCount; i++) *p = channel == 3 ? 255 : 0, p += 4;
         } else {
            // Read the data.
            for (i = 0; i < pixelCount; i++)
               *p = stbi__get8(s), p += 4;
         }
      }
   }

   if (req_comp && req_comp != 4) {
      out = stbi__convert_format(out, 4, req_comp, w, h);
      if (out == NULL) return out; // stbi__convert_format frees input on failure
   }

   if (comp) *comp = channelCount;
   *y = h;
   *x = w;
   
   return out;
}

// *************************************************************************************************
// Softimage PIC loader
// by Tom Seddon
//
// See http://softimage.wiki.softimage.com/index.php/INFO:_PIC_file_format
// See http://ozviz.wasp.uwa.edu.au/~pbourke/dataformats/softimagepic/

static int stbi__pic_is4(stbi__context *s,const char *str)
{
   int i;
   for (i=0; i<4; ++i)
      if (stbi__get8(s) != (stbi_uc)str[i])
         return 0;

   return 1;
}

static int stbi__pic_test_core(stbi__context *s)
{
   int i;

   if (!stbi__pic_is4(s,"\x53\x80\xF6\x34"))
      return 0;

   for(i=0;i<84;++i)
      stbi__get8(s);

   if (!stbi__pic_is4(s,"PICT"))
      return 0;

   return 1;
}

typedef struct
{
   stbi_uc size,type,channel;
} stbi__pic_packet;

static stbi_uc *stbi__readval(stbi__context *s, int channel, stbi_uc *dest)
{
   int mask=0x80, i;

   for (i=0; i<4; ++i, mask>>=1) {
      if (channel & mask) {
         if (stbi__at_eof(s)) return stbi__errpuc("bad file","PIC file too short");
         dest[i]=stbi__get8(s);
      }
   }

   return dest;
}

static void stbi__copyval(int channel,stbi_uc *dest,const stbi_uc *src)
{
   int mask=0x80,i;

   for (i=0;i<4; ++i, mask>>=1)
      if (channel&mask)
         dest[i]=src[i];
}

static stbi_uc *stbi__pic_load_core(stbi__context *s,int width,int height,int *comp, stbi_uc *result)
{
   int act_comp=0,num_packets=0,y,chained;
   stbi__pic_packet packets[10];

   // this will (should...) cater for even some bizarre stuff like having data
    // for the same channel in multiple packets.
   do {
      stbi__pic_packet *packet;

      if (num_packets==sizeof(packets)/sizeof(packets[0]))
         return stbi__errpuc("bad format","too many packets");

      packet = &packets[num_packets++];

      chained = stbi__get8(s);
      packet->size    = stbi__get8(s);
      packet->type    = stbi__get8(s);
      packet->channel = stbi__get8(s);

      act_comp |= packet->channel;

      if (stbi__at_eof(s))          return stbi__errpuc("bad file","file too short (reading packets)");
      if (packet->size != 8)  return stbi__errpuc("bad format","packet isn't 8bpp");
   } while (chained);

   *comp = (act_comp & 0x10 ? 4 : 3); // has alpha channel?

   for(y=0; y<height; ++y) {
      int packet_idx;

      for(packet_idx=0; packet_idx < num_packets; ++packet_idx) {
         stbi__pic_packet *packet = &packets[packet_idx];
         stbi_uc *dest = result+y*width*4;

         switch (packet->type) {
            default:
               return stbi__errpuc("bad format","packet has bad compression type");

            case 0: {//uncompressed
               int x;

               for(x=0;x<width;++x, dest+=4)
                  if (!stbi__readval(s,packet->channel,dest))
                     return 0;
               break;
            }

            case 1://Pure RLE
               {
                  int left=width, i;

                  while (left>0) {
                     stbi_uc count,value[4];

                     count=stbi__get8(s);
                     if (stbi__at_eof(s))   return stbi__errpuc("bad file","file too short (pure read count)");

                     if (count > left)
                        count = (stbi_uc) left;

                     if (!stbi__readval(s,packet->channel,value))  return 0;

                     for(i=0; i<count; ++i,dest+=4)
                        stbi__copyval(packet->channel,dest,value);
                     left -= count;
                  }
               }
               break;

            case 2: {//Mixed RLE
               int left=width;
               while (left>0) {
                  int count = stbi__get8(s), i;
                  if (stbi__at_eof(s))  return stbi__errpuc("bad file","file too short (mixed read count)");

                  if (count >= 128) { // Repeated
                     stbi_uc value[4];
                     int i;

                     if (count==128)
                        count = stbi__get16be(s);
                     else
                        count -= 127;
                     if (count > left)
                        return stbi__errpuc("bad file","scanline overrun");

                     if (!stbi__readval(s,packet->channel,value))
                        return 0;

                     for(i=0;i<count;++i, dest += 4)
                        stbi__copyval(packet->channel,dest,value);
                  } else { // Raw
                     ++count;
                     if (count>left) return stbi__errpuc("bad file","scanline overrun");

                     for(i=0;i<count;++i, dest+=4)
                        if (!stbi__readval(s,packet->channel,dest))
                           return 0;
                  }
                  left-=count;
               }
               break;
            }
         }
      }
   }

   return result;
}

static stbi_uc *stbi__pic_load(stbi__context *s,int *px,int *py,int *comp,int req_comp)
{
   stbi_uc *result;
   int i, x,y;

   for (i=0; i<92; ++i)
      stbi__get8(s);

   x = stbi__get16be(s);
   y = stbi__get16be(s);
   if (stbi__at_eof(s))  return stbi__errpuc("bad file","file too short (pic header)");
   if ((1 << 28) / x < y) return stbi__errpuc("too large", "Image too large to decode");

   stbi__get32be(s); //skip `ratio'
   stbi__get16be(s); //skip `fields'
   stbi__get16be(s); //skip `pad'

   // intermediate buffer is RGBA
   result = (stbi_uc *) stbi__malloc(x*y*4);
   memset(result, 0xff, x*y*4);

   if (!stbi__pic_load_core(s,x,y,comp, result)) {
      free(result);
      result=0;
   }
   *px = x;
   *py = y;
   if (req_comp == 0) req_comp = *comp;
   result=stbi__convert_format(result,4,req_comp,x,y);

   return result;
}

static int stbi__pic_test(stbi__context *s)
{
   int r = stbi__pic_test_core(s);
   stbi__rewind(s);
   return r;
}

// *************************************************************************************************
// GIF loader -- public domain by Jean-Marc Lienher -- simplified/shrunk by stb
typedef struct 
{
   stbi__int16 prefix;
   stbi_uc first;
   stbi_uc suffix;
} stbi__gif_lzw;

typedef struct
{
   int w,h;
   stbi_uc *out;                 // output buffer (always 4 components)
   int flags, bgindex, ratio, transparent, eflags;
   stbi_uc  pal[256][4];
   stbi_uc lpal[256][4];
   stbi__gif_lzw codes[4096];
   stbi_uc *color_table;
   int parse, step;
   int lflags;
   int start_x, start_y;
   int max_x, max_y;
   int cur_x, cur_y;
   int line_size;
} stbi__gif;

static int stbi__gif_test_raw(stbi__context *s)
{
   int sz;
   if (stbi__get8(s) != 'G' || stbi__get8(s) != 'I' || stbi__get8(s) != 'F' || stbi__get8(s) != '8') return 0;
   sz = stbi__get8(s);
   if (sz != '9' && sz != '7') return 0;
   if (stbi__get8(s) != 'a') return 0;
   return 1;
}

static int stbi__gif_test(stbi__context *s)
{
   int r = stbi__gif_test_raw(s);
   stbi__rewind(s);
   return r;
}

static void stbi__gif_parse_colortable(stbi__context *s, stbi_uc pal[256][4], int num_entries, int transp)
{
   int i;
   for (i=0; i < num_entries; ++i) {
      pal[i][2] = stbi__get8(s);
      pal[i][1] = stbi__get8(s);
      pal[i][0] = stbi__get8(s);
      pal[i][3] = transp ? 0 : 255;
   }   
}

static int stbi__gif_header(stbi__context *s, stbi__gif *g, int *comp, int is_info)
{
   stbi_uc version;
   if (stbi__get8(s) != 'G' || stbi__get8(s) != 'I' || stbi__get8(s) != 'F' || stbi__get8(s) != '8')
      return stbi__err("not GIF", "Corrupt GIF");

   version = stbi__get8(s);
   if (version != '7' && version != '9')    return stbi__err("not GIF", "Corrupt GIF");
   if (stbi__get8(s) != 'a')                      return stbi__err("not GIF", "Corrupt GIF");
 
   stbi__g_failure_reason = "";
   g->w = stbi__get16le(s);
   g->h = stbi__get16le(s);
   g->flags = stbi__get8(s);
   g->bgindex = stbi__get8(s);
   g->ratio = stbi__get8(s);
   g->transparent = -1;

   if (comp != 0) *comp = 4;  // can't actually tell whether it's 3 or 4 until we parse the comments

   if (is_info) return 1;

   if (g->flags & 0x80)
      stbi__gif_parse_colortable(s,g->pal, 2 << (g->flags & 7), -1);

   return 1;
}

static int stbi__gif_info_raw(stbi__context *s, int *x, int *y, int *comp)
{
   stbi__gif g;   
   if (!stbi__gif_header(s, &g, comp, 1)) {
      stbi__rewind( s );
      return 0;
   }
   if (x) *x = g.w;
   if (y) *y = g.h;
   return 1;
}

static void stbi__out_gif_code(stbi__gif *g, stbi__uint16 code)
{
   stbi_uc *p, *c;

   // recurse to decode the prefixes, since the linked-list is backwards,
   // and working backwards through an interleaved image would be nasty
   if (g->codes[code].prefix >= 0)
      stbi__out_gif_code(g, g->codes[code].prefix);

   if (g->cur_y >= g->max_y) return;
  
   p = &g->out[g->cur_x + g->cur_y];
   c = &g->color_table[g->codes[code].suffix * 4];

   if (c[3] >= 128) {
      p[0] = c[2];
      p[1] = c[1];
      p[2] = c[0];
      p[3] = c[3];
   }
   g->cur_x += 4;

   if (g->cur_x >= g->max_x) {
      g->cur_x = g->start_x;
      g->cur_y += g->step;

      while (g->cur_y >= g->max_y && g->parse > 0) {
         g->step = (1 << g->parse) * g->line_size;
         g->cur_y = g->start_y + (g->step >> 1);
         --g->parse;
      }
   }
}

static stbi_uc *stbi__process_gif_raster(stbi__context *s, stbi__gif *g)
{
   stbi_uc lzw_cs;
   stbi__int32 len, code;
   stbi__uint32 first;
   stbi__int32 codesize, codemask, avail, oldcode, bits, valid_bits, clear;
   stbi__gif_lzw *p;

   lzw_cs = stbi__get8(s);
   clear = 1 << lzw_cs;
   first = 1;
   codesize = lzw_cs + 1;
   codemask = (1 << codesize) - 1;
   bits = 0;
   valid_bits = 0;
   for (code = 0; code < clear; code++) {
      g->codes[code].prefix = -1;
      g->codes[code].first = (stbi_uc) code;
      g->codes[code].suffix = (stbi_uc) code;
   }

   // support no starting clear code
   avail = clear+2;
   oldcode = -1;

   len = 0;
   for(;;) {
      if (valid_bits < codesize) {
         if (len == 0) {
            len = stbi__get8(s); // start new block
            if (len == 0) 
               return g->out;
         }
         --len;
         bits |= (stbi__int32) stbi__get8(s) << valid_bits;
         valid_bits += 8;
      } else {
         stbi__int32 code = bits & codemask;
         bits >>= codesize;
         valid_bits -= codesize;
         // @OPTIMIZE: is there some way we can accelerate the non-clear path?
         if (code == clear) {  // clear code
            codesize = lzw_cs + 1;
            codemask = (1 << codesize) - 1;
            avail = clear + 2;
            oldcode = -1;
            first = 0;
         } else if (code == clear + 1) { // end of stream code
            stbi__skip(s, len);
            while ((len = stbi__get8(s)) > 0)
               stbi__skip(s,len);
            return g->out;
         } else if (code <= avail) {
            if (first) return stbi__errpuc("no clear code", "Corrupt GIF");

            if (oldcode >= 0) {
               p = &g->codes[avail++];
               if (avail > 4096)        return stbi__errpuc("too many codes", "Corrupt GIF");
               p->prefix = (stbi__int16) oldcode;
               p->first = g->codes[oldcode].first;
               p->suffix = (code == avail) ? p->first : g->codes[code].first;
            } else if (code == avail)
               return stbi__errpuc("illegal code in raster", "Corrupt GIF");

            stbi__out_gif_code(g, (stbi__uint16) code);

            if ((avail & codemask) == 0 && avail <= 0x0FFF) {
               codesize++;
               codemask = (1 << codesize) - 1;
            }

            oldcode = code;
         } else {
            return stbi__errpuc("illegal code in raster", "Corrupt GIF");
         }
      } 
   }
}

static void stbi__fill_gif_background(stbi__gif *g)
{
   int i;
   stbi_uc *c = g->pal[g->bgindex];
   // @OPTIMIZE: write a dword at a time
   for (i = 0; i < g->w * g->h * 4; i += 4) {
      stbi_uc *p  = &g->out[i];
      p[0] = c[2];
      p[1] = c[1];
      p[2] = c[0];
      p[3] = c[3];
   }
}

// this function is designed to support animated gifs, although stb_image doesn't support it
static stbi_uc *stbi__gif_load_next(stbi__context *s, stbi__gif *g, int *comp, int req_comp)
{
   int i;
   stbi_uc *old_out = 0;

   if (g->out == 0) {
      if (!stbi__gif_header(s, g, comp,0))     return 0; // stbi__g_failure_reason set by stbi__gif_header
      g->out = (stbi_uc *) stbi__malloc(4 * g->w * g->h);
      if (g->out == 0)                      return stbi__errpuc("outofmem", "Out of memory");
      stbi__fill_gif_background(g);
   } else {
      // animated-gif-only path
      if (((g->eflags & 0x1C) >> 2) == 3) {
         old_out = g->out;
         g->out = (stbi_uc *) stbi__malloc(4 * g->w * g->h);
         if (g->out == 0)                   return stbi__errpuc("outofmem", "Out of memory");
         memcpy(g->out, old_out, g->w*g->h*4);
      }
   }
    
   for (;;) {
      switch (stbi__get8(s)) {
         case 0x2C: /* Image Descriptor */
         {
            stbi__int32 x, y, w, h;
            stbi_uc *o;

            x = stbi__get16le(s);
            y = stbi__get16le(s);
            w = stbi__get16le(s);
            h = stbi__get16le(s);
            if (((x + w) > (g->w)) || ((y + h) > (g->h)))
               return stbi__errpuc("bad Image Descriptor", "Corrupt GIF");

            g->line_size = g->w * 4;
            g->start_x = x * 4;
            g->start_y = y * g->line_size;
            g->max_x   = g->start_x + w * 4;
            g->max_y   = g->start_y + h * g->line_size;
            g->cur_x   = g->start_x;
            g->cur_y   = g->start_y;

            g->lflags = stbi__get8(s);

            if (g->lflags & 0x40) {
               g->step = 8 * g->line_size; // first interlaced spacing
               g->parse = 3;
            } else {
               g->step = g->line_size;
               g->parse = 0;
            }

            if (g->lflags & 0x80) {
               stbi__gif_parse_colortable(s,g->lpal, 2 << (g->lflags & 7), g->eflags & 0x01 ? g->transparent : -1);
               g->color_table = (stbi_uc *) g->lpal;       
            } else if (g->flags & 0x80) {
               for (i=0; i < 256; ++i)  // @OPTIMIZE: stbi__jpeg_reset only the previous transparent
                  g->pal[i][3] = 255; 
               if (g->transparent >= 0 && (g->eflags & 0x01))
                  g->pal[g->transparent][3] = 0;
               g->color_table = (stbi_uc *) g->pal;
            } else
               return stbi__errpuc("missing color table", "Corrupt GIF");
   
            o = stbi__process_gif_raster(s, g);
            if (o == NULL) return NULL;

            if (req_comp && req_comp != 4)
               o = stbi__convert_format(o, 4, req_comp, g->w, g->h);
            return o;
         }

         case 0x21: // Comment Extension.
         {
            int len;
            if (stbi__get8(s) == 0xF9) { // Graphic Control Extension.
               len = stbi__get8(s);
               if (len == 4) {
                  g->eflags = stbi__get8(s);
                  stbi__get16le(s); // delay
                  g->transparent = stbi__get8(s);
               } else {
                  stbi__skip(s, len);
                  break;
               }
            }
            while ((len = stbi__get8(s)) != 0)
               stbi__skip(s, len);
            break;
         }

         case 0x3B: // gif stream termination code
            return (stbi_uc *) s; // using '1' causes warning on some compilers

         default:
            return stbi__errpuc("unknown code", "Corrupt GIF");
      }
   }
}

static stbi_uc *stbi__gif_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   stbi_uc *u = 0;
   stbi__gif g;
   memset(&g, 0, sizeof(g));

   u = stbi__gif_load_next(s, &g, comp, req_comp);
   if (u == (stbi_uc *) s) u = 0;  // end of animated gif marker
   if (u) {
      *x = g.w;
      *y = g.h;
   }

   return u;
}

static int stbi__gif_info(stbi__context *s, int *x, int *y, int *comp)
{
   return stbi__gif_info_raw(s,x,y,comp);
}


// *************************************************************************************************
// Radiance RGBE HDR loader
// originally by Nicolas Schulz
#ifndef STBI_NO_HDR
static int stbi__hdr_test_core(stbi__context *s)
{
   const char *signature = "#?RADIANCE\n";
   int i;
   for (i=0; signature[i]; ++i)
      if (stbi__get8(s) != signature[i])
         return 0;
   return 1;
}

static int stbi__hdr_test(stbi__context* s)
{
   int r = stbi__hdr_test_core(s);
   stbi__rewind(s);
   return r;
}

#define STBI__HDR_BUFLEN  1024
static char *stbi__hdr_gettoken(stbi__context *z, char *buffer)
{
   int len=0;
   char c = '\0';

   c = (char) stbi__get8(z);

   while (!stbi__at_eof(z) && c != '\n') {
      buffer[len++] = c;
      if (len == STBI__HDR_BUFLEN-1) {
         // flush to end of line
         while (!stbi__at_eof(z) && stbi__get8(z) != '\n')
            ;
         break;
      }
      c = (char) stbi__get8(z);
   }

   buffer[len] = 0;
   return buffer;
}

static void stbi__hdr_convert(float *output, stbi_uc *input, int req_comp)
{
   if ( input[3] != 0 ) {
      float f1;
      // Exponent
      f1 = (float) ldexp(1.0f, input[3] - (int)(128 + 8));
      if (req_comp <= 2)
         output[0] = (input[0] + input[1] + input[2]) * f1 / 3;
      else {
         output[0] = input[0] * f1;
         output[1] = input[1] * f1;
         output[2] = input[2] * f1;
      }
      if (req_comp == 2) output[1] = 1;
      if (req_comp == 4) output[3] = 1;
   } else {
      switch (req_comp) {
         case 4: output[3] = 1; /* fallthrough */
         case 3: output[0] = output[1] = output[2] = 0;
                 break;
         case 2: output[1] = 1; /* fallthrough */
         case 1: output[0] = 0;
                 break;
      }
   }
}

static float *stbi__hdr_load(stbi__context *s, int *x, int *y, int *comp, int req_comp)
{
   char buffer[STBI__HDR_BUFLEN];
   char *token;
   int valid = 0;
   int width, height;
   stbi_uc *scanline;
   float *hdr_data;
   int len;
   unsigned char count, value;
   int i, j, k, c1,c2, z;


   // Check identifier
   if (strcmp(stbi__hdr_gettoken(s,buffer), "#?RADIANCE") != 0)
      return stbi__errpf("not HDR", "Corrupt HDR image");
   
   // Parse header
   for(;;) {
      token = stbi__hdr_gettoken(s,buffer);
      if (token[0] == 0) break;
      if (strcmp(token, "FORMAT=32-bit_rle_rgbe") == 0) valid = 1;
   }

   if (!valid)    return stbi__errpf("unsupported format", "Unsupported HDR format");

   // Parse width and height
   // can't use sscanf() if we're not using stdio!
   token = stbi__hdr_gettoken(s,buffer);
   if (strncmp(token, "-Y ", 3))  return stbi__errpf("unsupported data layout", "Unsupported HDR format");
   token += 3;
   height = (int) strtol(token, &token, 10);
   while (*token == ' ') ++token;
   if (strncmp(token, "+X ", 3))  return stbi__errpf("unsupported data layout", "Unsupported HDR format");
   token += 3;
   width = (int) strtol(token, NULL, 10);

   *x = width;
   *y = height;

   if (comp) *comp = 3;
   if (req_comp == 0) req_comp = 3;

   // Read data
   hdr_data = (float *) stbi__malloc(height * width * req_comp * sizeof(float));

   // Load image data
   // image data is stored as some number of sca
   if ( width < 8 || width >= 32768) {
      // Read flat data
      for (j=0; j < height; ++j) {
         for (i=0; i < width; ++i) {
            stbi_uc rgbe[4];
           main_decode_loop:
            stbi__getn(s, rgbe, 4);
            stbi__hdr_convert(hdr_data + j * width * req_comp + i * req_comp, rgbe, req_comp);
         }
      }
   } else {
      // Read RLE-encoded data
      scanline = NULL;

      for (j = 0; j < height; ++j) {
         c1 = stbi__get8(s);
         c2 = stbi__get8(s);
         len = stbi__get8(s);
         if (c1 != 2 || c2 != 2 || (len & 0x80)) {
            // not run-length encoded, so we have to actually use THIS data as a decoded
            // pixel (note this can't be a valid pixel--one of RGB must be >= 128)
            stbi_uc rgbe[4];
            rgbe[0] = (stbi_uc) c1;
            rgbe[1] = (stbi_uc) c2;
            rgbe[2] = (stbi_uc) len;
            rgbe[3] = (stbi_uc) stbi__get8(s);
            stbi__hdr_convert(hdr_data, rgbe, req_comp);
            i = 1;
            j = 0;
            free(scanline);
            goto main_decode_loop; // yes, this makes no sense
         }
         len <<= 8;
         len |= stbi__get8(s);
         if (len != width) { free(hdr_data); free(scanline); return stbi__errpf("invalid decoded scanline length", "corrupt HDR"); }
         if (scanline == NULL) scanline = (stbi_uc *) stbi__malloc(width * 4);
            
         for (k = 0; k < 4; ++k) {
            i = 0;
            while (i < width) {
               count = stbi__get8(s);
               if (count > 128) {
                  // Run
                  value = stbi__get8(s);
                  count -= 128;
                  for (z = 0; z < count; ++z)
                     scanline[i++ * 4 + k] = value;
               } else {
                  // Dump
                  for (z = 0; z < count; ++z)
                     scanline[i++ * 4 + k] = stbi__get8(s);
               }
            }
         }
         for (i=0; i < width; ++i)
            stbi__hdr_convert(hdr_data+(j*width + i)*req_comp, scanline + i*4, req_comp);
      }
      free(scanline);
   }

   return hdr_data;
}

static int stbi__hdr_info(stbi__context *s, int *x, int *y, int *comp)
{
   char buffer[STBI__HDR_BUFLEN];
   char *token;
   int valid = 0;

   if (strcmp(stbi__hdr_gettoken(s,buffer), "#?RADIANCE") != 0) {
       stbi__rewind( s );
       return 0;
   }

   for(;;) {
      token = stbi__hdr_gettoken(s,buffer);
      if (token[0] == 0) break;
      if (strcmp(token, "FORMAT=32-bit_rle_rgbe") == 0) valid = 1;
   }

   if (!valid) {
       stbi__rewind( s );
       return 0;
   }
   token = stbi__hdr_gettoken(s,buffer);
   if (strncmp(token, "-Y ", 3)) {
       stbi__rewind( s );
       return 0;
   }
   token += 3;
   *y = (int) strtol(token, &token, 10);
   while (*token == ' ') ++token;
   if (strncmp(token, "+X ", 3)) {
       stbi__rewind( s );
       return 0;
   }
   token += 3;
   *x = (int) strtol(token, NULL, 10);
   *comp = 3;
   return 1;
}
#endif // STBI_NO_HDR

static int stbi__bmp_info(stbi__context *s, int *x, int *y, int *comp)
{
   int hsz;
   if (stbi__get8(s) != 'B' || stbi__get8(s) != 'M') {
       stbi__rewind( s );
       return 0;
   }
   stbi__skip(s,12);
   hsz = stbi__get32le(s);
   if (hsz != 12 && hsz != 40 && hsz != 56 && hsz != 108 && hsz != 124) {
       stbi__rewind( s );
       return 0;
   }
   if (hsz == 12) {
      *x = stbi__get16le(s);
      *y = stbi__get16le(s);
   } else {
      *x = stbi__get32le(s);
      *y = stbi__get32le(s);
   }
   if (stbi__get16le(s) != 1) {
       stbi__rewind( s );
       return 0;
   }
   *comp = stbi__get16le(s) / 8;
   return 1;
}

static int stbi__psd_info(stbi__context *s, int *x, int *y, int *comp)
{
   int channelCount;
   if (stbi__get32be(s) != 0x38425053) {
       stbi__rewind( s );
       return 0;
   }
   if (stbi__get16be(s) != 1) {
       stbi__rewind( s );
       return 0;
   }
   stbi__skip(s, 6);
   channelCount = stbi__get16be(s);
   if (channelCount < 0 || channelCount > 16) {
       stbi__rewind( s );
       return 0;
   }
   *y = stbi__get32be(s);
   *x = stbi__get32be(s);
   if (stbi__get16be(s) != 8) {
       stbi__rewind( s );
       return 0;
   }
   if (stbi__get16be(s) != 3) {
       stbi__rewind( s );
       return 0;
   }
   *comp = 4;
   return 1;
}

static int stbi__pic_info(stbi__context *s, int *x, int *y, int *comp)
{
   int act_comp=0,num_packets=0,chained;
   stbi__pic_packet packets[10];

   stbi__skip(s, 92);

   *x = stbi__get16be(s);
   *y = stbi__get16be(s);
   if (stbi__at_eof(s))  return 0;
   if ( (*x) != 0 && (1 << 28) / (*x) < (*y)) {
       stbi__rewind( s );
       return 0;
   }

   stbi__skip(s, 8);

   do {
      stbi__pic_packet *packet;

      if (num_packets==sizeof(packets)/sizeof(packets[0]))
         return 0;

      packet = &packets[num_packets++];
      chained = stbi__get8(s);
      packet->size    = stbi__get8(s);
      packet->type    = stbi__get8(s);
      packet->channel = stbi__get8(s);
      act_comp |= packet->channel;

      if (stbi__at_eof(s)) {
          stbi__rewind( s );
          return 0;
      }
      if (packet->size != 8) {
          stbi__rewind( s );
          return 0;
      }
   } while (chained);

   *comp = (act_comp & 0x10 ? 4 : 3);

   return 1;
}

static int stbi__info_main(stbi__context *s, int *x, int *y, int *comp)
{
   if (stbi__jpeg_info(s, x, y, comp))
       return 1;
   if (stbi__png_info(s, x, y, comp))
       return 1;
   if (stbi__gif_info(s, x, y, comp))
       return 1;
   if (stbi__bmp_info(s, x, y, comp))
       return 1;
   if (stbi__psd_info(s, x, y, comp))
       return 1;
   if (stbi__pic_info(s, x, y, comp))
       return 1;
   #ifndef STBI_NO_HDR
   if (stbi__hdr_info(s, x, y, comp))
       return 1;
   #endif
   // test tga last because it's a crappy test!
   if (stbi__tga_info(s, x, y, comp))
       return 1;
   return stbi__err("unknown image type", "Image not of any known type, or corrupt");
}

#ifndef STBI_NO_STDIO
STBIDEF int stbi_info(char const *filename, int *x, int *y, int *comp)
{
    FILE *f = stbi__fopen(filename, "rb");
    int result;
    if (!f) return stbi__err("can't fopen", "Unable to open file");
    result = stbi_info_from_file(f, x, y, comp);
    fclose(f);
    return result;
}

STBIDEF int stbi_info_from_file(FILE *f, int *x, int *y, int *comp)
{
   int r;
   stbi__context s;
   long pos = ftell(f);
   stbi__start_file(&s, f);
   r = stbi__info_main(&s,x,y,comp);
   fseek(f,pos,SEEK_SET);
   return r;
}
#endif // !STBI_NO_STDIO

STBIDEF int stbi_info_from_memory(stbi_uc const *buffer, int len, int *x, int *y, int *comp)
{
   stbi__context s;
   stbi__start_mem(&s,buffer,len);
   return stbi__info_main(&s,x,y,comp);
}

STBIDEF int stbi_info_from_callbacks(stbi_io_callbacks const *c, void *user, int *x, int *y, int *comp)
{
   stbi__context s;
   stbi__start_callbacks(&s, (stbi_io_callbacks *) c, user);
   return stbi__info_main(&s,x,y,comp);
}

#endif // STB_IMAGE_IMPLEMENTATION

/*
   revision history:
      1.46 (2014-08-26)
             fix broken tRNS chunk (colorkey-style transparency) in non-paletted PNG
      1.45 (2014-08-16)
             fix MSVC-ARM internal compiler error by wrapping malloc
      1.44 (2014-08-07)
		       various warning fixes from Ronny Chevalier
      1.43 (2014-07-15)
             fix MSVC-only compiler problem in code changed in 1.42
      1.42 (2014-07-09)
             don't define _CRT_SECURE_NO_WARNINGS (affects user code)
             fixes to stbi__cleanup_jpeg path
             added STBI_ASSERT to avoid requiring assert.h
      1.41 (2014-06-25)
             fix search&replace from 1.36 that messed up comments/error messages
      1.40 (2014-06-22)
             fix gcc struct-initialization warning
      1.39 (2014-06-15)
             fix to TGA optimization when req_comp != number of components in TGA;
             fix to GIF loading because BMP wasn't rewinding (whoops, no GIFs in my test suite)
             add support for BMP version 5 (more ignored fields)
      1.38 (2014-06-06)
             suppress MSVC warnings on integer casts truncating values
             fix accidental rename of 'skip' field of I/O
      1.37 (2014-06-04)
             remove duplicate typedef
      1.36 (2014-06-03)
             convert to header file single-file library
             if de-iphone isn't set, load iphone images color-swapped instead of returning NULL
      1.35 (2014-05-27)
             various warnings
             fix broken STBI_SIMD path
             fix bug where stbi_load_from_file no longer left file pointer in correct place
             fix broken non-easy path for 32-bit BMP (possibly never used)
             TGA optimization by Arseny Kapoulkine
      1.34 (unknown)
             use STBI_NOTUSED in stbi__resample_row_generic(), fix one more leak in tga failure case
      1.33 (2011-07-14)
             make stbi_is_hdr work in STBI_NO_HDR (as specified), minor compiler-friendly improvements
      1.32 (2011-07-13)
             support for "info" function for all supported filetypes (SpartanJ)
      1.31 (2011-06-20)
             a few more leak fixes, bug in PNG handling (SpartanJ)
      1.30 (2011-06-11)
             added ability to load files via callbacks to accomidate custom input streams (Ben Wenger)
             removed deprecated format-specific test/load functions
             removed support for installable file formats (stbi_loader) -- would have been broken for IO callbacks anyway
             error cases in bmp and tga give messages and don't leak (Raymond Barbiero, grisha)
             fix inefficiency in decoding 32-bit BMP (David Woo)
      1.29 (2010-08-16)
             various warning fixes from Aurelien Pocheville 
      1.28 (2010-08-01)
             fix bug in GIF palette transparency (SpartanJ)
      1.27 (2010-08-01)
             cast-to-stbi_uc to fix warnings
      1.26 (2010-07-24)
             fix bug in file buffering for PNG reported by SpartanJ
      1.25 (2010-07-17)
             refix trans_data warning (Won Chun)
      1.24 (2010-07-12)
             perf improvements reading from files on platforms with lock-heavy fgetc()
             minor perf improvements for jpeg
             deprecated type-specific functions so we'll get feedback if they're needed
             attempt to fix trans_data warning (Won Chun)
      1.23   fixed bug in iPhone support
      1.22 (2010-07-10)
             removed image *writing* support
             stbi_info support from Jetro Lauha
             GIF support from Jean-Marc Lienher
             iPhone PNG-extensions from James Brown
             warning-fixes from Nicolas Schulz and Janez Zemva (i.stbi__err. Janez (U+017D)emva)
      1.21   fix use of 'stbi_uc' in header (reported by jon blow)
      1.20   added support for Softimage PIC, by Tom Seddon
      1.19   bug in interlaced PNG corruption check (found by ryg)
      1.18 2008-08-02
             fix a threading bug (local mutable static)
      1.17   support interlaced PNG
      1.16   major bugfix - stbi__convert_format converted one too many pixels
      1.15   initialize some fields for thread safety
      1.14   fix threadsafe conversion bug
             header-file-only version (#define STBI_HEADER_FILE_ONLY before including)
      1.13   threadsafe
      1.12   const qualifiers in the API
      1.11   Support installable IDCT, colorspace conversion routines
      1.10   Fixes for 64-bit (don't use "unsigned long")
             optimized upsampling by Fabian "ryg" Giesen
      1.09   Fix format-conversion for PSD code (bad global variables!)
      1.08   Thatcher Ulrich's PSD code integrated by Nicolas Schulz
      1.07   attempt to fix C++ warning/errors again
      1.06   attempt to fix C++ warning/errors again
      1.05   fix TGA loading to return correct *comp and use good luminance calc
      1.04   default float alpha is 1, not 255; use 'void *' for stbi_image_free
      1.03   bugfixes to STBI_NO_STDIO, STBI_NO_HDR
      1.02   support for (subset of) HDR files, float interface for preferred access to them
      1.01   fix bug: possible bug in handling right-side up bmps... not sure
             fix bug: the stbi__bmp_load() and stbi__tga_load() functions didn't work at all
      1.00   interface to zlib that skips zlib header
      0.99   correct handling of alpha in palette
      0.98   TGA loader by lonesock; dynamically add loaders (untested)
      0.97   jpeg errors on too large a file; also catch another malloc failure
      0.96   fix detection of invalid v value - particleman@mollyrocket forum
      0.95   during header scan, seek to markers in case of padding
      0.94   STBI_NO_STDIO to disable stdio usage; rename all #defines the same
      0.93   handle jpegtran output; verbose errors
      0.92   read 4,8,16,24,32-bit BMP files of several formats
      0.91   output 24-bit Windows 3.0 BMP files
      0.90   fix a few more warnings; bump version number to approach 1.0
      0.61   bugfixes due to Marc LeBlanc, Christopher Lloyd
      0.60   fix compiling as c++
      0.59   fix warnings: merge Dave Moore's -Wall fixes
      0.58   fix bug: zlib uncompressed mode len/nlen was wrong endian
      0.57   fix bug: jpg last huffman symbol before marker was >9 bits but less than 16 available
      0.56   fix bug: zlib uncompressed mode len vs. nlen
      0.55   fix bug: restart_interval not initialized to 0
      0.54   allow NULL for 'int *comp'
      0.53   fix bug in png 3->4; speedup png decoding
      0.52   png handles req_comp=3,4 directly; minor cleanup; jpeg comments
      0.51   obey req_comp requests, 1-component jpegs return as 1-component,
             on 'test' only check type, not whether we support this variant
      0.50   first released version
*/
#pragma GCC diagnostic pop

heman_image* hut_read_image(const char* filename, int nbands)
{
    int width = 0, height = 0;
    stbi_uc* bytes;
    heman_image* retval;
    int bands_in_file;
    bytes = stbi_load(filename, &width, &height, &bands_in_file, nbands);
    assert(bytes);
    printf("%4d x %4d x %d :: %s\n", width, height, nbands, filename);
    retval = heman_import_u8(width, height, nbands, bytes, 0, 1);
    stbi_image_free(bytes);
    return retval;
}

void hut_write_image(const char* filename, heman_image* img, float minv, float maxv)
{
    printf("Writing to \"%s\".\n", filename);
    int width, height, ncomp;
    heman_image_info(img, &width, &height, &ncomp);
    unsigned char* bytes = (unsigned char*) malloc(width * height * ncomp);
    heman_export_u8(img, minv, maxv, bytes);
    stbi_write_png(filename, width, height, ncomp, bytes, width * ncomp);
    free(bytes);
}

void hut_write_image_scaled(const char* filename, heman_image* img, int dwidth, int dheight)
{
    printf("Writing to \"%s\".\n", filename);
    int width, height, ncomp;
    heman_image_info(img, &width, &height, &ncomp);
    unsigned char* bytes = (unsigned char*) malloc(width * height * ncomp);
    heman_export_u8(img, 0, 1, bytes);
    unsigned char* resized = (unsigned char*) malloc(dwidth * dheight * 3);
    stbir_resize_uint8(bytes, width, height, 0, resized, dwidth, dheight, 0, 3);
    stbi_write_png(filename, dwidth, dheight, ncomp, resized, dwidth * ncomp);
    free(resized);
    free(bytes);
}

static const int SIZE = 512;

#define COUNT(a) (sizeof(a) / sizeof(a[0]))
#define OUTFOLDER "build/"

int main(int argc, char** argv)
{
    printf("%d threads available.\n", omp_get_max_threads());
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
    hut_write_image(OUTFOLDER "terrainpts.png", voronoi, 0, 1);
    hut_write_image(OUTFOLDER "terrainpts_toon.png", toon, 0, 1);
}
