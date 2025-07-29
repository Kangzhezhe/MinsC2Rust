use test_project::urlparser::{
    ParseURL, MAX_URL_AUTHORITY_LEN, MAX_URL_FRAGMENT_LEN, MAX_URL_PATH_LEN, MAX_URL_PORT_LEN,
    MAX_URL_QUERY_LEN, MAX_URL_SCHEME_LEN, URL_PARTS,
};

use ntest::timeout;
#[test]
#[timeout(60000)]
pub fn test_parse_url() {
    let mut url_parts = URL_PARTS {
        scheme: String::new(),
        authority: String::new(),
        port: String::new(),
        path: String::new(),
        query: String::new(),
        fragment: String::new(),
    };

    // Test case 1: Basic HTTP URL
    assert!(ParseURL(
        "http://sullewarehouse.com/login".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, "http");
    assert_eq!(url_parts.authority, "sullewarehouse.com");
    assert_eq!(url_parts.port, ""); // No port specified
    assert_eq!(url_parts.path, "/login");
    assert_eq!(url_parts.query, ""); // No query
    assert_eq!(url_parts.fragment, ""); // No fragment

    // Test case 2: HTTPS URL with port
    assert!(ParseURL(
        "https://sullewarehouse.com:1000/login".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, "https");
    assert_eq!(url_parts.authority, "sullewarehouse.com");
    assert_eq!(url_parts.port, "1000");
    assert_eq!(url_parts.path, "/login");
    assert_eq!(url_parts.query, "");
    assert_eq!(url_parts.fragment, "");

    // Test case 3: URL with query parameters
    assert!(ParseURL(
        "https://sullewarehouse.com:1000/api/get?username=myuser".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, "https");
    assert_eq!(url_parts.authority, "sullewarehouse.com");
    assert_eq!(url_parts.port, "1000");
    assert_eq!(url_parts.path, "/api/get");
    assert_eq!(url_parts.query, "?username=myuser");
    assert_eq!(url_parts.fragment, "");

    // Test case 4: URL without scheme
    assert!(ParseURL(
        "sullewarehouse.com/register".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, ""); // No scheme
    assert_eq!(url_parts.authority, "sullewarehouse.com");
    assert_eq!(url_parts.port, "");
    assert_eq!(url_parts.path, "/register");
    assert_eq!(url_parts.query, "");
    assert_eq!(url_parts.fragment, "");

    // Test case 5: IPv6 URL
    assert!(ParseURL(
        "http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, "http");
    assert_eq!(
        url_parts.authority,
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    );
    assert_eq!(url_parts.port, "");
    assert_eq!(url_parts.path, "/newpage");
    assert_eq!(url_parts.query, "");
    assert_eq!(url_parts.fragment, "");

    // Test case 6: IPv6 URL with port
    assert!(ParseURL(
        "https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog".to_string(),
        &mut url_parts
    ));
    assert_eq!(url_parts.scheme, "https");
    assert_eq!(
        url_parts.authority,
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    );
    assert_eq!(url_parts.port, "2678");
    assert_eq!(url_parts.path, "/blog");
    assert_eq!(url_parts.query, "");
    assert_eq!(url_parts.fragment, "");

    println!("All tests passed!");
}
