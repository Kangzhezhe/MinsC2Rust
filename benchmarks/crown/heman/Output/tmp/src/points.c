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
#include <memory.h>
#include <assert.h>
#include <limits.h>
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

// Transforms even the sequence 0,1,2,3,... into reasonably good random numbers.
unsigned int randhash(unsigned int seed)
{
    unsigned int i = (seed ^ 12345391u) * 2654435769u;
    i ^= (i << 6) ^ (i >> 26);
    i *= 2654435769u;
    i += (i << 5) ^ (i >> 12);
    return i;
}

float randhashf(unsigned int seed, float a, float b)
{
    return (b - a) * randhash(seed) / (float) UINT_MAX + a;
}

heman_image* heman_points_create(HEMAN_FLOAT* xy, int npoints, int nbands)
{
    heman_points* img = malloc(sizeof(heman_image));
    img->width = npoints;
    img->height = 1;
    img->nbands = nbands;
    int nbytes = sizeof(HEMAN_FLOAT) * npoints * nbands;
    img->data = malloc(nbytes);
    memcpy(img->data, xy, nbytes);
    return img;
}

void heman_points_destroy(heman_points* img)
{
    free(img->data);
    free(img);
}

heman_points* heman_points_from_grid(HEMAN_FLOAT width, HEMAN_FLOAT height,
    HEMAN_FLOAT cellsize, HEMAN_FLOAT jitter)
{
    int cols = width / cellsize;
    int rows = height / cellsize;
    int ncells = cols * rows;
    heman_points* result = heman_image_create(ncells, 1, 2);
    HEMAN_FLOAT rscale = 2.0 * jitter / (HEMAN_FLOAT) RAND_MAX;

// TODO it would be good to avoid ANSI rand() and add some determinism
// in a thread-safe way.  Maybe we should add a seed argument and use
// Bridson's randhash?

    int j;
#pragma omp parallel for
    for (j = 0; j < rows; j++) {
        HEMAN_FLOAT* dst = result->data + j * cols * 2;
        HEMAN_FLOAT y = cellsize * 0.5 + cellsize * j;
        HEMAN_FLOAT x = cellsize * 0.5;
        for (int i = 0; i < cols; i++) {
            HEMAN_FLOAT rx = rand() * rscale - jitter;
            HEMAN_FLOAT ry = rand() * rscale - jitter;
            *dst++ = x + rx;
            *dst++ = y + ry;
            x += cellsize;
        }
    }

    return result;
}

kmVec2 sample_annulus(float radius, kmVec2 center, unsigned int* seedptr)
{
    unsigned int seed = *seedptr;
    kmVec2 r;
    float rscale = 1.0f / UINT_MAX;
    while (1) {
        r.x = 4 * rscale * randhash(seed++) - 2;
        r.y = 4 * rscale * randhash(seed++) - 2;
        float r2 = kmVec2LengthSq(&r);
        if (r2 > 1 && r2 <= 4) {
            break;
        }
    }
    *seedptr = seed;
    kmVec2Scale(&r, &r, radius);
    kmVec2Add(&r, &r, &center);
    return r;
}

#define GRIDF(vec) \
    grid[(int) (vec.x * invcell) + ncols * (int) (vec.y * invcell)]

#define GRIDI(vec) grid[(int) vec.y * ncols + (int) vec.x]

heman_points* heman_points_from_poisson(
    HEMAN_FLOAT width, HEMAN_FLOAT height, HEMAN_FLOAT radius)
{
    int maxattempts = 30;
    float rscale = 1.0f / UINT_MAX;
    unsigned int seed = 0;
    kmVec2 rvec;
    rvec.x = rvec.y = radius;
    float r2 = radius * radius;

    // Acceleration grid.
    float cellsize = radius / sqrtf(2);
    float invcell = 1.0f / cellsize;
    int ncols = ceil(width * invcell);
    int nrows = ceil(height * invcell);
    int maxcol = ncols - 1;
    int maxrow = nrows - 1;
    int ncells = ncols * nrows;
    int* grid = malloc(ncells * sizeof(int));
    for (int i = 0; i < ncells; i++) {
        grid[i] = -1;
    }

    // Active list and resulting sample list.
    int* actives = malloc(ncells * sizeof(int));
    int nactives = 0;
    heman_points* result = heman_image_create(ncells, 1, 2);
    kmVec2* samples = (kmVec2*) result->data;
    int nsamples = 0;

    // First sample.
    kmVec2 pt;
    pt.x = width * randhash(seed++) * rscale;
    pt.y = height * randhash(seed++) * rscale;
    GRIDF(pt) = actives[nactives++] = nsamples;
    samples[nsamples++] = pt;

    while (nsamples < ncells) {
        int aindex = MIN(randhashf(seed++, 0, nactives), nactives - 1);
        int sindex = actives[aindex];
        int found = 0;
        kmVec2 j, minj, maxj, delta;
        int attempt;
        for (attempt = 0; attempt < maxattempts && !found; attempt++) {
            pt = sample_annulus(radius, samples[sindex], &seed);

            // Check that this sample is within bounds.
            if (pt.x < 0 || pt.x >= width || pt.y < 0 || pt.y >= height) {
                continue;
            }

            // Test proximity to nearby samples.
            minj = maxj = pt;
            kmVec2Add(&maxj, &maxj, &rvec);
            kmVec2Subtract(&minj, &minj, &rvec);
            kmVec2Scale(&minj, &minj, invcell);
            kmVec2Scale(&maxj, &maxj, invcell);
            minj.x = CLAMP((int) minj.x, 0, maxcol);
            maxj.x = CLAMP((int) maxj.x, 0, maxcol);
            minj.y = CLAMP((int) minj.y, 0, maxrow);
            maxj.y = CLAMP((int) maxj.y, 0, maxrow);
            int reject = 0;
            for (j.y = minj.y; j.y <= maxj.y && !reject; j.y++) {
                for (j.x = minj.x; j.x <= maxj.x && !reject; j.x++) {
                    int entry = GRIDI(j);
                    if (entry > -1 && entry != sindex) {
                        kmVec2Subtract(&delta, &samples[entry], &pt);
                        if (kmVec2LengthSq(&delta) < r2) {
                            reject = 1;
                        }
                    }
                }
            }
            if (reject) {
                continue;
            }
            found = 1;
        }
        if (found) {
            GRIDF(pt) = actives[nactives++] = nsamples;
            samples[nsamples++] = pt;
        } else {
            if (--nactives <= 0) {
                break;
            }
            actives[aindex] = actives[nactives];
        }
    }

    // The following line probably isn't necessary.  Paranoia.
    result->width = nsamples;

    free(grid);
    free(actives);
    return result;
}

#undef GRIDF
#undef GRIDI

#define NGRID_INDEX(fpt) \
    ((int) (fpt.x * invcell) + ncols * (int) (fpt.y * invcell))

#define GRID_INDEX(fpt) (gcapacity * NGRID_INDEX(fpt))

#define GRID_INSERT(fpt, sindex)                       \
    gindex = NGRID_INDEX(fpt);                         \
    grid[gcapacity * gindex + ngrid[gindex]] = sindex; \
    ngrid[gindex]++

#define NGRID_BEGIN(ipt) ((int) ipt.y * ncols + (int) ipt.x)

#define GRID_BEGIN(ipt) (NGRID_BEGIN(ipt) * gcapacity)

#define GRID_END(ipt) (GRID_BEGIN(ipt) + ngrid[NGRID_BEGIN(ipt)])

heman_points* heman_points_from_density(
    heman_image* density, HEMAN_FLOAT minradius, HEMAN_FLOAT maxradius)
{
    assert(density->nbands == 1);
    float width = 1, height = 1;
    int maxattempts = 30;
    float rscale = 1.0f / UINT_MAX;
    unsigned int seed = 0;
    kmVec2 rvec;
    rvec.x = rvec.y = maxradius;
    int gindex;

    // Acceleration grid.
    float cellsize = maxradius / sqrtf(2);
    float invcell = 1.0f / cellsize;
    int ncols = ceil(width * invcell);
    int nrows = ceil(height * invcell);
    int maxcol = ncols - 1;
    int maxrow = nrows - 1;
    int ncells = ncols * nrows;
    int ntexels = cellsize * density->width;
    int gcapacity = ntexels * ntexels;
    int* grid = malloc(ncells * sizeof(int) * gcapacity);
    int* ngrid = malloc(ncells * sizeof(int));
    for (int i = 0; i < ncells; i++) {
        ngrid[i] = 0;
    }

    // Active list and resulting sample list.
    int* actives = malloc(ncells * sizeof(int));
    int nactives = 0;
    int maxsamples = ncells * gcapacity;
    heman_points* result = heman_image_create(maxsamples, 1, 2);
    kmVec2* samples = (kmVec2*) result->data;
    int nsamples = 0;

    // First sample.
    kmVec2 pt;
    pt.x = width * randhash(seed++) * rscale;
    pt.y = height * randhash(seed++) * rscale;
    actives[nactives++] = nsamples;
    GRID_INSERT(pt, nsamples);
    samples[nsamples++] = pt;

    while (nsamples < maxsamples) {
        int aindex = MIN(randhashf(seed++, 0, nactives), nactives - 1);
        int sindex = actives[aindex];
        int found = 0;
        kmVec2 j, minj, maxj, delta;
        int attempt;
        for (attempt = 0; attempt < maxattempts && !found; attempt++) {
            pt = sample_annulus(maxradius, samples[sindex], &seed);

            // Check that this sample is within bounds.
            if (pt.x < 0 || pt.x >= width || pt.y < 0 || pt.y >= height) {
                continue;
            }

            // Test proximity to nearby samples.
            minj = maxj = pt;
            kmVec2Add(&maxj, &maxj, &rvec);
            kmVec2Subtract(&minj, &minj, &rvec);
            kmVec2Scale(&minj, &minj, invcell);
            kmVec2Scale(&maxj, &maxj, invcell);
            minj.x = CLAMP((int) minj.x, 0, maxcol);
            maxj.x = CLAMP((int) maxj.x, 0, maxcol);
            minj.y = CLAMP((int) minj.y, 0, maxrow);
            maxj.y = CLAMP((int) maxj.y, 0, maxrow);
            int reject = 0;

            HEMAN_FLOAT densityval;
            heman_image_sample(density, pt.x, pt.y, &densityval);

            // The following square root seems to lead to more satisfying
            // results, although we should perhaps let the client decide...
            densityval = sqrt(densityval);

            float mindist = maxradius - densityval * (maxradius - minradius);
            float r2 = mindist * mindist;

            for (j.y = minj.y; j.y <= maxj.y && !reject; j.y++) {
                for (j.x = minj.x; j.x <= maxj.x && !reject; j.x++) {
                    for (int g = GRID_BEGIN(j); g < GRID_END(j); ++g) {
                        int entry = grid[g];
                        if (entry != sindex) {
                            kmVec2Subtract(&delta, &samples[entry], &pt);
                            if (kmVec2LengthSq(&delta) < r2) {
                                reject = 1;
                            }
                        }
                    }
                }
            }
            if (reject) {
                continue;
            }
            found = 1;
        }
        if (found && ngrid[NGRID_INDEX(pt)] >= gcapacity) {
            found = 0;
        }
        if (found) {
            actives[nactives++] = nsamples;
            GRID_INSERT(pt, nsamples);
            samples[nsamples++] = pt;
        } else {
            if (--nactives <= 0) {
                break;
            }
            actives[aindex] = actives[nactives];
        }
    }

    // We don't usually fill the pre-allocated buffer, since it was
    // allocated for the worst case, so adjust the size:
    result->width = nsamples;

    free(grid);
    free(ngrid);
    free(actives);
    return result;
}
