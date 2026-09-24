// HTTP server on port 80 (raw lwIP). GET /status is open; everything else needs X-Factum-Key.
//   GET  /status                -> id, mode, battery, uptime, wifi, efforts, intent, imu
//   GET  /config                -> the settable fields
//   POST /config {partial}      -> merge into cfg, save to flash
//   POST /calibrate {"phase":"rest"|"close"|"open"|"apply"}
//   POST /buzz  {"ms":100}      -> pulse the motor
//   POST /mode  {"mode":0..2}   -> HAND_FACTUM / HAND_DIRECT / MOUSE (ignored while wired)
#include "cfgsrv.h"
#include "config.h"
#include "json.h"
#include "io.h"
#include "emg.h"
#include "imu.h"
#include "net.h"
#include "modes.h"
#include "wire.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"

#define REQ_MAX 2048
typedef struct { char buf[REQ_MAX]; int len; } conn_t;
static struct tcp_pcb *listen_pcb;

static int reply(struct tcp_pcb *pcb, int code, const char *body) {
  static char hdr[160];
  const char *txt = code == 200 ? "OK" : code == 401 ? "Unauthorized" : code == 404 ? "Not Found" : "Bad Request";
  int n = snprintf(hdr, sizeof hdr, "HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %u\r\n"
                   "Access-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n", code, txt, (unsigned)strlen(body));
  tcp_write(pcb, hdr, n, TCP_WRITE_FLAG_COPY);
  tcp_write(pcb, body, strlen(body), TCP_WRITE_FLAG_COPY);
  tcp_output(pcb);
  return code;
}

static bool has_key(const char *req) {
  const char *k = strstr(req, "X-Factum-Key:"); if (!k) k = strstr(req, "x-factum-key:");
  if (!k) return false;
  k += 13; while (*k == ' ') k++;
  size_t n = strlen(cfg.factum_key);
  return strncmp(k, cfg.factum_key, n) == 0 && (k[n] == '\r' || k[n] == '\n');
}

static void status_json(char *b, int n) {
  imu_t m = imu_get(); effort_t e = modes_last_effort();
  snprintf(b, n, "{\"id\":\"%s\",\"mode\":%d,\"wired\":%s,\"battery\":%.2f,\"pct\":%d,\"uptime\":%lu,"
           "\"ip\":\"%s\",\"rssi\":%d,\"c\":[%.3f,%.3f],\"intent\":%d,\"imu\":%s,\"o\":[%.1f,%.1f,%.1f]}",
           cfg.band_id, modes_current(), wire_present() ? "true" : "false", battery_volts(), battery_percent(),
           (unsigned long)(to_ms_since_boot(get_absolute_time()) / 1000), net_ip(), net_rssi(), e.flex, e.ext,
           modes_last_intent(), imu_ok() ? "true" : "false", m.yaw, m.pitch, m.roll);
}

static void config_json(char *b, int n) {
  int o = snprintf(b, n, "{\"band_id\":\"%s\",\"factum_ip\":\"%s\",\"factum_port\":%d,\"hand_ip\":\"%s\",\"hand_port\":%d,"
                   "\"ap_ssid\":\"%s\",\"flex_on\":%.3f,\"flex_off\":%.3f,\"ext_on\":%.3f,\"ext_off\":%.3f,\"flex_max\":%.3f,"
                   "\"force_limit\":%.2f,\"mouse_gain\":%.3f,\"mouse_deadzone\":%.1f,\"mouse_accel\":%.2f,\"last_mode\":%d,"
                   "\"bt_slot\":%d,\"wifi\":[", cfg.band_id, cfg.factum_ip, cfg.factum_port, cfg.hand_ip, cfg.hand_port,
                   cfg.ap_ssid, cfg.flex_on, cfg.flex_off, cfg.ext_on, cfg.ext_off, cfg.flex_max, cfg.force_limit,
                   cfg.mouse_gain, cfg.mouse_deadzone, cfg.mouse_accel, cfg.last_mode, cfg.bt_slot);
  for (int i = 0; i < CFG_N_WIFI && o < n; i++)
    o += snprintf(b + o, n - o, "%s{\"ssid\":\"%s\"}", i ? "," : "", cfg.wifi[i].ssid);   // passwords never leave the band
  snprintf(b + o, n - o, "]}");
}

static void merge_config(const char *body) {
  float f; char s[64]; size_t len;
  if (json_get_str(body, "band_id", s, sizeof s)) strncpy(cfg.band_id, s, sizeof cfg.band_id - 1);
  if (json_get_str(body, "factum_key", s, sizeof s)) strncpy(cfg.factum_key, s, sizeof cfg.factum_key - 1);
  if (json_get_str(body, "factum_ip", s, sizeof s)) strncpy(cfg.factum_ip, s, 15);
  if (json_get_str(body, "hand_ip", s, sizeof s)) strncpy(cfg.hand_ip, s, 15);
  if (json_get_str(body, "ap_ssid", s, sizeof s)) strncpy(cfg.ap_ssid, s, CFG_STR - 1);
  if (json_get_str(body, "ap_pass", s, sizeof s)) strncpy(cfg.ap_pass, s, CFG_STR - 1);
  if (json_get_num(body, "factum_port", &f)) cfg.factum_port = (uint16_t)f;
  if (json_get_num(body, "hand_port", &f)) cfg.hand_port = (uint16_t)f;
  if (json_get_num(body, "flex_on", &f)) cfg.flex_on = f;   if (json_get_num(body, "flex_off", &f)) cfg.flex_off = f;
  if (json_get_num(body, "ext_on", &f)) cfg.ext_on = f;     if (json_get_num(body, "ext_off", &f)) cfg.ext_off = f;
  if (json_get_num(body, "flex_max", &f)) cfg.flex_max = f; if (json_get_num(body, "force_limit", &f)) cfg.force_limit = f;
  if (json_get_num(body, "mouse_gain", &f)) cfg.mouse_gain = f;
  if (json_get_num(body, "mouse_deadzone", &f)) cfg.mouse_deadzone = f;
  if (json_get_num(body, "mouse_accel", &f)) cfg.mouse_accel = f;
  const char *w = json_get_arr_obj(body, "wifi", 0, &len);
  if (w) {                                                   // a wifi list replaces the whole list
    memset(cfg.wifi, 0, sizeof cfg.wifi);
    for (int i = 0; i < CFG_N_WIFI; i++) {
      w = json_get_arr_obj(body, "wifi", i, &len); if (!w) break;
      char obj[160]; if (len >= sizeof obj) len = sizeof obj - 1; memcpy(obj, w, len); obj[len] = 0;
      json_get_str(obj, "ssid", cfg.wifi[i].ssid, sizeof cfg.wifi[i].ssid);
      json_get_str(obj, "pass", cfg.wifi[i].pass, sizeof cfg.wifi[i].pass);
    }
  }
}

static void handle(struct tcp_pcb *pcb, conn_t *c) {
  static char out[1024]; char *req = c->buf; req[c->len] = 0;
  char method[8] = {0}, path[32] = {0};
  sscanf(req, "%7s %31s", method, path);
  const char *body = strstr(req, "\r\n\r\n"); body = body ? body + 4 : "";
  bool get = !strcmp(method, "GET"), post = !strcmp(method, "POST");
  if (get && !strcmp(path, "/status")) { status_json(out, sizeof out); reply(pcb, 200, out); return; }
  if (!has_key(req)) { reply(pcb, 401, "{\"error\":\"X-Factum-Key required\"}"); return; }
  if (get && !strcmp(path, "/config")) { config_json(out, sizeof out); reply(pcb, 200, out); return; }
  if (post && !strcmp(path, "/config")) {
    merge_config(body); bool ok = config_save();
    reply(pcb, ok ? 200 : 500, ok ? "{\"saved\":true}" : "{\"saved\":false}"); return;
  }
  if (post && !strcmp(path, "/calibrate")) {
    char ph[16] = {0}; json_get_str(body, "phase", ph, sizeof ph); bool ok = true;
    if (!strcmp(ph, "rest")) emg_cal_start(CAL_REST); else if (!strcmp(ph, "close")) emg_cal_start(CAL_CLOSE);
    else if (!strcmp(ph, "open")) emg_cal_start(CAL_OPEN); else if (!strcmp(ph, "apply")) ok = emg_cal_apply();
    else { reply(pcb, 400, "{\"error\":\"phase\"}"); return; }
    emg_cal_json(out, sizeof out); reply(pcb, ok ? 200 : 409, out); return;
  }
  if (post && !strcmp(path, "/buzz")) { float ms = 100; json_get_num(body, "ms", &ms); buzz((uint16_t)ms); reply(pcb, 200, "{\"ok\":true}"); return; }
  if (post && !strcmp(path, "/mode")) {
    float m = -1; json_get_num(body, "mode", &m);
    if (m < 0 || m >= MODE_COUNT) { reply(pcb, 400, "{\"error\":\"mode\"}"); return; }
    modes_switch((band_mode_t)(int)m); reply(pcb, 200, "{\"ok\":true}"); return;
  }
  reply(pcb, 404, "{\"error\":\"no such endpoint\"}");
}

static void conn_close(struct tcp_pcb *pcb, conn_t *c) {
  tcp_arg(pcb, NULL); tcp_recv(pcb, NULL); tcp_err(pcb, NULL); tcp_sent(pcb, NULL);
  free(c); if (tcp_close(pcb) != ERR_OK) tcp_abort(pcb);
}
static err_t on_sent(void *arg, struct tcp_pcb *pcb, u16_t len) { (void)len; conn_close(pcb, arg); return ERR_OK; }
static err_t on_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
  conn_t *c = arg; (void)err;
  if (!p) { conn_close(pcb, c); return ERR_OK; }
  int n = p->tot_len; if (c->len + n >= REQ_MAX - 1) n = REQ_MAX - 1 - c->len;
  pbuf_copy_partial(p, c->buf + c->len, n, 0); c->len += n; c->buf[c->len] = 0;
  tcp_recved(pcb, p->tot_len); pbuf_free(p);
  const char *hdr_end = strstr(c->buf, "\r\n\r\n");
  if (hdr_end) {
    const char *cl = strstr(c->buf, "Content-Length:");
    int want = cl ? atoi(cl + 15) : 0;
    if ((int)strlen(hdr_end + 4) >= want) { handle(pcb, c); tcp_sent(pcb, on_sent); }
  }
  return ERR_OK;
}
static void on_err(void *arg, err_t err) { (void)err; free(arg); }
static err_t on_accept(void *arg, struct tcp_pcb *pcb, err_t err) {
  (void)arg; if (err != ERR_OK || !pcb) return ERR_VAL;
  conn_t *c = calloc(1, sizeof *c); if (!c) { tcp_abort(pcb); return ERR_ABRT; }
  tcp_arg(pcb, c); tcp_recv(pcb, on_recv); tcp_err(pcb, on_err);
  return ERR_OK;
}

void cfgsrv_start(void) {
  if (listen_pcb) return;
  cyw43_arch_lwip_begin();
  struct tcp_pcb *p = tcp_new_ip_type(IPADDR_TYPE_ANY);
  if (p && tcp_bind(p, IP_ANY_TYPE, 80) == ERR_OK) { listen_pcb = tcp_listen_with_backlog(p, 2); tcp_accept(listen_pcb, on_accept); }
  else if (p) tcp_close(p);
  cyw43_arch_lwip_end();
  printf("cfgsrv: %s\n", listen_pcb ? "listening on :80" : "failed");
}
