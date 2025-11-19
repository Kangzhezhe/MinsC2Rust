#include "quadtree.h"
#include <stdio.h>

/* private prototypes */
static int
split_node_(quadtree_t *tree, quadtree_node_t *node);

static int
insert_(quadtree_t* tree, quadtree_node_t *root, quadtree_point_t *point, void *key);

static int
node_contains_(quadtree_node_t *outer, quadtree_point_t *it);

static quadtree_node_t *
get_quadrant_(quadtree_node_t *root, quadtree_point_t *point);

/* private implementations */
static int
node_contains_(quadtree_node_t *outer, quadtree_point_t *it) {
  return outer->bounds != NULL
      && outer->bounds->nw->x <= it->x
      && outer->bounds->nw->y >= it->y
      && outer->bounds->se->x >= it->x
      && outer->bounds->se->y <= it->y;
}

static void
elision_(void* key){}

static void
reset_node_(quadtree_t *tree, quadtree_node_t *node){
  if(tree->key_free != NULL) {
    quadtree_node_reset(node, tree->key_free);
  } else {
    quadtree_node_reset(node, elision_);
  }
}

static quadtree_node_t *
get_quadrant_(quadtree_node_t *root, quadtree_point_t *point) {
  if(node_contains_(root->nw, point)) return root->nw;
  if(node_contains_(root->ne, point)) return root->ne;
  if(node_contains_(root->sw, point)) return root->sw;
  if(node_contains_(root->se, point)) return root->se;
  return NULL;
}


static int
split_node_(quadtree_t *tree, quadtree_node_t *node){
  quadtree_node_t *nw;
  quadtree_node_t *ne;
  quadtree_node_t *sw;
  quadtree_node_t *se;
  quadtree_point_t *old;
  void *key;

  double x  = node->bounds->nw->x;
  double y  = node->bounds->nw->y;
  double hw = node->bounds->width / 2;
  double hh = node->bounds->height / 2;

                                    //minx,   miny,       maxx,       maxy
  if(!(nw = quadtree_node_with_bounds(x,      y - hh,     x + hw,     y))) return 0;
  if(!(ne = quadtree_node_with_bounds(x + hw, y - hh,     x + hw * 2, y))) return 0;
  if(!(sw = quadtree_node_with_bounds(x,      y - hh * 2, x + hw,     y - hh))) return 0;
  if(!(se = quadtree_node_with_bounds(x + hw, y - hh * 2, x + hw * 2, y - hh))) return 0;

  node->nw = nw;
  node->ne = ne;
  node->sw = sw;
  node->se = se;

  old = node->point;
  key   = node->key;
  node->point = NULL;
  node->key   = NULL;

  return insert_(tree, node, old, key);
}


static quadtree_point_t*
find_(quadtree_node_t* node, double x, double y) {
  if(!node){
    return NULL;
  }
  if(quadtree_node_isleaf(node)){
    if(node->point->x == x && node->point->y == y)
      return node->point;
  } else if(quadtree_node_ispointer(node)){
    quadtree_point_t test;
    test.x = x;
    test.y = y;
    return find_(get_quadrant_(node, &test), x, y);
  }

  return NULL;
}

/* cribbed from the google closure library. */
static int
insert_(quadtree_t* tree, quadtree_node_t *root, quadtree_point_t *point, void *key) {
  if(quadtree_node_isempty(root)){
    root->point = point;
    root->key   = key;
    return 1; /* normal insertion flag */
  } else if(quadtree_node_isleaf(root)){
    if(root->point->x == point->x && root->point->y == point->y){
      reset_node_(tree, root);
      root->point = point;
      root->key   = key;
      return 2; /* replace insertion flag */
    } else {
      if(!split_node_(tree, root)){
        return 0; /* failed insertion flag */
      }
      return insert_(tree, root, point, key);
    }
  } else if(quadtree_node_ispointer(root)){
    quadtree_node_t* quadrant = get_quadrant_(root, point);
    return quadrant == NULL ? 0 : insert_(tree, quadrant, point, key);
  }
  return 0;
}


/* public */
quadtree_t*
quadtree_new(double minx, double miny, double maxx, double maxy) {
  quadtree_t *tree;
  if(!(tree = malloc(sizeof(*tree))))
    return NULL;
  tree->root = quadtree_node_with_bounds(minx, miny, maxx, maxy);
  if(!(tree->root))
    return NULL;
  tree->key_free = NULL;
  tree->length = 0;
  return tree;
}

int
quadtree_insert(quadtree_t *tree, double x, double y, void *key) {
  quadtree_point_t *point;
  int insert_status;

  if(!(point = quadtree_point_new(x, y))) return 0;
  if(!node_contains_(tree->root, point)){
    quadtree_point_free(point);
    return 0;
  }
  
  if(!(insert_status = insert_(tree, tree->root, point, key))){
    quadtree_point_free(point);
    return 0;
  }
  if (insert_status == 1) tree->length++;
  return insert_status;
}

quadtree_point_t*
quadtree_search(quadtree_t *tree, double x, double y) {
  return find_(tree->root, x, y);
}

void
quadtree_free(quadtree_t *tree) {
  if(tree->key_free != NULL) {
    quadtree_node_free(tree->root, tree->key_free);
  } else {
    quadtree_node_free(tree->root, elision_);
  }
  free(tree);
}

void
quadtree_walk(quadtree_node_t *root, void (*descent)(quadtree_node_t *node),
                                     void (*ascent)(quadtree_node_t *node)) {
  (*descent)(root);
  if(root->nw != NULL) quadtree_walk(root->nw, descent, ascent);
  if(root->ne != NULL) quadtree_walk(root->ne, descent, ascent);
  if(root->sw != NULL) quadtree_walk(root->sw, descent, ascent);
  if(root->se != NULL) quadtree_walk(root->se, descent, ascent);
  (*ascent)(root);
}




#ifndef INFINITY
  // no infinity defined? high chance we are compiling as c89
  #include <float.h>
  #include <math.h>
  #define INFINITY DBL_MAX
  #define fmin(a,b) (((a)<(b))?(a):(b))
  #define fmax(a,b) (((a)>(b))?(a):(b))
#endif



void
quadtree_bounds_extend(quadtree_bounds_t *bounds, double x, double y){
  bounds->nw->x = fmin(x, bounds->nw->x);
  bounds->nw->y = fmax(y, bounds->nw->y);
  bounds->se->x = fmax(x, bounds->se->x);
  bounds->se->y = fmin(y, bounds->se->y);
  bounds->width  = fabs(bounds->nw->x - bounds->se->x);
  bounds->height = fabs(bounds->nw->y - bounds->se->y);
}

void
quadtree_bounds_free(quadtree_bounds_t *bounds){
  quadtree_point_free(bounds->nw);
  quadtree_point_free(bounds->se);
  free(bounds);
}


quadtree_bounds_t*
quadtree_bounds_new(void){
  quadtree_bounds_t *bounds;
  if((bounds = malloc(sizeof(*bounds))) == NULL)
    return NULL;
  bounds->nw     = quadtree_point_new(INFINITY, -INFINITY);
  bounds->se     = quadtree_point_new(-INFINITY, INFINITY);
  bounds->width  = 0;
  bounds->height = 0;
  return bounds;
}



/* helpers */

int
quadtree_node_ispointer(quadtree_node_t *node){
  return node->nw != NULL
      && node->ne != NULL
      && node->sw != NULL
      && node->se != NULL
      && !quadtree_node_isleaf(node);
}

int
quadtree_node_isempty(quadtree_node_t *node){
  return node->nw == NULL
      && node->ne == NULL
      && node->sw == NULL
      && node->se == NULL
      && !quadtree_node_isleaf(node);
}

int
quadtree_node_isleaf(quadtree_node_t *node){
  return node->point != NULL;
}

void
quadtree_node_reset(quadtree_node_t* node, void (*key_free)(void*)) {
  quadtree_point_free(node->point);
  (*key_free)(node->key);
}

/* api */
quadtree_node_t*
quadtree_node_new(void) {
  quadtree_node_t *node;
  if(!(node = malloc(sizeof(*node))))
    return NULL;
  node->ne     = NULL;
  node->nw     = NULL;
  node->se     = NULL;
  node->sw     = NULL;
  node->point  = NULL;
  node->bounds = NULL;
  node->key    = NULL;
  return node;
}

quadtree_node_t*
quadtree_node_with_bounds(double minx, double miny, double maxx, double maxy){
  quadtree_node_t* node;
  if(!(node = quadtree_node_new())) return NULL;
  if(!(node->bounds = quadtree_bounds_new())) return NULL;
  quadtree_bounds_extend(node->bounds, maxx, maxy);
  quadtree_bounds_extend(node->bounds, minx, miny);
  return node;
}

void
quadtree_node_free(quadtree_node_t* node, void (*key_free)(void*)) {
  if(node->nw != NULL) quadtree_node_free(node->nw, key_free);
  if(node->ne != NULL) quadtree_node_free(node->ne, key_free);
  if(node->sw != NULL) quadtree_node_free(node->sw, key_free);
  if(node->se != NULL) quadtree_node_free(node->se, key_free);

  quadtree_bounds_free(node->bounds);
  quadtree_node_reset(node, key_free);
  free(node);
}


quadtree_point_t*
quadtree_point_new(double x, double y) {
  quadtree_point_t* point;
  if(!(point = malloc(sizeof(*point))))
    return NULL;
  point->x = x;
  point->y = y;
  return point;
}

void
quadtree_point_free(quadtree_point_t *point){
  free(point);
}
