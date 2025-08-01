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

#include <assert.h>
#include <stdlib.h>

#ifndef HEADER_8E9D0ABA3C76B989
#define HEADER_8E9D0ABA3C76B989

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


#ifndef MAT3_H_INCLUDED
#define MAT3_H_INCLUDED

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

struct kmVec3;
struct kmQuaternion;
struct kmMat4;

typedef struct kmMat3{
	kmScalar mat[9];
} kmMat3;

#ifdef __cplusplus
extern "C" {
#endif

kmMat3* kmMat3Fill(kmMat3* pOut, const kmScalar* pMat);
kmMat3* kmMat3Adjugate(kmMat3* pOut, const kmMat3* pIn);
kmMat3* kmMat3Identity(kmMat3* pOut);
kmMat3* kmMat3Inverse(kmMat3* pOut, const kmMat3* pM);
int  kmMat3IsIdentity(const kmMat3* pIn);
kmMat3* kmMat3Transpose(kmMat3* pOut, const kmMat3* pIn);
kmScalar kmMat3Determinant(const kmMat3* pIn);
kmMat3* kmMat3Multiply(kmMat3* pOut, const kmMat3* pM1, const kmMat3* pM2);
kmMat3* kmMat3ScalarMultiply(kmMat3* pOut, const kmMat3* pM, const kmScalar pFactor);

kmMat3* kmMat3Assign(kmMat3* pOut, const kmMat3* pIn);
kmMat3* kmMat3AssignMat4(kmMat3* pOut, const struct kmMat4* pIn);
int  kmMat3AreEqual(const kmMat3* pM1, const kmMat3* pM2);

struct kmVec3* kmMat3GetUpVec3(struct kmVec3* pOut, const kmMat3* pIn);
struct kmVec3* kmMat3GetRightVec3(struct kmVec3* pOut, const kmMat3* pIn);
struct kmVec3* kmMat3GetForwardVec3(struct kmVec3* pOut, const kmMat3* pIn);

kmMat3* kmMat3RotationX(kmMat3* pOut, const kmScalar radians);
kmMat3* kmMat3RotationY(kmMat3* pOut, const kmScalar radians);
kmMat3* kmMat3RotationZ(kmMat3* pOut, const kmScalar radians);

kmMat3* kmMat3Rotation(kmMat3* pOut, const kmScalar radians);
kmMat3* kmMat3Scaling(kmMat3* pOut, const kmScalar x, const kmScalar y);
kmMat3* kmMat3Translation(kmMat3* pOut, const kmScalar x, const kmScalar y);

kmMat3* kmMat3RotationQuaternion(kmMat3* pOut, const struct kmQuaternion* pIn);

kmMat3* kmMat3RotationAxisAngle(kmMat3* pOut, const struct kmVec3* axis, kmScalar radians);
struct kmVec3* kmMat3RotationToAxisAngle(struct kmVec3* pAxis, kmScalar* radians, const kmMat3* pIn);
kmMat3* kmMat3LookAt(kmMat3* pOut, const struct kmVec3* pEye, const struct kmVec3* pCenter, const struct kmVec3* pUp);

#ifdef __cplusplus
}
#endif
#endif /* MAT3_H_INCLUDED */


#endif /* header guard */
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

const kmVec2 KM_VEC2_POS_Y = { 0, 1 };
const kmVec2 KM_VEC2_NEG_Y = { 0, -1 };
const kmVec2 KM_VEC2_NEG_X = { -1, 0 };
const kmVec2 KM_VEC2_POS_X = { 1, 0 };
const kmVec2 KM_VEC2_ZERO = { 0, 0 };

kmVec2* kmVec2Fill(kmVec2* pOut, kmScalar x, kmScalar y)
{
    pOut->x = x;
    pOut->y = y;
    return pOut;
}

kmScalar kmVec2Length(const kmVec2* pIn)
{
    return sqrtf(kmSQR(pIn->x) + kmSQR(pIn->y));
}

kmScalar kmVec2LengthSq(const kmVec2* pIn)
{
    return kmSQR(pIn->x) + kmSQR(pIn->y);
}

kmVec2* kmVec2Lerp(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2, kmScalar t) {
    pOut->x = pV1->x + t * ( pV2->x - pV1->x ); 
    pOut->y = pV1->y + t * ( pV2->y - pV1->y ); 
    return pOut;
}

kmVec2* kmVec2Normalize(kmVec2* pOut, const kmVec2* pIn)
{
        if (!pIn->x && !pIn->y)
                return kmVec2Assign(pOut, pIn);

	kmScalar l = 1.0f / kmVec2Length(pIn);

	kmVec2 v;
	v.x = pIn->x * l;
	v.y = pIn->y * l;
    
	pOut->x = v.x;
	pOut->y = v.y;

	return pOut;
}

kmVec2* kmVec2Add(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2)
{
	pOut->x = pV1->x + pV2->x;
	pOut->y = pV1->y + pV2->y;

	return pOut;
}

kmScalar kmVec2Dot(const kmVec2* pV1, const kmVec2* pV2)
{
    return pV1->x * pV2->x + pV1->y * pV2->y;
}

kmScalar kmVec2Cross(const kmVec2* pV1, const kmVec2* pV2) 
{
    return pV1->x * pV2->y - pV1->y * pV2->x;
}

kmVec2* kmVec2Subtract(kmVec2* pOut, const kmVec2* pV1, const kmVec2* pV2)
{
	pOut->x = pV1->x - pV2->x;
	pOut->y = pV1->y - pV2->y;

	return pOut;
}

kmVec2* kmVec2Mul( kmVec2* pOut,const kmVec2* pV1, const kmVec2* pV2 ) {
    pOut->x = pV1->x * pV2->x;
    pOut->y = pV1->y * pV2->y;
    return pOut;
}

kmVec2* kmVec2Div( kmVec2* pOut,const kmVec2* pV1, const kmVec2* pV2 ) {
    if ( pV2->x && pV2->y ){
        pOut->x = pV1->x / pV2->x;
        pOut->y = pV1->y / pV2->y;
    }
    return pOut;
}

kmVec2* kmVec2Transform(kmVec2* pOut, const kmVec2* pV, const kmMat3* pM)
{
    kmVec2 v;

    v.x = pV->x * pM->mat[0] + pV->y * pM->mat[3] + pM->mat[6];
    v.y = pV->x * pM->mat[1] + pV->y * pM->mat[4] + pM->mat[7];

    pOut->x = v.x;
    pOut->y = v.y;

    return pOut;
}

kmVec2* kmVec2TransformCoord(kmVec2* pOut, const kmVec2* pV, const kmMat3* pM)
{
	assert(0);
    return NULL;
}

kmVec2* kmVec2Scale(kmVec2* pOut, const kmVec2* pIn, const kmScalar s)
{
	pOut->x = pIn->x * s;
	pOut->y = pIn->y * s;

	return pOut;
}

int kmVec2AreEqual(const kmVec2* p1, const kmVec2* p2)
{
	return (
				(p1->x < p2->x + kmEpsilon && p1->x > p2->x - kmEpsilon) &&
				(p1->y < p2->y + kmEpsilon && p1->y > p2->y - kmEpsilon)
			);
}

/**
 * Assigns pIn to pOut. Returns pOut. If pIn and pOut are the same
 * then nothing happens but pOut is still returned
 */
kmVec2* kmVec2Assign(kmVec2* pOut, const kmVec2* pIn) {
	if (pOut == pIn) {
		return pOut;
	}

	pOut->x = pIn->x;
	pOut->y = pIn->y;

	return pOut;
}

/**
 * Rotates the point anticlockwise around a center
 * by an amount of degrees.
 *
 * Code ported from Irrlicht: http://irrlicht.sourceforge.net/
 */
kmVec2* kmVec2RotateBy(kmVec2* pOut, const kmVec2* pIn,
      const kmScalar degrees, const kmVec2* center)
{
   kmScalar x, y;
   const kmScalar radians = kmDegreesToRadians(degrees);
   const kmScalar cs = cosf(radians), sn = sinf(radians);

   pOut->x = pIn->x - center->x;
   pOut->y = pIn->y - center->y;

   x = pOut->x * cs - pOut->y * sn;
   y = pOut->x * sn + pOut->y * cs;

   pOut->x = x + center->x;
   pOut->y = y + center->y;

   return pOut;
}

/**
 * 	Returns the angle in degrees between the two vectors
 */
kmScalar kmVec2DegreesBetween(const kmVec2* v1, const kmVec2* v2) {
	if(kmVec2AreEqual(v1, v2)) {
		return 0.0;
	}
	
	kmVec2 t1, t2;
	kmVec2Normalize(&t1, v1);
	kmVec2Normalize(&t2, v2);
	
	kmScalar cross = kmVec2Cross(&t1, &t2);
	kmScalar dot = kmVec2Dot(&t1, &t2);

	/*
	 * acos is only defined for -1 to 1. Outside the range we 
	 * get NaN even if that's just because of a floating point error
	 * so we clamp to the -1 - 1 range
	 */

	if(dot > 1.0) dot = 1.0;
	if(dot < -1.0) dot = -1.0;

	return kmRadiansToDegrees(atan2(cross, dot));
}

/**
 * Returns the distance between the two points
 */
kmScalar kmVec2DistanceBetween(const kmVec2* v1, const kmVec2* v2) {
	kmVec2 diff;
	kmVec2Subtract(&diff, v2, v1);
	return fabs(kmVec2Length(&diff));
}
/**
 * Returns the point mid-way between two others
 */
kmVec2* kmVec2MidPointBetween(kmVec2* pOut, const kmVec2* v1, const kmVec2* v2) {
	kmVec2 sum;
    kmVec2Add(&sum, v1, v2);
    pOut->x = sum.x / 2.0f;
    pOut->y = sum.y / 2.0f;

	return pOut;
}

/**
 * Reflects a vector about a given surface normal. The surface normal is
 * assumed to be of unit length.
 */
kmVec2* kmVec2Reflect(kmVec2* pOut, const kmVec2* pIn, const kmVec2* normal) {
	kmVec2 tmp;
	kmVec2Scale(&tmp, normal, 2.0f * kmVec2Dot(pIn, normal));
	kmVec2Subtract(pOut, pIn, &tmp);

	return pOut;
}
