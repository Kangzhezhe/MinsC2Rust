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

#include <stdlib.h>
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

#ifndef QUATERNION_H_INCLUDED
#define QUATERNION_H_INCLUDED

#ifdef __cplusplus
extern "C" {
#endif


struct kmMat4;
struct kmMat3;
struct kmVec3;

typedef struct kmQuaternion {
	kmScalar x;
	kmScalar y;
	kmScalar z;
	kmScalar w;
} kmQuaternion;

int kmQuaternionAreEqual(const kmQuaternion* p1, const kmQuaternion* p2);
kmQuaternion* kmQuaternionFill(kmQuaternion* pOut, kmScalar x, kmScalar y, kmScalar z, kmScalar w);
kmScalar 	kmQuaternionDot(const kmQuaternion* q1, const kmQuaternion* q2); /**< Returns the dot product of the 2 quaternions*/

kmQuaternion* kmQuaternionExp(kmQuaternion* pOut, const kmQuaternion* pIn); /**< Returns the exponential of the quaternion*/

/**< Makes the passed quaternion an identity quaternion*/

kmQuaternion* kmQuaternionIdentity(kmQuaternion* pOut);

/**< Returns the inverse of the passed Quaternion*/

kmQuaternion* kmQuaternionInverse(kmQuaternion* pOut, const kmQuaternion* pIn);

/**< Returns true if the quaternion is an identity quaternion*/

int kmQuaternionIsIdentity(const kmQuaternion* pIn);

/**< Returns the length of the quaternion*/

kmScalar kmQuaternionLength(const kmQuaternion* pIn);

/**< Returns the length of the quaternion squared (prevents a sqrt)*/

kmScalar kmQuaternionLengthSq(const kmQuaternion* pIn);

/**< Returns the natural logarithm*/

kmQuaternion* kmQuaternionLn(kmQuaternion* pOut, const kmQuaternion* pIn);

/**< Multiplies 2 quaternions together*/

kmQuaternion* kmQuaternionMultiply(kmQuaternion* pOut, const kmQuaternion* q1, const kmQuaternion* q2);

/**< Normalizes a quaternion*/

kmQuaternion* kmQuaternionNormalize(kmQuaternion* pOut, const kmQuaternion* pIn);

/**< Rotates a quaternion around an axis*/

kmQuaternion* kmQuaternionRotationAxisAngle(kmQuaternion* pOut, const struct kmVec3* pV, kmScalar angle);

/**< Creates a quaternion from a rotation matrix*/

kmQuaternion* kmQuaternionRotationMatrix(kmQuaternion* pOut, const struct kmMat3* pIn);

/**< Create a quaternion from yaw, pitch and roll*/

kmQuaternion* kmQuaternionRotationPitchYawRoll(kmQuaternion* pOut, kmScalar pitch, kmScalar yaw, kmScalar roll);
/**< Interpolate between 2 quaternions*/
kmQuaternion* kmQuaternionSlerp(kmQuaternion* pOut, const kmQuaternion* q1, const kmQuaternion* q2, kmScalar t);

/**< Get the axis and angle of rotation from a quaternion*/
void kmQuaternionToAxisAngle(const kmQuaternion* pIn, struct kmVec3* pVector, kmScalar* pAngle);

/**< Scale a quaternion*/
kmQuaternion* kmQuaternionScale(kmQuaternion* pOut, const kmQuaternion* pIn, kmScalar s);
kmQuaternion* kmQuaternionAssign(kmQuaternion* pOut, const kmQuaternion* pIn);
kmQuaternion* kmQuaternionAdd(kmQuaternion* pOut, const kmQuaternion* pQ1, const kmQuaternion* pQ2);
kmQuaternion* kmQuaternionSubtract(kmQuaternion* pOut, const kmQuaternion* pQ1, const kmQuaternion* pQ2);

kmQuaternion* kmQuaternionRotationBetweenVec3(kmQuaternion* pOut, const struct kmVec3* vec1, const struct kmVec3* vec2, const struct kmVec3* fallback);
struct kmVec3* kmQuaternionMultiplyVec3(struct kmVec3* pOut, const kmQuaternion* q, const struct kmVec3* v);

kmVec3* kmQuaternionGetUpVec3(kmVec3* pOut, const kmQuaternion* pIn);
kmVec3* kmQuaternionGetRightVec3(kmVec3* pOut, const kmQuaternion* pIn);
kmVec3* kmQuaternionGetForwardVec3RH(kmVec3* pOut, const kmQuaternion* pIn);
kmVec3* kmQuaternionGetForwardVec3LH(kmVec3* pOut, const kmQuaternion* pIn);

kmScalar kmQuaternionGetPitch(const kmQuaternion* q);
kmScalar kmQuaternionGetYaw(const kmQuaternion* q);
kmScalar kmQuaternionGetRoll(const kmQuaternion* q);

kmQuaternion* kmQuaternionLookRotation(kmQuaternion* pOut, const kmVec3* direction, const kmVec3* up);

#ifdef __cplusplus
}
#endif

#endif

kmMat3* kmMat3Fill(kmMat3* pOut, const kmScalar* pMat)
{
    memcpy(pOut->mat, pMat, sizeof(kmScalar) * 9);
    return pOut;
}

/** Sets pOut to an identity matrix returns pOut*/
kmMat3* kmMat3Identity(kmMat3* pOut)
{
	memset(pOut->mat, 0, sizeof(kmScalar) * 9);
	pOut->mat[0] = pOut->mat[4] = pOut->mat[8] = 1.0f;
	return pOut;
}

kmScalar kmMat3Determinant(const kmMat3* pIn)
{
    kmScalar output;
    /*
    calculating the determinant following the rule of sarus,
        | 0  3  6 | 0  3 |
    m = | 1  4  7 | 1  4 |
        | 2  5  8 | 2  5 |
    now sum up the products of the diagonals going to the right (i.e. 0,4,8)
    and subtract the products of the other diagonals (i.e. 2,4,6)
    */

    output = pIn->mat[0] * pIn->mat[4] * pIn->mat[8] + pIn->mat[1] * pIn->mat[5] * pIn->mat[6] + pIn->mat[2] * pIn->mat[3] * pIn->mat[7];
    output -= pIn->mat[2] * pIn->mat[4] * pIn->mat[6] + pIn->mat[0] * pIn->mat[5] * pIn->mat[7] + pIn->mat[1] * pIn->mat[3] * pIn->mat[8];

    return output;
}


kmMat3* kmMat3Adjugate(kmMat3* pOut, const kmMat3* pIn)
{
    pOut->mat[0] = pIn->mat[4] * pIn->mat[8] - pIn->mat[5] * pIn->mat[7];
    pOut->mat[1] = pIn->mat[2] * pIn->mat[7] - pIn->mat[1] * pIn->mat[8];
    pOut->mat[2] = pIn->mat[1] * pIn->mat[5] - pIn->mat[2] * pIn->mat[4];
    pOut->mat[3] = pIn->mat[5] * pIn->mat[6] - pIn->mat[3] * pIn->mat[8];
    pOut->mat[4] = pIn->mat[0] * pIn->mat[8] - pIn->mat[2] * pIn->mat[6];
    pOut->mat[5] = pIn->mat[2] * pIn->mat[3] - pIn->mat[0] * pIn->mat[5];
    pOut->mat[6] = pIn->mat[3] * pIn->mat[7] - pIn->mat[4] * pIn->mat[6];
    pOut->mat[7] = pIn->mat[1] * pIn->mat[6] - pIn->mat[0] * pIn->mat[7];
    pOut->mat[8] = pIn->mat[0] * pIn->mat[4] - pIn->mat[1] * pIn->mat[3];

    return pOut;
}

kmMat3* kmMat3Inverse(kmMat3* pOut, const kmMat3* pM)
{
    kmScalar determinate = kmMat3Determinant(pM);
    kmScalar detInv;
    kmMat3 adjugate;

    if(determinate == 0.0)
    {
        return NULL;
    }

    detInv = 1.0 / determinate;

	kmMat3Adjugate(&adjugate, pM);
	kmMat3ScalarMultiply(pOut, &adjugate, detInv);

	return pOut;
}

/** Returns true if pIn is an identity matrix */
int kmMat3IsIdentity(const kmMat3* pIn)
{
	static kmScalar identity [] = { 	1.0f, 0.0f, 0.0f,
										0.0f, 1.0f, 0.0f,
										0.0f, 0.0f, 1.0f};

	return (memcmp(identity, pIn->mat, sizeof(kmScalar) * 9) == 0);
}

/** Sets pOut to the transpose of pIn, returns pOut */
kmMat3* kmMat3Transpose(kmMat3* pOut, const kmMat3* pIn)
{
    kmScalar temp[9];
    
    temp[0] = pIn->mat[0];
    temp[1] = pIn->mat[3];
    temp[2] = pIn->mat[6];

    temp[3] = pIn->mat[1];
    temp[4] = pIn->mat[4];
    temp[5] = pIn->mat[7];

    temp[6] = pIn->mat[2];
    temp[7] = pIn->mat[5];
    temp[8] = pIn->mat[8];
        
    memcpy(&pOut->mat, temp, sizeof(kmScalar)*9);

	return pOut;
}

/* Multiplies pM1 with pM2, stores the result in pOut, returns pOut */
kmMat3* kmMat3Multiply(kmMat3* pOut, const kmMat3* pM1, const kmMat3* pM2)
{
	kmScalar mat[9];

	const kmScalar *m1 = pM1->mat, *m2 = pM2->mat;

	mat[0] = m1[0] * m2[0] + m1[3] * m2[1] + m1[6] * m2[2];
	mat[1] = m1[1] * m2[0] + m1[4] * m2[1] + m1[7] * m2[2];
	mat[2] = m1[2] * m2[0] + m1[5] * m2[1] + m1[8] * m2[2];

	mat[3] = m1[0] * m2[3] + m1[3] * m2[4] + m1[6] * m2[5];
	mat[4] = m1[1] * m2[3] + m1[4] * m2[4] + m1[7] * m2[5];
	mat[5] = m1[2] * m2[3] + m1[5] * m2[4] + m1[8] * m2[5];

	mat[6] = m1[0] * m2[6] + m1[3] * m2[7] + m1[6] * m2[8];
	mat[7] = m1[1] * m2[6] + m1[4] * m2[7] + m1[7] * m2[8];
	mat[8] = m1[2] * m2[6] + m1[5] * m2[7] + m1[8] * m2[8];

	memcpy(pOut->mat, mat, sizeof(kmScalar)*9);

	return pOut;
}

kmMat3* kmMat3ScalarMultiply(kmMat3* pOut, const kmMat3* pM, const kmScalar pFactor)
{
    kmScalar mat[9];
    int i;

    for(i = 0; i < 9; i++)
    {
        mat[i] = pM->mat[i] * pFactor;
    }

    memcpy(pOut->mat, mat, sizeof(kmScalar)*9);

	return pOut;
}

/** Assigns the value of pIn to pOut */
kmMat3* kmMat3Assign(kmMat3* pOut, const kmMat3* pIn)
{
	assert(pOut != pIn); /*You have tried to self-assign!!*/

	memcpy(pOut->mat, pIn->mat, sizeof(kmScalar)*9);

	return pOut;
}

kmMat3* kmMat3AssignMat4(kmMat3* pOut, const kmMat4* pIn) {
    pOut->mat[0] = pIn->mat[0];
    pOut->mat[1] = pIn->mat[1];
    pOut->mat[2] = pIn->mat[2];

    pOut->mat[3] = pIn->mat[4];
    pOut->mat[4] = pIn->mat[5];
    pOut->mat[5] = pIn->mat[6];

    pOut->mat[6] = pIn->mat[8];
    pOut->mat[7] = pIn->mat[9];
    pOut->mat[8] = pIn->mat[10];
    return pOut;
}

/** Returns true if the 2 matrices are equal (approximately) */
int kmMat3AreEqual(const kmMat3* pMat1, const kmMat3* pMat2)
{
	int i;
	if (pMat1 == pMat2) {
		return KM_TRUE;
	}

	for (i = 0; i < 9; ++i) {
		if (!(pMat1->mat[i] + kmEpsilon > pMat2->mat[i] &&
            pMat1->mat[i] - kmEpsilon < pMat2->mat[i])) {
			return KM_FALSE;
        }
	}

	return KM_TRUE;
}

/* Rotation around the z axis so everything stays planar in XY */
kmMat3* kmMat3Rotation(kmMat3* pOut, const kmScalar radians)
{
	/*
         |  cos(A)  -sin(A)   0  |
     M = |  sin(A)   cos(A)   0  |
         |  0        0        1  |
	*/

	pOut->mat[0] = cosf(radians);
	pOut->mat[1] = sinf(radians);
	pOut->mat[2] = 0.0f;

	pOut->mat[3] = -sinf(radians);
	pOut->mat[4] = cosf(radians);
	pOut->mat[5] = 0.0f;

	pOut->mat[6] = 0.0f;
	pOut->mat[7] = 0.0f;
	pOut->mat[8] = 1.0f;

	return pOut;
}

/** Builds a scaling matrix */
kmMat3* kmMat3Scaling(kmMat3* pOut, const kmScalar x, const kmScalar y)
{
/*	memset(pOut->mat, 0, sizeof(kmScalar) * 9);*/
	kmMat3Identity(pOut);
	pOut->mat[0] = x;
	pOut->mat[4] = y;

	return pOut;
}

kmMat3* kmMat3Translation(kmMat3* pOut, const kmScalar x, const kmScalar y)
{
/*    memset(pOut->mat, 0, sizeof(kmScalar) * 9);*/
	kmMat3Identity(pOut);
	pOut->mat[6] = x;
	pOut->mat[7] = y;
/*    pOut->mat[8] = 1.0;*/

    return pOut;
}


kmMat3* kmMat3RotationQuaternion(kmMat3* pOut, const kmQuaternion* pIn)
{
    if (!pIn || !pOut) {
	return NULL;
    }

    /* First row */
    pOut->mat[0] = 1.0f - 2.0f * (pIn->y * pIn->y + pIn->z * pIn->z);
    pOut->mat[1] = 2.0f * (pIn->x * pIn->y - pIn->w * pIn->z);
    pOut->mat[2] = 2.0f * (pIn->x * pIn->z + pIn->w * pIn->y);

    /* Second row */
    pOut->mat[3] = 2.0f * (pIn->x * pIn->y + pIn->w * pIn->z);
    pOut->mat[4] = 1.0f - 2.0f * (pIn->x * pIn->x + pIn->z * pIn->z);
    pOut->mat[5] = 2.0f * (pIn->y * pIn->z - pIn->w * pIn->x);

    /* Third row */
    pOut->mat[6] = 2.0f * (pIn->x * pIn->z - pIn->w * pIn->y);
    pOut->mat[7] = 2.0f * (pIn->y * pIn->z + pIn->w * pIn->x);
    pOut->mat[8] = 1.0f - 2.0f * (pIn->x * pIn->x + pIn->y * pIn->y);

    return pOut;
}

kmMat3* kmMat3RotationAxisAngle(kmMat3* pOut, const struct kmVec3* axis, kmScalar radians)
{
    kmScalar rcos = cosf(radians);
    kmScalar rsin = sinf(radians);

    pOut->mat[0] = rcos + axis->x * axis->x * (1 - rcos);
    pOut->mat[1] = axis->z * rsin + axis->y * axis->x * (1 - rcos);
    pOut->mat[2] = -axis->y * rsin + axis->z * axis->x * (1 - rcos);

    pOut->mat[3] = -axis->z * rsin + axis->x * axis->y * (1 - rcos);
    pOut->mat[4] = rcos + axis->y * axis->y * (1 - rcos);
    pOut->mat[5] = axis->x * rsin + axis->z * axis->y * (1 - rcos);

    pOut->mat[6] = axis->y * rsin + axis->x * axis->z * (1 - rcos);
    pOut->mat[7] = -axis->x * rsin + axis->y * axis->z * (1 - rcos);
    pOut->mat[8] = rcos + axis->z * axis->z * (1 - rcos);

    return pOut;
}

kmVec3* kmMat3RotationToAxisAngle(kmVec3* pAxis, kmScalar* radians, const kmMat3* pIn)
{
    /*Surely not this easy?*/
    kmQuaternion temp;
    kmQuaternionRotationMatrix(&temp, pIn);
    kmQuaternionToAxisAngle(&temp, pAxis, radians);
    return pAxis;
}

/**
 * Builds an X-axis rotation matrix and stores it in pOut, returns pOut
 */
kmMat3* kmMat3RotationX(kmMat3* pOut, const kmScalar radians)
{
	/*
		 |  1  0       0      |
	 M = |  0  cos(A) -sin(A) |
	     |  0  sin(A)  cos(A) |

	*/

	pOut->mat[0] = 1.0f;
	pOut->mat[1] = 0.0f;
	pOut->mat[2] = 0.0f;

	pOut->mat[3] = 0.0f;
	pOut->mat[4] = cosf(radians);
	pOut->mat[5] = sinf(radians);

	pOut->mat[6] = 0.0f;
	pOut->mat[7] = -sinf(radians);
	pOut->mat[8] = cosf(radians);

	return pOut;
}

/**
 * Builds a rotation matrix using the rotation around the Y-axis
 * The result is stored in pOut, pOut is returned.
 */
kmMat3* kmMat3RotationY(kmMat3* pOut, const kmScalar radians)
{
	/*
	     |  cos(A)  0   sin(A) |
	 M = |  0       1   0      |
	     | -sin(A)  0   cos(A) |
	*/

	pOut->mat[0] = cosf(radians);
	pOut->mat[1] = 0.0f;
	pOut->mat[2] = -sinf(radians);

	pOut->mat[3] = 0.0f;
	pOut->mat[4] = 1.0f;
	pOut->mat[5] = 0.0f;

	pOut->mat[6] = sinf(radians);
	pOut->mat[7] = 0.0f;
	pOut->mat[8] = cosf(radians);

	return pOut;
}

/**
 * Builds a rotation matrix around the Z-axis. The resulting
 * matrix is stored in pOut. pOut is returned.
 */
kmMat3* kmMat3RotationZ(kmMat3* pOut, const kmScalar radians)
{
	/*
	     |  cos(A)  -sin(A)   0  |
	 M = |  sin(A)   cos(A)   0  |
	     |  0        0        1  |
	*/

	pOut->mat[0] = cosf(radians);
	pOut->mat[1] =-sinf(radians);
	pOut->mat[2] = 0.0f;

	pOut->mat[3] = sinf(radians);
	pOut->mat[4] = cosf(radians);
	pOut->mat[5] = 0.0f;

	pOut->mat[6] = 0.0f;
	pOut->mat[7] = 0.0f;
	pOut->mat[8] = 1.0f;

	return pOut;
}

kmVec3* kmMat3GetUpVec3(kmVec3* pOut, const kmMat3* pIn) {
	pOut->x = pIn->mat[3];
	pOut->y = pIn->mat[4];
	pOut->z = pIn->mat[5];

	kmVec3Normalize(pOut, pOut);

	return pOut;
}

kmVec3* kmMat3GetRightVec3(kmVec3* pOut, const kmMat3* pIn) {
	pOut->x = pIn->mat[0];
	pOut->y = pIn->mat[1];
	pOut->z = pIn->mat[2];

	kmVec3Normalize(pOut, pOut);

	return pOut;
}

kmVec3* kmMat3GetForwardVec3(kmVec3* pOut, const kmMat3* pIn) {
	pOut->x = pIn->mat[6];
	pOut->y = pIn->mat[7];
	pOut->z = pIn->mat[8];

	kmVec3Normalize(pOut, pOut);

	return pOut;
}

kmMat3* kmMat3LookAt(kmMat3* pOut, const kmVec3* pEye,
                     const kmVec3* pCenter, const kmVec3* pUp)
{
    kmVec3 f, up, s, u;

    kmVec3Subtract(&f, pCenter, pEye);
    kmVec3Normalize(&f, &f);

    kmVec3Assign(&up, pUp);
    kmVec3Normalize(&up, &up);

    kmVec3Cross(&s, &f, &up);
    kmVec3Normalize(&s, &s);

    kmVec3Cross(&u, &s, &f);
    kmVec3Normalize(&s, &s);

    pOut->mat[0] = s.x;
    pOut->mat[3] = s.y;
    pOut->mat[6] = s.z;

    pOut->mat[1] = u.x;
    pOut->mat[4] = u.y;
    pOut->mat[7] = u.z;

    pOut->mat[2] = -f.x;
    pOut->mat[5] = -f.y;
    pOut->mat[8] = -f.z;

    return pOut;
}
