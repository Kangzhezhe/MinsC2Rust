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


#include <memory.h>
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

#ifndef VEC4_H_INCLUDED
#define VEC4_H_INCLUDED


struct kmMat4;

#pragma pack(push)  /* push current alignment to stack */
#pragma pack(1)     /* set alignment to 1 byte boundary */

typedef struct kmVec4
{
	kmScalar x;
	kmScalar y;
	kmScalar z;
	kmScalar w;
} kmVec4;

#pragma pack(pop)

#ifdef __cplusplus
extern "C" {
#endif

kmVec4* kmVec4Fill(kmVec4* pOut, kmScalar x, kmScalar y, kmScalar z, kmScalar w);
kmVec4* kmVec4Add(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2);
kmScalar kmVec4Dot(const kmVec4* pV1, const kmVec4* pV2);
kmScalar kmVec4Length(const kmVec4* pIn);
kmScalar kmVec4LengthSq(const kmVec4* pIn);
kmVec4* kmVec4Lerp(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2, kmScalar t);
kmVec4* kmVec4Normalize(kmVec4* pOut, const kmVec4* pIn);
kmVec4* kmVec4Scale(kmVec4* pOut, const kmVec4* pIn, const kmScalar s); /**< Scales a vector to length s*/
kmVec4* kmVec4Subtract(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2);
kmVec4* kmVec4Mul( kmVec4* pOut,const kmVec4* pV1, const kmVec4* pV2 ); 
kmVec4* kmVec4Div( kmVec4* pOut,const kmVec4* pV1, const kmVec4* pV2 ); 

kmVec4* kmVec4MultiplyMat4(kmVec4* pOut, const kmVec4* pV, const struct kmMat4* pM);
kmVec4* kmVec4Transform(kmVec4* pOut, const kmVec4* pV, const struct kmMat4* pM);
kmVec4* kmVec4TransformArray(kmVec4* pOut, unsigned int outStride,
			const kmVec4* pV, unsigned int vStride, const struct kmMat4* pM, unsigned int count);
int 	kmVec4AreEqual(const kmVec4* p1, const kmVec4* p2);
kmVec4* kmVec4Assign(kmVec4* pOut, const kmVec4* pIn);

#ifdef __cplusplus
}
#endif

#endif /* VEC4_H_INCLUDED */
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

#ifndef MAT4_H_INCLUDED
#define MAT4_H_INCLUDED


struct kmVec3;
struct kmMat3;
struct kmQuaternion;
struct kmPlane;

/*
A 4x4 matrix

        | 0   4   8  12 |
mat = | 1   5   9  13 |
        | 2   6  10  14 |
        | 3   7  11  15 |
*/

#ifdef __cplusplus
extern "C" {
#endif

typedef struct kmMat4 {
	kmScalar mat[16];
} kmMat4;

kmMat4* kmMat4Fill(kmMat4* pOut, const kmScalar* pMat);


kmMat4* kmMat4Identity(kmMat4* pOut);

kmMat4* kmMat4Inverse(kmMat4* pOut, const kmMat4* pM);


int kmMat4IsIdentity(const kmMat4* pIn);

kmMat4* kmMat4Transpose(kmMat4* pOut, const kmMat4* pIn);
kmMat4* kmMat4Multiply(kmMat4* pOut, const kmMat4* pM1, const kmMat4* pM2);

kmMat4* kmMat4Assign(kmMat4* pOut, const kmMat4* pIn);
kmMat4* kmMat4AssignMat3(kmMat4* pOut, const struct kmMat3* pIn);

int kmMat4AreEqual(const kmMat4* pM1, const kmMat4* pM2);

kmMat4* kmMat4RotationX(kmMat4* pOut, const kmScalar radians);
kmMat4* kmMat4RotationY(kmMat4* pOut, const kmScalar radians);
kmMat4* kmMat4RotationZ(kmMat4* pOut, const kmScalar radians);
kmMat4* kmMat4RotationYawPitchRoll(kmMat4* pOut, const kmScalar pitch, const kmScalar yaw, const kmScalar roll);
kmMat4* kmMat4RotationQuaternion(kmMat4* pOut, const struct kmQuaternion* pQ);
kmMat4* kmMat4RotationTranslation(kmMat4* pOut, const struct kmMat3* rotation, const struct kmVec3* translation);
kmMat4* kmMat4Scaling(kmMat4* pOut, const kmScalar x, const kmScalar y, const kmScalar z);
kmMat4* kmMat4Translation(kmMat4* pOut, const kmScalar x, const kmScalar y, const kmScalar z);

struct kmVec3* kmMat4GetUpVec3(struct kmVec3* pOut, const kmMat4* pIn);
struct kmVec3* kmMat4GetRightVec3(struct kmVec3* pOut, const kmMat4* pIn);
struct kmVec3* kmMat4GetForwardVec3RH(struct kmVec3* pOut, const kmMat4* pIn);
struct kmVec3* kmMat4GetForwardVec3LH(struct kmVec3* pOut, const kmMat4* pIn);

kmMat4* kmMat4PerspectiveProjection(kmMat4* pOut, kmScalar fovY, kmScalar aspect, kmScalar zNear, kmScalar zFar);
kmMat4* kmMat4OrthographicProjection(kmMat4* pOut, kmScalar left, kmScalar right, kmScalar bottom, kmScalar top, kmScalar nearVal, kmScalar farVal);
kmMat4* kmMat4LookAt(kmMat4* pOut, const struct kmVec3* pEye, const struct kmVec3* pCenter, const struct kmVec3* pUp);

kmMat4* kmMat4RotationAxisAngle(kmMat4* pOut, const struct kmVec3* axis, kmScalar radians);
struct kmMat3* kmMat4ExtractRotation(struct kmMat3* pOut, const kmMat4* pIn);
struct kmPlane* kmMat4ExtractPlane(struct kmPlane* pOut, const kmMat4* pIn, const kmEnum plane);
struct kmVec3* kmMat4RotationToAxisAngle(struct kmVec3* pAxis, kmScalar* radians, const kmMat4* pIn);
#ifdef __cplusplus
}
#endif
#endif /* MAT4_H_INCLUDED */


kmVec4* kmVec4Fill(kmVec4* pOut, kmScalar x, kmScalar y, kmScalar z, kmScalar w)
{
    pOut->x = x;
    pOut->y = y;
    pOut->z = z;
    pOut->w = w;
    return pOut;
}


/** Adds 2 4D vectors together. The result is store in pOut, the function returns*/
/** pOut so that it can be nested in another function.*/
kmVec4* kmVec4Add(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2) {
	pOut->x = pV1->x + pV2->x;
	pOut->y = pV1->y + pV2->y;
	pOut->z = pV1->z + pV2->z;
	pOut->w = pV1->w + pV2->w;

	return pOut;
}

/** Returns the dot product of 2 4D vectors*/
kmScalar kmVec4Dot(const kmVec4* pV1, const kmVec4* pV2) {
	return (  pV1->x * pV2->x
			+ pV1->y * pV2->y
			+ pV1->z * pV2->z
			+ pV1->w * pV2->w );
}

/** Returns the length of a 4D vector, this uses a sqrt so if the squared length will do use*/
/** kmVec4LengthSq*/
kmScalar kmVec4Length(const kmVec4* pIn) {
	return sqrtf(kmSQR(pIn->x) + kmSQR(pIn->y) + kmSQR(pIn->z) + kmSQR(pIn->w));
}

/** Returns the length of the 4D vector squared.*/
kmScalar kmVec4LengthSq(const kmVec4* pIn) {
	return kmSQR(pIn->x) + kmSQR(pIn->y) + kmSQR(pIn->z) + kmSQR(pIn->w);
}

/** Returns the interpolation of 2 4D vectors based on t.*/
kmVec4* kmVec4Lerp(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2, kmScalar t) {
    pOut->x = pV1->x + t * ( pV2->x - pV1->x ); 
    pOut->y = pV1->y + t * ( pV2->y - pV1->y ); 
    pOut->z = pV1->z + t * ( pV2->z - pV1->z ); 
    pOut->w = pV1->w + t * ( pV2->w - pV1->w ); 
    return pOut;
}

/** Normalizes a 4D vector. The result is stored in pOut. pOut is returned*/
kmVec4* kmVec4Normalize(kmVec4* pOut, const kmVec4* pIn) {
    if (!pIn->x && !pIn->y && !pIn->z && !pIn->w){
        return kmVec4Assign(pOut, pIn);
    }

	kmScalar l = 1.0f / kmVec4Length(pIn);
    pOut->x = pIn->x * l;
	pOut->y = pIn->y * l;
	pOut->z = pIn->z * l;
	pOut->w = pIn->w * l;

	return pOut;
}

/** Scales a vector to the required length. This performs a Normalize before multiplying by S.*/
kmVec4* kmVec4Scale(kmVec4* pOut, const kmVec4* pIn, const kmScalar s) {
	kmVec4Normalize(pOut, pIn);

	pOut->x *= s;
	pOut->y *= s;
	pOut->z *= s;
	pOut->w *= s;
	return pOut;
}

/** Subtracts one 4D pV2 from pV1. The result is stored in pOut. pOut is returned*/
kmVec4* kmVec4Subtract(kmVec4* pOut, const kmVec4* pV1, const kmVec4* pV2) {
	pOut->x = pV1->x - pV2->x;
	pOut->y = pV1->y - pV2->y;
	pOut->z = pV1->z - pV2->z;
	pOut->w = pV1->w - pV2->w;

	return pOut;
}

kmVec4* kmVec4Mul( kmVec4* pOut,const kmVec4* pV1, const kmVec4* pV2 ) {
    pOut->x = pV1->x * pV2->x;
    pOut->y = pV1->y * pV2->y;
    pOut->z = pV1->z * pV2->z;
    pOut->w = pV1->w * pV2->w;
    return pOut;
}

kmVec4* kmVec4Div( kmVec4* pOut,const kmVec4* pV1, const kmVec4* pV2 ) {
    if ( pV2->x && pV2->y && pV2->z && pV2->w){
        pOut->x = pV1->x / pV2->x;
        pOut->y = pV1->y / pV2->y;
        pOut->z = pV1->z / pV2->z;
        pOut->w = pV1->w / pV2->w;
    }
    return pOut;
}

/** Multiplies a 4D vector by a matrix, the result is stored in pOut, and pOut is returned.*/
kmVec4* kmVec4MultiplyMat4(kmVec4* pOut, const kmVec4* pV, const struct kmMat4* pM) {
    pOut->x = pV->x * pM->mat[0] + pV->y * pM->mat[4] + pV->z * pM->mat[8] + pV->w * pM->mat[12];
    pOut->y = pV->x * pM->mat[1] + pV->y * pM->mat[5] + pV->z * pM->mat[9] + pV->w * pM->mat[13];
    pOut->z = pV->x * pM->mat[2] + pV->y * pM->mat[6] + pV->z * pM->mat[10] + pV->w * pM->mat[14];
    pOut->w = pV->x * pM->mat[3] + pV->y * pM->mat[7] + pV->z * pM->mat[11] + pV->w * pM->mat[15];
    return pOut;
}

kmVec4* kmVec4Transform(kmVec4* pOut, const kmVec4* pV, const kmMat4* pM) {
    return kmVec4MultiplyMat4(pOut, pV, pM);
}

/** Loops through an input array transforming each vec4 by the matrix.*/
kmVec4* kmVec4TransformArray(kmVec4* pOut, unsigned int outStride,
			const kmVec4* pV, unsigned int vStride, const kmMat4* pM, unsigned int count) {
    unsigned int i = 0;
    /*Go through all of the vectors*/
    while (i < count) {
        const kmVec4* in = pV + (i * vStride); /*Get a pointer to the current input*/
        kmVec4* out = pOut + (i * outStride); /*and the current output*/
        kmVec4Transform(out, in, pM); /*Perform transform on it*/
        ++i;
    }

    return pOut;
}

int kmVec4AreEqual(const kmVec4* p1, const kmVec4* p2) {
	return (
		(p1->x < p2->x + kmEpsilon && p1->x > p2->x - kmEpsilon) &&
		(p1->y < p2->y + kmEpsilon && p1->y > p2->y - kmEpsilon) &&
		(p1->z < p2->z + kmEpsilon && p1->z > p2->z - kmEpsilon) &&
		(p1->w < p2->w + kmEpsilon && p1->w > p2->w - kmEpsilon)
	);
}

kmVec4* kmVec4Assign(kmVec4* pOut, const kmVec4* pIn) {
	assert(pOut != pIn);

	memcpy(pOut, pIn, sizeof(kmScalar) * 4);

	return pOut;
}

