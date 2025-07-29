pub struct SListEntry<T> {
    pub data: T,
    pub next: Option<Box<SListEntry<T>>>,
}

impl<T: Clone> Clone for SListEntry<T> {
    fn clone(&self) -> Self {
        SListEntry {
            data: self.data.clone(),
            next: self.next.clone(),
        }
    }
}

impl<T: PartialEq> PartialEq for SListEntry<T> {
    fn eq(&self, other: &Self) -> bool {
        self.data == other.data && self.next == other.next
    }
}

pub struct SListIterator<T> {
    pub prev_next: Option<Box<SListEntry<T>>>,
    pub current: Option<Box<SListEntry<T>>>,
}
pub fn slist_append<T>(
    list: &mut Option<Box<SListEntry<T>>>,
    data: T,
) -> &mut Option<Box<SListEntry<T>>> {
    let newentry = Box::new(SListEntry { data, next: None });

    if list.is_none() {
        *list = Some(newentry);
    } else {
        let mut rover = list.as_mut().unwrap();
        while rover.next.is_some() {
            rover = rover.next.as_mut().unwrap();
        }
        rover.next = Some(newentry);
    }

    list
}

pub fn slist_nth_entry<T>(
    list: Option<Box<SListEntry<T>>>,
    n: usize,
) -> Option<Box<SListEntry<T>>> {
    let mut entry = list;
    let mut i = 0;

    while i < n {
        match entry {
            Some(ref mut current) => {
                entry = current.next.take();
                i += 1;
            }
            None => return None,
        }
    }

    entry
}

pub fn slist_length<T>(list: Option<Box<SListEntry<T>>>) -> usize {
    let mut length: usize = 0;
    let mut entry = list;

    while let Some(node) = entry {
        length += 1;
        entry = node.next;
    }

    length
}

pub fn slist_sort_internal<T, F>(
    list: &mut Option<Box<SListEntry<T>>>,
    compare_func: F,
) -> Option<Box<SListEntry<T>>>
where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering,
{
    return list.take();
    if list.is_none() || list.as_ref().unwrap().next.is_none() {
        return list.take();
    }

    let mut pivot = list.take().unwrap();
    let mut less_list: Option<Box<SListEntry<T>>> = None;
    let mut more_list: Option<Box<SListEntry<T>>> = None;
    let mut rover = pivot.next.take();

    while let Some(mut node) = rover {
        let next = node.next.take();
        match compare_func(&node.data, &pivot.data) {
            std::cmp::Ordering::Less => {
                node.next = less_list.take();
                less_list = Some(node);
            }
            _ => {
                node.next = more_list.take();
                more_list = Some(node);
            }
        }
        rover = next;
    }

    let less_list_end = slist_sort_internal(&mut less_list, &compare_func);
    let more_list_end = slist_sort_internal(&mut more_list, &compare_func);

    *list = less_list.take();
    if list.is_none() {
        *list = Some(pivot.clone());
    } else {
        less_list_end.unwrap().next = Some(pivot.clone());
    }

    pivot.next = more_list.take();

    if more_list.is_none() {
        Some(pivot)
    } else {
        more_list_end
    }
}

pub fn slist_prepend<T: Clone>(
    list: &mut Option<Box<SListEntry<T>>>,
    data: T,
) -> Option<Box<SListEntry<T>>> {
    let newentry = Box::new(SListEntry {
        data,
        next: list.take(),
    });

    *list = Some(newentry.clone());

    Some(newentry)
}

pub fn slist_free<T>(list: Option<Box<SListEntry<T>>>) {
    let mut entry = list;

    while let Some(mut current_entry) = entry {
        entry = current_entry.next.take();
    }
}

pub fn slist_data<T>(listentry: &SListEntry<T>) -> T
where
    T: Clone,
{
    listentry.data.clone()
}

pub fn slist_nth_data<T: Clone>(list: Option<Box<SListEntry<T>>>, n: usize) -> Option<T> {
    let entry = slist_nth_entry(list, n);

    match entry {
        Some(entry) => Some(entry.data.clone()),
        None => None,
    }
}

pub fn slist_iter_next<T>(iter: &mut SListIterator<T>) -> Option<T>
where
    T: Clone + PartialEq,
{
    if iter.current.is_none()
        || iter.current.as_ref().map(|x| &**x) != iter.prev_next.as_ref().map(|x| &**x)
    {
        iter.current = iter.prev_next.clone();
    } else {
        if let Some(current) = &iter.current {
            iter.prev_next = current.next.clone();
            iter.current = current.next.clone();
        }
    }

    if iter.current.is_none() {
        None
    } else {
        iter.current.as_ref().map(|x| x.data.clone())
    }
}

pub fn slist_iterate<T>(list: &mut Option<Box<SListEntry<T>>>, iter: &mut SListIterator<T>) {
    iter.prev_next = list.take();
    iter.current = None;
}

pub fn slist_iter_has_more<T: PartialEq>(iter: &SListIterator<T>) -> bool {
    let current_ref = iter.current.as_ref().map(|x| &**x);
    let prev_next_ref = iter.prev_next.as_ref().map(|x| &**x);

    if iter.current.is_none() || current_ref != prev_next_ref {
        iter.prev_next.is_some()
    } else {
        iter.current.as_ref().unwrap().next.is_some()
    }
}

pub fn slist_iter_remove<T: PartialEq>(iter: &mut SListIterator<T>) {
    let current_ref = iter.current.as_ref().map(|x| &**x);
    let prev_next_ref = iter.prev_next.as_ref().map(|x| &**x);

    if iter.current.is_none() || current_ref != prev_next_ref {
        // Either we have not yet read the first item, we have
        // reached the end of the list, or we have already removed
        // the current value. Either way, do nothing.
    } else {
        // Remove the current entry
        if let Some(current) = iter.current.take() {
            if let Some(prev_next) = &mut iter.prev_next {
                prev_next.next = current.next;
            }
        }
    }
}

pub fn slist_find_data<T, F>(
    list: Option<Box<SListEntry<T>>>,
    callback: F,
    data: T,
) -> Option<Box<SListEntry<T>>>
where
    T: PartialEq + Clone,
    F: Fn(&T, &T) -> bool,
{
    let mut rover = list;

    while let Some(entry) = rover {
        if callback(&entry.data, &data) {
            return Some(entry);
        }
        rover = entry.next;
    }

    None
}

pub fn slist_to_array<T: Clone>(list: Option<Box<SListEntry<T>>>) -> Option<Vec<T>> {
    let length = slist_length(list.clone());

    let mut array = Vec::with_capacity(length);

    let mut rover = list;

    for _ in 0..length {
        if let Some(node) = rover {
            array.push(node.data.clone());
            rover = node.next;
        } else {
            return None;
        }
    }

    Some(array)
}

pub fn slist_sort<T, F>(list: &mut Option<Box<SListEntry<T>>>, compare_func: F)
where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering,
{
    *list = slist_sort_internal(list, compare_func);
}

pub fn slist_remove_entry<T: PartialEq>(
    list: &mut Option<Box<SListEntry<T>>>,
    entry: &Option<Box<SListEntry<T>>>,
) -> bool {
    if list.is_none() || entry.is_none() {
        return false;
    }

    let entry = entry.as_ref().unwrap();

    if let Some(ref mut head) = list {
        if **head == **entry {
            *list = head.next.take();
            return true;
        }
    }

    let mut rover = list.as_mut();

    while let Some(current) = rover {
        if let Some(ref mut next) = current.next {
            if **next == **entry {
                current.next = next.next.take();
                return true;
            }
        }
        rover = current.next.as_mut();
    }

    false
}

pub fn slist_next<T>(listentry: Option<Box<SListEntry<T>>>) -> Option<Box<SListEntry<T>>> {
    listentry.and_then(|entry| entry.next)
}
