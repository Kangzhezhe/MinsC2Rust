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

#ifndef KAZMATH_AABB3D_H_INCLUDED
#define KAZMATH_AABB3D_H_INCLUDED

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

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A struture that represents an axis-aligned
 * bounding box.
 */
typedef struct kmAABB3 {
    kmVec3 min; /** The max corner of the box */
    kmVec3 max; /** The min corner of the box */
} kmAABB3;


kmAABB3* kmAABB3Initialize(kmAABB3* pBox, const kmVec3* centre, const kmScalar width, const kmScalar height, const kmScalar depth);
int kmAABB3ContainsPoint(const kmAABB3* pBox, const kmVec3* pPoint);
kmAABB3* kmAABB3Assign(kmAABB3* pOut, const kmAABB3* pIn);
kmAABB3* kmAABB3Scale(kmAABB3* pOut, const kmAABB3* pIn, kmScalar s);
kmBool kmAABB3IntersectsTriangle(kmAABB3* box, const kmVec3* p1, const kmVec3* p2, const kmVec3* p3);
kmBool kmAABB3IntersectsAABB(const kmAABB3* box, const kmAABB3* other);
kmEnum kmAABB3ContainsAABB(const kmAABB3* container, const kmAABB3* to_check);
kmScalar kmAABB3DiameterX(const kmAABB3* aabb);
kmScalar kmAABB3DiameterY(const kmAABB3* aabb);
kmScalar kmAABB3DiameterZ(const kmAABB3* aabb);
kmVec3* kmAABB3Centre(const kmAABB3* aabb, kmVec3* pOut);
kmAABB3* kmAABB3ExpandToContain(kmAABB3* pOut, const kmAABB3* pIn, const kmAABB3* other);

#ifdef __cplusplus
}
#endif

#endif


/**
    Initializes the AABB around a central point. If centre is NULL then the origin
    is used. Returns pBox.
*/
kmAABB3* kmAABB3Initialize(kmAABB3* pBox, const kmVec3* centre, const kmScalar width, const kmScalar height, const kmScalar depth) {
    if(!pBox) return 0;
    
    kmVec3 origin;
    kmVec3* point = centre ? (kmVec3*) centre : &origin;
    kmVec3Zero(&origin);
    
    pBox->min.x = point->x - (width / 2);
    pBox->min.y = point->y - (height / 2);
    pBox->min.z = point->z - (depth / 2);
    
    pBox->max.x = point->x + (width / 2);
    pBox->max.y = point->y + (height / 2);
    pBox->max.z = point->z + (depth / 2);
    
    return pBox;
}

/**
 * Returns KM_TRUE if point is in the specified AABB, returns
 * KM_FALSE otherwise.
 */
int kmAABB3ContainsPoint(const kmAABB3* pBox, const kmVec3* pPoint)
{
    if(pPoint->x >= pBox->min.x && pPoint->x <= pBox->max.x &&
       pPoint->y >= pBox->min.y && pPoint->y <= pBox->max.y &&
       pPoint->z >= pBox->min.z && pPoint->z <= pBox->max.z) {
        return KM_TRUE;
    }
       
    return KM_FALSE;
}

/**
 * Assigns pIn to pOut, returns pOut.
 */
kmAABB3* kmAABB3Assign(kmAABB3* pOut, const kmAABB3* pIn)
{
    kmVec3Assign(&pOut->min, &pIn->min);
    kmVec3Assign(&pOut->max, &pIn->max);
    return pOut;
}

/**
 * Scales pIn by s, stores the resulting AABB in pOut. Returns pOut
 */
kmAABB3* kmAABB3Scale(kmAABB3* pOut, const kmAABB3* pIn, kmScalar s)
{
	assert(0 && "Not implemented");
    return pOut;
}

kmBool kmAABB3IntersectsTriangle(kmAABB3* box, const kmVec3* p1, const kmVec3* p2, const kmVec3* p3) {
    assert(0 && "Not implemented");
    return KM_TRUE;
}

kmBool kmAABB3IntersectsAABB(const kmAABB3* box, const kmAABB3* other) {
    return kmAABB3ContainsAABB(box, other) != KM_CONTAINS_NONE;
}

kmEnum kmAABB3ContainsAABB(const kmAABB3* container, const kmAABB3* to_check) {
    kmVec3 corners[8];
    kmEnum result = KM_CONTAINS_ALL;
    kmBool found = KM_FALSE;
        
    kmVec3Fill(&corners[0], to_check->min.x, to_check->min.y, to_check->min.z);
    kmVec3Fill(&corners[1], to_check->max.x, to_check->min.y, to_check->min.z);
    kmVec3Fill(&corners[2], to_check->max.x, to_check->max.y, to_check->min.z);
    kmVec3Fill(&corners[3], to_check->min.x, to_check->max.y, to_check->min.z);
    kmVec3Fill(&corners[4], to_check->min.x, to_check->min.y, to_check->max.z);
    kmVec3Fill(&corners[5], to_check->max.x, to_check->min.y, to_check->max.z);
    kmVec3Fill(&corners[6], to_check->max.x, to_check->max.y, to_check->max.z);
    kmVec3Fill(&corners[7], to_check->min.x, to_check->max.y, to_check->max.z);
        
    for(kmUchar i = 0; i < 8; ++i) {
        if(!kmAABB3ContainsPoint(container, &corners[i])) {
            result = KM_CONTAINS_PARTIAL;
            if(found) {
                /*If we previously found a corner that was within the container*/
                /*We know that partial is the final result*/
                return result;
            }
        } else {
            found = KM_TRUE;
        }
    }
    
    if(!found) {
        result = KM_CONTAINS_NONE;
    }
    
    return result;
}

kmScalar kmAABB3DiameterX(const kmAABB3* aabb) {
    return fabs(aabb->max.x - aabb->min.x);
}

kmScalar kmAABB3DiameterY(const kmAABB3* aabb) {
    return fabs(aabb->max.y - aabb->min.y);
}

kmScalar kmAABB3DiameterZ(const kmAABB3* aabb) {
    return fabs(aabb->max.z - aabb->min.z);
}

kmVec3* kmAABB3Centre(const kmAABB3* aabb, kmVec3* pOut) {
    kmVec3Add(pOut, &aabb->min, &aabb->max);
    kmVec3Scale(pOut, pOut, 0.5);
    return pOut;
}

/**
 * @brief kmAABB3ExpandToContain
 * @param pOut - The resulting AABB
 * @param pIn - The original AABB
 * @param other - Another AABB that you want pIn expanded to contain
 * @return
 */
kmAABB3* kmAABB3ExpandToContain(kmAABB3* pOut, const kmAABB3* pIn, const kmAABB3* other) {
    kmAABB3 result;

    result.min.x = (pIn->min.x < other->min.x)?pIn->min.x:other->min.x;
    result.max.x = (pIn->max.x > other->max.x)?pIn->max.x:other->max.x;
    result.min.y = (pIn->min.y < other->min.y)?pIn->min.y:other->min.y;
    result.max.y = (pIn->max.y > other->max.y)?pIn->max.y:other->max.y;
    result.min.z = (pIn->min.z < other->min.z)?pIn->min.z:other->min.z;
    result.max.z = (pIn->max.z > other->max.z)?pIn->max.z:other->max.z;

    kmAABB3Assign(pOut, &result);

    return pOut;
}
