#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "urlparser.h"

void test_parse_url() {
    URL_PARTS url_parts;

    // Test case 1: Basic HTTP URL
    assert(ParseURL("http://sullewarehouse.com/login", &url_parts));
    assert(strcmp(url_parts.scheme, "http") == 0);
    assert(strcmp(url_parts.authority, "sullewarehouse.com") == 0);
    assert(strlen(url_parts.port) == 0); // No port specified
    assert(strcmp(url_parts.path, "/login") == 0);
    assert(strlen(url_parts.query) == 0); // No query
    assert(strlen(url_parts.fragment) == 0); // No fragment

    // Test case 2: HTTPS URL with port
    assert(ParseURL("https://sullewarehouse.com:1000/login", &url_parts));
    assert(strcmp(url_parts.scheme, "https") == 0);
    assert(strcmp(url_parts.authority, "sullewarehouse.com") == 0);
    assert(strcmp(url_parts.port, "1000") == 0);
    assert(strcmp(url_parts.path, "/login") == 0);
    assert(strlen(url_parts.query) == 0);
    assert(strlen(url_parts.fragment) == 0);

    // Test case 3: URL with query parameters
    assert(ParseURL("https://sullewarehouse.com:1000/api/get?username=myuser", &url_parts));
    assert(strcmp(url_parts.scheme, "https") == 0);
    assert(strcmp(url_parts.authority, "sullewarehouse.com") == 0);
    assert(strcmp(url_parts.port, "1000") == 0);
    assert(strcmp(url_parts.path, "/api/get") == 0);
    assert(strcmp(url_parts.query, "?username=myuser") == 0);
    assert(strlen(url_parts.fragment) == 0);

    // Test case 4: URL without scheme
    assert(ParseURL("sullewarehouse.com/register", &url_parts));
    assert(strlen(url_parts.scheme) == 0); // No scheme
    assert(strcmp(url_parts.authority, "sullewarehouse.com") == 0);
    assert(strlen(url_parts.port) == 0);
    assert(strcmp(url_parts.path, "/register") == 0);
    assert(strlen(url_parts.query) == 0);
    assert(strlen(url_parts.fragment) == 0);

    // Test case 5: IPv6 URL
    assert(ParseURL("http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/newpage", &url_parts));
    assert(strcmp(url_parts.scheme, "http") == 0);
    assert(strcmp(url_parts.authority, "2001:0db8:85a3:0000:0000:8a2e:0370:7334") == 0);
    assert(strlen(url_parts.port) == 0);
    assert(strcmp(url_parts.path, "/newpage") == 0);
    assert(strlen(url_parts.query) == 0);
    assert(strlen(url_parts.fragment) == 0);

    // Test case 6: IPv6 URL with port
    assert(ParseURL("https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:2678/blog", &url_parts));
    assert(strcmp(url_parts.scheme, "https") == 0);
    assert(strcmp(url_parts.authority, "2001:0db8:85a3:0000:0000:8a2e:0370:7334") == 0);
    assert(strcmp(url_parts.port, "2678") == 0);
    assert(strcmp(url_parts.path, "/blog") == 0);
    assert(strlen(url_parts.query) == 0);
    assert(strlen(url_parts.fragment) == 0);

    printf("All tests passed!\n");
}

int main() {
    test_parse_url();
    return 0;
}