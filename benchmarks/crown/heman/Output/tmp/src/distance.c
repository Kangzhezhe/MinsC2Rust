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
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>

const HEMAN_FLOAT INF = 1E20;

#define NEW(t, n) calloc(n, sizeof(t))
#define SDISTFIELD_TEXEL(x, y) (*(sdf->data + y * width + x))
#define COORDFIELD_TEXEL(x, y, c) (*(cf->data + 2 * (y * width + x) + c))

static void edt(
    HEMAN_FLOAT* f, HEMAN_FLOAT* d, HEMAN_FLOAT* z, uint16_t* w, int n)
{
    int k = 0;
    HEMAN_FLOAT s;
    w[0] = 0;
    z[0] = -INF;
    z[1] = +INF;
    for (int q = 1; q < n; ++q) {
        s = ((f[q] + SQR(q)) - (f[w[k]] + SQR(w[k]))) / (2 * q - 2 * w[k]);
        while (s <= z[k]) {
            --k;
            s = ((f[q] + SQR(q)) - (f[w[k]] + SQR(w[k]))) / (2 * q - 2 * w[k]);
        }
        w[++k] = q;
        z[k] = s;
        z[k + 1] = +INF;
    }
    k = 0;
    for (int q = 0; q < n; ++q) {
        while (z[k + 1] < q) {
            ++k;
        }
        d[q] = SQR(q - w[k]) + f[w[k]];
    }
}

static void edt_with_payload(HEMAN_FLOAT* f, HEMAN_FLOAT* d, HEMAN_FLOAT* z,
    uint16_t* w, int n, HEMAN_FLOAT* payload_in, HEMAN_FLOAT* payload_out)
{
    int k = 0;
    HEMAN_FLOAT s;
    w[0] = 0;
    z[0] = -INF;
    z[1] = +INF;
    for (int q = 1; q < n; ++q) {
        s = ((f[q] + SQR(q)) - (f[w[k]] + SQR(w[k]))) / (2 * q - 2 * w[k]);
        while (s <= z[k]) {
            --k;
            s = ((f[q] + SQR(q)) - (f[w[k]] + SQR(w[k]))) / (2 * q - 2 * w[k]);
        }
        w[++k] = q;
        z[k] = s;
        z[k + 1] = +INF;
    }
    k = 0;
    for (int q = 0; q < n; ++q) {
        while (z[k + 1] < q) {
            ++k;
        }
        d[q] = SQR(q - w[k]) + f[w[k]];
        payload_out[q * 2] = payload_in[w[k] * 2];
        payload_out[q * 2 + 1] = payload_in[w[k] * 2 + 1];
    }
}

static void transform_to_distance(heman_image* sdf)
{
    int width = sdf->width;
    int height = sdf->height;
    int size = width * height;
    HEMAN_FLOAT* ff = NEW(HEMAN_FLOAT, size);
    HEMAN_FLOAT* dd = NEW(HEMAN_FLOAT, size);
    HEMAN_FLOAT* zz = NEW(HEMAN_FLOAT, (height + 1) * (width + 1));
    uint16_t* ww = NEW(uint16_t, size);

    int x;
#pragma omp parallel for
    for (x = 0; x < width; ++x) {
        HEMAN_FLOAT* f = ff + height * x;
        HEMAN_FLOAT* d = dd + height * x;
        HEMAN_FLOAT* z = zz + (height + 1) * x;
        uint16_t* w = ww + height * x;
        for (int y = 0; y < height; ++y) {
            f[y] = SDISTFIELD_TEXEL(x, y);
        }
        edt(f, d, z, w, height);
        for (int y = 0; y < height; ++y) {
            SDISTFIELD_TEXEL(x, y) = d[y];
        }
    }

    int y;
#pragma omp parallel for
    for (y = 0; y < height; ++y) {
        HEMAN_FLOAT* f = ff + width * y;
        HEMAN_FLOAT* d = dd + width * y;
        HEMAN_FLOAT* z = zz + (width + 1) * y;
        uint16_t* w = ww + width * y;
        for (int x = 0; x < width; ++x) {
            f[x] = SDISTFIELD_TEXEL(x, y);
        }
        edt(f, d, z, w, width);
        for (int x = 0; x < width; ++x) {
            SDISTFIELD_TEXEL(x, y) = d[x];
        }
    }

    free(ff);
    free(dd);
    free(zz);
    free(ww);
}

static void transform_to_coordfield(heman_image* sdf, heman_image* cf)
{
    int width = sdf->width;
    int height = sdf->height;
    int size = width * height;
    HEMAN_FLOAT* ff = NEW(HEMAN_FLOAT, size);
    HEMAN_FLOAT* dd = NEW(HEMAN_FLOAT, size);
    HEMAN_FLOAT* zz = NEW(HEMAN_FLOAT, (height + 1) * (width + 1));
    uint16_t* ww = NEW(uint16_t, size);

    int x;
#pragma omp parallel for
    for (x = 0; x < width; ++x) {
        HEMAN_FLOAT* pl1 = NEW(HEMAN_FLOAT, height * 2);
        HEMAN_FLOAT* pl2 = NEW(HEMAN_FLOAT, height * 2);
        HEMAN_FLOAT* f = ff + height * x;
        HEMAN_FLOAT* d = dd + height * x;
        HEMAN_FLOAT* z = zz + (height + 1) * x;
        uint16_t* w = ww + height * x;
        for (int y = 0; y < height; ++y) {
            f[y] = SDISTFIELD_TEXEL(x, y);
            pl1[y * 2] = COORDFIELD_TEXEL(x, y, 0);
            pl1[y * 2 + 1] = COORDFIELD_TEXEL(x, y, 1);
        }
        edt_with_payload(f, d, z, w, height, pl1, pl2);
        for (int y = 0; y < height; ++y) {
            SDISTFIELD_TEXEL(x, y) = d[y];
            COORDFIELD_TEXEL(x, y, 0) = pl2[2 * y];
            COORDFIELD_TEXEL(x, y, 1) = pl2[2 * y + 1];
        }
        free(pl1);
        free(pl2);
    }

    int y;
#pragma omp parallel for
    for (y = 0; y < height; ++y) {
        HEMAN_FLOAT* pl1 = NEW(HEMAN_FLOAT, width * 2);
        HEMAN_FLOAT* pl2 = NEW(HEMAN_FLOAT, width * 2);
        HEMAN_FLOAT* f = ff + width * y;
        HEMAN_FLOAT* d = dd + width * y;
        HEMAN_FLOAT* z = zz + (width + 1) * y;
        uint16_t* w = ww + width * y;
        for (int x = 0; x < width; ++x) {
            f[x] = SDISTFIELD_TEXEL(x, y);
            pl1[x * 2] = COORDFIELD_TEXEL(x, y, 0);
            pl1[x * 2 + 1] = COORDFIELD_TEXEL(x, y, 1);
        }
        edt_with_payload(f, d, z, w, width, pl1, pl2);
        for (int x = 0; x < width; ++x) {
            SDISTFIELD_TEXEL(x, y) = d[x];
            COORDFIELD_TEXEL(x, y, 0) = pl2[2 * x];
            COORDFIELD_TEXEL(x, y, 1) = pl2[2 * x + 1];
        }
        free(pl1);
        free(pl2);
    }

    free(ff);
    free(dd);
    free(zz);
    free(ww);
}

heman_image* heman_distance_create_sdf(heman_image* src)
{
    assert(src->nbands == 1 && "Distance field input must have only 1 band.");
    heman_image* positive = heman_image_create(src->width, src->height, 1);
    heman_image* negative = heman_image_create(src->width, src->height, 1);
    int size = src->height * src->width;
    HEMAN_FLOAT* pptr = positive->data;
    HEMAN_FLOAT* nptr = negative->data;
    HEMAN_FLOAT* sptr = src->data;
    for (int i = 0; i < size; ++i, ++sptr) {
        *pptr++ = *sptr ? INF : 0;
        *nptr++ = *sptr ? 0 : INF;
    }
    transform_to_distance(positive);
    transform_to_distance(negative);
    HEMAN_FLOAT inv = 1.0f / src->width;
    pptr = positive->data;
    nptr = negative->data;
    for (int i = 0; i < size; ++i, ++pptr, ++nptr) {
        *pptr = (sqrt(*pptr) - sqrt(*nptr)) * inv;
    }
    heman_image_destroy(negative);
    return positive;
}

heman_image* heman_distance_create_df(heman_image* src)
{
    assert(src->nbands == 1 && "Distance field input must have only 1 band.");
    heman_image* positive = heman_image_create(src->width, src->height, 1);
    int size = src->height * src->width;
    HEMAN_FLOAT* pptr = positive->data;
    HEMAN_FLOAT* sptr = src->data;
    for (int i = 0; i < size; ++i, ++sptr) {
        *pptr++ = *sptr ? 0 : INF;
    }
    transform_to_distance(positive);
    HEMAN_FLOAT inv = 1.0f / src->width;
    pptr = positive->data;
    for (int i = 0; i < size; ++i, ++pptr) {
        *pptr = sqrt(*pptr) * inv;
    }
    return positive;
}

heman_image* heman_distance_identity_cpcf(int width, int height)
{
    heman_image* retval = heman_image_create(width, height, 2);
    HEMAN_FLOAT* cdata = retval->data;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            *cdata++ = x;
            *cdata++ = y;
        }
    }
    return retval;
}

heman_image* heman_distance_create_cpcf(heman_image* src)
{
    heman_image* negative = heman_image_create(src->width, src->height, 1);
    int size = src->height * src->width;
    HEMAN_FLOAT* nptr = negative->data;
    HEMAN_FLOAT* sptr = src->data;
    for (int i = 0; i < size; ++i) {
        HEMAN_FLOAT val = 0;
        for (int b = 0; b < src->nbands; ++b) {
            val += *sptr++;
        }
        *nptr++ = val ? 0 : INF;
    }
    heman_image* coordfield = heman_distance_identity_cpcf(src->width, src->height);
    transform_to_coordfield(negative, coordfield);
    heman_image_destroy(negative);
    return coordfield;
}

heman_image* heman_distance_from_cpcf(heman_image* cf)
{
    assert(cf->nbands == 2 && "Coordinate field input must have 2 bands.");
    heman_image* udf = heman_image_create(cf->width, cf->height, 1);
    HEMAN_FLOAT* dptr = udf->data;
    HEMAN_FLOAT* sptr = cf->data;
    HEMAN_FLOAT scale = 1.0f / sqrt(SQR(cf->width) + SQR(cf->height));
    for (int y = 0; y < cf->height; y++) {
        for (int x = 0; x < cf->width; x++) {
            HEMAN_FLOAT u = *sptr++;
            HEMAN_FLOAT v = *sptr++;
            HEMAN_FLOAT dist = sqrt(SQR(u - x) + SQR(v - y)) * scale;
            *dptr++ = dist;
        }
    }
    return udf;
}
