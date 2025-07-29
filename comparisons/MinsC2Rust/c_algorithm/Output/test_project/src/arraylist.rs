pub struct ArrayList<T> {
    pub data: Vec<T>,
    pub length: usize,
    pub _alloced: usize,
}

pub type ArrayListCompareFunc<T> = fn(value1: &T, value2: &T) -> i32;
pub type ArrayListEqualFunc<T> = fn(value1: &T, value2: &T) -> i32;

impl<T> Clone for ArrayList<T> where T: Clone {
    fn clone(&self) -> Self {
        ArrayList {
            data: self.data.clone(),
            length: self.length,
            _alloced: self._alloced,
        }
    }
}
pub fn arraylist_enlarge<T: Clone>(arraylist: &mut ArrayList<T>) -> bool {
    let newsize = arraylist._alloced * 2;
    let mut new_data = Vec::with_capacity(newsize);

    new_data.extend_from_slice(&arraylist.data);

    arraylist.data = new_data;
    arraylist._alloced = newsize;

    true
}

pub fn arraylist_insert<T: Clone>(arraylist: &mut ArrayList<T>, index: usize, data: T) -> bool {
    if index > arraylist.length {
        return false;
    }

    if arraylist.length + 1 > arraylist._alloced {
        if !arraylist_enlarge(arraylist) {
            return false;
        }
    }

    arraylist.data.insert(index, data);
    arraylist.length += 1;

    true
}

pub fn arraylist_sort_internal<T: Clone>(list_data: &mut [T], list_length: usize, compare_func: ArrayListCompareFunc<T>) {
    if list_length <= 1 {
        return;
    }

    let pivot = list_data[list_length - 1].clone();
    let mut list1_length = 0;

    for i in 0..list_length - 1 {
        if compare_func(&list_data[i], &pivot) < 0 {
            list_data.swap(i, list1_length);
            list1_length += 1;
        }
    }

    let list2_length = list_length - list1_length - 1;

    list_data.swap(list_length - 1, list1_length);

    arraylist_sort_internal(&mut list_data[0..list1_length], list1_length, compare_func);
    arraylist_sort_internal(&mut list_data[list1_length + 1..], list2_length, compare_func);
}

pub fn arraylist_append<T: Clone>(arraylist: &mut Box<ArrayList<T>>, data: T) -> bool {
    arraylist_insert(arraylist, arraylist.length, data)
}

pub fn arraylist_new<T>(length: usize) -> Option<Box<ArrayList<T>>> {
    let mut new_length = length;

    if new_length == 0 {
        new_length = 16;
    }

    let new_arraylist = ArrayList {
        data: Vec::with_capacity(new_length),
        length: 0,
        _alloced: new_length,
    };

    Some(Box::new(new_arraylist))
}

pub fn arraylist_remove_range<T>(arraylist: &mut ArrayList<T>, index: usize, length: usize) {
    if index > arraylist.length || index + length > arraylist.length {
        return;
    }

    let start = index + length;
    let end = arraylist.length;
    let range_to_remove = start..end;

    arraylist.data.drain(index..index + length);

    arraylist.length -= length;
}

pub fn arraylist_free<T>(arraylist: Option<Box<ArrayList<T>>>) {
    if let Some(mut arraylist) = arraylist {
        arraylist.data.clear();
    }
}

pub fn arraylist_prepend<T: Clone>(arraylist: &mut ArrayList<T>, data: T) -> bool {
    arraylist_insert(arraylist, 0, data)
}

pub fn arraylist_sort<T: Clone>(arraylist: &mut ArrayList<T>, compare_func: ArrayListCompareFunc<T>) {
    arraylist_sort_internal(&mut arraylist.data, arraylist.length, compare_func);
}

pub fn arraylist_index_of<T>(arraylist: &ArrayList<T>, callback: ArrayListEqualFunc<T>, data: &T) -> i32 {
    for i in 0..arraylist.length {
        if callback(&arraylist.data[i], data) != 0 {
            return i as i32;
        }
    }
    -1
}

pub fn arraylist_clear<T>(arraylist: &mut ArrayList<T>) {
    arraylist.length = 0;
}

pub fn arraylist_remove<T>(arraylist: &mut ArrayList<T>, index: usize) {
    arraylist_remove_range(arraylist, index, 1);
}

