use std::str;

pub const MAX_URL_FRAGMENT_LEN: usize = 256;
pub const MAX_URL_SCHEME_LEN: usize = 32;
pub const MAX_URL_PATH_LEN: usize = 1024;
pub const MAX_URL_QUERY_LEN: usize = 1024;
pub const MAX_URL_AUTHORITY_LEN: usize = 512;
pub const MAX_URL_PORT_LEN: usize = 64;

pub struct URL_PARTS {
    pub scheme: String,
    pub authority: String,
    pub port: String,
    pub path: String,
    pub query: String,
    pub fragment: String,
}

pub fn ParseURL(URL: String, pURL_Parts: &mut URL_PARTS) -> bool {
    let mut i: usize;
    let mut c: u8;
    let mut b: bool = false;

    // Clear the data
    *pURL_Parts = URL_PARTS {
        scheme: String::new(),
        authority: String::new(),
        port: String::new(),
        path: String::new(),
        query: String::new(),
        fragment: String::new(),
    };

    // Setup our parser pointer
    let mut string = URL.as_bytes();

    // Check for the authority preceding double slash
    let authority = match str::from_utf8(string).unwrap().find("//") {
        Some(pos) => {
            let scheme_end = pos;
            i = 0;
            while i < scheme_end {
                c = string[i];
                if c == b':' || c == b'/' {
                    break;
                }
                if pURL_Parts.scheme.len() == MAX_URL_SCHEME_LEN - 1 {
                    return false;
                }
                pURL_Parts.scheme.push(c as char);
                i += 1;
            }
            &string[pos + 2..]
        }
        None => string,
    };

    c = authority[0];
    if c == b'[' {
        b = true;
        string = &authority[1..];
    } else {
        string = authority;
    }

    // Parse the authority
    i = 0;
    while i < string.len() {
        c = string[i];
        if c == b' ' {
            i += 1;
            continue;
        }
        if c == b'/' || c == b'?' || c == b'#' || (c == b':' && !b) {
            break;
        }
        if b && c == b']' {
            i += 1;
            break;
        }
        if pURL_Parts.authority.len() == MAX_URL_AUTHORITY_LEN - 1 {
            return false;
        }
        pURL_Parts.authority.push(c as char);
        i += 1;
    }

    string = &string[i..];

    // Check for a port number
    if !string.is_empty() && string[0] == b':' {
        string = &string[1..];
        i = 0;
        while i < string.len() {
            c = string[i];
            if c == b'/' || c == b'?' || c == b'#' {
                break;
            }
            if pURL_Parts.port.len() == MAX_URL_PORT_LEN - 1 {
                return false;
            }
            pURL_Parts.port.push(c as char);
            i += 1;
        }
        string = &string[i..];
    }

    // Check for a path
    if !string.is_empty() && string[0] == b'/' {
        i = 0;
        while i < string.len() {
            c = string[i];
            if c == b'?' || c == b'#' {
                break;
            }
            if pURL_Parts.path.len() == MAX_URL_PATH_LEN - 1 {
                return false;
            }
            pURL_Parts.path.push(c as char);
            i += 1;
        }
        string = &string[i..];
    }

    // Check for a query
    if !string.is_empty() && string[0] == b'?' {
        i = 0;
        while i < string.len() {
            c = string[i];
            if c == b'#' {
                break;
            }
            if pURL_Parts.query.len() == MAX_URL_QUERY_LEN - 1 {
                return false;
            }
            pURL_Parts.query.push(c as char);
            i += 1;
        }
        string = &string[i..];
    }

    // Check for a fragment
    if !string.is_empty() && string[0] == b'#' {
        i = 0;
        while i < string.len() {
            c = string[i];
            if pURL_Parts.fragment.len() == MAX_URL_FRAGMENT_LEN - 1 {
                return false;
            }
            pURL_Parts.fragment.push(c as char);
            i += 1;
        }
    }

    true
}

