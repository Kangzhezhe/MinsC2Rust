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

kmScalar kmPlaneDot(const kmPlane* pP, const kmVec4* pV)
{
    /*a*x + b*y + c*z + d*w*/

    return (pP->a * pV->x +
	    pP->b * pV->y +
	    pP->c * pV->z +
	    pP->d * pV->w);
}

kmScalar kmPlaneDotCoord(const kmPlane* pP, const kmVec3* pV)
{
    return (pP->a * pV->x +
	    pP->b * pV->y +
	    pP->c * pV->z + pP->d);
}

kmScalar kmPlaneDotNormal(const kmPlane* pP, const kmVec3* pV)
{
    return (pP->a * pV->x +
	    pP->b * pV->y +
	    pP->c * pV->z);
}

kmPlane* kmPlaneFromNormalAndDistance(kmPlane* plane, const struct kmVec3* normal, const kmScalar dist) {
    plane->a = normal->x;
    plane->b = normal->y;
    plane->c = normal->z;
    plane->d = dist;

    return plane;
}

kmPlane* kmPlaneFromPointAndNormal(kmPlane* pOut, const kmVec3* pPoint, const kmVec3* pNormal)
{
    /*
	Planea = Nx
	Planeb = Ny
	Planec = Nz
	Planed = −N⋅P
    */


    pOut->a = pNormal->x;
    pOut->b = pNormal->y;
    pOut->c = pNormal->z;
    pOut->d = -kmVec3Dot(pNormal, pPoint);

    return pOut;
}

/**
 * Creates a plane from 3 points. The result is stored in pOut.
 * pOut is returned.
 */
kmPlane* kmPlaneFromPoints(kmPlane* pOut, const kmVec3* p1, const kmVec3* p2, const kmVec3* p3)
{
    /*
    v = (B − A) × (C − A)
    n = 1⁄|v| v
    Outa = nx
    Outb = ny
    Outc = nz
    Outd = −n⋅A
    */

    kmVec3 n, v1, v2;
    kmVec3Subtract(&v1, p2, p1); /*Create the vectors for the 2 sides of the triangle*/
    kmVec3Subtract(&v2, p3, p1);
    kmVec3Cross(&n, &v1, &v2); /*Use the cross product to get the normal*/

    kmVec3Normalize(&n, &n); /*Normalize it and assign to pOut->m_N*/

    pOut->a = n.x;
    pOut->b = n.y;
    pOut->c = n.z;
    pOut->d = kmVec3Dot(kmVec3Scale(&n, &n, -1.0), p1);

    return pOut;
}

/* Added by tlensing (http://icedcoffee-framework.org)*/
kmVec3* kmPlaneIntersectLine(kmVec3* pOut, const kmPlane* pP, const kmVec3* pV1, const kmVec3* pV2)
{
    /*
     n = (Planea, Planeb, Planec)
     d = V − U
     Out = U − d⋅(Pd + n⋅U)⁄(d⋅n) [iff d⋅n ≠ 0]
     */
    kmVec3 d; /* direction from V1 to V2*/
    kmVec3Subtract(&d, pV2, pV1); /* Get the direction vector*/
    
    kmVec3 n; /* plane normal*/
    n.x = pP->a;
    n.y = pP->b;
    n.z = pP->c;
    kmVec3Normalize(&n, &n);
    
    kmScalar nt = -(n.x * pV1->x + n.y * pV1->y + n.z * pV1->z + pP->d);
    kmScalar dt = (n.x * d.x + n.y * d.y + n.z * d.z);
    
    if (fabs(dt) < kmEpsilon) {
        pOut = NULL;
        return pOut; /* line parallel or contained*/
    }
    
    kmScalar t = nt/dt;
    pOut->x = pV1->x + d.x * t;
    pOut->y = pV1->y + d.y * t;
    pOut->z = pV1->z + d.z * t;
    
    return pOut;
}

kmPlane* kmPlaneNormalize(kmPlane* pOut, const kmPlane* pP)
{
	kmVec3 n;
        kmScalar l = 0;

        if (!pP->a && !pP->b && !pP->c) {
                pOut->a = pP->a;
                pOut->b = pP->b;
                pOut->c = pP->c;
                pOut->d = pP->d;
                return pOut;
        }

	n.x = pP->a;
	n.y = pP->b;
	n.z = pP->c;

	l = 1.0f / kmVec3Length(&n); /*Get 1/length*/
	kmVec3Normalize(&n, &n); /*Normalize the vector and assign to pOut*/

	pOut->a = n.x;
	pOut->b = n.y;
	pOut->c = n.z;

	pOut->d = pP->d * l; /*Scale the D value and assign to pOut*/

	return pOut;
}

kmPlane* kmPlaneScale(kmPlane* pOut, const kmPlane* pP, kmScalar s)
{
	assert(0 && "Not implemented");
    return NULL;
}

/**
 * Returns POINT_INFRONT_OF_PLANE if pP is infront of pIn. Returns
 * POINT_BEHIND_PLANE if it is behind. Returns POINT_ON_PLANE otherwise
 */
KM_POINT_CLASSIFICATION kmPlaneClassifyPoint(const kmPlane* pIn, const kmVec3* pP)
{
   /* This function will determine if a point is on, in front of, or behind*/
   /* the plane.  First we store the dot product of the plane and the point.*/
   kmScalar distance = pIn->a * pP->x + pIn->b * pP->y + pIn->c * pP->z + pIn->d;

   /* Simply put if the dot product is greater than 0 then it is infront of it.*/
   /* If it is less than 0 then it is behind it.  And if it is 0 then it is on it.*/
   if(distance > kmEpsilon) return POINT_INFRONT_OF_PLANE;
   if(distance < -kmEpsilon) return POINT_BEHIND_PLANE;

   return POINT_ON_PLANE;
}

kmPlane* kmPlaneExtractFromMat4(kmPlane* pOut, const struct kmMat4* pIn, kmInt row) {
    int scale = (row < 0) ? -1 : 1;
	row = abs(row) - 1;
	
	pOut->a = pIn->mat[3] + scale * pIn->mat[row];
	pOut->b = pIn->mat[7] + scale * pIn->mat[row + 4];
	pOut->c = pIn->mat[11] + scale * pIn->mat[row + 8];
	pOut->d = pIn->mat[15] + scale * pIn->mat[row + 12];
	
	return kmPlaneNormalize(pOut, pOut);
}

kmVec3* kmPlaneGetIntersection(kmVec3* pOut, const kmPlane* p1, const kmPlane* p2, const kmPlane* p3) {
    kmVec3 n1, n2, n3, cross;
    kmVec3 r1, r2, r3;
    double denom = 0;
    
    kmVec3Fill(&n1, p1->a, p1->b, p1->c);
    kmVec3Fill(&n2, p2->a, p2->b, p2->c);
    kmVec3Fill(&n3, p3->a, p3->b, p3->c);
    
    kmVec3Cross(&cross, &n2, &n3);

    denom = kmVec3Dot(&n1, &cross);

    if (kmAlmostEqual(denom, 0.0)) {
        return NULL;
    }

    kmVec3Cross(&r1, &n2, &n3);
    kmVec3Cross(&r2, &n3, &n1);
    kmVec3Cross(&r3, &n1, &n2);

    kmVec3Scale(&r1, &r1, -p1->d);
    kmVec3Scale(&r2, &r2, p2->d);
    kmVec3Scale(&r3, &r3, p3->d);

    kmVec3Subtract(pOut, &r1, &r2);
    kmVec3Subtract(pOut, pOut, &r3);
    kmVec3Scale(pOut, pOut, 1.0 / denom);

    /*p = -d1 * ( n2.Cross ( n3 ) ) – d2 * ( n3.Cross ( n1 ) ) – d3 * ( n1.Cross ( n2 ) ) / denom;*/

    return pOut;
}

kmPlane* kmPlaneFill(kmPlane* plane, kmScalar a, kmScalar b, kmScalar c, kmScalar d) {
    plane->a = a;
    plane->b = b;
    plane->c = c;
    plane->d = d;

    return plane;
}
