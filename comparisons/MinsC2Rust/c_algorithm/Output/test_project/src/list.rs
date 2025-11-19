pub static variable1: i32 = 50;
pub static variable2: i32 = 0;
pub static variable3: i32 = 0;
pub static variable4: i32 = 0;

#[derive(Debug)]
pub struct ListEntry<T> {
    pub data: T,
    pub prev: Option<Box<ListEntry<T>>>,
    pub next: Option<Box<ListEntry<T>>>,
}

impl<T> Clone for ListEntry<T>
where
    T: Clone,
{
    fn clone(&self) -> Self {
        ListEntry {
            data: self.data.clone(),
            prev: self.prev.clone(),
            next: self.next.clone(),
        }
    }
}

impl<T> PartialEq for ListEntry<T>
where
    T: PartialEq,
{
    fn eq(&self, other: &Self) -> bool {
        self.data == other.data && self.prev == other.prev && self.next == other.next
    }
}

pub struct ListIterator<T> {
    pub prev_next: Option<Box<ListEntry<T>>>,
    pub current: Option<Box<ListEntry<T>>>,
}
pub fn list_append<T>(list: &mut Option<Box<ListEntry<T>>>, data: T) -> Option<Box<ListEntry<T>>>
where
    T: Clone,
{
    let mut newentry = Box::new(ListEntry {
        data,
        prev: None,
        next: None,
    });

    if list.is_none() {
        *list = Some(newentry);
        return list.clone();
    }

    let mut rover = list.as_mut().unwrap();
    while rover.next.is_some() {
        rover = rover.next.as_mut().unwrap();
    }

    newentry.prev = Some(Box::new(ListEntry {
        data: rover.data.clone(),
        prev: rover.prev.clone(),
        next: None,
    }));
    rover.next = Some(newentry);

    rover.next.clone()
}

pub fn list_prev<T>(listentry: Option<Box<ListEntry<T>>>) -> Option<Box<ListEntry<T>>> {
    match listentry {
        Some(entry) => entry.prev,
        None => None,
    }
}

pub fn list_next<T>(listentry: Option<Box<ListEntry<T>>>) -> Option<Box<ListEntry<T>>> {
    match listentry {
        Some(entry) => entry.next,
        None => None,
    }
}

pub fn list_nth_entry<T>(list: Option<Box<ListEntry<T>>>, n: usize) -> Option<Box<ListEntry<T>>>
where
    T: Clone,
{
    let mut entry = list;

    for _ in 0..n {
        if entry.is_none() {
            return None;
        }
        entry = entry.and_then(|e| e.next);
    }

    entry
}

pub fn list_length<T>(list: Option<Box<ListEntry<T>>>) -> usize {
    let mut length = 0;
    let mut entry = list;

    while let Some(node) = entry {
        length += 1;
        entry = node.next;
    }

    length
}

pub fn list_sort_internal<T, F>(list: &mut Option<Box<ListEntry<T>>>, compare_func: F) -> Option<Box<ListEntry<T>>>
where
    T: Clone,
    F: Fn(&T, &T) -> i32,
{
    return None;
    if list.is_none() {
        return None;
    }

    let mut pivot = list.take().unwrap();
    if pivot.next.is_none() {
        let pivot_clone = pivot.clone();
        *list = Some(pivot);
        return Some(pivot_clone);
    }

    let mut less_list: Option<Box<ListEntry<T>>> = None;
    let mut more_list: Option<Box<ListEntry<T>>> = None;
    let mut rover = pivot.next.take();

    while let Some(mut current) = rover {
        let next = current.next.take();
        let current_data = current.data.clone();
        if compare_func(&current_data, &pivot.data) < 0 {
            current.prev = None;
            current.next = less_list.take();
            let current_clone = current.clone();
            if let Some(ref mut less) = current.next {
                less.prev = Some(current_clone);
            }
            less_list = Some(current);
        } else {
            current.prev = None;
            current.next = more_list.take();
            let current_clone = current.clone();
            if let Some(ref mut more) = current.next {
                more.prev = Some(current_clone);
            }
            more_list = Some(current);
        }
        rover = next;
    }

    let mut less_list_end = list_sort_internal(&mut less_list, &compare_func);
    let more_list_end = list_sort_internal(&mut more_list, &compare_func);

    *list = less_list.take();
    if let Some(ref mut less_end) = less_list_end {
        let pivot_clone = pivot.clone();
        pivot.prev = Some(less_end.clone());
        less_end.next = Some(pivot_clone);
    } else {
        pivot.prev = None;
        *list = Some(pivot.clone());
    }

    pivot.next = more_list.take();
    let pivot_clone = pivot.clone();
    if let Some(ref mut more) = pivot.next {
        more.prev = Some(pivot_clone);
    }

    if more_list_end.is_none() {
        Some(pivot)
    } else {
        more_list_end
    }
}

pub fn list_free<T>(list: Option<Box<ListEntry<T>>>) {
    let mut entry = list;

    while let Some(mut current_entry) = entry {
        entry = current_entry.next.take();
    }
}

pub fn list_nth_data<T>(list: Option<Box<ListEntry<T>>>, n: usize) -> Option<T>
where
    T: Clone,
{
    let entry = list_nth_entry(list, n);

    if entry.is_none() {
        None
    } else {
        entry.map(|e| e.data)
    }
}

pub fn list_iterate<T>(list: &mut Option<Box<ListEntry<T>>>, iter: &mut ListIterator<T>) {
    iter.prev_next = list.take();
    iter.current = None;
}

pub fn list_remove_data<T, F>(list: &mut Option<Box<ListEntry<T>>>, callback: F, data: T) -> usize
where
    T: Clone + PartialEq,
    F: Fn(&T, &T) -> bool,
{
    let mut entries_removed = 0;
    let mut rover = list.take();

    while let Some(mut current) = rover {
        let next = current.next.take();

        if callback(&current.data, &data) {
            if let Some(mut prev) = current.prev.take() {
                prev.next = current.next.take();
            } else {
                *list = current.next.take();
            }

            if let Some(next_node) = current.next.as_mut() {
                next_node.prev = current.prev.take();
            }

            entries_removed += 1;
        } else {
            let current_clone = current.clone();
            if let Some(mut prev) = current.prev.take() {
                prev.next = Some(current_clone.clone());
            } else {
                *list = Some(current_clone.clone());
            }

            if let Some(next_node) = current.next.as_mut() {
                next_node.prev = Some(current_clone);
            }
        }

        rover = next;
    }

    entries_removed
}

pub fn list_iter_has_more<T>(iter: &ListIterator<T>) -> bool
where
    T: PartialEq,
{
    if iter.current.is_none() || iter.current.as_ref().map(|x| &**x) != iter.prev_next.as_ref().map(|x| &**x) {
        iter.prev_next.is_some()
    } else {
        iter.current.as_ref().unwrap().next.is_some()
    }
}

pub fn list_prepend<T>(list: &mut Option<Box<ListEntry<T>>>, data: T) -> Option<Box<ListEntry<T>>>
where
    T: Clone,
{
    let mut newentry = Box::new(ListEntry {
        data,
        prev: None,
        next: None,
    });

    if let Some(ref mut head) = list {
        head.prev = Some(newentry.clone());
        newentry.next = Some(head.clone());
    }

    *list = Some(newentry.clone());

    Some(newentry)
}

pub fn list_iter_remove<T>(iter: &mut ListIterator<T>)
where
    T: Clone + PartialEq,
{
    if iter.current.is_none() || iter.current.as_ref().map(|x| &**x) != iter.prev_next.as_ref().map(|x| &**x) {
        // Either we have not yet read the first item, we have
        // reached the end of the list, or we have already removed
        // the current value. Either way, do nothing.
    } else {
        // Remove the current entry
        let mut current = iter.current.take().unwrap();
        if let Some(ref mut prev_next) = iter.prev_next {
            *prev_next = current.next.take().unwrap_or_else(|| Box::new(ListEntry {
                data: current.data.clone(),
                prev: None,
                next: None,
            }));
        }

        if let Some(ref mut next) = current.next {
            next.prev = current.prev.clone();
        }

        iter.current = None;
    }
}

pub fn list_to_array<T: Clone>(list: Option<Box<ListEntry<T>>>) -> Vec<T> {
    let length = list_length(list.clone());
    let mut array = Vec::with_capacity(length);

    let mut rover = list;

    for _ in 0..length {
        if let Some(node) = rover {
            array.push(node.data.clone());
            rover = node.next;
        }
    }

    array
}

pub fn list_data<T>(listentry: Option<Box<ListEntry<T>>>) -> Option<T>
where
    T: Clone,
{
    match listentry {
        Some(entry) => Some(entry.data.clone()),
        None => None,
    }
}

pub fn list_sort<T, F>(list: &mut Option<Box<ListEntry<T>>>, compare_func: F)
where
    T: Clone,
    F: Fn(&T, &T) -> i32,
{
    *list = list_sort_internal(list, compare_func);
}

pub fn list_find_data<T, F>(list: Option<Box<ListEntry<T>>>, callback: F, data: T) -> Option<Box<ListEntry<T>>>
where
    T: Clone + PartialEq,
    F: Fn(T, T) -> bool,
{
    let mut rover = list;

    while let Some(node) = rover {
        if callback(node.data.clone(), data.clone()) {
            return Some(node);
        }
        rover = node.next;
    }

    None
}

pub fn list_remove_entry<T>(list: &mut Option<Box<ListEntry<T>>>, entry: Option<Box<ListEntry<T>>>) -> bool
where
    T: Clone,
{
    if list.is_none() || entry.is_none() {
        return false;
    }

    let mut entry = entry.unwrap();

    if entry.prev.is_none() {
        *list = entry.next.take();

        if let Some(ref mut next_entry) = list {
            next_entry.prev = None;
        }
    } else {
        let mut prev_entry = entry.prev.take().unwrap();
        let mut next_entry = entry.next.take();

        if let Some(ref mut next_entry_inner) = next_entry {
            next_entry_inner.prev = Some(Box::new((*prev_entry).clone()));
        }

        if let Some(ref mut prev_entry_inner) = prev_entry.next {
            prev_entry_inner.next = next_entry;
        }
    }

    true
}

pub fn list_iter_next<T>(iter: &mut ListIterator<T>) -> Option<T>
where
    T: Clone + PartialEq,
{
    if iter.current.is_none() || iter.current.as_ref().map(|x| &**x) != iter.prev_next.as_ref().map(|x| &**x) {
        iter.current = iter.prev_next.take();
    } else {
        if let Some(ref mut current) = iter.current {
            iter.prev_next = current.next.clone();
            iter.current = current.next.clone();
        }
    }

    if iter.current.is_none() {
        None
    } else {
        Some(iter.current.as_ref().unwrap().data.clone())
    }
}

