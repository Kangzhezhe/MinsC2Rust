use ntest::timeout;
use std::cell::RefCell;
use std::rc::Rc;
use test_project::quadtree::{
    elision_, find_, get_quadrant_, insert_, node_contains_, quadtree_bounds_extend,
    quadtree_bounds_free, quadtree_bounds_new, quadtree_free, quadtree_insert, quadtree_new,
    quadtree_node_free, quadtree_node_isempty, quadtree_node_isleaf, quadtree_node_ispointer,
    quadtree_node_new, quadtree_node_reset, quadtree_node_t, quadtree_node_with_bounds,
    quadtree_point_free, quadtree_point_new, quadtree_search, quadtree_walk, reset_node_,
    split_node_, QuadtreeNode,
};
pub fn ascent<T>(node: Rc<RefCell<QuadtreeNode<T>>>) {

    // Function implementation
}

pub fn descent(node: Rc<RefCell<quadtree_node_t>>) {
    let mut node = node.borrow_mut();
    if let Some(ne) = &node.ne {
        descent(Rc::clone(ne));
    }
    if let Some(nw) = &node.nw {
        descent(Rc::clone(nw));
    }
    if let Some(se) = &node.se {
        descent(Rc::clone(se));
    }
    if let Some(sw) = &node.sw {
        descent(Rc::clone(sw));
    }
}

#[test]
#[timeout(60000)]
pub fn test_bounds() {
    let bounds = quadtree_bounds_new().unwrap();
    {
        let bounds_ref = bounds.borrow();
        let nw = bounds_ref.nw.borrow();
        let se = bounds_ref.se.borrow();
        assert_eq!(nw.x, f64::INFINITY);
        assert_eq!(se.x, -f64::INFINITY);
    }

    quadtree_bounds_extend(Rc::clone(&bounds), 5.0, 5.0);
    {
        let bounds_ref = bounds.borrow();
        let nw = bounds_ref.nw.borrow();
        let se = bounds_ref.se.borrow();
        assert_eq!(nw.x, 5.0);
        assert_eq!(se.x, 5.0);
    }

    quadtree_bounds_extend(Rc::clone(&bounds), 10.0, 10.0);
    {
        let bounds_ref = bounds.borrow();
        let nw = bounds_ref.nw.borrow();
        let se = bounds_ref.se.borrow();
        assert_eq!(nw.y, 10.0);
        assert_eq!(se.y, 5.0);
        assert_eq!(bounds_ref.width, 5.0);
        assert_eq!(bounds_ref.height, 5.0);
    }

    quadtree_bounds_free(bounds);
}

#[test]
#[timeout(60000)]
pub fn test_points() {
    let point = quadtree_point_new(5.0, 6.0);
    assert!(point.as_ref().unwrap().x == 5.0);
    assert!(point.as_ref().unwrap().y == 6.0);
    quadtree_point_free(Rc::new(RefCell::new(point.unwrap())));
}

#[test]
#[timeout(60000)]
pub fn test_node() {
    let node = quadtree_node_new::<i32>();
    let node_ref = node.as_ref().unwrap();
    assert!(!quadtree_node_isleaf(node_ref));
    assert!(quadtree_node_isempty(node_ref));
    assert!(!quadtree_node_ispointer(node_ref));
}
