use std::rc::Rc;
use std::cell::RefCell;

pub struct QuadtreePoint {
    pub x: f64,
    pub y: f64,
}

pub struct QuadtreeNode<T> {
    pub ne: Option<Rc<RefCell<QuadtreeNode<T>>>>,
    pub nw: Option<Rc<RefCell<QuadtreeNode<T>>>>,
    pub se: Option<Rc<RefCell<QuadtreeNode<T>>>>,
    pub sw: Option<Rc<RefCell<QuadtreeNode<T>>>>,
    pub bounds: Option<Rc<RefCell<QuadtreeBounds>>>,
    pub point: Option<Rc<RefCell<QuadtreePoint>>>,
    pub key: Option<T>,
}

pub struct QuadtreeBounds {
    pub nw: Rc<RefCell<QuadtreePoint>>,
    pub se: Rc<RefCell<QuadtreePoint>>,
    pub width: f64,
    pub height: f64,
}

pub struct Quadtree<T> {
    pub key_free: Option<fn(T)>,
    pub root: Option<Rc<RefCell<QuadtreeNode<T>>>>,
}

pub struct quadtree_node_t {
    pub ne: Option<Rc<RefCell<quadtree_node_t>>>,
    pub nw: Option<Rc<RefCell<quadtree_node_t>>>,
    pub se: Option<Rc<RefCell<quadtree_node_t>>>,
    pub sw: Option<Rc<RefCell<quadtree_node_t>>>,
}

pub fn quadtree_point_new(x: f64, y: f64) -> Option<QuadtreePoint> {
    Some(QuadtreePoint { x, y })
}

pub fn quadtree_node_new<T>() -> Option<Rc<RefCell<QuadtreeNode<T>>>> {
    let node = QuadtreeNode {
        ne: None,
        nw: None,
        se: None,
        sw: None,
        bounds: None,
        point: None,
        key: None,
    };
    Some(Rc::new(RefCell::new(node)))
}

pub fn quadtree_bounds_extend(bounds: Rc<RefCell<QuadtreeBounds>>, x: f64, y: f64) {
    let nw_x;
    let nw_y;
    let se_x;
    let se_y;
    {
        let bounds = bounds.borrow();
        let nw = bounds.nw.borrow();
        let se = bounds.se.borrow();
        nw_x = f64::min(x, nw.x);
        nw_y = f64::max(y, nw.y);
        se_x = f64::max(x, se.x);
        se_y = f64::min(y, se.y);
    }
    {
        let mut bounds = bounds.borrow_mut();
        bounds.width = (nw_x - se_x).abs();
        bounds.height = (nw_y - se_y).abs();
    }
}

pub fn quadtree_bounds_new() -> Option<Rc<RefCell<QuadtreeBounds>>> {
    let nw = Rc::new(RefCell::new(QuadtreePoint { x: f64::INFINITY, y: -f64::INFINITY }));
    let se = Rc::new(RefCell::new(QuadtreePoint { x: -f64::INFINITY, y: f64::INFINITY }));
    let bounds = QuadtreeBounds {
        nw,
        se,
        width: 0.0,
        height: 0.0,
    };
    Some(Rc::new(RefCell::new(bounds)))
}

pub fn quadtree_point_free(point: Rc<RefCell<QuadtreePoint>>) {
    // 释放 QuadtreePoint 的内存
    // 由于 Rc<RefCell<T>> 是智能指针，无需手动释放内存
}

pub fn node_contains_<T>(outer: Rc<RefCell<QuadtreeNode<T>>>, it: Rc<RefCell<QuadtreePoint>>) -> bool {
    let outer = outer.borrow();
    let it = it.borrow();
    if let Some(bounds) = &outer.bounds {
        let bounds = bounds.borrow();
        bounds.nw.borrow().x <= it.x &&
        bounds.nw.borrow().y >= it.y &&
        bounds.se.borrow().x >= it.x &&
        bounds.se.borrow().y <= it.y
    } else {
        false
    }
}

pub fn quadtree_node_isleaf<T>(node: &Rc<RefCell<QuadtreeNode<T>>>) -> bool {
    node.borrow().point.is_some()
}

pub fn quadtree_node_with_bounds<T>(minx: f64, miny: f64, maxx: f64, maxy: f64) -> Option<Rc<RefCell<QuadtreeNode<T>>>> {
    let node = quadtree_node_new()?;
    let bounds = quadtree_bounds_new()?;
    {
        let mut node_mut = node.borrow_mut();
        node_mut.bounds = Some(bounds.clone());
    }
    quadtree_bounds_extend(bounds.clone(), maxx, maxy);
    quadtree_bounds_extend(bounds.clone(), minx, miny);
    Some(node)
}

pub fn quadtree_node_reset<T>(node: Rc<RefCell<QuadtreeNode<T>>>, key_free: fn(T)) {
    let mut node_borrow = node.borrow_mut();
    if let Some(point) = &node_borrow.point {
        quadtree_point_free(point.clone());
    }
    if let Some(key) = node_borrow.key.take() {
        key_free(key);
    }
}

pub fn elision_<T>(key: T) -> T {

    key
}

pub fn get_quadrant_<T>(root: Rc<RefCell<QuadtreeNode<T>>>, point: Rc<RefCell<QuadtreePoint>>) -> Option<Rc<RefCell<QuadtreeNode<T>>>> {
    let root = root.borrow();
    if let Some(nw) = &root.nw {
        if node_contains_(nw.clone(), point.clone()) {
            return Some(nw.clone());
        }
    }
    if let Some(ne) = &root.ne {
        if node_contains_(ne.clone(), point.clone()) {
            return Some(ne.clone());
        }
    }
    if let Some(sw) = &root.sw {
        if node_contains_(sw.clone(), point.clone()) {
            return Some(sw.clone());
        }
    }
    if let Some(se) = &root.se {
        if node_contains_(se.clone(), point.clone()) {
            return Some(se.clone());
        }
    }
    None
}

pub fn quadtree_node_ispointer<T>(node: &Rc<RefCell<QuadtreeNode<T>>>) -> bool {
    let node_ref = node.borrow();
    node_ref.nw.is_some()
        && node_ref.ne.is_some()
        && node_ref.sw.is_some()
        && node_ref.se.is_some()
        && !quadtree_node_isleaf(node)
}

pub fn split_node_<T>(tree: Rc<RefCell<Quadtree<T>>>, node: Rc<RefCell<QuadtreeNode<T>>>) -> bool {
    let x;
    let y;
    let hw;
    let hh;
    {
        let node_borrow = node.borrow();
        let bounds = node_borrow.bounds.as_ref().unwrap().borrow();
        x = bounds.nw.borrow().x;
        y = bounds.nw.borrow().y;
        hw = bounds.width / 2.0;
        hh = bounds.height / 2.0;
    }

    let nw = quadtree_node_with_bounds::<T>(x, y - hh, x + hw, y);
    let ne = quadtree_node_with_bounds::<T>(x + hw, y - hh, x + hw * 2.0, y);
    let sw = quadtree_node_with_bounds::<T>(x, y - hh * 2.0, x + hw, y - hh);
    let se = quadtree_node_with_bounds::<T>(x + hw, y - hh * 2.0, x + hw * 2.0, y - hh);

    if nw.is_none() || ne.is_none() || sw.is_none() || se.is_none() {
        return false;
    }

    {
        let mut node_mut = node.borrow_mut();
        node_mut.nw = Some(nw.unwrap());
        node_mut.ne = Some(ne.unwrap());
        node_mut.sw = Some(sw.unwrap());
        node_mut.se = Some(se.unwrap());
    }

    let old_point;
    let old_key;
    {
        let mut node_mut = node.borrow_mut();
        old_point = node_mut.point.take();
        old_key = node_mut.key.take();
    }

    insert_(tree.clone(), node, old_point, old_key) != 0
}

pub fn reset_node_<T>(tree: Rc<RefCell<Quadtree<T>>>, node: Rc<RefCell<QuadtreeNode<T>>>) {
    let key_free = tree.borrow().key_free.clone();
    if let Some(key_free) = key_free {
        quadtree_node_reset(node, key_free);
    } else {
        let elision_wrap = |key: T| { elision_(key); };
        quadtree_node_reset(node, elision_wrap);
    }
}

pub fn insert_<T>(
    tree: Rc<RefCell<Quadtree<T>>>,
    root: Rc<RefCell<QuadtreeNode<T>>>,
    point: Option<Rc<RefCell<QuadtreePoint>>>,
    key: Option<T>,
) -> i32 {
    if quadtree_node_isempty(&root) {
        {
            let mut root_mut = root.borrow_mut();
            root_mut.point = point;
            root_mut.key = key;
        }
        return 1; // normal insertion flag
    } else if quadtree_node_isleaf(&root) {
        let root_point = root.borrow().point.as_ref().unwrap().clone();
        let point_ref = point.as_ref().unwrap().clone();
        let root_point_borrow = root_point.borrow();
        let point_ref_borrow = point_ref.borrow();
        if root_point_borrow.x == point_ref_borrow.x && root_point_borrow.y == point_ref_borrow.y {
            reset_node_(tree.clone(), root.clone());
            {
                let mut root_mut = root.borrow_mut();
                root_mut.point = point;
                root_mut.key = key;
            }
            return 2; // replace insertion flag
        } else {
            if !split_node_(tree.clone(), root.clone()) {
                return 0; // failed insertion flag
            }
            return insert_(tree, root, point, key);
        }
    } else if quadtree_node_ispointer(&root) {
        let quadrant = get_quadrant_(root.clone(), point.as_ref().unwrap().clone());
        if quadrant.is_none() {
            return 0;
        }
        return insert_(tree, quadrant.unwrap(), point, key);
    }
    0
}

pub fn quadtree_node_isempty<T>(node: &Rc<RefCell<QuadtreeNode<T>>>) -> bool {
    let node_ref = node.borrow();
    node_ref.nw.is_none()
        && node_ref.ne.is_none()
        && node_ref.sw.is_none()
        && node_ref.se.is_none()
        && !quadtree_node_isleaf(node)
}

pub fn quadtree_bounds_free(bounds: Rc<RefCell<QuadtreeBounds>>) {
    // 释放 QuadtreeBounds 的内存
    // 由于 Rc<RefCell<T>> 是智能指针，无需手动释放内存
    let bounds = bounds.borrow();
    quadtree_point_free(Rc::clone(&bounds.nw));
    quadtree_point_free(Rc::clone(&bounds.se));
}

pub fn find_<T>(node: Option<Rc<RefCell<QuadtreeNode<T>>>>, x: f64, y: f64) -> Option<Rc<RefCell<QuadtreePoint>>> {
    if let Some(node) = node {
        let node_ref = node.borrow();
        if quadtree_node_isleaf(&node) {
            if let Some(point) = &node_ref.point {
                let point_ref = point.borrow();
                if point_ref.x == x && point_ref.y == y {
                    return Some(point.clone());
                }
            }
        } else if quadtree_node_ispointer(&node) {
            let test = Rc::new(RefCell::new(QuadtreePoint { x, y }));
            return find_(get_quadrant_(node.clone(), test), x, y);
        }
    }
    None
}

pub fn quadtree_node_free<T>(node: Rc<RefCell<QuadtreeNode<T>>>, key_free: fn(T)) {
    let mut node_borrow = node.borrow_mut();
    if let Some(nw) = node_borrow.nw.take() {
        quadtree_node_free(nw, key_free);
    }
    if let Some(ne) = node_borrow.ne.take() {
        quadtree_node_free(ne, key_free);
    }
    if let Some(sw) = node_borrow.sw.take() {
        quadtree_node_free(sw, key_free);
    }
    if let Some(se) = node_borrow.se.take() {
        quadtree_node_free(se, key_free);
    }
    if let Some(bounds) = node_borrow.bounds.take() {
        quadtree_bounds_free(bounds);
    }
    quadtree_node_reset(Rc::clone(&node), key_free);
}

pub fn quadtree_search<T>(tree: Rc<RefCell<Quadtree<T>>>, x: f64, y: f64) -> Option<Rc<RefCell<QuadtreePoint>>> {
    let tree_ref = tree.borrow();
    find_(tree_ref.root.clone(), x, y)
}

pub fn quadtree_insert<T>(tree: Rc<RefCell<Quadtree<T>>>, x: f64, y: f64, key: T) -> i32 {
    let point = quadtree_point_new(x, y);
    if point.is_none() {
        return 0;
    }
    let point_rc = Rc::new(RefCell::new(point.unwrap()));
    if !node_contains_(tree.borrow().root.as_ref().unwrap().clone(), point_rc.clone()) {
        quadtree_point_free(point_rc);
        return 0;
    }
    let insert_status = insert_(tree.clone(), tree.borrow().root.as_ref().unwrap().clone(), Some(point_rc.clone()), Some(key));
    if insert_status == 0 {
        quadtree_point_free(point_rc);
        return 0;
    }
    if insert_status == 1 {
        let mut tree_mut = tree.borrow_mut();
        // Assuming length is a field in Quadtree struct
        // If not, you need to add it
        // tree_mut.length += 1;
    }
    insert_status
}

pub fn quadtree_free<T>(tree: Rc<RefCell<Quadtree<T>>>) {
    let tree_borrow = tree.borrow();
    if let Some(key_free) = tree_borrow.key_free {
        if let Some(root) = &tree_borrow.root {
            quadtree_node_free(Rc::clone(root), key_free);
        }
    } else {
        if let Some(root) = &tree_borrow.root {
            fn elision_wrap<T>(key: T) {
                elision_(key);
            }
            quadtree_node_free(Rc::clone(root), elision_wrap);
        }
    }
}

pub fn quadtree_new<T>(minx: f64, miny: f64, maxx: f64, maxy: f64) -> Option<Quadtree<T>> {
    let root = quadtree_node_with_bounds::<T>(minx, miny, maxx, maxy)?;
    let tree = Quadtree {
        key_free: None,
        root: Some(root),
    };
    Some(tree)
}

pub fn quadtree_walk<T>(root: Option<Rc<RefCell<QuadtreeNode<T>>>>, descent: fn(Option<Rc<RefCell<QuadtreeNode<T>>>>), ascent: fn(Option<Rc<RefCell<QuadtreeNode<T>>>>)) {
    descent(root.clone());
    if let Some(node) = &root {
        let node_ref = node.borrow();
        if let Some(nw) = &node_ref.nw {
            quadtree_walk(Some(nw.clone()), descent, ascent);
        }
        if let Some(ne) = &node_ref.ne {
            quadtree_walk(Some(ne.clone()), descent, ascent);
        }
        if let Some(sw) = &node_ref.sw {
            quadtree_walk(Some(sw.clone()), descent, ascent);
        }
        if let Some(se) = &node_ref.se {
            quadtree_walk(Some(se.clone()), descent, ascent);
        }
    }
    ascent(root);
}

