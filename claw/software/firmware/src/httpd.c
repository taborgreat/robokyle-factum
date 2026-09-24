// Hand HTTP server (raw lwIP, port 80). The band is the only commander; Factum only reads /status and writes /config.
//   POST /open | /close {"force":0..1} | /grip {"name":..,"preview":bool} | /stop | /estop | /keepalive
//   GET  /status (open)      GET/POST /config (X-Factum-Key)
#include "httpd.h"
#include "gripper.h"
#include "hcfg.h"
#include "json.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"

#define REQ_MAX 1024
typedef struct { char buf[REQ_MAX]; int len; } conn_t;
static struct tcp_pcb *listen_pcb;

static void reply(struct tcp_pcb *pcb, int code, const char *body) {
  char hdr[160];
  int n = snprintf(hdr, sizeof hdr, "HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %u\r\nConnection: close\r\n\r\n",
                   code, code == 200 ? "OK" : code == 401 ? "Unauthorized" : code == 404 ? "Not Found" : "Bad Request", (unsigned)strlen(body));
  tcp_write(pcb, hdr, n, TCP_WRITE_FLAG_COPY); tcp_write(pcb, body, strlen(body), TCP_WRITE_FLAG_COPY); tcp_output(pcb);
}
static bool has_key(const char *req) {
  const char *k = strstr(req, "X-Factum-Key:"); if (!k) k = strstr(req, "x-factum-key:");
  if (!k) return false; k += 13; while (*k == ' ') k++;
  size_t n = strlen(hc.factum_key); return !strncmp(k, hc.factum_key, n) && (k[n] == '\r' || k[n] == '\n');
}
static void config_json(char *b, int n) {
  int o = snprintf(b, n, "{\"hand_id\":\"%s\",\"pos_open\":%u,\"pos_closed\":%u,\"torque_min\":%u,\"torque_max\":%u,\"speed\":%u,\"wifi\":[",
                   hc.hand_id, hc.pos_open, hc.pos_closed, hc.torque_min, hc.torque_max, hc.speed);
  for (int i = 0; i < 4 && o < n; i++) o += snprintf(b + o, n - o, "%s{\"ssid\":\"%s\"}", i ? "," : "", hc.wifi[i].ssid);
  snprintf(b + o, n - o, "]}");
}
static void merge(const char *body) {
  float f; char s[64]; size_t len;
  if (json_get_str(body, "hand_id", s, sizeof s)) strncpy(hc.hand_id, s, 15);
  if (json_get_str(body, "factum_key", s, sizeof s)) strncpy(hc.factum_key, s, 31);
  if (json_get_num(body, "pos_open", &f)) hc.pos_open = (uint16_t)f;     if (json_get_num(body, "pos_closed", &f)) hc.pos_closed = (uint16_t)f;
  if (json_get_num(body, "torque_min", &f)) hc.torque_min = (uint16_t)f; if (json_get_num(body, "torque_max", &f)) hc.torque_max = (uint16_t)f;
  if (json_get_num(body, "speed", &f)) hc.speed = (uint16_t)f;
  if (json_get_arr_obj(body, "wifi", 0, &len)) {
    memset(hc.wifi, 0, sizeof hc.wifi);
    for (int i = 0; i < 4; i++) { const char *w = json_get_arr_obj(body, "wifi", i, &len); if (!w) break;
      char obj[160]; if (len >= sizeof obj) len = sizeof obj - 1; memcpy(obj, w, len); obj[len] = 0;
      json_get_str(obj, "ssid", hc.wifi[i].ssid, 32); json_get_str(obj, "pass", hc.wifi[i].pass, 64); }
  }
}

static void handle(struct tcp_pcb *pcb, conn_t *c) {
  static char out[512]; char method[8] = {0}, path[32] = {0};
  sscanf(c->buf, "%7s %31s", method, path);
  const char *body = strstr(c->buf, "\r\n\r\n"); body = body ? body + 4 : "";
  bool post = !strcmp(method, "POST");
  uint32_t now = to_ms_since_boot(get_absolute_time());
  if (!strcmp(path, "/status")) { gr_status_json(out, sizeof out); reply(pcb, 200, out); return; }
  if (post && !strcmp(path, "/keepalive")) { gr_keepalive(now); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/open")) { gr_keepalive(now); gr_open(); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/close")) { float f = 0.5f; json_get_num(body, "force", &f); gr_keepalive(now); gr_close(f); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/grip")) { char name[16] = "open"; bool pv = false; json_get_str(body, "name", name, sizeof name); json_get_bool(body, "preview", &pv); gr_keepalive(now); gr_grip(name, pv); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/stop")) { gr_stop(); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/estop")) { gr_estop(); reply(pcb, 200, "{\"estop\":true}"); return; }
  if (!strcmp(path, "/config")) {
    if (!has_key(c->buf)) { reply(pcb, 401, "{\"error\":\"X-Factum-Key required\"}"); return; }
    if (post) { merge(body); bool ok = hcfg_save(); reply(pcb, ok ? 200 : 500, ok ? "{\"saved\":true}" : "{\"saved\":false}"); }
    else { config_json(out, sizeof out); reply(pcb, 200, out); }
    return;
  }
  reply(pcb, 404, "{\"error\":\"no such endpoint\"}");
}

static void conn_close(struct tcp_pcb *pcb, conn_t *c) { tcp_arg(pcb, NULL); tcp_recv(pcb, NULL); tcp_err(pcb, NULL); tcp_sent(pcb, NULL); free(c); if (tcp_close(pcb) != ERR_OK) tcp_abort(pcb); }
static err_t on_sent(void *arg, struct tcp_pcb *pcb, u16_t len) { (void)len; conn_close(pcb, arg); return ERR_OK; }
static err_t on_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
  conn_t *c = arg; (void)err;
  if (!p) { conn_close(pcb, c); return ERR_OK; }
  int n = p->tot_len; if (c->len + n >= REQ_MAX - 1) n = REQ_MAX - 1 - c->len;
  pbuf_copy_partial(p, c->buf + c->len, n, 0); c->len += n; c->buf[c->len] = 0;
  tcp_recved(pcb, p->tot_len); pbuf_free(p);
  const char *he = strstr(c->buf, "\r\n\r\n");
  if (he) { const char *cl = strstr(c->buf, "Content-Length:"); int want = cl ? atoi(cl + 15) : 0;
    if ((int)strlen(he + 4) >= want) { handle(pcb, c); tcp_sent(pcb, on_sent); } }
  return ERR_OK;
}
static void on_err(void *arg, err_t err) { (void)err; free(arg); }
static err_t on_accept(void *arg, struct tcp_pcb *pcb, err_t err) {
  (void)arg; if (err != ERR_OK || !pcb) return ERR_VAL;
  conn_t *c = calloc(1, sizeof *c); if (!c) { tcp_abort(pcb); return ERR_ABRT; }
  tcp_arg(pcb, c); tcp_recv(pcb, on_recv); tcp_err(pcb, on_err); return ERR_OK;
}
void httpd_start(void) {
  if (listen_pcb) return;
  cyw43_arch_lwip_begin();
  struct tcp_pcb *p = tcp_new_ip_type(IPADDR_TYPE_ANY);
  if (p && tcp_bind(p, IP_ANY_TYPE, 80) == ERR_OK) { listen_pcb = tcp_listen_with_backlog(p, 4); tcp_accept(listen_pcb, on_accept); }
  cyw43_arch_lwip_end();
  printf("httpd: %s\n", listen_pcb ? "listening on :80" : "failed");
}
