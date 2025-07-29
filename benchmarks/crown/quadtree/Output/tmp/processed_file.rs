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