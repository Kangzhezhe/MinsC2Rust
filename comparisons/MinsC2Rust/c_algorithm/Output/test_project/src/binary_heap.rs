pub enum BinaryHeapType {
    Min,
    Max,
}

pub type BinaryHeapValue<T> = Box<dyn std::cmp::PartialOrd<T>>;

pub struct BinaryHeap<T: std::cmp::PartialOrd> {
    pub heap_type: BinaryHeapType,
    pub values: Vec<T>,
    pub num_values: usize,
    pub alloced_size: usize,
    pub compare_func: fn(&T, &T) -> i32,
}

pub fn binary_heap_cmp<T: std::cmp::PartialOrd>(heap: &BinaryHeap<T>, data1: &T, data2: &T) -> i32 {
    match heap.heap_type {
        BinaryHeapType::Min => (heap.compare_func)(data1, data2),
        BinaryHeapType::Max => -(heap.compare_func)(data1, data2),
    }
}

pub fn binary_heap_insert<T: std::cmp::PartialOrd + Clone>(
    heap: &mut BinaryHeap<T>,
    value: T,
) -> bool {
    let mut index = heap.num_values;
    heap.num_values += 1;

    if heap.num_values >= heap.alloced_size {
        let new_size = heap.alloced_size * 2;
        let mut new_values = Vec::with_capacity(new_size);
        new_values.extend_from_slice(&heap.values);
        heap.alloced_size = new_size;
        heap.values = new_values;
    }

    while index > 0 {
        let parent = (index - 1) / 2;

        if binary_heap_cmp(heap, &heap.values[parent], &value) < 0 {
            break;
        } else {
            heap.values[index] = heap.values[parent].clone();
            index = parent;
        }
    }

    heap.values[index] = value;
    true
}

pub fn binary_heap_new<T: std::cmp::PartialOrd + Clone>(
    heap_type: BinaryHeapType,
    compare_func: fn(&T, &T) -> i32,
) -> Option<BinaryHeap<T>> {
    let mut heap = BinaryHeap {
        heap_type,
        values: Vec::with_capacity(16),
        num_values: 0,
        alloced_size: 16,
        compare_func,
    };

    Some(heap)
}

pub fn binary_heap_free<T: std::cmp::PartialOrd>(heap: BinaryHeap<T>) {
    // Rust的Vec会自动管理内存，不需要手动释放
    // heap.values会在heap离开作用域时自动释放
    // heap本身也会在离开作用域时自动释放
}

pub fn binary_heap_num_entries<T: std::cmp::PartialOrd>(heap: &BinaryHeap<T>) -> usize {
    heap.num_values
}

pub fn binary_heap_pop<T: std::cmp::PartialOrd + Clone>(heap: &mut BinaryHeap<T>) -> Option<T> {
    if heap.num_values == 0 {
        return None;
    }

    let result = heap.values[0].clone();

    let new_value = heap.values[heap.num_values - 1].clone();
    heap.num_values -= 1;

    let mut index = 0;

    loop {
        let child1 = index * 2 + 1;
        let child2 = index * 2 + 2;

        if child1 < heap.num_values && binary_heap_cmp(heap, &new_value, &heap.values[child1]) > 0 {
            let next_index = if child2 < heap.num_values
                && binary_heap_cmp(heap, &heap.values[child1], &heap.values[child2]) > 0
            {
                child2
            } else {
                child1
            };

            heap.values[index] = heap.values[next_index].clone();
            index = next_index;
        } else if child2 < heap.num_values
            && binary_heap_cmp(heap, &new_value, &heap.values[child2]) > 0
        {
            heap.values[index] = heap.values[child2].clone();
            index = child2;
        } else {
            heap.values[index] = new_value;
            break;
        }
    }

    Some(result)
}
