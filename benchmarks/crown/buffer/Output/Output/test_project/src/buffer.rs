pub const BUFFER_DEFAULT_SIZE: usize = 1024;

#[derive(Clone)]
pub struct Buffer {
    pub len: usize,
    pub alloc: String,
    pub data: String,
}

pub fn buffer_resize(buffer: &mut Buffer, n: usize) -> i32 {
    let n = ((n + 1023) / 1024) * 1024;
    buffer.len = n;
    buffer.alloc = String::with_capacity(n + 1);
    buffer.data = buffer.alloc.clone();
    buffer.alloc.push('\0');
    0
}

pub fn buffer_length(buffer: &Buffer) -> usize {
    buffer.data.len()
}

pub fn buffer_append_n(buffer: &mut Buffer, str: &str, len: usize) -> i32 {
    let prev = buffer.data.len();
    let needed = len + prev;

    if buffer.len > needed {
        buffer.data.push_str(&str[..len]);
        return 0;
    }

    let ret = buffer_resize(buffer, needed);
    if ret == -1 {
        return -1;
    }

    buffer.data.push_str(&str[..len]);
    0
}

pub fn buffer_new_with_size(n: usize) -> Result<Buffer, String> {
    let mut buffer = Buffer {
        len: n,
        alloc: String::with_capacity(n + 1),
        data: String::with_capacity(n + 1),
    };
    buffer.alloc.push_str(&"\0".repeat(n + 1));
    buffer.data.push_str(&"\0".repeat(n + 1));
    Ok(buffer)
}

pub fn buffer_trim_right(buffer: &mut Buffer) {
    let mut i = buffer_length(buffer) - 1;
    while i >= 0 {
        let c = buffer.data.chars().nth(i as usize).unwrap();
        if !c.is_whitespace() {
            break;
        }
        buffer.data.truncate(i as usize);
        i -= 1;
        if i < 0 {
            break;
        }
    }
}

pub fn buffer_trim_left(buffer: &mut Buffer) {
    while let Some(c) = buffer.data.chars().next() {
        if !c.is_whitespace() {
            break;
        }
        buffer.data = buffer.data[1..].to_string();
    }
}

pub fn buffer_fill(buffer: &mut Buffer, c: i32) {
    buffer.data = vec![c as u8; buffer.len].iter().map(|&b| b as char).collect();
}

pub fn buffer_free(buffer: Buffer) {
    // Function to free the buffer's allocated memory
    // No explicit free needed in Rust due to ownership and drop semantics
}

pub fn buffer_prepend(buffer: &mut Buffer, str: String) -> i32 {
    let len = str.len();
    let prev = buffer.data.len();
    let needed = len + prev;

    if buffer.len > needed {
        // enough space
    } else {
        // resize
        let ret = buffer_resize(buffer, needed);
        if ret == -1 {
            return -1;
        }
    }

    // move
    let mut new_data = String::with_capacity(needed + 1);
    new_data.push_str(&str);
    new_data.push_str(&buffer.data);
    buffer.data = new_data;

    0
}

pub fn buffer_append(buffer: &mut Buffer, str: &str) -> i32 {
    buffer_append_n(buffer, str, str.len())
}

pub fn buffer_new() -> Result<Buffer, String> {
    buffer_new_with_size(BUFFER_DEFAULT_SIZE)
}

pub fn buffer_size(buffer: &Buffer) -> usize {
    buffer.len
}

pub fn buffer_slice(buf: &Buffer, from: usize, to: isize) -> Result<Buffer, String> {
    let len = buf.data.len();

    // bad range
    if to < from as isize {
        return Err("Invalid range".to_string());
    }

    // relative to end
    let to = if to < 0 {
        len - (!to as usize)
    } else {
        to as usize
    };

    // cap end
    let to = if to > len { len } else { to };

    let n = to - from;
    let mut self_buf = buffer_new_with_size(n)?;
    self_buf.data = buf.data[from..to].to_string();
    Ok(self_buf)
}

pub fn buffer_new_with_copy(str: String) -> Result<Buffer, String> {
    let len = str.len();
    let mut buffer = buffer_new_with_size(len)?;
    buffer.alloc = str.clone();
    buffer.data = str;
    Ok(buffer)
}

pub fn buffer_trim(buffer: &mut Buffer) {
    buffer_trim_left(buffer);
    buffer_trim_right(buffer);
}

pub fn buffer_compact(buffer: &mut Buffer) -> i32 {
    let len = buffer_length(buffer);
    let rem = buffer.len - len;
    let mut buf = String::with_capacity(len + 1);
    buf.push_str(&buffer.data);
    buffer.alloc = buf.clone();
    buffer.data = buf;
    buffer.len = len;
    rem as i32
}

pub fn buffer_indexof(buffer: &Buffer, str: String) -> i32 {
    let sub = buffer.data.find(&str);
    match sub {
        Some(index) => index as i32,
        None => -1,
    }
}

pub fn buffer_clear(buffer: &mut Buffer) {  
    buffer_fill(buffer, 0);  
}

pub fn buffer_appendf(buffer: &mut Buffer, format: String, args: Vec<String>) -> i32 {
    let length = buffer_length(buffer);
    let required = format.len();
    if buffer_resize(buffer, length + required) == -1 {
        return -1;
    }
    let dst = &mut buffer.data[length..];
    let mut s = dst.to_string();
    let formatted_args = format!("{}", args.join(" "));
    let result = std::fmt::write(&mut s, format_args!("{}", formatted_args));
    if result.is_err() {
        -1
    } else {
        0
    }
}

pub fn buffer_equals(buffer: &Buffer, other: &Buffer) -> bool {
    buffer.data == other.data
}

