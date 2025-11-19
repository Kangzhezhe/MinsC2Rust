use ::libc;
extern "C" {
    fn malloc(_: libc::c_ulong) -> *mut libc::c_void;
    fn free(_: *mut libc::c_void);
    fn fabs(_: libc::c_double) -> libc::c_double;
    fn fmax(_: libc::c_double, _: libc::c_double) -> libc::c_double;
    fn fmin(_: libc::c_double, _: libc::c_double) -> libc::c_double;
}
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_point {
    pub x: libc::c_double,
    pub y: libc::c_double,
}
pub type quadtree_point_t = quadtree_point;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_bounds {
    pub nw: *mut quadtree_point_t,
    pub se: *mut quadtree_point_t,
    pub width: libc::c_double,
    pub height: libc::c_double,
}
pub type quadtree_bounds_t = quadtree_bounds;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree_node {
    pub ne: *mut quadtree_node,
    pub nw: *mut quadtree_node,
    pub se: *mut quadtree_node,
    pub sw: *mut quadtree_node,
    pub bounds: *mut quadtree_bounds_t,
    pub point: *mut quadtree_point_t,
    pub key: *mut libc::c_void,
}
pub type quadtree_node_t = quadtree_node;
#[derive(Copy, Clone)]
#[repr(C)]
pub struct quadtree {
    pub root: *mut quadtree_node_t,
    pub key_free: Option::<unsafe extern "C" fn(*mut libc::c_void) -> ()>,
    pub length: libc::c_uint,
}
pub type quadtree_t = quadtree;
unsafe extern "C" fn node_contains_(
    mut outer: *mut quadtree_node_t,
    mut it: *mut quadtree_point_t,
) -> libc::c_int {
    return (!((*outer).bounds).is_null() && (*(*(*outer).bounds).nw).x <= (*it).x
        && (*(*(*outer).bounds).nw).y >= (*it).y && (*(*(*outer).bounds).se).x >= (*it).x
        && (*(*(*outer).bounds).se).y <= (*it).y) as libc::c_int;
}
unsafe extern "C" fn elision_(mut key: *mut libc::c_void) {}
unsafe extern "C" fn reset_node_(
    mut tree: *mut quadtree_t,
    mut node: *mut quadtree_node_t,
) {
    if ((*tree).key_free).is_some() {
        quadtree_node_reset(node, (*tree).key_free);
    } else {
        quadtree_node_reset(
            node,
            Some(elision_ as unsafe extern "C" fn(*mut libc::c_void) -> ()),
        );
    };
}
unsafe extern "C" fn get_quadrant_(
    mut root: *mut quadtree_node_t,
    mut point: *mut quadtree_point_t,
) -> *mut quadtree_node_t {
    if node_contains_((*root).nw, point) != 0 {
        return (*root).nw;
    }
    if node_contains_((*root).ne, point) != 0 {
        return (*root).ne;
    }
    if node_contains_((*root).sw, point) != 0 {
        return (*root).sw;
    }
    if node_contains_((*root).se, point) != 0 {
        return (*root).se;
    }
    return 0 as *mut quadtree_node_t;
}
unsafe extern "C" fn split_node_(
    mut tree: *mut quadtree_t,
    mut node: *mut quadtree_node_t,
) -> libc::c_int {
    let mut nw: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    let mut ne: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    let mut sw: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    let mut se: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    let mut old: *mut quadtree_point_t = 0 as *mut quadtree_point_t;
    let mut key: *mut libc::c_void = 0 as *mut libc::c_void;
    let mut x: libc::c_double = (*(*(*node).bounds).nw).x;
    let mut y: libc::c_double = (*(*(*node).bounds).nw).y;
    let mut hw: libc::c_double = (*(*node).bounds).width
        / 2 as libc::c_int as libc::c_double;
    let mut hh: libc::c_double = (*(*node).bounds).height
        / 2 as libc::c_int as libc::c_double;
    nw = quadtree_node_with_bounds(x, y - hh, x + hw, y);
    if nw.is_null() {
        return 0 as libc::c_int;
    }
    ne = quadtree_node_with_bounds(
        x + hw,
        y - hh,
        x + hw * 2 as libc::c_int as libc::c_double,
        y,
    );
    if ne.is_null() {
        return 0 as libc::c_int;
    }
    sw = quadtree_node_with_bounds(
        x,
        y - hh * 2 as libc::c_int as libc::c_double,
        x + hw,
        y - hh,
    );
    if sw.is_null() {
        return 0 as libc::c_int;
    }
    se = quadtree_node_with_bounds(
        x + hw,
        y - hh * 2 as libc::c_int as libc::c_double,
        x + hw * 2 as libc::c_int as libc::c_double,
        y - hh,
    );
    if se.is_null() {
        return 0 as libc::c_int;
    }
    (*node).nw = nw;
    (*node).ne = ne;
    (*node).sw = sw;
    (*node).se = se;
    old = (*node).point;
    key = (*node).key;
    (*node).point = 0 as *mut quadtree_point_t;
    (*node).key = 0 as *mut libc::c_void;
    return insert_(tree, node, old, key);
}
unsafe extern "C" fn find_(
    mut node: *mut quadtree_node_t,
    mut x: libc::c_double,
    mut y: libc::c_double,
) -> *mut quadtree_point_t {
    if node.is_null() {
        return 0 as *mut quadtree_point_t;
    }
    if quadtree_node_isleaf(node) != 0 {
        if (*(*node).point).x == x && (*(*node).point).y == y {
            return (*node).point;
        }
    } else if quadtree_node_ispointer(node) != 0 {
        let mut test: quadtree_point_t = quadtree_point { x: 0., y: 0. };
        test.x = x;
        test.y = y;
        return find_(get_quadrant_(node, &mut test), x, y);
    }
    return 0 as *mut quadtree_point_t;
}
unsafe extern "C" fn insert_(
    mut tree: *mut quadtree_t,
    mut root: *mut quadtree_node_t,
    mut point: *mut quadtree_point_t,
    mut key: *mut libc::c_void,
) -> libc::c_int {
    if quadtree_node_isempty(root) != 0 {
        (*root).point = point;
        (*root).key = key;
        return 1 as libc::c_int;
    } else if quadtree_node_isleaf(root) != 0 {
        if (*(*root).point).x == (*point).x && (*(*root).point).y == (*point).y {
            reset_node_(tree, root);
            (*root).point = point;
            (*root).key = key;
            return 2 as libc::c_int;
        } else {
            if split_node_(tree, root) == 0 {
                return 0 as libc::c_int;
            }
            return insert_(tree, root, point, key);
        }
    } else if quadtree_node_ispointer(root) != 0 {
        let mut quadrant: *mut quadtree_node_t = get_quadrant_(root, point);
        return if quadrant.is_null() {
            0 as libc::c_int
        } else {
            insert_(tree, quadrant, point, key)
        };
    }
    return 0 as libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_new(
    mut minx: libc::c_double,
    mut miny: libc::c_double,
    mut maxx: libc::c_double,
    mut maxy: libc::c_double,
) -> *mut quadtree_t {
    let mut tree: *mut quadtree_t = 0 as *mut quadtree_t;
    tree = malloc(::core::mem::size_of::<quadtree_t>() as libc::c_ulong)
        as *mut quadtree_t;
    if tree.is_null() {
        return 0 as *mut quadtree_t;
    }
    (*tree).root = quadtree_node_with_bounds(minx, miny, maxx, maxy);
    if ((*tree).root).is_null() {
        return 0 as *mut quadtree_t;
    }
    (*tree).key_free = None;
    (*tree).length = 0 as libc::c_int as libc::c_uint;
    return tree;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_insert(
    mut tree: *mut quadtree_t,
    mut x: libc::c_double,
    mut y: libc::c_double,
    mut key: *mut libc::c_void,
) -> libc::c_int {
    let mut point: *mut quadtree_point_t = 0 as *mut quadtree_point_t;
    let mut insert_status: libc::c_int = 0;
    point = quadtree_point_new(x, y);
    if point.is_null() {
        return 0 as libc::c_int;
    }
    if node_contains_((*tree).root, point) == 0 {
        quadtree_point_free(point);
        return 0 as libc::c_int;
    }
    insert_status = insert_(tree, (*tree).root, point, key);
    if insert_status == 0 {
        quadtree_point_free(point);
        return 0 as libc::c_int;
    }
    if insert_status == 1 as libc::c_int {
        (*tree).length = ((*tree).length).wrapping_add(1);
        (*tree).length;
    }
    return insert_status;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_search(
    mut tree: *mut quadtree_t,
    mut x: libc::c_double,
    mut y: libc::c_double,
) -> *mut quadtree_point_t {
    return find_((*tree).root, x, y);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_free(mut tree: *mut quadtree_t) {
    if ((*tree).key_free).is_some() {
        quadtree_node_free((*tree).root, (*tree).key_free);
    } else {
        quadtree_node_free(
            (*tree).root,
            Some(elision_ as unsafe extern "C" fn(*mut libc::c_void) -> ()),
        );
    }
    free(tree as *mut libc::c_void);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_walk(
    mut root: *mut quadtree_node_t,
    mut descent: Option::<unsafe extern "C" fn(*mut quadtree_node_t) -> ()>,
    mut ascent: Option::<unsafe extern "C" fn(*mut quadtree_node_t) -> ()>,
) {
    (Some(descent.expect("non-null function pointer")))
        .expect("non-null function pointer")(root);
    if !((*root).nw).is_null() {
        quadtree_walk((*root).nw, descent, ascent);
    }
    if !((*root).ne).is_null() {
        quadtree_walk((*root).ne, descent, ascent);
    }
    if !((*root).sw).is_null() {
        quadtree_walk((*root).sw, descent, ascent);
    }
    if !((*root).se).is_null() {
        quadtree_walk((*root).se, descent, ascent);
    }
    (Some(ascent.expect("non-null function pointer")))
        .expect("non-null function pointer")(root);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_bounds_extend(
    mut bounds: *mut quadtree_bounds_t,
    mut x: libc::c_double,
    mut y: libc::c_double,
) {
    (*(*bounds).nw).x = fmin(x, (*(*bounds).nw).x);
    (*(*bounds).nw).y = fmax(y, (*(*bounds).nw).y);
    (*(*bounds).se).x = fmax(x, (*(*bounds).se).x);
    (*(*bounds).se).y = fmin(y, (*(*bounds).se).y);
    (*bounds).width = fabs((*(*bounds).nw).x - (*(*bounds).se).x);
    (*bounds).height = fabs((*(*bounds).nw).y - (*(*bounds).se).y);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_bounds_free(mut bounds: *mut quadtree_bounds_t) {
    quadtree_point_free((*bounds).nw);
    quadtree_point_free((*bounds).se);
    free(bounds as *mut libc::c_void);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_bounds_new() -> *mut quadtree_bounds_t {
    let mut bounds: *mut quadtree_bounds_t = 0 as *mut quadtree_bounds_t;
    bounds = malloc(::core::mem::size_of::<quadtree_bounds_t>() as libc::c_ulong)
        as *mut quadtree_bounds_t;
    if bounds.is_null() {
        return 0 as *mut quadtree_bounds_t;
    }
    (*bounds)
        .nw = quadtree_point_new(
        ::core::f32::INFINITY as libc::c_double,
        -::core::f32::INFINITY as libc::c_double,
    );
    (*bounds)
        .se = quadtree_point_new(
        -::core::f32::INFINITY as libc::c_double,
        ::core::f32::INFINITY as libc::c_double,
    );
    (*bounds).width = 0 as libc::c_int as libc::c_double;
    (*bounds).height = 0 as libc::c_int as libc::c_double;
    return bounds;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_ispointer(
    mut node: *mut quadtree_node_t,
) -> libc::c_int {
    return (!((*node).nw).is_null() && !((*node).ne).is_null() && !((*node).sw).is_null()
        && !((*node).se).is_null() && quadtree_node_isleaf(node) == 0) as libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_isempty(
    mut node: *mut quadtree_node_t,
) -> libc::c_int {
    return (((*node).nw).is_null() && ((*node).ne).is_null() && ((*node).sw).is_null()
        && ((*node).se).is_null() && quadtree_node_isleaf(node) == 0) as libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_isleaf(
    mut node: *mut quadtree_node_t,
) -> libc::c_int {
    return ((*node).point != 0 as *mut libc::c_void as *mut quadtree_point_t)
        as libc::c_int;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_reset(
    mut node: *mut quadtree_node_t,
    mut key_free: Option::<unsafe extern "C" fn(*mut libc::c_void) -> ()>,
) {
    quadtree_point_free((*node).point);
    (Some(key_free.expect("non-null function pointer")))
        .expect("non-null function pointer")((*node).key);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_new() -> *mut quadtree_node_t {
    let mut node: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    node = malloc(::core::mem::size_of::<quadtree_node_t>() as libc::c_ulong)
        as *mut quadtree_node_t;
    if node.is_null() {
        return 0 as *mut quadtree_node_t;
    }
    (*node).ne = 0 as *mut quadtree_node;
    (*node).nw = 0 as *mut quadtree_node;
    (*node).se = 0 as *mut quadtree_node;
    (*node).sw = 0 as *mut quadtree_node;
    (*node).point = 0 as *mut quadtree_point_t;
    (*node).bounds = 0 as *mut quadtree_bounds_t;
    (*node).key = 0 as *mut libc::c_void;
    return node;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_with_bounds(
    mut minx: libc::c_double,
    mut miny: libc::c_double,
    mut maxx: libc::c_double,
    mut maxy: libc::c_double,
) -> *mut quadtree_node_t {
    let mut node: *mut quadtree_node_t = 0 as *mut quadtree_node_t;
    node = quadtree_node_new();
    if node.is_null() {
        return 0 as *mut quadtree_node_t;
    }
    (*node).bounds = quadtree_bounds_new();
    if ((*node).bounds).is_null() {
        return 0 as *mut quadtree_node_t;
    }
    quadtree_bounds_extend((*node).bounds, maxx, maxy);
    quadtree_bounds_extend((*node).bounds, minx, miny);
    return node;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_node_free(
    mut node: *mut quadtree_node_t,
    mut key_free: Option::<unsafe extern "C" fn(*mut libc::c_void) -> ()>,
) {
    if !((*node).nw).is_null() {
        quadtree_node_free((*node).nw, key_free);
    }
    if !((*node).ne).is_null() {
        quadtree_node_free((*node).ne, key_free);
    }
    if !((*node).sw).is_null() {
        quadtree_node_free((*node).sw, key_free);
    }
    if !((*node).se).is_null() {
        quadtree_node_free((*node).se, key_free);
    }
    quadtree_bounds_free((*node).bounds);
    quadtree_node_reset(node, key_free);
    free(node as *mut libc::c_void);
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_point_new(
    mut x: libc::c_double,
    mut y: libc::c_double,
) -> *mut quadtree_point_t {
    let mut point: *mut quadtree_point_t = 0 as *mut quadtree_point_t;
    point = malloc(::core::mem::size_of::<quadtree_point_t>() as libc::c_ulong)
        as *mut quadtree_point_t;
    if point.is_null() {
        return 0 as *mut quadtree_point_t;
    }
    (*point).x = x;
    (*point).y = y;
    return point;
}
#[no_mangle]
pub unsafe extern "C" fn quadtree_point_free(mut point: *mut quadtree_point_t) {
    free(point as *mut libc::c_void);
}
