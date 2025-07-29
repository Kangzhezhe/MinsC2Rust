#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//
// Copyright (c) 2023 Brian Sullender
// All rights reserved.
//
// This source code is licensed under the terms provided in the README file.
//
// https://github.com/b-sullender/url-parser
//

#ifndef URL_PARSER_H
#define URL_PARSER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Maximum scheme length
#define MAX_URL_SCHEME_LEN 32
// Maximum authority length
#define MAX_URL_AUTHORITY_LEN 512
// Maximum port length
#define MAX_URL_PORT_LEN 64
// Maximum path length
#define MAX_URL_PATH_LEN 1024
// Maximum query length
#define MAX_URL_QUERY_LEN 1024
// Maximum fragment length
#define MAX_URL_FRAGMENT_LEN 256

typedef struct URL_PARTS {
    char scheme[MAX_URL_SCHEME_LEN];
    char authority[MAX_URL_AUTHORITY_LEN];
    char port[MAX_URL_PORT_LEN];
    char path[MAX_URL_PATH_LEN];
    char query[MAX_URL_QUERY_LEN];
    char fragment[MAX_URL_FRAGMENT_LEN];
} URL_PARTS;

// ParseURL
// This function parses a URL string
// @URL: The URL string the parse
// @pURL_Parts: A pointer to a URL_PARTS struct to fill
// @return: true on success, false otherwise
bool ParseURL(char* URL, URL_PARTS* pURL_Parts);

// PrintURL
// This function prints each part of a URL_PARTS struct individually,
// and the entire URL on a single line. For testing purposes only
// @pURL_Parts: A pointer to a URL_PARTS struct to print
void PrintURL(struct URL_PARTS* pURL_Parts);

#endif // !URL_PARSER_H

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