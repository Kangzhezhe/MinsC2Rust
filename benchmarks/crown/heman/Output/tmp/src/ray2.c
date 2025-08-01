#include <assert.h>
#include <stdio.h>
/*
Copyright (c) 2011, Luke Benstead.
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

#ifndef RAY_2_H
#define RAY_2_H

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

#ifdef __cplusplus
extern "C" {
#endif

typedef struct kmRay2 {
    kmVec2 start;
    kmVec2 dir;
} kmRay2;

void kmRay2Fill(kmRay2* ray, kmScalar px, kmScalar py, kmScalar vx, kmScalar vy);
void kmRay2FillWithEndpoints( kmRay2 *ray, const kmVec2 *start, const kmVec2 *end );

kmBool kmLine2WithLineIntersection(const kmVec2 *ptA, const kmVec2 *vecA,
                                   const kmVec2 *ptB, const kmVec2 *vecB,
                                   kmScalar *outTA, kmScalar *outTB,
                                   kmVec2 *outIntersection );

kmBool kmSegment2WithSegmentIntersection( const kmRay2 *segmentA, 
                                          const kmRay2 *segmentB, 
                                          kmVec2 *intersection );

kmBool kmRay2IntersectLineSegment(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, kmVec2* intersection);
kmBool kmRay2IntersectTriangle(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, const kmVec2* p3, kmVec2* intersection, kmVec2* normal_out, kmScalar* distance);

kmBool kmRay2IntersectBox(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, const kmVec2* p3, const kmVec2* p4,
kmVec2* intersection, kmVec2* normal_out);

kmBool kmRay2IntersectCircle(const kmRay2* ray, const kmVec2 centre, const kmScalar radius, kmVec2* intersection);

#ifdef __cplusplus
}
#endif

#endif

void kmRay2Fill(kmRay2* ray, kmScalar px, kmScalar py, kmScalar vx, kmScalar vy) {
    ray->start.x = px;
    ray->start.y = py;    
    ray->dir.x = vx;
    ray->dir.y = vy;
}

void kmRay2FillWithEndpoints( kmRay2 *ray, const kmVec2 *start, const kmVec2 *end ) {
    ray->start.x = start->x; 
    ray->start.y = start->y; 
    ray->dir.x = end->x - start->x; 
    ray->dir.y = end->y - start->y; 
}
 

/* 
    Lines are defined by a pt and a vector. It outputs the vector multiply factor
    that gives the intersection point 
*/
kmBool kmLine2WithLineIntersection(const kmVec2 *ptA, const kmVec2 *vecA, // first line 
                                   const kmVec2 *ptB, const kmVec2 *vecB, // seconf line
                                   kmScalar *outTA, kmScalar *outTB,
                                   kmVec2 *outIntersection )
{
    kmScalar x1 = ptA->x;
    kmScalar y1 = ptA->y;
    kmScalar x2 = x1 + vecA->x;
    kmScalar y2 = y1 + vecA->y;
    kmScalar x3 = ptB->x;
    kmScalar y3 = ptB->y;
    kmScalar x4 = x3 + vecB->x;
    kmScalar y4 = y3 + vecB->y;

    kmScalar denom = (y4 -y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
    
    /*If denom is zero, the lines are parallel*/
    if(denom > -kmEpsilon && denom < kmEpsilon) {
        return KM_FALSE;
    }
    
    kmScalar ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
    kmScalar ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;
    
    kmScalar x = x1 + ua * (x2 - x1);
    kmScalar y = y1 + ua * (y2 - y1);
    
    if( outTA ){ 
        *outTA = ua;
    }
    if( outTB ){ 
        *outTB = ub; 
    }
    if( outIntersection ){
        outIntersection->x = x;
        outIntersection->y = y; 
    }
    return KM_TRUE;
} 

kmBool kmSegment2WithSegmentIntersection( const kmRay2 *segmentA, const kmRay2 *segmentB, kmVec2 *intersection )
{
    kmScalar ua;
    kmScalar ub;
    kmVec2   pt; 

    if( kmLine2WithLineIntersection( &(segmentA->start), &(segmentA->dir), 
                                    &(segmentB->start), &(segmentB->start),
                                    &ua, &ub, &pt ) && 
        (0.0 <= ua) && (ua <= 1.0) && (0.0 <= ub) && (ub <= 1.0)) {
        intersection->x = pt.x;
        intersection->y = pt.y;
        return KM_TRUE;    
    }

    return KM_FALSE;        
} 

kmBool kmRay2IntersectLineSegment(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, kmVec2* intersection) {
    
    kmScalar ua;
    kmScalar ub;
    kmVec2   pt; 

    kmRay2   otherSegment; 
    kmRay2FillWithEndpoints(&otherSegment, p1, p2); 

    if( kmLine2WithLineIntersection( &(ray->start), &(ray->dir), 
                                     &(otherSegment.start), &(otherSegment.dir),
                                     &ua, &ub, &pt ) && 
        (0.0 <= ua) && (0.0 <= ub) && (ub <= 1.0)) {
        
        intersection->x = pt.x;
        intersection->y = pt.y;
        return KM_TRUE;    
    }

    return KM_FALSE;        
}

void calculate_line_normal(kmVec2 p1, kmVec2 p2, kmVec2 other_point, kmVec2* normal_out) {
    /*
        A = (3,4)
        B = (2,1)
        C = (1,3)

        AB = (2,1) - (3,4) = (-1,-3)
        AC = (1,3) - (3,4) = (-2,-1)
        N = n(AB) = (-3,1)
        D = dot(N,AC) = 6 + -1 = 5

        since D > 0:
          N = -N = (3,-1)
    */
    
    kmVec2 edge, other_edge;
    kmVec2Subtract(&edge, &p2, &p1);
    kmVec2Subtract(&other_edge, &other_point, &p1);
    kmVec2Normalize(&edge, &edge);
    kmVec2Normalize(&other_edge, &other_edge);
    
    kmVec2 n;
    n.x = edge.y;
    n.y = -edge.x;
    
    kmScalar d = kmVec2Dot(&n, &other_edge);
    if(d > 0.0f) {
        n.x = -n.x;
        n.y = -n.y;
    }

    normal_out->x = n.x;
    normal_out->y = n.y;
    kmVec2Normalize(normal_out, normal_out);
}

kmBool kmRay2IntersectTriangle(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, const kmVec2* p3, kmVec2* intersection, kmVec2* normal_out, kmScalar* distance_out) {
    kmVec2 intersect;
    kmVec2 final_intersect;
    kmVec2 normal;
    kmScalar distance = 10000.0f;
    kmBool intersected = KM_FALSE;
 
    if(kmRay2IntersectLineSegment(ray, p1, p2, &intersect)) {
        kmVec2 tmp;
        kmScalar this_distance = kmVec2Length(kmVec2Subtract(&tmp, &intersect, &ray->start));
        kmVec2 this_normal;
        calculate_line_normal(*p1, *p2, *p3, &this_normal);                                   
        if(this_distance < distance && kmVec2Dot(&this_normal, &ray->dir) < 0.0f) {
            final_intersect.x = intersect.x;
            final_intersect.y = intersect.y;
            distance = this_distance;
            kmVec2Assign(&normal, &this_normal);
            intersected = KM_TRUE;                        
        }
    }
    
    if(kmRay2IntersectLineSegment(ray, p2, p3, &intersect)) {
        kmVec2 tmp;
        kmScalar this_distance = kmVec2Length(kmVec2Subtract(&tmp, &intersect, &ray->start));
        
        kmVec2 this_normal;
        calculate_line_normal(*p2, *p3, *p1, &this_normal);
        
        if(this_distance < distance && kmVec2Dot(&this_normal, &ray->dir) < 0.0f) {
            final_intersect.x = intersect.x;
            final_intersect.y = intersect.y;
            distance = this_distance;
            kmVec2Assign(&normal, &this_normal);
            intersected = KM_TRUE;                                
        }   
    }
    
    if(kmRay2IntersectLineSegment(ray, p3, p1, &intersect)) {

        kmVec2 tmp;
        kmScalar this_distance = kmVec2Length(kmVec2Subtract(&tmp, &intersect, &ray->start));
        
        kmVec2 this_normal;
        calculate_line_normal(*p3, *p1, *p2, &this_normal);                           
        if(this_distance < distance && kmVec2Dot(&this_normal, &ray->dir) < 0.0f) {
            final_intersect.x = intersect.x;
            final_intersect.y = intersect.y;
            distance = this_distance;
            kmVec2Assign(&normal, &this_normal);
            intersected = KM_TRUE;                                
        }          
    }
    
    if(intersected) {
        intersection->x = final_intersect.x;
        intersection->y = final_intersect.y;
        if(normal_out) {
            normal_out->x = normal.x;
            normal_out->y = normal.y;
        }
        if(distance) {
            *distance_out = distance;
        }
    }
    
    return intersected;
}

kmBool kmRay2IntersectBox(const kmRay2* ray, const kmVec2* p1, const kmVec2* p2, const kmVec2* p3, const kmVec2* p4,
kmVec2* intersection, kmVec2* normal_out) {
    kmBool intersected = KM_FALSE;
    kmVec2 intersect, final_intersect, normal;
    kmScalar distance = 10000.0f;
    
    const kmVec2* points[4];
    points[0] = p1;
    points[1] = p2;
    points[2] = p3; 
    points[3] = p4;

    unsigned int i = 0;
    for(; i < 4; ++i) {
        const kmVec2* this_point = points[i];
        const kmVec2* next_point = (i == 3) ? points[0] : points[i+1];
        const kmVec2* other_point = (i == 3 || i == 0) ? points[1] : points[0];
        
        if(kmRay2IntersectLineSegment(ray, this_point, next_point, &intersect)) {
            
            kmVec2 tmp;
            kmScalar this_distance = kmVec2Length(kmVec2Subtract(&tmp, &intersect, &ray->start));
            
            kmVec2 this_normal;
            
            calculate_line_normal(*this_point, *next_point, *other_point, &this_normal);
            if(this_distance < distance && kmVec2Dot(&this_normal, &ray->dir) < 0.0f) {
                kmVec2Assign(&final_intersect, &intersect);
                distance = this_distance;
                intersected = KM_TRUE;        
                kmVec2Assign(&normal, &this_normal);
            }
        }
    }
    
    if(intersected) {
        intersection->x = final_intersect.x;
        intersection->y = final_intersect.y;
        if(normal_out) {
            normal_out->x = normal.x;
            normal_out->y = normal.y;
        }
    }
    
    return intersected;    
}

kmBool kmRay2IntersectCircle(const kmRay2* ray, const kmVec2 centre, const kmScalar radius, kmVec2* intersection) {
    assert(0 && "Not implemented");
    return KM_TRUE;
}
