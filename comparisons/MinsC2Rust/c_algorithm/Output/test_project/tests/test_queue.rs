use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Once, Mutex};

// 定义全局计数器
static ASSERT_COUNT: AtomicUsize = AtomicUsize::new(0);

// 初始化一次性的打印钩子
static INIT: Once = Once::new();
static PRINT_ON_EXIT: Mutex<Option<PrintOnExit>> = Mutex::new(None);

fn initialize() {
    INIT.call_once(|| {
        // 注册退出时打印的钩子
        *PRINT_ON_EXIT.lock().unwrap() = Some(PrintOnExit);
        // 在 panic 时也打印统计信息
        std::panic::set_hook(Box::new(|_| {
            print_assert_counts();
        }));
    });
}

// 打印断言统计信息
fn print_assert_counts() {
    println!(
        "Total assertions made: {}",
        ASSERT_COUNT.load(Ordering::Relaxed)
    );
}

// 自定义退出打印器
struct PrintOnExit;

impl Drop for PrintOnExit {
    fn drop(&mut self) {
        print_assert_counts();
    }
}

// 自定义 assert! 宏
macro_rules! assert {
    ($cond:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        if !$cond {
            panic!("assertion failed: {}", stringify!($cond));
        }
        print_assert_counts();
    }};
    ($cond:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        if !$cond {
            panic!($($arg)+);
        }
        print_assert_counts();
    }};
}

// 自定义 assert_eq! 宏
macro_rules! assert_eq {
    ($left:expr, $right:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left != *right {
            panic!(
                "assertion failed: (left == right)\n  left: {:?},\n right: {:?}",
                left, right
            );
        }
        print_assert_counts();
    }};
    ($left:expr, $right:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left != *right {
            panic!(
                "assertion failed: (left == right)\n  left: {:?},\n right: {:?}: {}",
                left, right, format!($($arg)+)
            );
        }
        print_assert_counts();
    }};
}

// 自定义 assert_ne! 宏
macro_rules! assert_ne {
    ($left:expr, $right:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left == *right {
            panic!(
                "assertion failed: (left != right)\n  left: {:?},\n right: {:?}",
                left, right
            );
        }
        print_assert_counts();
    }};
    ($left:expr, $right:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left == *right {
            panic!(
                "assertion failed: (left != right)\n  left: {:?},\n right: {:?}: {}",
                left, right, format!($($arg)+)
            );
        }
        print_assert_counts();
    }};
}
use test_project::queue::{
    queue_free, queue_is_empty, queue_new, queue_peek_head, queue_peek_tail, queue_pop_head,
    queue_pop_tail, queue_push_head, queue_push_tail, Queue, QueueEntry,
};
pub fn generate_queue() -> Queue<i32> {
    let mut queue = queue_new::<i32>();
    let variable1 = 0;
    let variable2 = 1;
    let variable3 = 2;
    let variable4 = 3;

    for _ in 0..1000 {
        queue_push_head(&mut queue, variable1);
        queue_push_head(&mut queue, variable2);
        queue_push_head(&mut queue, variable3);
        queue_push_head(&mut queue, variable4);
    }

    queue
}

#[test]
pub fn test_queue_pop_head() {
    let mut queue: Queue<i32> = queue_new();

    assert!(queue_pop_head(&mut queue).is_none());

    queue_free(&mut queue);

    let mut queue = generate_queue();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_pop_head(&mut queue), Some(3));
        assert_eq!(queue_pop_head(&mut queue), Some(2));
        assert_eq!(queue_pop_head(&mut queue), Some(1));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
    }

    assert!(queue_pop_head(&mut queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_pop_tail() {
    let mut queue: Queue<i32> = queue_new();

    assert!(queue_pop_tail(&mut queue).is_none());

    queue_free(&mut queue);

    let mut queue = generate_queue();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_pop_tail(&mut queue), Some(0));
        assert_eq!(queue_pop_tail(&mut queue), Some(1));
        assert_eq!(queue_pop_tail(&mut queue), Some(2));
        assert_eq!(queue_pop_tail(&mut queue), Some(3));
    }

    assert!(queue_pop_tail(&mut queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_new_free() {
    let mut queue: Queue<i32> = queue_new();

    queue_free(&mut queue);

    queue = queue_new();

    for i in 0..1000 {
        queue_push_head(&mut queue, i);
    }

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_is_empty() {
    let mut queue = queue_new::<i32>();

    assert!(queue_is_empty(&queue));

    let variable1 = 1;
    queue_push_head(&mut queue, variable1);

    assert!(!queue_is_empty(&queue));

    queue_pop_head(&mut queue);

    assert!(queue_is_empty(&queue));

    queue_push_tail(&mut queue, variable1);

    assert!(!queue_is_empty(&queue));

    queue_pop_tail(&mut queue);

    assert!(queue_is_empty(&queue));

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_peek_head() {
    let mut queue = queue_new::<i32>();

    assert!(queue_peek_head(&queue).is_none());

    queue_free(&mut queue);

    let mut queue = generate_queue();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_peek_head(&queue), Some(3));
        assert_eq!(queue_pop_head(&mut queue), Some(3));
        assert_eq!(queue_peek_head(&queue), Some(2));
        assert_eq!(queue_pop_head(&mut queue), Some(2));
        assert_eq!(queue_peek_head(&queue), Some(1));
        assert_eq!(queue_pop_head(&mut queue), Some(1));
        assert_eq!(queue_peek_head(&queue), Some(0));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
    }

    assert!(queue_peek_head(&queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_push_tail() {
    let mut queue = queue_new();
    let variable1 = 1;
    let variable2 = 2;
    let variable3 = 3;
    let variable4 = 4;

    for _ in 0..1000 {
        queue_push_tail(&mut queue, &variable1);
        queue_push_tail(&mut queue, &variable2);
        queue_push_tail(&mut queue, &variable3);
        queue_push_tail(&mut queue, &variable4);
    }

    assert!(!queue_is_empty(&queue));

    assert_eq!(queue_pop_head(&mut queue), Some(&variable1));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable2));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable3));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable4));

    assert_eq!(queue_pop_tail(&mut queue), Some(&variable4));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable3));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable2));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable1));

    queue_free(&mut queue);

    let mut queue = queue_new();
    assert!(!queue_push_tail(&mut queue, &variable1));
    queue_free(&mut queue);
}

#[test]
pub fn test_queue_push_head() {
    let mut queue = queue_new();
    let variable1 = 1;
    let variable2 = 2;
    let variable3 = 3;
    let variable4 = 4;

    for _ in 0..1000 {
        queue_push_head(&mut queue, &variable1);
        queue_push_head(&mut queue, &variable2);
        queue_push_head(&mut queue, &variable3);
        queue_push_head(&mut queue, &variable4);
    }

    assert!(!queue_is_empty(&queue));

    assert_eq!(queue_pop_tail(&mut queue), Some(&variable1));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable2));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable3));
    assert_eq!(queue_pop_tail(&mut queue), Some(&variable4));

    assert_eq!(queue_pop_head(&mut queue), Some(&variable4));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable3));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable2));
    assert_eq!(queue_pop_head(&mut queue), Some(&variable1));

    queue_free(&mut queue);

    let mut queue = queue_new();
    assert!(!queue_push_head(&mut queue, &variable1));
    queue_free(&mut queue);
}

#[test]
pub fn test_queue_peek_tail() {
    let mut queue = queue_new::<i32>();

    // Check peeking into an empty queue
    assert!(queue_peek_tail(&queue).is_none());

    queue_free(&mut queue);

    // Pop off all the values from the queue, making sure that peek
    // has the correct value beforehand
    let mut queue = generate_queue();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_peek_tail(&queue), Some(0));
        assert_eq!(queue_pop_tail(&mut queue), Some(0));
        assert_eq!(queue_peek_tail(&queue), Some(1));
        assert_eq!(queue_pop_tail(&mut queue), Some(1));
        assert_eq!(queue_peek_tail(&queue), Some(2));
        assert_eq!(queue_pop_tail(&mut queue), Some(2));
        assert_eq!(queue_peek_tail(&queue), Some(3));
        assert_eq!(queue_pop_tail(&mut queue), Some(3));
    }

    assert!(queue_peek_tail(&queue).is_none());

    queue_free(&mut queue);
}
