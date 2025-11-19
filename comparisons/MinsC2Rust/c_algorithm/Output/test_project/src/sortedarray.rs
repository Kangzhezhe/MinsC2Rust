pub struct SortedArray<T> {
    pub data: Vec<T>,
    pub length: usize,
    pub _alloced: usize,
    pub equ_func: fn(&T, &T) -> bool,
    pub cmp_func: fn(&T, &T) -> std::cmp::Ordering,
}

pub fn sortedarray_insert<T>(sortedarray: &mut SortedArray<T>, data: T) -> bool {
    let mut left = 0;
    let mut right = sortedarray.length;
    let mut index = 0;

    right = if right > 1 { right } else { 0 };

    while left != right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(&data, &sortedarray.data[index]);
        match order {
            std::cmp::Ordering::Less => right = index,
            std::cmp::Ordering::Greater => left = index + 1,
            std::cmp::Ordering::Equal => break,
        }
    }

    if sortedarray.length > 0 && (sortedarray.cmp_func)(&data, &sortedarray.data[index]) == std::cmp::Ordering::Greater {
        index += 1;
    }

    if sortedarray.length + 1 > sortedarray._alloced {
        let newsize = sortedarray._alloced * 2;
        sortedarray.data.reserve(newsize);
        sortedarray._alloced = newsize;
    }

    sortedarray.data.insert(index, data);
    sortedarray.length += 1;

    true
}

pub fn sortedarray_new<T>(length: usize, equ_func: fn(&T, &T) -> bool, cmp_func: fn(&T, &T) -> std::cmp::Ordering) -> Option<SortedArray<T>> {
    let mut length = length;
    if length == 0 {
        length = 16;
    }

    let mut data = Vec::<T>::with_capacity(length);

    let sortedarray = SortedArray {
        data: data,
        length: 0,
        _alloced: length,
        equ_func: equ_func,
        cmp_func: cmp_func,
    };

    Some(sortedarray)
}

pub fn sortedarray_last_index<T: Clone>(
    sortedarray: &SortedArray<T>,
    data: T,
    left: usize,
    right: usize,
) -> usize {
    let mut index = right;
    let mut left = left;
    let mut right = right;

    while left < right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(&data, &sortedarray.data[index]);
        if order <= std::cmp::Ordering::Equal {
            left = index + 1;
        } else {
            right = index;
        }
    }

    index
}

pub fn sortedarray_first_index<T: Clone>(
    sortedarray: &SortedArray<T>,
    data: T,
    left: usize,
    right: usize,
) -> usize {
    let mut left = left;
    let mut right = right;
    let mut index = left;

    while left < right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(&data, &sortedarray.data[index]);

        if order == std::cmp::Ordering::Greater {
            left = index + 1;
        } else {
            right = index;
        }
    }

    index
}

pub fn sortedarray_get<T>(array: &SortedArray<T>, i: usize) -> Option<&T> {
    if i >= array.length {
        return None;
    }
    Some(&array.data[i])
}

pub fn sortedarray_length<T>(array: &SortedArray<T>) -> usize {
    array.length
}

pub fn sortedarray_free<T>(sortedarray: Option<Box<SortedArray<T>>>) {
    if let Some(mut sortedarray) = sortedarray {
        sortedarray.data.clear();
    }
}

pub fn sortedarray_remove_range<T>(sortedarray: &mut SortedArray<T>, index: usize, length: usize) {
    if index > sortedarray.length || index + length > sortedarray.length {
        return;
    }

    let start = index + length;
    let end = sortedarray.length;
    let range_to_remove = start..end;

    sortedarray.data.drain(index..index + length);

    sortedarray.length -= length;
}

pub fn sortedarray_index_of<T: Clone>(
    sortedarray: &SortedArray<T>,
    data: T,
) -> isize {
    if sortedarray.data.is_empty() {
        return -1;
    }

    let mut left = 0;
    let mut right = sortedarray.length;
    let mut index = 0;

    right = if right > 1 { right } else { 0 };

    while left != right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(&data, &sortedarray.data[index]);

        if order == std::cmp::Ordering::Less {
            right = index;
        } else if order == std::cmp::Ordering::Greater {
            left = index + 1;
        } else {
            left = sortedarray_first_index(sortedarray, data.clone(), left, index);
            right = sortedarray_last_index(sortedarray, data.clone(), index, right);

            for i in left..=right {
                if (sortedarray.equ_func)(&data, &sortedarray.data[i]) {
                    return i as isize;
                }
            }

            return -1;
        }
    }

    -1
}

pub fn sortedarray_remove<T>(sortedarray: &mut SortedArray<T>, index: usize) {
    sortedarray_remove_range(sortedarray, index, 1);
}

