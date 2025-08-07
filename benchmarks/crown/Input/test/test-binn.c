#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <string.h>
#include <math.h>  /* for fabs */
#include <assert.h>
#include "binn.h"

#define BINN_MAGIC            0x1F22B11F

#define MAX_BINN_HEADER       9  // [1:type][4:size][4:count]
#define MIN_BINN_SIZE         3  // [1:type][1:size][1:count]
#define CHUNK_SIZE            256  // 1024

typedef unsigned short int     u16;
typedef unsigned int           u32;
typedef unsigned long long int u64;

extern void* (*malloc_fn)(int len);
extern void* (*realloc_fn)(void *ptr, int len);
extern void  (*free_fn)(void *ptr);

BINN_PRIVATE int CalcAllocation(int needed_size, int alloc_size) ;
BINN_PRIVATE BOOL IsValidBinnHeader(const void *pbuf, int *ptype, int *pcount, int *psize, int *pheadersize);

/*************************************************************************************/

void test_binn_version() {
  char *version = binn_version();
  assert(version);
  assert(strcmp(version,"3.0.0")==0);
}

/*************************************************************************************/

BINN_PRIVATE void copy_be16(u16 *pdest, u16 *psource);
BINN_PRIVATE void copy_be32(u32 *pdest, u32 *psource);
BINN_PRIVATE void copy_be64(u64 *pdest, u64 *psource);

void test_endianess() {
  u16 vshort1, vshort2, vshort3;
  u32 vint1, vint2, vint3;
  u64 value1, value2, value3;

  printf("testing endianess... ");

  /* tobe16 */
  vshort1 = 0x1122;
  copy_be16(&vshort2, &vshort1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vshort2 == 0x2211);
#else
  assert(vshort2 == 0x1122);
#endif
  copy_be16(&vshort3, &vshort2);
  assert(vshort3 == vshort1);

  vshort1 = 0xF123;
  copy_be16(&vshort2, &vshort1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vshort2 == 0x23F1);
#else
  assert(vshort2 == 0xF123);
#endif
  copy_be16(&vshort3, &vshort2);
  assert(vshort3 == vshort1);

  vshort1 = 0x0123;
  copy_be16(&vshort2, &vshort1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vshort2 == 0x2301);
#else
  assert(vshort2 == 0x0123);
#endif
  copy_be16(&vshort3, &vshort2);
  assert(vshort3 == vshort1);

  /* tobe32 */
  vint1 = 0x11223344;
  copy_be32(&vint2, &vint1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vint2 == 0x44332211);
#else
  assert(vint2 == 0x11223344);
#endif
  copy_be32(&vint3, &vint2);
  assert(vint3 == vint1);

  vint1 = 0xF1234580;
  copy_be32(&vint2, &vint1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vint2 == 0x804523F1);
#else
  assert(vint2 == 0xF1234580);
#endif
  copy_be32(&vint3, &vint2);
  assert(vint3 == vint1);

  vint1 = 0x00112233;
  copy_be32(&vint2, &vint1);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(vint2 == 0x33221100);
#else
  assert(vint2 == 0x00112233);
#endif
  copy_be32(&vint3, &vint2);
  assert(vint3 == vint1);

  /* tobe64 */
  value1 = 0x1122334455667788;
  copy_be64(&value2, &value1);
  //printf("v1: %llx\n", value1);
  //printf("v2: %llx\n", value2);
#if __BYTE_ORDER == __LITTLE_ENDIAN
  assert(value2 == 0x8877665544332211);
#else
  assert(value2 == 0x1122334455667788);
#endif
  copy_be64(&value3, &value2);
  assert(value3 == value1);

  printf("OK\n");

}

/***************************************************************************/

void * memdup(void *src, int size) {
  void *dest;

  if (src == NULL || size <= 0) return NULL;
  dest = malloc(size);
  if (dest == NULL) return NULL;
  memcpy(dest, src, size);
  return dest;

}

/***************************************************************************/

char * i64toa(int64 value, char *buf, int radix) {
#ifdef _MSC_VER
  return _i64toa(value, buf, radix);
#else
  switch (radix) {
  case 10:
    snprintf(buf, 64, "%" INT64_FORMAT, value);
    break;
  case 16:
    snprintf(buf, 64, "%" INT64_HEX_FORMAT, value);
    break;
  default:
    buf[0] = 0;
  }
  return buf;
#endif
}

/*************************************************************************************/

void pass_int64(int64 a) {

  assert(a == 9223372036854775807);
  assert(a > 9223372036854775806);

}

int64 return_int64() {

  return 9223372036854775807;

}

int64 return_passed_int64(int64 a) {

  return a;

}

/*************************************************************************************/

void test_int64() {
  int64 i64;
  //uint64 b;
  //long long int b;  -- did not work!
  char buf[64];

  printf("testing int64... ");

  pass_int64(9223372036854775807);

  i64 = return_int64();
  assert(i64 == 9223372036854775807);

  /*  do not worked!
  b = 9223372036854775807;
  printf("value of b1=%" G_GINT64_FORMAT "\n", b);
  snprintf(64, buf, "%" G_GINT64_FORMAT, b);
  printf(" value of b2=%s\n", buf);

  ltoa(i64, buf, 10);
  printf(" value of i64=%s\n", buf);
  */

  i64toa(i64, buf, 10);
  //printf(" value of i64=%s\n", buf);
  assert(strcmp(buf, "9223372036854775807") == 0);

  i64 = return_passed_int64(-987654321987654321);
  assert(i64 == -987654321987654321);

  //snprintf(64, buf, "%" G_GINT64_FORMAT, i64);
  i64toa(i64, buf, 10);
  assert(strcmp(buf, "-987654321987654321") == 0);

  printf("OK\n");

}

/*************************************************************************************/

//! this code may not work on processors that does not use the default float standard
//  original name: AlmostEqual2sComplement
BOOL AlmostEqualFloats(float A, float B, int maxUlps) {
  int aInt, bInt, intDiff;
  // Make sure maxUlps is non-negative and small enough that the
  // default NAN won't compare as equal to anything.
  assert(maxUlps > 0 && maxUlps < 4 * 1024 * 1024);
  aInt = *(int*)&A;
  bInt = *(int*)&B;
  // Make aInt lexicographically ordered as a twos-complement int
  if (aInt < 0) aInt = 0x80000000 - aInt;
  if (bInt < 0) bInt = 0x80000000 - bInt;
  intDiff = abs(aInt - bInt);
  if (intDiff <= maxUlps) return TRUE;
  return FALSE;
}

/*************************************************************************************/

#define VERYSMALL  (1.0E-150)
#define EPSILON    (1.0E-8)

#ifndef max
#define max(a,b)   (((a) > (b)) ? (a) : (b))
#endif

#ifndef min
#define min(a,b)   (((a) < (b)) ? (a) : (b))
#endif

BOOL AlmostEqualDoubles(double a, double b) {
    double absDiff, maxAbs, absA, absB;

    absDiff = fabs(a - b);
    if (absDiff < VERYSMALL) return TRUE;

    absA = fabs(a);
    absB = fabs(b);
    maxAbs  = max(absA, absB);
    if ((absDiff / maxAbs) < EPSILON)
      return TRUE;
    printf("a=%g b=%g\n", a, b);
    return FALSE;
}

/*************************************************************************************/

void test_floating_point_numbers() {
  char  buf[256];
  float f1;
  double d1;

  printf("testing floating point... ");

  f1 = 1.25;
  assert(f1 == 1.25);
  d1 = 1.25;
  assert(d1 == 1.25);

  d1 = 0;
  d1 = f1;
  assert(d1 == 1.25);
  f1 = 0;
  f1 = d1;
  assert(f1 == 1.25);

  d1 = 1.234;
  assert(AlmostEqualDoubles(d1, 1.234) == TRUE);
  f1 = d1;
  assert(AlmostEqualFloats(f1, 1.234, 2) == TRUE);

  d1 = 1.2345;
  assert(AlmostEqualDoubles(d1, 1.2345) == TRUE);
  f1 = d1;
  assert(AlmostEqualFloats(f1, 1.2345, 2) == TRUE);


  // from string to number, and back to string

  d1 = atof("1.234");  // converts from string to double
  assert(AlmostEqualDoubles(d1, 1.234) == TRUE);
  f1 = d1;             // converts from double to float
  assert(AlmostEqualFloats(f1, 1.234, 2) == TRUE);

  /*
  sprintf(buf, "%f", d1);  // from double to string
  assert(buf[0] != 0);
  assert(strcmp(buf, "1.234") == 0);
  */

  sprintf(buf, "%g", d1);
  assert(buf[0] != 0);
  assert(strcmp(buf, "1.234") == 0);


  d1 = atof("12.34");
  assert(d1 == 12.34);
  f1 = d1;
  assert(AlmostEqualFloats(f1, 12.34, 2) == TRUE);

  /*
  sprintf(buf, "%f", d1);  // from double to string
  assert(buf[0] != 0);
  assert(strcmp(buf, "12.34") == 0);
  */

  sprintf(buf, "%g", d1);
  assert(buf[0] != 0);
  assert(strcmp(buf, "12.34") == 0);


  d1 = atof("1.234e25");
  assert(AlmostEqualDoubles(d1, 1.234e25) == TRUE);
  f1 = d1;
  assert(AlmostEqualFloats(f1, 1.234e25, 2) == TRUE);

  sprintf(buf, "%g", d1);
  assert(buf[0] != 0);
  //printf("\nbuf=%s\n", buf);
  //assert(strcmp(buf, "1.234e+025") == 0);


  printf("OK\n");

}

/*************************************************************************************/

void print_binn(binn *map) {
  unsigned char *p;
  int size, i;
  p = binn_ptr(map);
  size = binn_size(map);
  for(i=0; i<size; i++){
    printf("%02x ", p[i]);
  }
  puts("");
}


/*************************************************************************************/



void test_create_binn_structures() {
    binn *list, *map, *obj;

    list = binn_list();
    assert(list != INVALID_BINN);

    map = binn_map();
    assert(map != INVALID_BINN);

    obj = binn_object();
    assert(obj != INVALID_BINN);

    assert(list->header == BINN_MAGIC);
    assert(list->type == BINN_LIST);
    assert(list->count == 0);
    assert(list->pbuf != NULL);
    assert(list->alloc_size > MAX_BINN_HEADER);
    assert(list->used_size == MAX_BINN_HEADER);
    assert(list->pre_allocated == FALSE);

    assert(map->header == BINN_MAGIC);
    assert(map->type == BINN_MAP);
    assert(map->count == 0);
    assert(map->pbuf != NULL);
    assert(map->alloc_size > MAX_BINN_HEADER);
    assert(map->used_size == MAX_BINN_HEADER);
    assert(map->pre_allocated == FALSE);

    assert(obj->header == BINN_MAGIC);
    assert(obj->type == BINN_OBJECT);
    assert(obj->count == 0);
    assert(obj->pbuf != NULL);
    assert(obj->alloc_size > MAX_BINN_HEADER);
    assert(obj->used_size == MAX_BINN_HEADER);
    assert(obj->pre_allocated == FALSE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_preallocated_binn() {
    static const int fix_size = 512;
    char *ptr = malloc(fix_size);
    assert(ptr != NULL);

    binn *obj1 = binn_new(BINN_OBJECT, fix_size, ptr);
    assert(obj1 != INVALID_BINN);

    assert(obj1->header == BINN_MAGIC);
    assert(obj1->type == BINN_OBJECT);
    assert(obj1->count == 0);
    assert(obj1->pbuf != NULL);
    assert(obj1->alloc_size == fix_size);
    assert(obj1->used_size == MAX_BINN_HEADER);
    assert(obj1->pre_allocated == TRUE);

    binn_free(obj1);
    free(ptr);
}

void test_invalid_read_operations() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();
    char *ptr;
    int type, size;

    ptr = binn_ptr(list);
    assert(ptr != NULL);
    assert(binn_list_read(ptr, 0, &type, &size) == NULL);
    assert(binn_list_read(ptr, 1, &type, &size) == NULL);

    ptr = binn_ptr(map);
    assert(ptr != NULL);
    assert(binn_map_read(ptr, 0, &type, &size) == NULL);

    ptr = binn_ptr(obj);
    assert(ptr != NULL);
    assert(binn_object_read(ptr, NULL, &type, &size) == NULL);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_valid_add_operations() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();
    int i = 123;

    assert(binn_list_add(list, BINN_INT32, &i, 0) == TRUE);
    assert(binn_map_set(map, 5501, BINN_INT32, &i, 0) == TRUE);
    assert(binn_object_set(obj, "test", BINN_INT32, &i, 0) == TRUE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_read_keys() {
    binn *map = binn_map();
    int id;
    binn value;

    assert(binn_map_set(map, 5501, BINN_INT32, &(int){123}, 0) == TRUE);
    assert(binn_map_get_pair(binn_ptr(map), 1, &id, &value) == TRUE);
    assert(id == 5501);

    binn_free(map);
}

void test_binn_size_and_validation() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();
    char *ptr;
    int type, count, size, header_size;

    ptr = binn_ptr(obj);
    assert(ptr != NULL);
    assert(IsValidBinnHeader(ptr, &type, &count, &size, &header_size) == TRUE);
    assert(type == BINN_OBJECT);
    assert(count == 0);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_add_and_read_blob() {
    binn *list = binn_list();
    int blobsize = 150;
    char *pblob = malloc(blobsize);
    assert(pblob != NULL);
    memset(pblob, 55, blobsize);

    assert(binn_list_add(list, BINN_BLOB, pblob, blobsize) == TRUE);

    char *ptr = binn_list_blob(list, 1, &blobsize);
    assert(ptr != NULL);
    assert(memcmp(ptr, pblob, blobsize) == 0);

    free(pblob);
    binn_free(list);
}

void test_add_and_read_string() {
    binn *obj = binn_object();
    const char *key = "test_key";
    const char *value = "test_value";

    assert(binn_object_set(obj, key, BINN_STRING, value, 0) == TRUE);

    char *read_value = binn_object_str(obj, key);
    assert(read_value != NULL);
    assert(strcmp(read_value, value) == 0);

    binn_free(obj);
}

void test_add_and_read_integer() {
    binn *list = binn_list();
    int value = 123;

    assert(binn_list_add(list, BINN_INT32, &value, 0) == TRUE);

    int read_value;
    assert(binn_list_get_int32(list, 1, &read_value) == TRUE);
    assert(read_value == value);

    binn_free(list);
}

/*************************************************************************************/

void test_invalid_binn() {

  char buffers[][20] = {
    { 0xE0 },
    { 0xE0, 0x7E },
    { 0xE0, 0x7E, 0x7F },
    { 0xE0, 0x7E, 0x7F, 0x12 },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34 },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0x01 },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0x7F },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01 },
    { 0xE0, 0x7E, 0x7F, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0xFF },
    { 0xE0, 0x7E, 0xFF, 0x12 },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34 },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0x01 },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0x7F },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01 },
    { 0xE0, 0x7E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x8E },
    { 0xE0, 0x8E, 0xFF },
    { 0xE0, 0x8E, 0xFF, 0x12 },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34 },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0x01 },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0x7F },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0x01 },
    { 0xE0, 0x8E, 0xFF, 0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF }
  };

  int count, size, i;
  char *ptr;

  puts("testing invalid binn buffers...");

  count = sizeof buffers / sizeof buffers[0];

  for (i=0; i < count; i++) {
    ptr = buffers[i];
    size = strlen(ptr);
    printf("checking invalid binn #%d   size: %d bytes\n", i, size);
    assert(binn_is_valid_ex(ptr, NULL, NULL, &size) == FALSE);
  }

  puts("OK");

}


void test_calc_allocation() {
    assert(CalcAllocation(512, 512) == 512);
    assert(CalcAllocation(510, 512) == 512);
    assert(CalcAllocation(1, 512) == 512);
    assert(CalcAllocation(0, 512) == 512);

    assert(CalcAllocation(513, 512) == 1024);
    assert(CalcAllocation(512 + CHUNK_SIZE, 512) == 1024);
    assert(CalcAllocation(1025, 512) == 2048);
    assert(CalcAllocation(1025, 1024) == 2048);
    assert(CalcAllocation(2100, 1024) == 4096);
}

void test_invalid_binn_creation() {
    char *ptr;
    binn *obj1;

    assert(binn_new(-1, 0, NULL) == INVALID_BINN);
    assert(binn_new(0, 0, NULL) == INVALID_BINN);
    assert(binn_new(5, 0, NULL) == INVALID_BINN);
    assert(binn_new(BINN_MAP, -1, NULL) == INVALID_BINN);

    ptr = (char *)&obj1;  // create a valid pointer
    assert(binn_new(BINN_MAP, -1, ptr) == INVALID_BINN);
    assert(binn_new(BINN_MAP, MIN_BINN_SIZE - 1, ptr) == INVALID_BINN);
}

void test_valid_binn_creation() {
    binn *list, *map, *obj;

    list = binn_new(BINN_LIST, 0, NULL);
    assert(list != INVALID_BINN);

    map = binn_new(BINN_MAP, 0, NULL);
    assert(map != INVALID_BINN);

    obj = binn_new(BINN_OBJECT, 0, NULL);
    assert(obj != INVALID_BINN);

    assert(list->header == BINN_MAGIC);
    assert(list->type == BINN_LIST);
    assert(list->count == 0);
    assert(list->pbuf != NULL);
    assert(list->alloc_size > MAX_BINN_HEADER);
    assert(list->used_size == MAX_BINN_HEADER);
    assert(list->pre_allocated == FALSE);

    assert(map->header == BINN_MAGIC);
    assert(map->type == BINN_MAP);
    assert(map->count == 0);
    assert(map->pbuf != NULL);
    assert(map->alloc_size > MAX_BINN_HEADER);
    assert(map->used_size == MAX_BINN_HEADER);
    assert(map->pre_allocated == FALSE);

    assert(obj->header == BINN_MAGIC);
    assert(obj->type == BINN_OBJECT);
    assert(obj->count == 0);
    assert(obj->pbuf != NULL);
    assert(obj->alloc_size > MAX_BINN_HEADER);
    assert(obj->used_size == MAX_BINN_HEADER);
    assert(obj->pre_allocated == FALSE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_preallocated_binn_creation() {
    static const int fix_size = 512;
    char *ptr = malloc(fix_size);
    assert(ptr != NULL);

    binn *obj1 = binn_new(BINN_OBJECT, fix_size, ptr);
    assert(obj1 != INVALID_BINN);

    assert(obj1->header == BINN_MAGIC);
    assert(obj1->type == BINN_OBJECT);
    assert(obj1->count == 0);
    assert(obj1->pbuf != NULL);
    assert(obj1->alloc_size == fix_size);
    assert(obj1->used_size == MAX_BINN_HEADER);
    assert(obj1->pre_allocated == TRUE);

    binn_free(obj1);
    free(ptr);
}

void test_invalid_binn_operations() {
    binn *list = binn_new(BINN_LIST, 0, NULL);
    binn *map = binn_new(BINN_MAP, 0, NULL);
    binn *obj = binn_new(BINN_OBJECT, 0, NULL);
    int i = 123;

    assert(binn_map_set(list, 55001, BINN_INT32, &i, 0) == FALSE);
    assert(binn_object_set(list, "test", BINN_INT32, &i, 0) == FALSE);

    assert(binn_list_add(map, BINN_INT32, &i, 0) == FALSE);
    assert(binn_object_set(map, "test", BINN_INT32, &i, 0) == FALSE);

    assert(binn_list_add(obj, BINN_INT32, &i, 0) == FALSE);
    assert(binn_map_set(obj, 55001, BINN_INT32, &i, 0) == FALSE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_valid_binn_operations() {
    binn *list = binn_new(BINN_LIST, 0, NULL);
    binn *map = binn_new(BINN_MAP, 0, NULL);
    binn *obj = binn_new(BINN_OBJECT, 0, NULL);
    int i = 0x1234;

    assert(binn_list_add(list, BINN_INT32, &i, 0) == TRUE);
    assert(binn_map_set(map, 5501, BINN_INT32, &i, 0) == TRUE);
    assert(binn_map_set(map, 5501, BINN_INT32, &i, 0) == FALSE);  // with the same ID
    assert(binn_object_set(obj, "test", BINN_INT32, &i, 0) == TRUE);
    assert(binn_object_set(obj, "test", BINN_INT32, &i, 0) == FALSE);  // with the same name

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_binn_size_operations() {
    binn *list = binn_new(BINN_LIST, 0, NULL);
    binn *map = binn_new(BINN_MAP, 0, NULL);
    binn *obj = binn_new(BINN_OBJECT, 0, NULL);

    assert(binn_size(NULL) == 0);
    assert(binn_size(list) == list->size);
    assert(binn_size(map) == map->size);
    assert(binn_size(obj) == obj->size);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_binn_blob_operations() {
    binn *list = binn_new(BINN_LIST, 0, NULL);
    int blobsize = 150;
    char *pblob = malloc(blobsize);
    assert(pblob != NULL);
    memset(pblob, 55, blobsize);

    assert(binn_list_add(list, BINN_BLOB, pblob, blobsize) == TRUE);

    char *ptr = binn_list_blob(list, 1, &blobsize);
    assert(ptr != NULL);
    assert(memcmp(ptr, pblob, blobsize) == 0);

    free(pblob);
    binn_free(list);
}

void test_binn_string_operations() {
    binn *obj = binn_new(BINN_OBJECT, 0, NULL);
    const char *key = "test_key";
    const char *value = "test_value";

    assert(binn_object_set(obj, key, BINN_STRING, value, 0) == TRUE);

    char *read_value = binn_object_str(obj, key);
    assert(read_value != NULL);
    assert(strcmp(read_value, value) == 0);

    binn_free(obj);
}

void test_binn_integer_operations() {
    binn *list = binn_new(BINN_LIST, 0, NULL);
    int value = 123;

    assert(binn_list_add(list, BINN_INT32, &value, 0) == TRUE);

    int read_value;
    assert(binn_list_get_int32(list, 1, &read_value) == TRUE);
    assert(read_value == value);

    binn_free(list);
}

/*************************************************************************************/

void test_create_and_add_values_no_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    assert(list != INVALID_BINN);
    assert(map != INVALID_BINN);
    assert(obj != INVALID_BINN);

    list->disable_int_compression = TRUE;
    map->disable_int_compression = TRUE;
    obj->disable_int_compression = TRUE;

    // Add integer values
    assert(binn_list_add_int32(list, 123) == TRUE);
    assert(binn_map_set_int32(map, 1001, 456) == TRUE);
    assert(binn_object_set_int32(obj, "int", 789) == TRUE);

    // Add double values
    assert(binn_list_add_double(list, 1.23) == TRUE);
    assert(binn_map_set_double(map, 1002, 4.56) == TRUE);
    assert(binn_object_set_double(obj, "double", 7.89) == TRUE);

    // Add boolean values
    assert(binn_list_add_bool(list, TRUE) == TRUE);
    assert(binn_map_set_bool(map, 1003, TRUE) == TRUE);
    assert(binn_object_set_bool(obj, "bool", TRUE) == TRUE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_create_and_add_values_with_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    assert(list != INVALID_BINN);
    assert(map != INVALID_BINN);
    assert(obj != INVALID_BINN);

    // Add integer values
    assert(binn_list_add_int32(list, 123) == TRUE);
    assert(binn_map_set_int32(map, 1001, 456) == TRUE);
    assert(binn_object_set_int32(obj, "int", 789) == TRUE);

    // Add double values
    assert(binn_list_add_double(list, 1.23) == TRUE);
    assert(binn_map_set_double(map, 1002, 4.56) == TRUE);
    assert(binn_object_set_double(obj, "double", 7.89) == TRUE);

    // Add boolean values
    assert(binn_list_add_bool(list, TRUE) == TRUE);
    assert(binn_map_set_bool(map, 1003, TRUE) == TRUE);
    assert(binn_object_set_bool(obj, "bool", TRUE) == TRUE);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_add_strings_and_blobs_no_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    char *str_list = "test list";
    char *str_map = "test map";
    char *str_obj = "test object";

    int blobsize = 150;
    char *pblob = malloc(blobsize);
    assert(pblob != NULL);
    memset(pblob, 55, blobsize);

    list->disable_int_compression = TRUE;
    map->disable_int_compression = TRUE;
    obj->disable_int_compression = TRUE;

    // Add string values
    assert(binn_list_add_str(list, str_list) == TRUE);
    assert(binn_map_set_str(map, 1004, str_map) == TRUE);
    assert(binn_object_set_str(obj, "text", str_obj) == TRUE);

    // Add blob values
    assert(binn_list_add_blob(list, pblob, blobsize) == TRUE);
    assert(binn_map_set_blob(map, 1005, pblob, blobsize) == TRUE);
    assert(binn_object_set_blob(obj, "blob", pblob, blobsize) == TRUE);

    free(pblob);
    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_add_strings_and_blobs_with_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    char *str_list = "test list";
    char *str_map = "test map";
    char *str_obj = "test object";

    int blobsize = 150;
    char *pblob = malloc(blobsize);
    assert(pblob != NULL);
    memset(pblob, 55, blobsize);

    // Add string values
    assert(binn_list_add_str(list, str_list) == TRUE);
    assert(binn_map_set_str(map, 1004, str_map) == TRUE);
    assert(binn_object_set_str(obj, "text", str_obj) == TRUE);

    // Add blob values
    assert(binn_list_add_blob(list, pblob, blobsize) == TRUE);
    assert(binn_map_set_blob(map, 1005, pblob, blobsize) == TRUE);
    assert(binn_object_set_blob(obj, "blob", pblob, blobsize) == TRUE);

    free(pblob);
    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_read_values_no_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    list->disable_int_compression = TRUE;
    map->disable_int_compression = TRUE;
    obj->disable_int_compression = TRUE;

    assert(binn_list_add_int32(list, 123) == TRUE);
    assert(binn_map_set_int32(map, 1001, 456) == TRUE);
    assert(binn_object_set_int32(obj, "int", 789) == TRUE);

    binn value;
    memset(&value, 0, sizeof(binn));

    // Read integer from list
    assert(binn_list_get_value(list, 1, &value) == TRUE);
    assert(value.vint == 123);

    // Read integer from map
    memset(&value, 0, sizeof(binn));
    assert(binn_map_get_value(map, 1001, &value) == TRUE);
    assert(value.vint == 456);

    // Read integer from object
    memset(&value, 0, sizeof(binn));
    assert(binn_object_get_value(obj, "int", &value) == TRUE);
    assert(value.vint == 789);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

void test_read_values_with_compression() {
    binn *list = binn_list();
    binn *map = binn_map();
    binn *obj = binn_object();

    assert(binn_list_add_int32(list, 123) == TRUE);
    assert(binn_map_set_int32(map, 1001, 456) == TRUE);
    assert(binn_object_set_int32(obj, "int", 789) == TRUE);

    binn value;
    memset(&value, 0, sizeof(binn));

    // Read integer from list
    assert(binn_list_get_value(list, 1, &value) == TRUE);
    assert(value.vint == 123);

    // Read integer from map
    memset(&value, 0, sizeof(binn));
    assert(binn_map_get_value(map, 1001, &value) == TRUE);
    assert(value.vint == 456);

    // Read integer from object
    memset(&value, 0, sizeof(binn));
    assert(binn_object_get_value(obj, "int", &value) == TRUE);
    assert(value.vint == 789);

    binn_free(list);
    binn_free(map);
    binn_free(obj);
}

/*************************************************************************************/


int main() {

  puts("\nStarting the unit/regression tests...\n");

  printf("sizeof(binn) = %ld\n\n", sizeof(binn));

  test_binn_version();

  test_endianess();

  test_int64();

  test_floating_point_numbers();

  test_calc_allocation();
  test_invalid_binn_creation();
  test_valid_binn_creation();
  test_preallocated_binn_creation();
  test_invalid_binn_operations();
  test_valid_binn_operations();
  test_binn_size_operations();
  test_binn_blob_operations();
  test_binn_string_operations();
  test_binn_integer_operations();   

  test_create_and_add_values_no_compression();
test_create_and_add_values_with_compression();
test_add_strings_and_blobs_no_compression();
test_add_strings_and_blobs_with_compression();
test_read_values_no_compression();
test_read_values_with_compression();

  test_create_binn_structures();
  test_preallocated_binn();
  test_invalid_read_operations();
  test_valid_add_operations();
  test_read_keys();
  test_binn_size_and_validation();
  test_add_and_read_blob();
  test_add_and_read_string();
  test_add_and_read_integer();

  test_invalid_binn();

  puts("\nAll tests pass! :)\n");
  return 0;

}
