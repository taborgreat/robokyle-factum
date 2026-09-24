// Minimal JSON helpers: enough for flat config objects and small arrays of flat objects. No allocation.
#pragma once
#include <stdbool.h>
#include <stddef.h>

// Find "key" at the top level of obj (a '{...}' string) and copy its string value. Returns false if absent.
bool json_get_str(const char *obj, const char *key, char *out, size_t n);
bool json_get_num(const char *obj, const char *key, float *out);
bool json_get_bool(const char *obj, const char *key, bool *out);
// Returns a pointer to the i-th '{' object inside the array value of key, or NULL. *len = object length.
const char *json_get_arr_obj(const char *obj, const char *key, int i, size_t *len);
// JSON-escape s into out (quotes, backslashes, control chars). Returns out.
char *json_escape(const char *s, char *out, size_t n);
