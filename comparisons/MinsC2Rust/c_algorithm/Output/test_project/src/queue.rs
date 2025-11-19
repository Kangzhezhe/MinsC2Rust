pub struct QueueEntry<T> {
    pub data: T,
    pub prev: Option<Box<QueueEntry<T>>>,
    pub next: Option<Box<QueueEntry<T>>>,
}

impl<T> Clone for QueueEntry<T>
where
    T: Clone,
{
    fn clone(&self) -> Self {
        QueueEntry {
            data: self.data.clone(),
            prev: self.prev.as_ref().map(|x| Box::new((**x).clone())),
            next: self.next.as_ref().map(|x| Box::new((**x).clone())),
        }
    }
}

pub struct Queue<T> {
    pub head: Option<Box<QueueEntry<T>>>,
    pub tail: Option<Box<QueueEntry<T>>>,
}

pub fn queue_is_empty<T>(queue: &Queue<T>) -> bool {
    queue.head.is_none()
}

pub fn queue_push_head<T: Clone>(queue: &mut Queue<T>, data: T) -> bool {
    let new_entry = Box::new(QueueEntry {
        data,
        prev: None,
        next: queue.head.take(),
    });

    if let Some(ref mut head) = queue.head {
        head.prev = Some(new_entry.clone());
    } else {
        queue.tail = Some(new_entry.clone());
    }

    queue.head = Some(new_entry);
    true
}

pub fn queue_new<T>() -> Queue<T> {
    Queue {
        head: None,
        tail: None,
    }
}

pub fn queue_pop_head<T>(queue: &mut Queue<T>) -> Option<T>
where
    T: Clone,
{
    if queue_is_empty(queue) {
        return None;
    }

    let mut entry = queue.head.take().unwrap();
    queue.head = entry.next.take();
    let result = entry.data.clone();

    if queue.head.is_none() {
        queue.tail = None;
    } else {
        queue.head.as_mut().unwrap().prev = None;
    }

    Some(result)
}

pub fn queue_pop_tail<T>(queue: &mut Queue<T>) -> Option<T>
where
    T: Clone,
{
    if queue_is_empty(queue) {
        return None;
    }

    let mut entry = queue.tail.take().unwrap();
    queue.tail = entry.prev.take();
    let result = entry.data.clone();

    if queue.tail.is_none() {
        queue.head = None;
    } else {
        queue.tail.as_mut().unwrap().next = None;
    }

    Some(result)
}

pub fn queue_push_tail<T: Clone>(queue: &mut Queue<T>, data: T) -> bool {
    let new_entry = Box::new(QueueEntry {
        data,
        prev: queue.tail.as_ref().map(|x| Box::new((**x).clone())),
        next: None,
    });

    if queue.tail.is_none() {
        queue.head = Some(new_entry.clone());
        queue.tail = Some(new_entry);
    } else {
        if let Some(ref mut tail) = queue.tail {
            tail.next = Some(new_entry.clone());
        }
        queue.tail = Some(new_entry);
    }

    true
}

pub fn queue_peek_head<T>(queue: &Queue<T>) -> Option<T>
where
    T: Clone,
{
    if queue_is_empty(queue) {
        None
    } else {
        queue.head.as_ref().map(|head| head.data.clone())
    }
}

pub fn queue_peek_tail<T>(queue: &Queue<T>) -> Option<T>
where
    T: Clone,
{
    if queue_is_empty(queue) {
        None
    } else {
        queue.tail.as_ref().map(|tail| tail.data.clone())
    }
}

pub fn queue_free<T: Clone>(queue: &mut Queue<T>) {
    while !queue_is_empty(queue) {
        queue_pop_head(queue);
    }
}
