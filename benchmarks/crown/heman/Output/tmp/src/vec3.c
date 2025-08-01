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
 * @file vec3.c
 */

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
#ifndef RAY3_H
#define RAY3_H


#ifdef __cplusplus
extern "C" {
#endif

typedef struct kmRay3 {
    kmVec3 start;
    kmVec3 dir;
} kmRay3;

struct kmPlane;

kmRay3* kmRay3Fill(kmRay3* ray, kmScalar px, kmScalar py, kmScalar pz, kmScalar vx, kmScalar vy, kmScalar vz);
kmRay3* kmRay3FromPointAndDirection(kmRay3* ray, const kmVec3* point, const kmVec3* direction);
kmBool kmRay3IntersectPlane(kmVec3* pOut, const kmRay3* ray, const struct kmPlane* plane);

#ifdef __cplusplus
}
#endif

#endif /* RAY3_H */

const kmVec3 KM_VEC3_POS_Z = { 0, 0, 1 };
const kmVec3 KM_VEC3_NEG_Z = { 0, 0, -1 };
const kmVec3 KM_VEC3_POS_Y = { 0, 1, 0 };
const kmVec3 KM_VEC3_NEG_Y = { 0, -1, 0 };
const kmVec3 KM_VEC3_NEG_X = { -1, 0, 0 };
const kmVec3 KM_VEC3_POS_X = { 1, 0, 0 };
const kmVec3 KM_VEC3_ZERO = { 0, 0, 0 };

/**
 * Fill a kmVec3 structure using 3 floating point values
 * The result is store in pOut, returns pOut
 */
kmVec3* kmVec3Fill(kmVec3* pOut, kmScalar x, kmScalar y, kmScalar z)
{
    pOut->x = x;
    pOut->y = y;
    pOut->z = z;
    return pOut;
}


/**
 * Returns the length of the vector
 */
kmScalar kmVec3Length(const kmVec3* pIn)
{
	return sqrtf(kmSQR(pIn->x) + kmSQR(pIn->y) + kmSQR(pIn->z));
}

/**
 * Returns the square of the length of the vector
 */
kmScalar kmVec3LengthSq(const kmVec3* pIn)
{
	return kmSQR(pIn->x) + kmSQR(pIn->y) + kmSQR(pIn->z);
}

/** Returns the interpolation of 2 4D vectors based on t.*/
kmVec3* kmVec3Lerp(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2, kmScalar t) {
    pOut->x = pV1->x + t * ( pV2->x - pV1->x ); 
    pOut->y = pV1->y + t * ( pV2->y - pV1->y ); 
    pOut->z = pV1->z + t * ( pV2->z - pV1->z ); 
    return pOut;
}

 /**
  * Returns the vector passed in set to unit length
  * the result is stored in pOut.
  */
kmVec3* kmVec3Normalize(kmVec3* pOut, const kmVec3* pIn)
{
        if (!pIn->x && !pIn->y && !pIn->z)
                return kmVec3Assign(pOut, pIn);

        kmScalar l = 1.0f / kmVec3Length(pIn);

	kmVec3 v;
	v.x = pIn->x * l;
	v.y = pIn->y * l;
	v.z = pIn->z * l;

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

	return pOut;
}

/**
 * Returns a vector perpendicular to 2 other vectors.
 * The result is stored in pOut.
 */
kmVec3* kmVec3Cross(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2)
{

	kmVec3 v;

	v.x = (pV1->y * pV2->z) - (pV1->z * pV2->y);
	v.y = (pV1->z * pV2->x) - (pV1->x * pV2->z);
	v.z = (pV1->x * pV2->y) - (pV1->y * pV2->x);

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

	return pOut;
}

/**
 * Returns the cosine of the angle between 2 vectors
 */
kmScalar kmVec3Dot(const kmVec3* pV1, const kmVec3* pV2)
{
	return (  pV1->x * pV2->x
			+ pV1->y * pV2->y
			+ pV1->z * pV2->z );
}

/**
 * Adds 2 vectors and returns the result. The resulting
 * vector is stored in pOut.
 */
kmVec3* kmVec3Add(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2)
{
	kmVec3 v;

	v.x = pV1->x + pV2->x;
	v.y = pV1->y + pV2->y;
	v.z = pV1->z + pV2->z;

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

	return pOut;
}

 /**
  * Subtracts 2 vectors and returns the result. The result is stored in
  * pOut.
  */
kmVec3* kmVec3Subtract(kmVec3* pOut, const kmVec3* pV1, const kmVec3* pV2)
{
	kmVec3 v;

	v.x = pV1->x - pV2->x;
	v.y = pV1->y - pV2->y;
	v.z = pV1->z - pV2->z;

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

	return pOut;
}

kmVec3* kmVec3Mul( kmVec3* pOut,const kmVec3* pV1, const kmVec3* pV2 ) {
    pOut->x = pV1->x * pV2->x;
    pOut->y = pV1->y * pV2->y;
    pOut->z = pV1->z * pV2->z;
    return pOut;
}

kmVec3* kmVec3Div( kmVec3* pOut,const kmVec3* pV1, const kmVec3* pV2 ) {
    if ( pV2->x && pV2->y && pV2->z ){
        pOut->x = pV1->x / pV2->x;
        pOut->y = pV1->y / pV2->y;
        pOut->z = pV1->z / pV2->z;
    }
    return pOut;
}

kmVec3* kmVec3MultiplyMat3(kmVec3* pOut, const kmVec3* pV, const kmMat3* pM) {
    kmVec3 v;

    v.x = pV->x * pM->mat[0] + pV->y * pM->mat[3] + pV->z * pM->mat[6];
    v.y = pV->x * pM->mat[1] + pV->y * pM->mat[4] + pV->z * pM->mat[7];
    v.z = pV->x * pM->mat[2] + pV->y * pM->mat[5] + pV->z * pM->mat[8];

    pOut->x = v.x;
    pOut->y = v.y;
    pOut->z = v.z;

    return pOut;
}

/**
 * Multiplies vector (x, y, z, 1) by a given matrix. The result
 * is stored in pOut. pOut is returned.
 */

kmVec3* kmVec3MultiplyMat4(kmVec3* pOut, const kmVec3* pV, const kmMat4* pM) {
    kmVec3 v;

    v.x = pV->x * pM->mat[0] + pV->y * pM->mat[4] + pV->z * pM->mat[8] + pM->mat[12];
    v.y = pV->x * pM->mat[1] + pV->y * pM->mat[5] + pV->z * pM->mat[9] + pM->mat[13];
    v.z = pV->x * pM->mat[2] + pV->y * pM->mat[6] + pV->z * pM->mat[10] + pM->mat[14];

    pOut->x = v.x;
    pOut->y = v.y;
    pOut->z = v.z;

    return pOut;
}


kmVec3* kmVec3Transform(kmVec3* pOut, const kmVec3* pV, const kmMat4* pM)
{
	/*
        @deprecated Should intead use kmVec3MultiplyMat4
	*/
    return kmVec3MultiplyMat4(pOut, pV, pM);
}

kmVec3* kmVec3InverseTransform(kmVec3* pOut, const kmVec3* pVect, const kmMat4* pM)
{
	kmVec3 v1, v2;

	v1.x = pVect->x - pM->mat[12];
	v1.y = pVect->y - pM->mat[13];
	v1.z = pVect->z - pM->mat[14];

	v2.x = v1.x * pM->mat[0] + v1.y * pM->mat[1] + v1.z * pM->mat[2];
	v2.y = v1.x * pM->mat[4] + v1.y * pM->mat[5] + v1.z * pM->mat[6];
	v2.z = v1.x * pM->mat[8] + v1.y * pM->mat[9] + v1.z * pM->mat[10];

	pOut->x = v2.x;
	pOut->y = v2.y;
	pOut->z = v2.z;

	return pOut;
}

kmVec3* kmVec3InverseTransformNormal(kmVec3* pOut, const kmVec3* pVect, const kmMat4* pM)
{
	kmVec3 v;

	v.x = pVect->x * pM->mat[0] + pVect->y * pM->mat[1] + pVect->z * pM->mat[2];
	v.y = pVect->x * pM->mat[4] + pVect->y * pM->mat[5] + pVect->z * pM->mat[6];
	v.z = pVect->x * pM->mat[8] + pVect->y * pM->mat[9] + pVect->z * pM->mat[10];

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

	return pOut;
}


kmVec3* kmVec3TransformCoord(kmVec3* pOut, const kmVec3* pV, const kmMat4* pM)
{
	/*
        a = (Vx, Vy, Vz, 1)
        b = (a×M)T
        Out = 1⁄bw(bx, by, bz)
	*/

    kmVec4 v;
    kmVec4 inV;
    kmVec4Fill(&inV, pV->x, pV->y, pV->z, 1.0);

    kmVec4Transform(&v, &inV,pM);

	pOut->x = v.x / v.w;
	pOut->y = v.y / v.w;
	pOut->z = v.z / v.w;

	return pOut;
}

kmVec3* kmVec3TransformNormal(kmVec3* pOut, const kmVec3* pV, const kmMat4* pM)
{
/*
    a = (Vx, Vy, Vz, 0)
    b = (a×M)T
    Out = (bx, by, bz)
*/
    /*Omits the translation, only scaling + rotating*/
	kmVec3 v;

	v.x = pV->x * pM->mat[0] + pV->y * pM->mat[4] + pV->z * pM->mat[8];
	v.y = pV->x * pM->mat[1] + pV->y * pM->mat[5] + pV->z * pM->mat[9];
	v.z = pV->x * pM->mat[2] + pV->y * pM->mat[6] + pV->z * pM->mat[10];

	pOut->x = v.x;
	pOut->y = v.y;
	pOut->z = v.z;

    return pOut;

}

/**
 * Scales a vector to length s. Does not normalize first,
 * you should do that!
 */
kmVec3* kmVec3Scale(kmVec3* pOut, const kmVec3* pIn, const kmScalar s)
{
	pOut->x = pIn->x * s;
	pOut->y = pIn->y * s;
	pOut->z = pIn->z * s;

	return pOut;
}

/**
 * Returns KM_TRUE if the 2 vectors are approximately equal
 */
int kmVec3AreEqual(const kmVec3* p1, const kmVec3* p2)
{
	if ((p1->x < (p2->x + kmEpsilon) && p1->x > (p2->x - kmEpsilon)) &&
		(p1->y < (p2->y + kmEpsilon) && p1->y > (p2->y - kmEpsilon)) &&
		(p1->z < (p2->z + kmEpsilon) && p1->z > (p2->z - kmEpsilon))) {
		return 1;
	}

	return 0;
}

/**
 * Assigns pIn to pOut. Returns pOut. If pIn and pOut are the same
 * then nothing happens but pOut is still returned
 */
kmVec3* kmVec3Assign(kmVec3* pOut, const kmVec3* pIn) {
	if (pOut == pIn) {
		return pOut;
	}

	pOut->x = pIn->x;
	pOut->y = pIn->y;
	pOut->z = pIn->z;

	return pOut;
}

/**
 * Sets all the elements of pOut to zero. Returns pOut.
 */
kmVec3* kmVec3Zero(kmVec3* pOut) {
	pOut->x = 0.0f;
	pOut->y = 0.0f;
	pOut->z = 0.0f;

	return pOut;
}

/**
 * Get the rotations that would make a (0,0,1) direction vector point in the same direction as this direction vector.
 * Useful for orienting vector towards a point.
 *
 * Returns a rotation vector containing the X (pitch) and Y (raw) rotations (in degrees) that when applied to a
 * +Z (e.g. 0, 0, 1) direction vector would make it point in the same direction as this vector. The Z (roll) rotation
 * is always 0, since two Euler rotations are sufficient to point in any given direction.
 *
 * Code ported from Irrlicht: http://irrlicht.sourceforge.net/
 */
kmVec3* kmVec3GetHorizontalAngle(kmVec3* pOut, const kmVec3 *pIn) {
   const kmScalar z1 = sqrt(pIn->x * pIn->x + pIn->z * pIn->z);

   pOut->y = kmRadiansToDegrees(atan2(pIn->x, pIn->z));
   if (pOut->y < 0)
      pOut->y += 360;
   if (pOut->y >= 360)
      pOut->y -= 360;

   pOut->x = kmRadiansToDegrees(atan2(z1, pIn->y)) - 90.0;
   if (pOut->x < 0)
      pOut->x += 360;
   if (pOut->x >= 360)
      pOut->x -= 360;

   return pOut;
}

/**
 * Builds a direction vector from input vector.
 * Input vector is assumed to be rotation vector composed from 3 Euler angle rotations, in degrees.
 * The forwards vector will be rotated by the input vector
 *
 * Code ported from Irrlicht: http://irrlicht.sourceforge.net/
 */
kmVec3* kmVec3RotationToDirection(kmVec3* pOut, const kmVec3* pIn, const kmVec3* forwards)
{
   const kmScalar xr = kmDegreesToRadians(pIn->x);
   const kmScalar yr = kmDegreesToRadians(pIn->y);
   const kmScalar zr = kmDegreesToRadians(pIn->z);
   const kmScalar cr = cos(xr), sr = sin(xr);
   const kmScalar cp = cos(yr), sp = sin(yr);
   const kmScalar cy = cos(zr), sy = sin(zr);

   const kmScalar srsp = sr*sp;
   const kmScalar crsp = cr*sp;

   const kmScalar pseudoMatrix[] = {
      (cp*cy), (cp*sy), (-sp),
      (srsp*cy-cr*sy), (srsp*sy+cr*cy), (sr*cp),
      (crsp*cy+sr*sy), (crsp*sy-sr*cy), (cr*cp)
   };

   pOut->x = forwards->x * pseudoMatrix[0] +
             forwards->y * pseudoMatrix[3] +
             forwards->z * pseudoMatrix[6];

   pOut->y = forwards->x * pseudoMatrix[1] +
             forwards->y * pseudoMatrix[4] +
             forwards->z * pseudoMatrix[7];

   pOut->z = forwards->x * pseudoMatrix[2] +
             forwards->y * pseudoMatrix[5] +
             forwards->z * pseudoMatrix[8];

   return pOut;
}

kmVec3* kmVec3ProjectOnToPlane(kmVec3* pOut, const kmVec3* point, const struct kmPlane* plane) {
    kmRay3 ray;
    kmVec3Assign(&ray.start, point);
    ray.dir.x = -plane->a;
    ray.dir.y = -plane->b;
    ray.dir.z = -plane->c;

    kmRay3IntersectPlane(pOut, &ray, plane);
    return pOut;
}

/**
 * Reflects a vector about a given surface normal. The surface normal is
 * assumed to be of unit length.
 */
kmVec3* kmVec3Reflect(kmVec3* pOut, const kmVec3* pIn, const kmVec3* normal) {
  kmVec3 tmp;
  kmVec3Scale(&tmp, normal, 2.0f * kmVec3Dot(pIn, normal));
  kmVec3Subtract(pOut, pIn, &tmp);

  return pOut;
}
