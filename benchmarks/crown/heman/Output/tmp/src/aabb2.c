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

#ifndef KAZMATH_AABB2D_H_INCLUDED
#define KAZMATH_AABB2D_H_INCLUDED

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

#ifdef __cplusplus
extern "C" {
#endif

/**
 * A struture that represents an axis-aligned
 * bounding box.
 */
typedef struct kmAABB2 {
    kmVec2 min; /** The max corner of the box */
    kmVec2 max; /** The min corner of the box */
} kmAABB2;


kmAABB2* kmAABB2Initialize(kmAABB2* pBox, const kmVec2* centre, const kmScalar width, const kmScalar height, const kmScalar depth);
kmAABB2* kmAABB2Sanitize(kmAABB2* pOut, const kmAABB2* pIn );
int kmAABB2ContainsPoint(const kmAABB2* pBox, const kmVec2* pPoint);
kmAABB2* kmAABB2Assign(kmAABB2* pOut, const kmAABB2* pIn);
kmAABB2* kmAABB2Translate(kmAABB2* pOut, const kmAABB2* pIn, const kmVec2 *translation );
kmAABB2* kmAABB2Scale(kmAABB2* pOut, const kmAABB2* pIn, kmScalar s);
kmAABB2* kmAABB2ScaleWithPivot( kmAABB2* pOut, const kmAABB2* pIn, const kmVec2 *pivot, kmScalar s );
kmEnum kmAABB2ContainsAABB(const kmAABB2* container, const kmAABB2* to_check);
kmScalar kmAABB2DiameterX(const kmAABB2* aabb);
kmScalar kmAABB2DiameterY(const kmAABB2* aabb);
kmVec2* kmAABB2Centre(const kmAABB2* aabb, kmVec2* pOut);
kmAABB2* kmAABB2ExpandToContain(kmAABB2* pOut, const kmAABB2* pIn, const kmAABB2* other);

#ifdef __cplusplus
}
#endif

#endif


/**
    Initializes the AABB around a central point. If centre is NULL then the origin
    is used. Returns pBox.
*/
kmAABB2* kmAABB2Initialize( kmAABB2* pBox, const kmVec2* centre, const kmScalar width, const kmScalar height, const kmScalar depth) {
    if(!pBox) return 0;
    
    kmVec2 origin;
    kmVec2* point = centre ? (kmVec2*) centre : &origin;
    kmVec2Fill(&origin, .0f, .0f);
    
    pBox->min.x = point->x - (width / 2);
    pBox->min.y = point->y - (height / 2);
    
    pBox->max.x = point->x + (width / 2);
    pBox->max.y = point->y + (height / 2);
    
    return pBox;
}

/** 
 *  Makes sure that min corresponds to the minimum values and max 
 *  to the maximum
 */
kmAABB2* kmAABB2Sanitize(kmAABB2* pOut, const kmAABB2* pIn)
{
    if( pIn->min.x <= pIn->max.x ){
        pOut->min.x = pIn->min.x;
        pOut->max.x = pIn->max.x; 
    }else{
        pOut->min.x = pIn->max.x;
        pOut->max.x = pIn->min.x; 
    }

    if( pIn->min.y <= pIn->max.y ){
        pOut->min.y = pIn->min.y;
        pOut->max.y = pIn->max.y; 
    }else{
        pOut->min.y = pIn->max.y;
        pOut->max.y = pIn->min.y; 
    }

    return pOut;
}

/**
 * Returns KM_TRUE if point is in the specified AABB, returns
 * KM_FALSE otherwise.
 */
int kmAABB2ContainsPoint(const kmAABB2* pBox, const kmVec2* pPoint)
{
    if(pPoint->x >= pBox->min.x && pPoint->x <= pBox->max.x &&
       pPoint->y >= pBox->min.y && pPoint->y <= pBox->max.y ) {
        return KM_TRUE;
    }
       
    return KM_FALSE;
}

/**
 * Assigns pIn to pOut, returns pOut.
 */
kmAABB2* kmAABB2Assign(kmAABB2* pOut, const kmAABB2* pIn)
{
    kmVec2Assign(&pOut->min, &pIn->min);
    kmVec2Assign(&pOut->max, &pIn->max);
    return pOut;
}

kmAABB2* kmAABB2Translate( kmAABB2* pOut, const kmAABB2* pIn, const kmVec2 *translation )
{
    kmVec2Add( &(pOut->min), &(pIn->min), translation );
    kmVec2Add( &(pOut->max), &(pIn->max), translation );
    return pOut;
}

/**
 * Scales pIn by s, stores the resulting AABB in pOut. Returns pOut. 
 * It modifies both points, so position of the box will be changed. Use
 * kmAABB2ScaleWithPivot to specify the origin of the scale.
 */
kmAABB2* kmAABB2Scale(kmAABB2* pOut, const kmAABB2* pIn, kmScalar s)
{
    kmVec2Scale( &(pOut->max), &(pIn->max), s ); 
    kmVec2Scale( &(pOut->min), &(pIn->min), s ); 
    return pOut;
}

/** 
 * Scales pIn by s, using pivot as the origin for the scale.
 */
kmAABB2* kmAABB2ScaleWithPivot( kmAABB2* pOut, const kmAABB2* pIn, const kmVec2 *pivot, kmScalar s )
{
    kmVec2 translate;
    translate.x = -pivot->x;
    translate.y = -pivot->y;

    kmAABB2Translate( pOut, pIn, &translate ); 
    kmAABB2Scale( pOut, pIn, s );
    kmAABB2Translate( pOut, pIn, pivot ); 

    return pOut;
}

kmEnum kmAABB2ContainsAABB(const kmAABB2* container, const kmAABB2* to_check) {
    kmVec2 corners[4];
    kmVec2Fill(&corners[0], to_check->min.x, to_check->min.y);
    kmVec2Fill(&corners[1], to_check->max.x, to_check->min.y);
    kmVec2Fill(&corners[2], to_check->max.x, to_check->max.y);
    kmVec2Fill(&corners[3], to_check->min.x, to_check->max.y);
    
    // since KM_TRUE equals 1 , we can count the number of contained points
    // by actually adding the results: 
    int nContains = kmAABB2ContainsPoint( container, &corners[0] ) +
                    kmAABB2ContainsPoint( container, &corners[1] ) +
                    kmAABB2ContainsPoint( container, &corners[2] ) +
                    kmAABB2ContainsPoint( container, &corners[3] );

    if( nContains == 0 ){ 
        return KM_CONTAINS_NONE; 
    }else if( nContains < 4 ){
        return KM_CONTAINS_PARTIAL;
    }else{ 
        return KM_CONTAINS_ALL;
    }
}

kmScalar kmAABB2DiameterX(const kmAABB2* aabb) {
    return aabb->max.x - aabb->min.x;
}

kmScalar kmAABB2DiameterY(const kmAABB2* aabb) {
    return aabb->max.y - aabb->min.y;
}

kmVec2* kmAABB2Centre(const kmAABB2* aabb, kmVec2* pOut) {
    kmVec2Add(pOut, &aabb->min, &aabb->max);
    kmVec2Scale(pOut, pOut, 0.5);
    return pOut;
}

/**
 * @brief kmAABB2ExpandToContain
 * @param pOut - The resulting AABB
 * @param pIn - The original AABB
 * @param other - Another AABB that you want pIn expanded to contain
 * @return
 */
kmAABB2* kmAABB2ExpandToContain(kmAABB2* pOut, const kmAABB2* pIn, const kmAABB2* other) {
    kmAABB2 result;

    result.min.x = (pIn->min.x < other->min.x)?pIn->min.x:other->min.x;
    result.max.x = (pIn->max.x > other->max.x)?pIn->max.x:other->max.x;
    result.min.y = (pIn->min.y < other->min.y)?pIn->min.y:other->min.y;
    result.max.y = (pIn->max.y > other->max.y)?pIn->max.y:other->max.y;

    kmAABB2Assign(pOut, &result);

    return pOut;
}