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

/**
 * @file mat4.c
 */
#include <memory.h>
#include <assert.h>
#include <stdlib.h>

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

#ifndef PLANE_H_INCLUDED
#define PLANE_H_INCLUDED

#define KM_PLANE_LEFT 0
#define KM_PLANE_RIGHT 1
#define KM_PLANE_BOTTOM 2
#define KM_PLANE_TOP 3
#define KM_PLANE_NEAR 4
#define KM_PLANE_FAR 5


struct kmVec3;
struct kmVec4;
struct kmMat4;

typedef struct kmPlane {
	kmScalar 	a, b, c, d;
} kmPlane;

#ifdef __cplusplus
extern "C" {
#endif

typedef enum KM_POINT_CLASSIFICATION {
    POINT_BEHIND_PLANE = -1,
    POINT_ON_PLANE = 0,
    POINT_INFRONT_OF_PLANE = 1
} KM_POINT_CLASSIFICATION;

kmPlane* kmPlaneFill(kmPlane* plane, kmScalar a, kmScalar b, kmScalar c, kmScalar d);
kmScalar kmPlaneDot(const kmPlane* pP, const struct kmVec4* pV);
kmScalar kmPlaneDotCoord(const kmPlane* pP, const struct kmVec3* pV);
kmScalar kmPlaneDotNormal(const kmPlane* pP, const struct kmVec3* pV);
kmPlane* kmPlaneFromNormalAndDistance(kmPlane* plane, const struct kmVec3* normal, const kmScalar dist);
kmPlane* kmPlaneFromPointAndNormal(kmPlane* pOut, const struct kmVec3* pPoint, const struct kmVec3* pNormal);
kmPlane* kmPlaneFromPoints(kmPlane* pOut, const struct kmVec3* p1, const struct kmVec3* p2, const struct kmVec3* p3);
struct kmVec3* kmPlaneIntersectLine(struct kmVec3* pOut, const kmPlane* pP, const struct kmVec3* pV1, const struct kmVec3* pV2);
kmPlane* kmPlaneNormalize(kmPlane* pOut, const kmPlane* pP);
kmPlane* kmPlaneScale(kmPlane* pOut, const kmPlane* pP, kmScalar s);
KM_POINT_CLASSIFICATION kmPlaneClassifyPoint(const kmPlane* pIn, const struct kmVec3* pP); /** Classifys a point against a plane */

kmPlane* kmPlaneExtractFromMat4(kmPlane* pOut, const struct kmMat4* pIn, kmInt row);
struct kmVec3* kmPlaneGetIntersection(struct kmVec3* pOut, const kmPlane* p1, const kmPlane* p2, const kmPlane* p3);

#ifdef __cplusplus
}
#endif

#endif /* PLANE_H_INCLUDED */

/**
 * Fills a kmMat4 structure with the values from a 16
 * element array of kmScalars
 * @Params pOut - A pointer to the destination matrix
 * 		   pMat - A 16 element array of kmScalars
 * @Return Returns pOut so that the call can be nested
 */
kmMat4* kmMat4Fill(kmMat4* pOut, const kmScalar* pMat)
{
    memcpy(pOut->mat, pMat, sizeof(kmScalar) * 16);
    return pOut;
}

/**
 * Sets pOut to an identity matrix returns pOut
 * @Params pOut - A pointer to the matrix to set to identity
 * @Return Returns pOut so that the call can be nested
 */
kmMat4* kmMat4Identity(kmMat4* pOut)
{
	memset(pOut->mat, 0, sizeof(kmScalar) * 16);
	pOut->mat[0] = pOut->mat[5] = pOut->mat[10] = pOut->mat[15] = 1.0f;
	return pOut;
}

/**
 * Calculates the inverse of pM and stores the result in
 * pOut.
 * @Return Returns NULL if there is no inverse, else pOut
 */
kmMat4* kmMat4Inverse(kmMat4* pOut, const kmMat4* pM) {
    kmMat4 tmp;
    double det;
    int i;

    tmp.mat[0] = pM->mat[5]  * pM->mat[10] * pM->mat[15] -
             pM->mat[5]  * pM->mat[11] * pM->mat[14] -
             pM->mat[9]  * pM->mat[6]  * pM->mat[15] +
             pM->mat[9]  * pM->mat[7]  * pM->mat[14] +
             pM->mat[13] * pM->mat[6]  * pM->mat[11] -
             pM->mat[13] * pM->mat[7]  * pM->mat[10];

    tmp.mat[4] = -pM->mat[4]  * pM->mat[10] * pM->mat[15] +
              pM->mat[4]  * pM->mat[11] * pM->mat[14] +
              pM->mat[8]  * pM->mat[6]  * pM->mat[15] -
              pM->mat[8]  * pM->mat[7]  * pM->mat[14] -
              pM->mat[12] * pM->mat[6]  * pM->mat[11] +
              pM->mat[12] * pM->mat[7]  * pM->mat[10];

    tmp.mat[8] = pM->mat[4]  * pM->mat[9] * pM->mat[15] -
             pM->mat[4]  * pM->mat[11] * pM->mat[13] -
             pM->mat[8]  * pM->mat[5] * pM->mat[15] +
             pM->mat[8]  * pM->mat[7] * pM->mat[13] +
             pM->mat[12] * pM->mat[5] * pM->mat[11] -
             pM->mat[12] * pM->mat[7] * pM->mat[9];

    tmp.mat[12] = -pM->mat[4]  * pM->mat[9] * pM->mat[14] +
               pM->mat[4]  * pM->mat[10] * pM->mat[13] +
               pM->mat[8]  * pM->mat[5] * pM->mat[14] -
               pM->mat[8]  * pM->mat[6] * pM->mat[13] -
               pM->mat[12] * pM->mat[5] * pM->mat[10] +
               pM->mat[12] * pM->mat[6] * pM->mat[9];

    tmp.mat[1] = -pM->mat[1]  * pM->mat[10] * pM->mat[15] +
              pM->mat[1]  * pM->mat[11] * pM->mat[14] +
              pM->mat[9]  * pM->mat[2] * pM->mat[15] -
              pM->mat[9]  * pM->mat[3] * pM->mat[14] -
              pM->mat[13] * pM->mat[2] * pM->mat[11] +
              pM->mat[13] * pM->mat[3] * pM->mat[10];

    tmp.mat[5] = pM->mat[0]  * pM->mat[10] * pM->mat[15] -
             pM->mat[0]  * pM->mat[11] * pM->mat[14] -
             pM->mat[8]  * pM->mat[2] * pM->mat[15] +
             pM->mat[8]  * pM->mat[3] * pM->mat[14] +
             pM->mat[12] * pM->mat[2] * pM->mat[11] -
             pM->mat[12] * pM->mat[3] * pM->mat[10];

    tmp.mat[9] = -pM->mat[0]  * pM->mat[9] * pM->mat[15] +
              pM->mat[0]  * pM->mat[11] * pM->mat[13] +
              pM->mat[8]  * pM->mat[1] * pM->mat[15] -
              pM->mat[8]  * pM->mat[3] * pM->mat[13] -
              pM->mat[12] * pM->mat[1] * pM->mat[11] +
              pM->mat[12] * pM->mat[3] * pM->mat[9];

    tmp.mat[13] = pM->mat[0]  * pM->mat[9] * pM->mat[14] -
              pM->mat[0]  * pM->mat[10] * pM->mat[13] -
              pM->mat[8]  * pM->mat[1] * pM->mat[14] +
              pM->mat[8]  * pM->mat[2] * pM->mat[13] +
              pM->mat[12] * pM->mat[1] * pM->mat[10] -
              pM->mat[12] * pM->mat[2] * pM->mat[9];

    tmp.mat[2] = pM->mat[1]  * pM->mat[6] * pM->mat[15] -
             pM->mat[1]  * pM->mat[7] * pM->mat[14] -
             pM->mat[5]  * pM->mat[2] * pM->mat[15] +
             pM->mat[5]  * pM->mat[3] * pM->mat[14] +
             pM->mat[13] * pM->mat[2] * pM->mat[7] -
             pM->mat[13] * pM->mat[3] * pM->mat[6];

    tmp.mat[6] = -pM->mat[0]  * pM->mat[6] * pM->mat[15] +
              pM->mat[0]  * pM->mat[7] * pM->mat[14] +
              pM->mat[4]  * pM->mat[2] * pM->mat[15] -
              pM->mat[4]  * pM->mat[3] * pM->mat[14] -
              pM->mat[12] * pM->mat[2] * pM->mat[7] +
              pM->mat[12] * pM->mat[3] * pM->mat[6];

    tmp.mat[10] = pM->mat[0]  * pM->mat[5] * pM->mat[15] -
              pM->mat[0]  * pM->mat[7] * pM->mat[13] -
              pM->mat[4]  * pM->mat[1] * pM->mat[15] +
              pM->mat[4]  * pM->mat[3] * pM->mat[13] +
              pM->mat[12] * pM->mat[1] * pM->mat[7] -
              pM->mat[12] * pM->mat[3] * pM->mat[5];

    tmp.mat[14] = -pM->mat[0]  * pM->mat[5] * pM->mat[14] +
               pM->mat[0]  * pM->mat[6] * pM->mat[13] +
               pM->mat[4]  * pM->mat[1] * pM->mat[14] -
               pM->mat[4]  * pM->mat[2] * pM->mat[13] -
               pM->mat[12] * pM->mat[1] * pM->mat[6] +
               pM->mat[12] * pM->mat[2] * pM->mat[5];

    tmp.mat[3] = -pM->mat[1] * pM->mat[6] * pM->mat[11] +
              pM->mat[1] * pM->mat[7] * pM->mat[10] +
              pM->mat[5] * pM->mat[2] * pM->mat[11] -
              pM->mat[5] * pM->mat[3] * pM->mat[10] -
              pM->mat[9] * pM->mat[2] * pM->mat[7] +
              pM->mat[9] * pM->mat[3] * pM->mat[6];

    tmp.mat[7] = pM->mat[0] * pM->mat[6] * pM->mat[11] -
             pM->mat[0] * pM->mat[7] * pM->mat[10] -
             pM->mat[4] * pM->mat[2] * pM->mat[11] +
             pM->mat[4] * pM->mat[3] * pM->mat[10] +
             pM->mat[8] * pM->mat[2] * pM->mat[7] -
             pM->mat[8] * pM->mat[3] * pM->mat[6];

    tmp.mat[11] = -pM->mat[0] * pM->mat[5] * pM->mat[11] +
               pM->mat[0] * pM->mat[7] * pM->mat[9] +
               pM->mat[4] * pM->mat[1] * pM->mat[11] -
               pM->mat[4] * pM->mat[3] * pM->mat[9] -
               pM->mat[8] * pM->mat[1] * pM->mat[7] +
               pM->mat[8] * pM->mat[3] * pM->mat[5];

    tmp.mat[15] = pM->mat[0] * pM->mat[5] * pM->mat[10] -
              pM->mat[0] * pM->mat[6] * pM->mat[9] -
              pM->mat[4] * pM->mat[1] * pM->mat[10] +
              pM->mat[4] * pM->mat[2] * pM->mat[9] +
              pM->mat[8] * pM->mat[1] * pM->mat[6] -
              pM->mat[8] * pM->mat[2] * pM->mat[5];

    det = pM->mat[0] * tmp.mat[0] + pM->mat[1] * tmp.mat[4] + pM->mat[2] * tmp.mat[8] + pM->mat[3] * tmp.mat[12];

    if (det == 0) {
        return NULL;
    }

    det = 1.0 / det;

    for (i = 0; i < 16; i++) {
        pOut->mat[i] = tmp.mat[i] * det;
    }

    return pOut;
}
/**
 * Returns KM_TRUE if pIn is an identity matrix
 * KM_FALSE otherwise
 */
int  kmMat4IsIdentity(const kmMat4* pIn)
{
	static kmScalar identity [] = { 	1.0f, 0.0f, 0.0f, 0.0f,
	                                    0.0f, 1.0f, 0.0f, 0.0f,
	                                    0.0f, 0.0f, 1.0f, 0.0f,
	                                    0.0f, 0.0f, 0.0f, 1.0f
	                                 };

	return (memcmp(identity, pIn->mat, sizeof(kmScalar) * 16) == 0);
}

/**
 * Sets pOut to the transpose of pIn, returns pOut
 */
kmMat4* kmMat4Transpose(kmMat4* pOut, const kmMat4* pIn)
{
    int x, z;

    for (z = 0; z < 4; ++z) {
        for (x = 0; x < 4; ++x) {
	    pOut->mat[(z * 4) + x] = pIn->mat[(x * 4) + z];
        }
    }

    return pOut;
}

/**
 * Multiplies pM1 with pM2, stores the result in pOut, returns pOut
 */
kmMat4* kmMat4Multiply(kmMat4* pOut, const kmMat4* pM1, const kmMat4* pM2)
{
	kmScalar mat[16];

	const kmScalar *m1 = pM1->mat, *m2 = pM2->mat;

	mat[0] = m1[0] * m2[0] + m1[4] * m2[1] + m1[8] * m2[2] + m1[12] * m2[3];
	mat[1] = m1[1] * m2[0] + m1[5] * m2[1] + m1[9] * m2[2] + m1[13] * m2[3];
	mat[2] = m1[2] * m2[0] + m1[6] * m2[1] + m1[10] * m2[2] + m1[14] * m2[3];
	mat[3] = m1[3] * m2[0] + m1[7] * m2[1] + m1[11] * m2[2] + m1[15] * m2[3];

	mat[4] = m1[0] * m2[4] + m1[4] * m2[5] + m1[8] * m2[6] + m1[12] * m2[7];
	mat[5] = m1[1] * m2[4] + m1[5] * m2[5] + m1[9] * m2[6] + m1[13] * m2[7];
	mat[6] = m1[2] * m2[4] + m1[6] * m2[5] + m1[10] * m2[6] + m1[14] * m2[7];
	mat[7] = m1[3] * m2[4] + m1[7] * m2[5] + m1[11] * m2[6] + m1[15] * m2[7];

	mat[8] = m1[0] * m2[8] + m1[4] * m2[9] + m1[8] * m2[10] + m1[12] * m2[11];
	mat[9] = m1[1] * m2[8] + m1[5] * m2[9] + m1[9] * m2[10] + m1[13] * m2[11];
	mat[10] = m1[2] * m2[8] + m1[6] * m2[9] + m1[10] * m2[10] + m1[14] * m2[11];
	mat[11] = m1[3] * m2[8] + m1[7] * m2[9] + m1[11] * m2[10] + m1[15] * m2[11];

	mat[12] = m1[0] * m2[12] + m1[4] * m2[13] + m1[8] * m2[14] + m1[12] * m2[15];
	mat[13] = m1[1] * m2[12] + m1[5] * m2[13] + m1[9] * m2[14] + m1[13] * m2[15];
	mat[14] = m1[2] * m2[12] + m1[6] * m2[13] + m1[10] * m2[14] + m1[14] * m2[15];
	mat[15] = m1[3] * m2[12] + m1[7] * m2[13] + m1[11] * m2[14] + m1[15] * m2[15];


	memcpy(pOut->mat, mat, sizeof(kmScalar)*16);

	return pOut;
}

/**
 * Assigns the value of pIn to pOut
 */
kmMat4* kmMat4Assign(kmMat4* pOut, const kmMat4* pIn)
{
	assert(pOut != pIn && "You have tried to self-assign!!");

	memcpy(pOut->mat, pIn->mat, sizeof(kmScalar)*16);

	return pOut;
}

kmMat4* kmMat4AssignMat3(kmMat4* pOut, const kmMat3* pIn) {
    kmMat4Identity(pOut);

    pOut->mat[0] = pIn->mat[0];
    pOut->mat[1] = pIn->mat[1];
    pOut->mat[2] = pIn->mat[2];
    pOut->mat[3] = 0.0;

    pOut->mat[4] = pIn->mat[3];
    pOut->mat[5] = pIn->mat[4];
    pOut->mat[6] = pIn->mat[5];
    pOut->mat[7] = 0.0;

    pOut->mat[8] = pIn->mat[6];
    pOut->mat[9] = pIn->mat[7];
    pOut->mat[10] = pIn->mat[8];
    pOut->mat[11] = 0.0;

    return pOut;
}


/**
 * Returns KM_TRUE if the 2 matrices are equal (approximately)
 */
int kmMat4AreEqual(const kmMat4* pMat1, const kmMat4* pMat2)
{
    int i = 0;

	assert(pMat1 != pMat2 && "You are comparing the same thing!");

	for (i = 0; i < 16; ++i)
	{
		if (!(pMat1->mat[i] + kmEpsilon > pMat2->mat[i] &&
            pMat1->mat[i] - kmEpsilon < pMat2->mat[i])) {
			return KM_FALSE;
        }
	}

	return KM_TRUE;
}

/**
 * Build a rotation matrix from an axis and an angle. Result is stored in pOut.
 * pOut is returned.
 */
kmMat4* kmMat4RotationAxisAngle(kmMat4* pOut, const kmVec3* axis, kmScalar radians)
{
    kmQuaternion quat;
    kmQuaternionRotationAxisAngle(&quat, axis, radians);
    kmMat4RotationQuaternion(pOut, &quat);
    return pOut;
}

/**
 * Builds an X-axis rotation matrix and stores it in pOut, returns pOut
 */
kmMat4* kmMat4RotationX(kmMat4* pOut, const kmScalar radians)
{
	/*
		 |  1  0       0       0 |
	 M = |  0  cos(A) -sin(A)  0 |
	     |  0  sin(A)  cos(A)  0 |
	     |  0  0       0       1 |

	*/

	pOut->mat[0] = 1.0f;
	pOut->mat[1] = 0.0f;
	pOut->mat[2] = 0.0f;
	pOut->mat[3] = 0.0f;

	pOut->mat[4] = 0.0f;
	pOut->mat[5] = cosf(radians);
	pOut->mat[6] = sinf(radians);
	pOut->mat[7] = 0.0f;

	pOut->mat[8] = 0.0f;
	pOut->mat[9] = -sinf(radians);
	pOut->mat[10] = cosf(radians);
	pOut->mat[11] = 0.0f;

	pOut->mat[12] = 0.0f;
	pOut->mat[13] = 0.0f;
	pOut->mat[14] = 0.0f;
	pOut->mat[15] = 1.0f;

	return pOut;
}

/**
 * Builds a rotation matrix using the rotation around the Y-axis
 * The result is stored in pOut, pOut is returned.
 */
kmMat4* kmMat4RotationY(kmMat4* pOut, const kmScalar radians)
{
	/*
	     |  cos(A)  0   sin(A)  0 |
	 M = |  0       1   0       0 |
	     | -sin(A)  0   cos(A)  0 |
	     |  0       0   0       1 |
	*/

	pOut->mat[0] = cosf(radians);
	pOut->mat[1] = 0.0f;
	pOut->mat[2] = -sinf(radians);
	pOut->mat[3] = 0.0f;

	pOut->mat[4] = 0.0f;
	pOut->mat[5] = 1.0f;
	pOut->mat[6] = 0.0f;
	pOut->mat[7] = 0.0f;

	pOut->mat[8] = sinf(radians);
	pOut->mat[9] = 0.0f;
	pOut->mat[10] = cosf(radians);
	pOut->mat[11] = 0.0f;

	pOut->mat[12] = 0.0f;
	pOut->mat[13] = 0.0f;
	pOut->mat[14] = 0.0f;
	pOut->mat[15] = 1.0f;

	return pOut;
}

/**
 * Builds a rotation matrix around the Z-axis. The resulting
 * matrix is stored in pOut. pOut is returned.
 */
kmMat4* kmMat4RotationZ(kmMat4* pOut, const kmScalar radians)
{
	/*
	     |  cos(A)  -sin(A)   0   0 |
	 M = |  sin(A)   cos(A)   0   0 |
	     |  0        0        1   0 |
	     |  0        0        0   1 |
	*/

	pOut->mat[0] = cosf(radians);
	pOut->mat[1] = sinf(radians);
	pOut->mat[2] = 0.0f;
	pOut->mat[3] = 0.0f;

	pOut->mat[4] = -sinf(radians);
	pOut->mat[5] = cosf(radians);
	pOut->mat[6] = 0.0f;
	pOut->mat[7] = 0.0f;

	pOut->mat[8] = 0.0f;
	pOut->mat[9] = 0.0f;
	pOut->mat[10] = 1.0f;
	pOut->mat[11] = 0.0f;

	pOut->mat[12] = 0.0f;
	pOut->mat[13] = 0.0f;
	pOut->mat[14] = 0.0f;
	pOut->mat[15] = 1.0f;

	return pOut;
}

/**
 * Builds a rotation matrix from pitch, yaw and roll. The resulting
 * matrix is stored in pOut and pOut is returned
 */
kmMat4* kmMat4RotationYawPitchRoll(kmMat4* pOut, const kmScalar pitch, const kmScalar yaw, const kmScalar roll)
{

    kmMat4 yaw_matrix;
    kmMat4RotationY(&yaw_matrix, yaw);

    kmMat4 pitch_matrix;
    kmMat4RotationX(&pitch_matrix, pitch);

    kmMat4 roll_matrix;
    kmMat4RotationZ(&roll_matrix, roll);

    kmMat4Multiply(pOut, &pitch_matrix, &roll_matrix);
    kmMat4Multiply(pOut, &yaw_matrix, pOut);

    return pOut;
}

/** Converts a quaternion to a rotation matrix,
 * the result is stored in pOut, returns pOut
 */
kmMat4* kmMat4RotationQuaternion(kmMat4* pOut, const kmQuaternion* pQ)
{    
    double xx = pQ->x * pQ->x;
    double xy = pQ->x * pQ->y;
    double xz = pQ->x * pQ->z;
    double xw = pQ->x * pQ->w;

    double yy = pQ->y * pQ->y;
    double yz = pQ->y * pQ->z;
    double yw = pQ->y * pQ->w;

    double zz = pQ->z * pQ->z;
    double zw = pQ->z * pQ->w;

    pOut->mat[0] = 1 - 2 * (yy + zz);
    pOut->mat[1] = 2 * (xy + zw);
    pOut->mat[2] = 2 * (xz - yw);
    pOut->mat[3] = 0;

    pOut->mat[4] = 2 * (xy - zw);
    pOut->mat[5] = 1 - 2 * (xx + zz);
    pOut->mat[6] = 2 * (yz + xw);
    pOut->mat[7] = 0.0;

    pOut->mat[8] = 2 * (xz + yw);
    pOut->mat[9] = 2 * (yz - xw);
    pOut->mat[10] = 1 - 2 * (xx + yy);
    pOut->mat[11] = 0.0;

    pOut->mat[12] = 0.0;
    pOut->mat[13] = 0.0;
    pOut->mat[14] = 0.0;
    pOut->mat[15] = 1.0;

    return pOut;
}

/** Builds a scaling matrix */
kmMat4* kmMat4Scaling(kmMat4* pOut, const kmScalar x, const kmScalar y,
                      kmScalar z)
{
	memset(pOut->mat, 0, sizeof(kmScalar) * 16);
	pOut->mat[0] = x;
	pOut->mat[5] = y;
	pOut->mat[10] = z;
	pOut->mat[15] = 1.0f;

	return pOut;
}

/**
 * Builds a translation matrix. All other elements in the matrix
 * will be set to zero except for the diagonal which is set to 1.0
 */
kmMat4* kmMat4Translation(kmMat4* pOut, const kmScalar x,
                          kmScalar y, const kmScalar z)
{
    /*FIXME: Write a test for this*/
    memset(pOut->mat, 0, sizeof(kmScalar) * 16);

    pOut->mat[0] = 1.0f;
    pOut->mat[5] = 1.0f;
    pOut->mat[10] = 1.0f;

    pOut->mat[12] = x;
    pOut->mat[13] = y;
    pOut->mat[14] = z;
    pOut->mat[15] = 1.0f;

    return pOut;
}

/**
 * Get the up vector from a matrix. pIn is the matrix you
 * wish to extract the vector from. pOut is a pointer to the
 * kmVec3 structure that should hold the resulting vector
 */
kmVec3* kmMat4GetUpVec3(kmVec3* pOut, const kmMat4* pIn)
{
    kmVec3MultiplyMat4(pOut, &KM_VEC3_POS_Y, pIn);
    kmVec3Normalize(pOut, pOut);
    return pOut;
}

/** Extract the right vector from a 4x4 matrix. The result is
 * stored in pOut. Returns pOut.
 */
kmVec3* kmMat4GetRightVec3(kmVec3* pOut, const kmMat4* pIn)
{
    kmVec3MultiplyMat4(pOut, &KM_VEC3_POS_X, pIn);
    kmVec3Normalize(pOut, pOut);
    return pOut;
}

/**
 * Extract the forward vector from a 4x4 matrix. The result is
 * stored in pOut. Returns pOut.
 */
kmVec3* kmMat4GetForwardVec3RH(kmVec3* pOut, const kmMat4* pIn)
{
    kmVec3MultiplyMat4(pOut, &KM_VEC3_NEG_Z, pIn);
    kmVec3Normalize(pOut, pOut);
    return pOut;
}

kmVec3* kmMat4GetForwardVec3LH(kmVec3* pOut, const kmMat4* pIn)
{
    kmVec3MultiplyMat4(pOut, &KM_VEC3_POS_Z, pIn);
    kmVec3Normalize(pOut, pOut);
	return pOut;
}

/**
 * Creates a perspective projection matrix in the
 * same way as gluPerspective
 */
kmMat4* kmMat4PerspectiveProjection(kmMat4* pOut, kmScalar fovY,
                                    kmScalar aspect, kmScalar zNear,
                                    kmScalar zFar)
{
	kmScalar r = kmDegreesToRadians(fovY / 2);
	kmScalar deltaZ = zFar - zNear;
	kmScalar s = sin(r);
    kmScalar cotangent = 0;

	if (deltaZ == 0 || s == 0 || aspect == 0) {
		return NULL;
	}

    /*cos(r) / sin(r) = cot(r)*/
	cotangent = cos(r) / s;

	kmMat4Identity(pOut);
	pOut->mat[0] = cotangent / aspect;
	pOut->mat[5] = cotangent;
	pOut->mat[10] = -(zFar + zNear) / deltaZ;
	pOut->mat[11] = -1;
	pOut->mat[14] = -2 * zNear * zFar / deltaZ;
	pOut->mat[15] = 0;

	return pOut;
}

/** Creates an orthographic projection matrix like glOrtho */
kmMat4* kmMat4OrthographicProjection(kmMat4* pOut, kmScalar left,
                                     kmScalar right, kmScalar bottom,
                                     kmScalar top, kmScalar nearVal,
                                     kmScalar farVal)
{
	kmScalar tx = -((right + left) / (right - left));
	kmScalar ty = -((top + bottom) / (top - bottom));
	kmScalar tz = -((farVal + nearVal) / (farVal - nearVal));

	kmMat4Identity(pOut);
	pOut->mat[0] = 2 / (right - left);
	pOut->mat[5] = 2 / (top - bottom);
	pOut->mat[10] = -2 / (farVal - nearVal);
	pOut->mat[12] = tx;
	pOut->mat[13] = ty;
	pOut->mat[14] = tz;

	return pOut;
}

/**
 * Builds a translation matrix in the same way as gluLookAt()
 * the resulting matrix is stored in pOut. pOut is returned.
 */
kmMat4* kmMat4LookAt(kmMat4* pOut, const kmVec3* pEye,
                     const kmVec3* pCenter, const kmVec3* pUp)
{
    kmVec3 f, up, s, u;
    kmMat4 translate;

    kmVec3Subtract(&f, pCenter, pEye);
    kmVec3Normalize(&f, &f);

    kmVec3Assign(&up, pUp);
    kmVec3Normalize(&up, &up);

    kmVec3Cross(&s, &f, &up);
    kmVec3Normalize(&s, &s);

    kmVec3Cross(&u, &s, &f);
    kmVec3Normalize(&s, &s);

    kmMat4Identity(pOut);

    pOut->mat[0] = s.x;
    pOut->mat[4] = s.y;
    pOut->mat[8] = s.z;

    pOut->mat[1] = u.x;
    pOut->mat[5] = u.y;
    pOut->mat[9] = u.z;

    pOut->mat[2] = -f.x;
    pOut->mat[6] = -f.y;
    pOut->mat[10] = -f.z;

    kmMat4Translation(&translate, -pEye->x, -pEye->y, -pEye->z);
    kmMat4Multiply(pOut, pOut, &translate);

    return pOut;
}

/**
 * Extract a 3x3 rotation matrix from the input 4x4 transformation.
 * Stores the result in pOut, returns pOut
 */
kmMat3* kmMat4ExtractRotation(kmMat3* pOut, const kmMat4* pIn)
{
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

/**
 * Take the rotation from a 4x4 transformation matrix, and return it as an axis and an angle (in radians)
 * returns the output axis.
 */
kmVec3* kmMat4RotationToAxisAngle(kmVec3* pAxis, kmScalar* radians, const kmMat4* pIn)
{
    /*Surely not this easy?*/
    kmQuaternion temp;
    kmMat3 rotation;
    kmMat4ExtractRotation(&rotation, pIn);
    kmQuaternionRotationMatrix(&temp, &rotation);
    kmQuaternionToAxisAngle(&temp, pAxis, radians);
    return pAxis;
}

/** Build a 4x4 OpenGL transformation matrix using a 3x3 rotation matrix,
 * and a 3d vector representing a translation. Assign the result to pOut,
 * pOut is also returned.
 */
kmMat4* kmMat4RotationTranslation(kmMat4* pOut, const kmMat3* rotation, const kmVec3* translation)
{
    pOut->mat[0] = rotation->mat[0];
    pOut->mat[1] = rotation->mat[1];
    pOut->mat[2] = rotation->mat[2];
    pOut->mat[3] = 0.0f;

    pOut->mat[4] = rotation->mat[3];
    pOut->mat[5] = rotation->mat[4];
    pOut->mat[6] = rotation->mat[5];
    pOut->mat[7] = 0.0f;

    pOut->mat[8] = rotation->mat[6];
    pOut->mat[9] = rotation->mat[7];
    pOut->mat[10] = rotation->mat[8];
    pOut->mat[11] = 0.0f;

    pOut->mat[12] = translation->x;
    pOut->mat[13] = translation->y;
    pOut->mat[14] = translation->z;
    pOut->mat[15] = 1.0f;

    return pOut;
}

kmPlane* kmMat4ExtractPlane(kmPlane* pOut, const kmMat4* pIn, const kmEnum plane)
{
    kmScalar t = 1.0f;

    switch(plane) {
        case KM_PLANE_RIGHT:
            pOut->a = pIn->mat[3] - pIn->mat[0];
            pOut->b = pIn->mat[7] - pIn->mat[4];
            pOut->c = pIn->mat[11] - pIn->mat[8];
            pOut->d = pIn->mat[15] - pIn->mat[12];
        break;
        case KM_PLANE_LEFT:
            pOut->a = pIn->mat[3] + pIn->mat[0];
            pOut->b = pIn->mat[7] + pIn->mat[4];
            pOut->c = pIn->mat[11] + pIn->mat[8];
            pOut->d = pIn->mat[15] + pIn->mat[12];
        break;
        case KM_PLANE_BOTTOM:
            pOut->a = pIn->mat[3] + pIn->mat[1];
            pOut->b = pIn->mat[7] + pIn->mat[5];
            pOut->c = pIn->mat[11] + pIn->mat[9];
            pOut->d = pIn->mat[15] + pIn->mat[13];
        break;
        case KM_PLANE_TOP:
            pOut->a = pIn->mat[3] - pIn->mat[1];
            pOut->b = pIn->mat[7] - pIn->mat[5];
            pOut->c = pIn->mat[11] - pIn->mat[9];
            pOut->d = pIn->mat[15] - pIn->mat[13];
        break;
        case KM_PLANE_FAR:
            pOut->a = pIn->mat[3] - pIn->mat[2];
            pOut->b = pIn->mat[7] - pIn->mat[6];
            pOut->c = pIn->mat[11] - pIn->mat[10];
            pOut->d = pIn->mat[15] - pIn->mat[14];
        break;
        case KM_PLANE_NEAR:
            pOut->a = pIn->mat[3] + pIn->mat[2];
            pOut->b = pIn->mat[7] + pIn->mat[6];
            pOut->c = pIn->mat[11] + pIn->mat[10];
            pOut->d = pIn->mat[15] + pIn->mat[14];
        break;
        default:
            assert(0 && "Invalid plane index");
    }

    t = sqrtf(pOut->a * pOut->a +
                    pOut->b * pOut->b +
                    pOut->c * pOut->c);
    pOut->a /= t;
    pOut->b /= t;
    pOut->c /= t;
    pOut->d /= t;

    return pOut;
}
