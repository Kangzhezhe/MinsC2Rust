#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <string.h>
#include <math.h>  /* for fabs */
#include <assert.h>

// TO ENABLE INLINE FUNCTIONS:
//   ON MSVC: enable the 'Inline Function Expansion' (/Ob2) compiler option, and maybe the
//            'Whole Program Optimitazion' (/GL), that requires the
//            'Link Time Code Generation' (/LTCG) linker option to be enabled too

#ifndef BINN_H
#define BINN_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

#define BINN_VERSION "3.0.0"  /* using semantic versioning */

#ifndef NULL
#ifdef __cplusplus
#define NULL    0
#else
#define NULL    ((void *)0)
#endif
#endif

#ifndef TRUE
#define TRUE  1
#endif

#ifndef FALSE
#define FALSE 0
#endif

#ifndef BOOL
typedef int BOOL;
#endif

#ifndef APIENTRY
 #ifdef _WIN32
  #define APIENTRY __stdcall
 #else
  //#define APIENTRY __attribute__((stdcall))
  #define APIENTRY 
 #endif
#endif

#define BINN_PRIVATE 

#ifdef _MSC_VER
  #define INLINE         __inline
  #define ALWAYS_INLINE  __forceinline
#else
  // you can change to 'extern inline' if using the gcc option -flto
  #define INLINE         static inline
  #define ALWAYS_INLINE  static inline
#endif

#ifndef int64
#if defined(_MSC_VER) || defined(__BORLANDC__)
  typedef __int64 int64;
  typedef unsigned __int64 uint64;
#else
  typedef long long int int64;
  typedef unsigned long long int uint64;
#endif
#endif

#ifdef _WIN32
#define INT64_FORMAT  "I64i"
#define UINT64_FORMAT "I64u"
#define INT64_HEX_FORMAT  "I64x"
#else
#define INT64_FORMAT  "lli"
#define UINT64_FORMAT "llu"
#define INT64_HEX_FORMAT  "llx"
#endif


// BINN CONSTANTS  ----------------------------------------

#define INVALID_BINN         0

// Storage Data Types  ------------------------------------

#define BINN_STORAGE_NOBYTES   0x00
#define BINN_STORAGE_BYTE      0x20  //  8 bits
#define BINN_STORAGE_WORD      0x40  // 16 bits -- the endianess (byte order) is automatically corrected
#define BINN_STORAGE_DWORD     0x60  // 32 bits -- the endianess (byte order) is automatically corrected
#define BINN_STORAGE_QWORD     0x80  // 64 bits -- the endianess (byte order) is automatically corrected
#define BINN_STORAGE_STRING    0xA0  // Are stored with null termination
#define BINN_STORAGE_BLOB      0xC0
#define BINN_STORAGE_CONTAINER 0xE0
#define BINN_STORAGE_VIRTUAL   0x80000

#define BINN_STORAGE_MIN       BINN_STORAGE_NOBYTES
#define BINN_STORAGE_MAX       BINN_STORAGE_CONTAINER

#define BINN_STORAGE_MASK      0xE0
#define BINN_STORAGE_MASK16    0xE000
#define BINN_STORAGE_HAS_MORE  0x10
#define BINN_TYPE_MASK         0x0F
#define BINN_TYPE_MASK16       0x0FFF

#define BINN_MAX_VALUE_MASK    0xFFFFF


// Data Formats  ------------------------------------------

#define BINN_LIST      0xE0
#define BINN_MAP       0xE1
#define BINN_OBJECT    0xE2

#define BINN_NULL      0x00
#define BINN_TRUE      0x01
#define BINN_FALSE     0x02

#define BINN_UINT8     0x20  // (BYTE) (unsigned byte) Is the default format for the BYTE type
#define BINN_INT8      0x21  // (BYTE) (signed byte, from -128 to +127. The 0x80 is the sign bit, so the range in hex is from 0x80 [-128] to 0x7F [127], being 0x00 = 0 and 0xFF = -1)
#define BINN_UINT16    0x40  // (WORD) (unsigned integer) Is the default format for the WORD type
#define BINN_INT16     0x41  // (WORD) (signed integer)
#define BINN_UINT32    0x60  // (DWORD) (unsigned integer) Is the default format for the DWORD type
#define BINN_INT32     0x61  // (DWORD) (signed integer)
#define BINN_UINT64    0x80  // (QWORD) (unsigned integer) Is the default format for the QWORD type
#define BINN_INT64     0x81  // (QWORD) (signed integer)

#define BINN_SCHAR     BINN_INT8
#define BINN_UCHAR     BINN_UINT8

#define BINN_STRING    0xA0  // (STRING) Raw String
#define BINN_DATETIME  0xA1  // (STRING) iso8601 format -- YYYY-MM-DD HH:MM:SS
#define BINN_DATE      0xA2  // (STRING) iso8601 format -- YYYY-MM-DD
#define BINN_TIME      0xA3  // (STRING) iso8601 format -- HH:MM:SS
#define BINN_DECIMAL   0xA4  // (STRING) High precision number - used for generic decimal values and for those ones that cannot be represented in the float64 format.
#define BINN_CURRENCYSTR  0xA5  // (STRING) With currency unit/symbol - check for some iso standard format
#define BINN_SINGLE_STR   0xA6  // (STRING) Can be restored to float32
#define BINN_DOUBLE_STR   0xA7  // (STRING) May be restored to float64

#define BINN_FLOAT32   0x62  // (DWORD) 
#define BINN_FLOAT64   0x82  // (QWORD) 
#define BINN_FLOAT     BINN_FLOAT32
#define BINN_SINGLE    BINN_FLOAT32
#define BINN_DOUBLE    BINN_FLOAT64

#define BINN_CURRENCY  0x83  // (QWORD)

#define BINN_BLOB      0xC0  // (BLOB) Raw Blob


// virtual types:

#define BINN_BOOL      0x80061  // (DWORD) The value may be 0 or 1

#ifdef BINN_EXTENDED
//#define BINN_SINGLE    0x800A1  // (STRING) Can be restored to float32
//#define BINN_DOUBLE    0x800A2  // (STRING) May be restored to float64
#endif

//#define BINN_BINN      0x800E1  // (CONTAINER)
//#define BINN_BINN_BUFFER  0x800C1  // (BLOB) user binn. it's not open by the parser


// extended content types:

// strings:

#define BINN_HTML      0xB001
#define BINN_XML       0xB002
#define BINN_JSON      0xB003
#define BINN_JAVASCRIPT 0xB004
#define BINN_CSS       0xB005

// blobs:

#define BINN_JPEG      0xD001
#define BINN_GIF       0xD002
#define BINN_PNG       0xD003
#define BINN_BMP       0xD004


// type families
#define BINN_FAMILY_NONE   0x00
#define BINN_FAMILY_NULL   0xf1
#define BINN_FAMILY_INT    0xf2
#define BINN_FAMILY_FLOAT  0xf3
#define BINN_FAMILY_STRING 0xf4
#define BINN_FAMILY_BLOB   0xf5
#define BINN_FAMILY_BOOL   0xf6
#define BINN_FAMILY_BINN   0xf7

// integer types related to signal
#define BINN_SIGNED_INT     11
#define BINN_UNSIGNED_INT   22


typedef void (*binn_mem_free)(void*);
#define BINN_STATIC      ((binn_mem_free)0)
#define BINN_TRANSIENT   ((binn_mem_free)-1)


// --- BINN STRUCTURE --------------------------------------------------------------


struct binn_struct {
  int    header;     // this struct header holds the magic number (BINN_MAGIC) that identifies this memory block as a binn structure
  BOOL   allocated;  // the struct can be allocated using malloc_fn() or can be on the stack
  BOOL   writable;   // did it was create for writing? it can use the pbuf if not unified with ptr
  BOOL   dirty;      // the container header is not written to the buffer
  //
  void  *pbuf;       // use *ptr below?
  BOOL   pre_allocated;
  int    alloc_size;
  int    used_size;
  //
  int    type;
  void  *ptr;
  int    size;
  int    count;
  //
  binn_mem_free freefn;  // used only when type == BINN_STRING or BINN_BLOB
  //
  union {
    signed char    vint8;
    signed short   vint16;
    signed int     vint32;
    int64          vint64;
    unsigned char  vuint8;
    unsigned short vuint16;
    unsigned int   vuint32;
    uint64         vuint64;
    //
    signed char    vchar;
    unsigned char  vuchar;
    signed short   vshort;
    unsigned short vushort;
    signed int     vint;
    unsigned int   vuint;
    //
    float          vfloat;
    double         vdouble;
    //
    BOOL           vbool;
  };
  //
  BOOL   disable_int_compression;
};

typedef struct binn_struct binn;



// --- GENERAL FUNCTIONS  ----------------------------------------------------------

char * APIENTRY binn_version();

void   APIENTRY binn_set_alloc_functions(void* (*new_malloc)(size_t), void* (*new_realloc)(void*,size_t), void (*new_free)(void*));

int    APIENTRY binn_create_type(int storage_type, int data_type_index);
BOOL   APIENTRY binn_get_type_info(int long_type, int *pstorage_type, int *pextra_type);

int    APIENTRY binn_get_write_storage(int type);
int    APIENTRY binn_get_read_storage(int type);

BOOL   APIENTRY binn_is_container(binn *item);


// --- WRITE FUNCTIONS  ------------------------------------------------------------

// create a new binn allocating memory for the structure
binn * APIENTRY binn_new(int type, int size, void *buffer);
binn * APIENTRY binn_list();
binn * APIENTRY binn_map();
binn * APIENTRY binn_object();

// create a new binn storing the structure on the stack
BOOL APIENTRY binn_create(binn *item, int type, int size, void *buffer);
BOOL APIENTRY binn_create_list(binn *list);
BOOL APIENTRY binn_create_map(binn *map);
BOOL APIENTRY binn_create_object(binn *object);

// create a new binn as a copy from another
binn * APIENTRY binn_copy(const void *old);


BOOL APIENTRY binn_list_add_new(binn *list, binn *value);
BOOL APIENTRY binn_map_set_new(binn *map, int id, binn *value);
BOOL APIENTRY binn_object_set_new(binn *obj, const char *key, binn *value);


// extended interface

BOOL   APIENTRY binn_list_add(binn *list, int type, void *pvalue, int size);
BOOL   APIENTRY binn_map_set(binn *map, int id, int type, void *pvalue, int size);
BOOL   APIENTRY binn_object_set(binn *obj, const char *key, int type, void *pvalue, int size);


// release memory

void   APIENTRY binn_free(binn *item);
void * APIENTRY binn_release(binn *item); // free the binn structure but keeps the binn buffer allocated, returning a pointer to it. use the free function to release the buffer later


// --- CREATING VALUES ---------------------------------------------------

binn * APIENTRY binn_value(int type, void *pvalue, int size, binn_mem_free freefn);

ALWAYS_INLINE binn * binn_int8(signed char value) {
  return binn_value(BINN_INT8, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_int16(short value) {
  return binn_value(BINN_INT16, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_int32(int value) {
  return binn_value(BINN_INT32, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_int64(int64 value) {
  return binn_value(BINN_INT64, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_uint8(unsigned char value) {
  return binn_value(BINN_UINT8, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_uint16(unsigned short value) {
  return binn_value(BINN_UINT16, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_uint32(unsigned int value) {
  return binn_value(BINN_UINT32, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_uint64(uint64 value) {
  return binn_value(BINN_UINT64, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_float(float value) {
  return binn_value(BINN_FLOAT, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_double(double value) {
  return binn_value(BINN_DOUBLE, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_bool(BOOL value) {
  return binn_value(BINN_BOOL, &value, 0, NULL);
}
ALWAYS_INLINE binn * binn_null() {
  return binn_value(BINN_NULL, NULL, 0, NULL);
}
ALWAYS_INLINE binn * binn_string(char *str, binn_mem_free freefn) {
  return binn_value(BINN_STRING, str, 0, freefn);
}
ALWAYS_INLINE binn * binn_blob(void *ptr, int size, binn_mem_free freefn) {
  return binn_value(BINN_BLOB, ptr, size, freefn);
}


// --- READ FUNCTIONS  -------------------------------------------------------------

// these functions accept pointer to the binn structure and pointer to the binn buffer
void * APIENTRY binn_ptr(const void *ptr);
int    APIENTRY binn_size(const void *ptr);
int    APIENTRY binn_type(const void *ptr);
int    APIENTRY binn_count(const void *ptr);

BOOL   APIENTRY binn_is_valid(const void *ptr, int *ptype, int *pcount, int *psize);
/* the function returns the values (type, count and size) and they don't need to be
   initialized. these values are read from the buffer. example:

   int type, count, size;
   result = binn_is_valid(ptr, &type, &count, &size);
*/
BOOL   APIENTRY binn_is_valid_ex(const void *ptr, int *ptype, int *pcount, int *psize);
/* if some value is informed (type, count or size) then the function will check if 
   the value returned from the serialized data matches the informed value. otherwise
   the values must be initialized to zero. example:

   int type=0, count=0, size = known_size;
   result = binn_is_valid_ex(ptr, &type, &count, &size);
*/

BOOL   APIENTRY binn_is_struct(const void *ptr);


// Loading a binn buffer into a binn value - this is optional

binn * APIENTRY binn_open(const void *data);              // allocated - unsecure
binn * APIENTRY binn_open_ex(const void *data, int size); // allocated - secure
BOOL   APIENTRY binn_load(const void *data, binn *item);  // on stack - unsecure
BOOL   APIENTRY binn_load_ex(const void *data, int size, binn *value); // secure


// easiest interface to use, but don't check if the value is there

signed char    APIENTRY binn_list_int8(const void *list, int pos);
short          APIENTRY binn_list_int16(const void *list, int pos);
int            APIENTRY binn_list_int32(const void *list, int pos);
int64          APIENTRY binn_list_int64(const void *list, int pos);
unsigned char  APIENTRY binn_list_uint8(const void *list, int pos);
unsigned short APIENTRY binn_list_uint16(const void *list, int pos);
unsigned int   APIENTRY binn_list_uint32(const void *list, int pos);
uint64         APIENTRY binn_list_uint64(const void *list, int pos);
float          APIENTRY binn_list_float(const void *list, int pos);
double         APIENTRY binn_list_double(const void *list, int pos);
BOOL           APIENTRY binn_list_bool(const void *list, int pos);
BOOL           APIENTRY binn_list_null(const void *list, int pos);
char *         APIENTRY binn_list_str(const void *list, int pos);
void *         APIENTRY binn_list_blob(const void *list, int pos, int *psize);
void *         APIENTRY binn_list_list(const void *list, int pos);
void *         APIENTRY binn_list_map(const void *list, int pos);
void *         APIENTRY binn_list_object(const void *list, int pos);

signed char    APIENTRY binn_map_int8(const void *map, int id);
short          APIENTRY binn_map_int16(const void *map, int id);
int            APIENTRY binn_map_int32(const void *map, int id);
int64          APIENTRY binn_map_int64(const void *map, int id);
unsigned char  APIENTRY binn_map_uint8(const void *map, int id);
unsigned short APIENTRY binn_map_uint16(const void *map, int id);
unsigned int   APIENTRY binn_map_uint32(const void *map, int id);
uint64         APIENTRY binn_map_uint64(const void *map, int id);
float          APIENTRY binn_map_float(const void *map, int id);
double         APIENTRY binn_map_double(const void *map, int id);
BOOL           APIENTRY binn_map_bool(const void *map, int id);
BOOL           APIENTRY binn_map_null(const void *map, int id);
char *         APIENTRY binn_map_str(const void *map, int id);
void *         APIENTRY binn_map_blob(const void *map, int id, int *psize);
void *         APIENTRY binn_map_list(const void *map, int id);
void *         APIENTRY binn_map_map(const void *map, int id);
void *         APIENTRY binn_map_object(const void *map, int id);

signed char    APIENTRY binn_object_int8(const void *obj, const char *key);
short          APIENTRY binn_object_int16(const void *obj, const char *key);
int            APIENTRY binn_object_int32(const void *obj, const char *key);
int64          APIENTRY binn_object_int64(const void *obj, const char *key);
unsigned char  APIENTRY binn_object_uint8(const void *obj, const char *key);
unsigned short APIENTRY binn_object_uint16(const void *obj, const char *key);
unsigned int   APIENTRY binn_object_uint32(const void *obj, const char *key);
uint64         APIENTRY binn_object_uint64(const void *obj, const char *key);
float          APIENTRY binn_object_float(const void *obj, const char *key);
double         APIENTRY binn_object_double(const void *obj, const char *key);
BOOL           APIENTRY binn_object_bool(const void *obj, const char *key);
BOOL           APIENTRY binn_object_null(const void *obj, const char *key);
char *         APIENTRY binn_object_str(const void *obj, const char *key);
void *         APIENTRY binn_object_blob(const void *obj, const char *key, int *psize);
void *         APIENTRY binn_object_list(const void *obj, const char *key);
void *         APIENTRY binn_object_map(const void *obj, const char *key);
void *         APIENTRY binn_object_object(const void *obj, const char *key);


// return a pointer to an allocated binn structure - must be released with the free() function or equivalent set in binn_set_alloc_functions()
binn * APIENTRY binn_list_value(const void *list, int pos);
binn * APIENTRY binn_map_value(const void *map, int id);
binn * APIENTRY binn_object_value(const void *obj, const char *key);

// read the value to a binn structure on the stack
BOOL APIENTRY binn_list_get_value(const void *list, int pos, binn *value);
BOOL APIENTRY binn_map_get_value(const void *map, int id, binn *value);
BOOL APIENTRY binn_object_get_value(const void *obj, const char *key, binn *value);

// single interface - these functions check the data type
BOOL APIENTRY binn_list_get(const void *list, int pos, int type, void *pvalue, int *psize);
BOOL APIENTRY binn_map_get(const void *map, int id, int type, void *pvalue, int *psize);
BOOL APIENTRY binn_object_get(const void *obj, const char *key, int type, void *pvalue, int *psize);

// these 3 functions return a pointer to the value and the data type
// they are thread-safe on big-endian devices
// on little-endian devices they are thread-safe only to return pointers to list, map, object, blob and strings
// the returned pointer to 16, 32 and 64 bits values must be used only by single-threaded applications
void * APIENTRY binn_list_read(const void *list, int pos, int *ptype, int *psize);
void * APIENTRY binn_map_read(const void *map, int id, int *ptype, int *psize);
void * APIENTRY binn_object_read(const void *obj, const char *key, int *ptype, int *psize);


// READ PAIR FUNCTIONS

// these functions use base 1 in the 'pos' argument

// on stack
BOOL APIENTRY binn_map_get_pair(const void *map, int pos, int *pid, binn *value);
BOOL APIENTRY binn_object_get_pair(const void *obj, int pos, char *pkey, binn *value);  // the key must be declared as: char key[256];

// allocated
binn * APIENTRY binn_map_pair(const void *map, int pos, int *pid);
binn * APIENTRY binn_object_pair(const void *obj, int pos, char *pkey);  // the key must be declared as: char key[256];

// these 2 functions return a pointer to the value and the data type
// they are thread-safe on big-endian devices
// on little-endian devices they are thread-safe only to return pointers to list, map, object, blob and strings
// the returned pointer to 16, 32 and 64 bits values must be used only by single-threaded applications
void * APIENTRY binn_map_read_pair(const void *ptr, int pos, int *pid, int *ptype, int *psize);
void * APIENTRY binn_object_read_pair(const void *ptr, int pos, char *pkey, int *ptype, int *psize);


// SEQUENTIAL READ FUNCTIONS

typedef struct binn_iter_struct {
    unsigned char *pnext;
    unsigned char *plimit;
    int   type;
    int   count;
    int   current;
} binn_iter;

BOOL   APIENTRY binn_iter_init(binn_iter *iter, const void *pbuf, int type);

// allocated
binn * APIENTRY binn_list_next_value(binn_iter *iter);
binn * APIENTRY binn_map_next_value(binn_iter *iter, int *pid);
binn * APIENTRY binn_object_next_value(binn_iter *iter, char *pkey);  // the key must be declared as: char key[256];

// on stack
BOOL   APIENTRY binn_list_next(binn_iter *iter, binn *value);
BOOL   APIENTRY binn_map_next(binn_iter *iter, int *pid, binn *value);
BOOL   APIENTRY binn_object_next(binn_iter *iter, char *pkey, binn *value);  // the key must be declared as: char key[256];

// these 3 functions return a pointer to the value and the data type
// they are thread-safe on big-endian devices
// on little-endian devices they are thread-safe only to return pointers to list, map, object, blob and strings
// the returned pointer to 16, 32 and 64 bits values must be used only by single-threaded applications
void * APIENTRY binn_list_read_next(binn_iter *iter, int *ptype, int *psize);
void * APIENTRY binn_map_read_next(binn_iter *iter, int *pid, int *ptype, int *psize);
void * APIENTRY binn_object_read_next(binn_iter *iter, char *pkey, int *ptype, int *psize);  // the key must be declared as: char key[256];


// --- MACROS ------------------------------------------------------------


#define binn_is_writable(item) (item)->writable;


// set values on stack allocated binn structures

#define binn_set_null(item)         do { (item)->type = BINN_NULL; } while (0)

#define binn_set_bool(item,value)   do { (item)->type = BINN_BOOL; (item)->vbool = value; (item)->ptr = &((item)->vbool); } while (0)

#define binn_set_int(item,value)    do { (item)->type = BINN_INT32; (item)->vint32 = value; (item)->ptr = &((item)->vint32); } while (0)
#define binn_set_int64(item,value)  do { (item)->type = BINN_INT64; (item)->vint64 = value; (item)->ptr = &((item)->vint64); } while (0)

#define binn_set_uint(item,value)   do { (item)->type = BINN_UINT32; (item)->vuint32 = value; (item)->ptr = &((item)->vuint32); } while (0)
#define binn_set_uint64(item,value) do { (item)->type = BINN_UINT64; (item)->vuint64 = value; (item)->ptr = &((item)->vuint64); } while (0)

#define binn_set_float(item,value)  do { (item)->type = BINN_FLOAT;  (item)->vfloat  = value; (item)->ptr = &((item)->vfloat); } while (0)
#define binn_set_double(item,value) do { (item)->type = BINN_DOUBLE; (item)->vdouble = value; (item)->ptr = &((item)->vdouble); } while (0)

//#define binn_set_string(item,str,pfree)    do { (item)->type = BINN_STRING; (item)->ptr = str; (item)->freefn = pfree; } while (0)
//#define binn_set_blob(item,ptr,size,pfree) do { (item)->type = BINN_BLOB;   (item)->ptr = ptr; (item)->freefn = pfree; (item)->size = size; } while (0)
BOOL APIENTRY binn_set_string(binn *item, char *str, binn_mem_free pfree);
BOOL APIENTRY binn_set_blob(binn *item, void *ptr, int size, binn_mem_free pfree);


//#define binn_double(value) {       (item)->type = BINN_DOUBLE; (item)->vdouble = value; (item)->ptr = &((item)->vdouble) }



// FOREACH MACROS
// --------------
//
// We must use these declarations inside the functions that will use the macros:
//
//  binn_iter iter;
//  binn value;
//  char key[256];  // only for objects
//  int  id;        // only for maps

#define binn_object_foreach(object, key, value)   \
    binn_iter_init(&iter, object, BINN_OBJECT);   \
    while (binn_object_next(&iter, key, &value))

#define binn_map_foreach(map, id, value)          \
    binn_iter_init(&iter, map, BINN_MAP);         \
    while (binn_map_next(&iter, &id, &value))

#define binn_list_foreach(list, value)            \
    binn_iter_init(&iter, list, BINN_LIST);       \
    while (binn_list_next(&iter, &value))

// If you need nested foreach loops, use the macros below for the nested loop
// Also we need to add an additional declaration on the function to hold the iterator
// We can add in the same line as the first iterator:
//
//  binn_iter iter, iter2;

#define binn_object_foreach2(object, key, value)   \
    binn_iter_init(&iter2, object, BINN_OBJECT);   \
    while (binn_object_next(&iter2, key, &value))

#define binn_map_foreach2(map, id, value)          \
    binn_iter_init(&iter2, map, BINN_MAP);         \
    while (binn_map_next(&iter2, &id, &value))

#define binn_list_foreach2(list, value)            \
    binn_iter_init(&iter2, list, BINN_LIST);       \
    while (binn_list_next(&iter2, &value))


/*************************************************************************************/
/*** SET FUNCTIONS *******************************************************************/
/*************************************************************************************/

ALWAYS_INLINE BOOL binn_list_add_int8(binn *list, signed char value) {
  return binn_list_add(list, BINN_INT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_int16(binn *list, short value) {
  return binn_list_add(list, BINN_INT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_int32(binn *list, int value) {
  return binn_list_add(list, BINN_INT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_int64(binn *list, int64 value) {
  return binn_list_add(list, BINN_INT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_uint8(binn *list, unsigned char value) {
  return binn_list_add(list, BINN_UINT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_uint16(binn *list, unsigned short value) {
  return binn_list_add(list, BINN_UINT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_uint32(binn *list, unsigned int value) {
  return binn_list_add(list, BINN_UINT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_uint64(binn *list, uint64 value) {
  return binn_list_add(list, BINN_UINT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_float(binn *list, float value) {
  return binn_list_add(list, BINN_FLOAT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_double(binn *list, double value) {
  return binn_list_add(list, BINN_FLOAT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_bool(binn *list, BOOL value) {
  return binn_list_add(list, BINN_BOOL, &value, 0);
}
ALWAYS_INLINE BOOL binn_list_add_null(binn *list) {
  return binn_list_add(list, BINN_NULL, NULL, 0);
}
ALWAYS_INLINE BOOL binn_list_add_str(binn *list, char *str) {
  return binn_list_add(list, BINN_STRING, str, 0);
}
ALWAYS_INLINE BOOL binn_list_add_blob(binn *list, void *ptr, int size) {
  return binn_list_add(list, BINN_BLOB, ptr, size);
}
ALWAYS_INLINE BOOL binn_list_add_list(binn *list, void *list2) {
  return binn_list_add(list, BINN_LIST, binn_ptr(list2), binn_size(list2));
}
ALWAYS_INLINE BOOL binn_list_add_map(binn *list, void *map) {
  return binn_list_add(list, BINN_MAP, binn_ptr(map), binn_size(map));
}
ALWAYS_INLINE BOOL binn_list_add_object(binn *list, void *obj) {
  return binn_list_add(list, BINN_OBJECT, binn_ptr(obj), binn_size(obj));
}
ALWAYS_INLINE BOOL binn_list_add_value(binn *list, binn *value) {
  return binn_list_add(list, value->type, binn_ptr(value), binn_size(value));
}

/*************************************************************************************/

ALWAYS_INLINE BOOL binn_map_set_int8(binn *map, int id, signed char value) {
  return binn_map_set(map, id, BINN_INT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_int16(binn *map, int id, short value) {
  return binn_map_set(map, id, BINN_INT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_int32(binn *map, int id, int value) {
  return binn_map_set(map, id, BINN_INT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_int64(binn *map, int id, int64 value) {
  return binn_map_set(map, id, BINN_INT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_uint8(binn *map, int id, unsigned char value) {
  return binn_map_set(map, id, BINN_UINT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_uint16(binn *map, int id, unsigned short value) {
  return binn_map_set(map, id, BINN_UINT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_uint32(binn *map, int id, unsigned int value) {
  return binn_map_set(map, id, BINN_UINT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_uint64(binn *map, int id, uint64 value) {
  return binn_map_set(map, id, BINN_UINT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_float(binn *map, int id, float value) {
  return binn_map_set(map, id, BINN_FLOAT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_double(binn *map, int id, double value) {
  return binn_map_set(map, id, BINN_FLOAT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_bool(binn *map, int id, BOOL value) {
  return binn_map_set(map, id, BINN_BOOL, &value, 0);
}
ALWAYS_INLINE BOOL binn_map_set_null(binn *map, int id) {
  return binn_map_set(map, id, BINN_NULL, NULL, 0);
}
ALWAYS_INLINE BOOL binn_map_set_str(binn *map, int id, char *str) {
  return binn_map_set(map, id, BINN_STRING, str, 0);
}
ALWAYS_INLINE BOOL binn_map_set_blob(binn *map, int id, void *ptr, int size) {
  return binn_map_set(map, id, BINN_BLOB, ptr, size);
}
ALWAYS_INLINE BOOL binn_map_set_list(binn *map, int id, void *list) {
  return binn_map_set(map, id, BINN_LIST, binn_ptr(list), binn_size(list));
}
ALWAYS_INLINE BOOL binn_map_set_map(binn *map, int id, void *map2) {
  return binn_map_set(map, id, BINN_MAP, binn_ptr(map2), binn_size(map2));
}
ALWAYS_INLINE BOOL binn_map_set_object(binn *map, int id, void *obj) {
  return binn_map_set(map, id, BINN_OBJECT, binn_ptr(obj), binn_size(obj));
}
ALWAYS_INLINE BOOL binn_map_set_value(binn *map, int id, binn *value) {
  return binn_map_set(map, id, value->type, binn_ptr(value), binn_size(value));
}

/*************************************************************************************/

ALWAYS_INLINE BOOL binn_object_set_int8(binn *obj, const char *key, signed char value) {
  return binn_object_set(obj, key, BINN_INT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_int16(binn *obj, const char *key, short value) {
  return binn_object_set(obj, key, BINN_INT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_int32(binn *obj, const char *key, int value) {
  return binn_object_set(obj, key, BINN_INT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_int64(binn *obj, const char *key, int64 value) {
  return binn_object_set(obj, key, BINN_INT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_uint8(binn *obj, const char *key, unsigned char value) {
  return binn_object_set(obj, key, BINN_UINT8, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_uint16(binn *obj, const char *key, unsigned short value) {
  return binn_object_set(obj, key, BINN_UINT16, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_uint32(binn *obj, const char *key, unsigned int value) {
  return binn_object_set(obj, key, BINN_UINT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_uint64(binn *obj, const char *key, uint64 value) {
  return binn_object_set(obj, key, BINN_UINT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_float(binn *obj, const char *key, float value) {
  return binn_object_set(obj, key, BINN_FLOAT32, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_double(binn *obj, const char *key, double value) {
  return binn_object_set(obj, key, BINN_FLOAT64, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_bool(binn *obj, const char *key, BOOL value) {
  return binn_object_set(obj, key, BINN_BOOL, &value, 0);
}
ALWAYS_INLINE BOOL binn_object_set_null(binn *obj, const char *key) {
  return binn_object_set(obj, key, BINN_NULL, NULL, 0);
}
ALWAYS_INLINE BOOL binn_object_set_str(binn *obj, const char *key, char *str) {
  return binn_object_set(obj, key, BINN_STRING, str, 0);
}
ALWAYS_INLINE BOOL binn_object_set_blob(binn *obj, const char *key, void *ptr, int size) {
  return binn_object_set(obj, key, BINN_BLOB, ptr, size);
}
ALWAYS_INLINE BOOL binn_object_set_list(binn *obj, const char *key, void *list) {
  return binn_object_set(obj, key, BINN_LIST, binn_ptr(list), binn_size(list));
}
ALWAYS_INLINE BOOL binn_object_set_map(binn *obj, const char *key, void *map) {
  return binn_object_set(obj, key, BINN_MAP, binn_ptr(map), binn_size(map));
}
ALWAYS_INLINE BOOL binn_object_set_object(binn *obj, const char *key, void *obj2) {
  return binn_object_set(obj, key, BINN_OBJECT, binn_ptr(obj2), binn_size(obj2));
}
ALWAYS_INLINE BOOL binn_object_set_value(binn *obj, const char *key, binn *value) {
  return binn_object_set(obj, key, value->type, binn_ptr(value), binn_size(value));
}

/*************************************************************************************/
/*** GET FUNCTIONS *******************************************************************/
/*************************************************************************************/

ALWAYS_INLINE BOOL binn_list_get_int8(const void *list, int pos, signed char *pvalue) {
  return binn_list_get(list, pos, BINN_INT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_int16(const void *list, int pos, short *pvalue) {
  return binn_list_get(list, pos, BINN_INT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_int32(const void *list, int pos, int *pvalue) {
  return binn_list_get(list, pos, BINN_INT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_int64(const void *list, int pos, int64 *pvalue) {
  return binn_list_get(list, pos, BINN_INT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_uint8(const void *list, int pos, unsigned char *pvalue) {
  return binn_list_get(list, pos, BINN_UINT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_uint16(const void *list, int pos, unsigned short *pvalue) {
  return binn_list_get(list, pos, BINN_UINT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_uint32(const void *list, int pos, unsigned int *pvalue) {
  return binn_list_get(list, pos, BINN_UINT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_uint64(const void *list, int pos, uint64 *pvalue) {
  return binn_list_get(list, pos, BINN_UINT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_float(const void *list, int pos, float *pvalue) {
  return binn_list_get(list, pos, BINN_FLOAT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_double(const void *list, int pos, double *pvalue) {
  return binn_list_get(list, pos, BINN_FLOAT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_bool(const void *list, int pos, BOOL *pvalue) {
  return binn_list_get(list, pos, BINN_BOOL, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_str(const void *list, int pos, char **pvalue) {
  return binn_list_get(list, pos, BINN_STRING, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_blob(const void *list, int pos, void **pvalue, int *psize) {
  return binn_list_get(list, pos, BINN_BLOB, pvalue, psize);
}
ALWAYS_INLINE BOOL binn_list_get_list(const void *list, int pos, void **pvalue) {
  return binn_list_get(list, pos, BINN_LIST, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_map(const void *list, int pos, void **pvalue) {
  return binn_list_get(list, pos, BINN_MAP, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_list_get_object(const void *list, int pos, void **pvalue) {
  return binn_list_get(list, pos, BINN_OBJECT, pvalue, NULL);
}

/***************************************************************************/

ALWAYS_INLINE BOOL binn_map_get_int8(const void *map, int id, signed char *pvalue) {
  return binn_map_get(map, id, BINN_INT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_int16(const void *map, int id, short *pvalue) {
  return binn_map_get(map, id, BINN_INT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_int32(const void *map, int id, int *pvalue) {
  return binn_map_get(map, id, BINN_INT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_int64(const void *map, int id, int64 *pvalue) {
  return binn_map_get(map, id, BINN_INT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_uint8(const void *map, int id, unsigned char *pvalue) {
  return binn_map_get(map, id, BINN_UINT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_uint16(const void *map, int id, unsigned short *pvalue) {
  return binn_map_get(map, id, BINN_UINT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_uint32(const void *map, int id, unsigned int *pvalue) {
  return binn_map_get(map, id, BINN_UINT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_uint64(const void *map, int id, uint64 *pvalue) {
  return binn_map_get(map, id, BINN_UINT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_float(const void *map, int id, float *pvalue) {
  return binn_map_get(map, id, BINN_FLOAT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_double(const void *map, int id, double *pvalue) {
  return binn_map_get(map, id, BINN_FLOAT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_bool(const void *map, int id, BOOL *pvalue) {
  return binn_map_get(map, id, BINN_BOOL, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_str(const void *map, int id, char **pvalue) {
  return binn_map_get(map, id, BINN_STRING, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_blob(const void *map, int id, void **pvalue, int *psize) {
  return binn_map_get(map, id, BINN_BLOB, pvalue, psize);
}
ALWAYS_INLINE BOOL binn_map_get_list(const void *map, int id, void **pvalue) {
  return binn_map_get(map, id, BINN_LIST, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_map(const void *map, int id, void **pvalue) {
  return binn_map_get(map, id, BINN_MAP, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_map_get_object(const void *map, int id, void **pvalue) {
  return binn_map_get(map, id, BINN_OBJECT, pvalue, NULL);
}

/***************************************************************************/

// usage:
//   if (binn_object_get_int32(obj, "key", &value) == FALSE) xxx;

ALWAYS_INLINE BOOL binn_object_get_int8(const void *obj, const char *key, signed char *pvalue) {
  return binn_object_get(obj, key, BINN_INT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_int16(const void *obj, const char *key, short *pvalue) {
  return binn_object_get(obj, key, BINN_INT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_int32(const void *obj, const char *key, int *pvalue) {
  return binn_object_get(obj, key, BINN_INT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_int64(const void *obj, const char *key, int64 *pvalue) {
  return binn_object_get(obj, key, BINN_INT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_uint8(const void *obj, const char *key, unsigned char *pvalue) {
  return binn_object_get(obj, key, BINN_UINT8, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_uint16(const void *obj, const char *key, unsigned short *pvalue) {
  return binn_object_get(obj, key, BINN_UINT16, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_uint32(const void *obj, const char *key, unsigned int *pvalue) {
  return binn_object_get(obj, key, BINN_UINT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_uint64(const void *obj, const char *key, uint64 *pvalue) {
  return binn_object_get(obj, key, BINN_UINT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_float(const void *obj, const char *key, float *pvalue) {
  return binn_object_get(obj, key, BINN_FLOAT32, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_double(const void *obj, const char *key, double *pvalue) {
  return binn_object_get(obj, key, BINN_FLOAT64, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_bool(const void *obj, const char *key, BOOL *pvalue) {
  return binn_object_get(obj, key, BINN_BOOL, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_str(const void *obj, const char *key, char **pvalue) {
  return binn_object_get(obj, key, BINN_STRING, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_blob(const void *obj, const char *key, void **pvalue, int *psize) {
  return binn_object_get(obj, key, BINN_BLOB, pvalue, psize);
}
ALWAYS_INLINE BOOL binn_object_get_list(const void *obj, const char *key, void **pvalue) {
  return binn_object_get(obj, key, BINN_LIST, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_map(const void *obj, const char *key, void **pvalue) {
  return binn_object_get(obj, key, BINN_MAP, pvalue, NULL);
}
ALWAYS_INLINE BOOL binn_object_get_object(const void *obj, const char *key, void **pvalue) {
  return binn_object_get(obj, key, BINN_OBJECT, pvalue, NULL);
}

/***************************************************************************/

BOOL   APIENTRY binn_get_int32(binn *value, int *pint);
BOOL   APIENTRY binn_get_int64(binn *value, int64 *pint);
BOOL   APIENTRY binn_get_double(binn *value, double *pfloat);
BOOL   APIENTRY binn_get_bool(binn *value, BOOL *pbool);
char * APIENTRY binn_get_str(binn *value);

// boolean string values:
// 1, true, yes, on
// 0, false, no, off

// boolean number values:
// !=0 [true]
// ==0 [false]


#ifdef __cplusplus
}
#endif

#endif //BINN_H

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
