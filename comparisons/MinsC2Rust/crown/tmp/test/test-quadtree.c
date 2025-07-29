#include <assert.h>
#include <stdio.h>

#ifndef __QUADTREE_H__
#define __QUADTREE_H__

#ifdef __cplusplus
extern "C" {
#endif

#define QUADTREE_VERSION "0.0.1"

#include <stdlib.h>
#include <math.h>

typedef struct quadtree_point {
  double x;
  double y;
} quadtree_point_t;

typedef struct quadtree_bounds {
  quadtree_point_t *nw;
  quadtree_point_t *se;
  double width;
  double height;
} quadtree_bounds_t;

typedef struct quadtree_node {
  struct quadtree_node *ne;
  struct quadtree_node *nw;
  struct quadtree_node *se;
  struct quadtree_node *sw;
  quadtree_bounds_t *bounds;
  quadtree_point_t  *point;
  void *key;
} quadtree_node_t;

typedef struct quadtree {
  quadtree_node_t *root;
  void (*key_free)(void *key);
  unsigned int length;
} quadtree_t;


quadtree_point_t*
quadtree_point_new(double x, double y);

void
quadtree_point_free(quadtree_point_t *point);


quadtree_bounds_t*
quadtree_bounds_new(void);

void
quadtree_bounds_extend(quadtree_bounds_t *bounds, double x, double y);

void
quadtree_bounds_free(quadtree_bounds_t *bounds);


quadtree_node_t*
quadtree_node_new(void);

void
quadtree_node_free(quadtree_node_t *node, void (*value_free)(void*));

int
quadtree_node_ispointer(quadtree_node_t *node);

int
quadtree_node_isempty(quadtree_node_t *node);

int
quadtree_node_isleaf(quadtree_node_t *node);

void
quadtree_node_reset(quadtree_node_t* node, void (*key_free)(void*));

quadtree_node_t*
quadtree_node_with_bounds(double minx, double miny, double maxx, double maxy);

quadtree_t*
quadtree_new(double minx, double miny, double maxx, double maxy);

void
quadtree_free(quadtree_t *tree);

quadtree_point_t*
quadtree_search(quadtree_t *tree, double x, double y);

int
quadtree_insert(quadtree_t *tree, double x, double y, void *key);

void
quadtree_walk(quadtree_node_t *root,
              void (*descent)(quadtree_node_t *node),
              void (*ascent)(quadtree_node_t *node));


#ifdef __cplusplus
}
#endif

#endif

#define test(fn) \
        printf("\x1b[33m" # fn "\x1b[0m "); \
        test_##fn(); \
        puts("\x1b[1;32m✓\x1b[0m");



void descent(quadtree_node_t *node){}

void ascent(quadtree_node_t *node){}

static void
test_node(void){
  quadtree_node_t *node = quadtree_node_new();
  assert(!quadtree_node_isleaf(node));
  assert(quadtree_node_isempty(node));
  assert(!quadtree_node_ispointer(node));
  free(node);
}

static void
test_bounds(void){
  quadtree_bounds_t *bounds = quadtree_bounds_new();

  assert(bounds);
  assert(bounds->nw->x == INFINITY);
  assert(bounds->se->x == -INFINITY);

  quadtree_bounds_extend(bounds, 5.0, 5.0);
  assert(bounds->nw->x == 5.0);
  assert(bounds->se->x == 5.0);

  quadtree_bounds_extend(bounds, 10.0, 10.0);
  assert(bounds->nw->y == 10.0);
  assert(bounds->nw->y == 10.0);
  assert(bounds->se->y == 5.0);
  assert(bounds->se->y == 5.0);

  assert(bounds->width == 5.0);
  assert(bounds->height == 5.0);

  quadtree_bounds_free(bounds);
}


static void
test_tree(void){
  int val = 10;

  quadtree_t *tree = quadtree_new(1, 1, 10, 10);
  assert(tree->root->bounds->nw->x == 1);
  assert(tree->root->bounds->nw->y == 10.0);
  assert(tree->root->bounds->se->x == 10.0);
  assert(tree->root->bounds->se->y == 1);


  assert(quadtree_insert(tree, 0, 0, &val) == 0);
  assert(quadtree_insert(tree, 110.0, 110.0, &val) == 0);

  assert(quadtree_insert(tree, 8.0, 2.0, &val) != 0);
  assert(tree->length == 1);
  assert(tree->root->point->x == 8.0);
  assert(tree->root->point->y == 2.0);

  assert(quadtree_insert(tree, 0.0, 1.0, &val) == 0); /* failed insertion */
  assert(quadtree_insert(tree, 2.0, 3.0, &val) == 1); /* normal insertion */
  assert(quadtree_insert(tree, 2.0, 3.0, &val) == 2); /* replacement insertion */
  assert(tree->length == 2);
  assert(tree->root->point == NULL);

  assert(quadtree_insert(tree, 3.0, 1.1, &val) == 1);
  assert(tree->length == 3);
  assert(quadtree_search(tree, 3.0, 1.1)->x == 3.0);
  quadtree_walk(tree->root, ascent, descent);
  quadtree_free(tree);
}

static void
test_points(void){
  quadtree_point_t *point = quadtree_point_new(5, 6);
  assert(point->x == 5);
  assert(point->y == 6);
  quadtree_point_free(point);
}

int
main(int argc, const char *argv[]){
  test(tree);
  test(node);
  test(bounds);
  test(points);
}
