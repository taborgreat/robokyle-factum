#include "json.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

// Locate the value start for "key" at nesting depth 1 of obj. Returns NULL if not found.
static const char *find_key(const char *obj, const char *key) {
  size_t kl = strlen(key); int depth = 0; bool in_str = false;
  for (const char *p = obj; *p; p++) {
    if (in_str) { if (*p == '\\' && p[1]) p++; else if (*p == '"') in_str = false; continue; }
    if (*p == '"') {
      if (depth == 1 && strncmp(p + 1, key, kl) == 0 && p[1 + kl] == '"') {
        const char *q = p + 2 + kl; while (isspace((unsigned char)*q)) q++;
        if (*q == ':') { q++; while (isspace((unsigned char)*q)) q++; return q; }
      }
      in_str = true; continue;
    }
    if (*p == '{' || *p == '[') depth++;
    else if (*p == '}' || *p == ']') depth--;
  }
  return NULL;
}

bool json_get_str(const char *obj, const char *key, char *out, size_t n) {
  const char *v = find_key(obj, key);
  if (!v || *v != '"') return false;
  v++; size_t i = 0;
  while (*v && *v != '"' && i + 1 < n) {
    if (*v == '\\' && v[1]) { v++; char c = *v; out[i++] = c == 'n' ? '\n' : c == 't' ? '\t' : c; v++; continue; }
    out[i++] = *v++;
  }
  out[i] = 0; return true;
}

bool json_get_num(const char *obj, const char *key, float *out) {
  const char *v = find_key(obj, key);
  if (!v || !(isdigit((unsigned char)*v) || *v == '-' || *v == '.')) return false;
  *out = strtof(v, NULL); return true;
}

bool json_get_bool(const char *obj, const char *key, bool *out) {
  const char *v = find_key(obj, key);
  if (!v) return false;
  if (!strncmp(v, "true", 4)) { *out = true; return true; }
  if (!strncmp(v, "false", 5)) { *out = false; return true; }
  return false;
}

const char *json_get_arr_obj(const char *obj, const char *key, int idx, size_t *len) {
  const char *v = find_key(obj, key);
  if (!v || *v != '[') return NULL;
  int depth = 0, i = -1; const char *start = NULL; bool in_str = false;
  for (const char *p = v; *p; p++) {
    if (in_str) { if (*p == '\\' && p[1]) p++; else if (*p == '"') in_str = false; continue; }
    if (*p == '"') { in_str = true; continue; }
    if (*p == '{') { if (depth == 1) { i++; start = p; } depth++; }
    else if (*p == '}') { depth--; if (depth == 1 && i == idx) { *len = (size_t)(p - start + 1); return start; } }
    else if (*p == '[') depth++;
    else if (*p == ']') { if (--depth == 0) break; }
  }
  return NULL;
}

char *json_escape(const char *s, char *out, size_t n) {
  size_t i = 0;
  for (; *s && i + 2 < n; s++) {
    if (*s == '"' || *s == '\\') { out[i++] = '\\'; out[i++] = *s; }
    else if ((unsigned char)*s < 0x20) { out[i++] = ' '; }
    else out[i++] = *s;
  }
  out[i] = 0; return out;
}
