#include "net.h"
#include "config.h"
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/udp.h"
#include "lwip/tcp.h"
#include "lwip/ip4_addr.h"
#include "lwip/netif.h"
#include "dhcpserver.h"

static bool chip_up, sta_up, ap_up;
static dhcp_server_t dhcp;
static char ip_str[16];

bool net_init(void) {
  if (cyw43_arch_init_with_country(CYW43_COUNTRY_USA)) { printf("net: cyw43 init failed\n"); return false; }
  chip_up = true; return true;
}

// STA join state machine: one profile at a time, 8 s each, then round-robin forever (Kyle walks in and out of
// range; the band must recover on its own).
#define JOIN_TIMEOUT_MS 8000
static int join_idx = -1; static uint32_t join_t0; static bool joining, sta_wanted;

static void join_next(void) {
  for (int tries = 0; tries < CFG_N_WIFI; tries++) {
    join_idx = (join_idx + 1) % CFG_N_WIFI;
    if (!cfg.wifi[join_idx].ssid[0]) continue;
    printf("net: joining %s\n", cfg.wifi[join_idx].ssid);
    if (cyw43_arch_wifi_connect_async(cfg.wifi[join_idx].ssid, cfg.wifi[join_idx].pass, CYW43_AUTH_WPA2_AES_PSK) == 0) {
      joining = true; join_t0 = to_ms_since_boot(get_absolute_time()); return;
    }
  }
  joining = false;
}

void net_start_sta(void) {
  if (!chip_up) return;
  net_stop();
  cyw43_arch_enable_sta_mode();
  sta_wanted = true; sta_up = false; join_idx = -1; join_next();
}

void net_tick(void) {
  if (!sta_wanted) return;
  int st = cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA);
  uint32_t now = to_ms_since_boot(get_absolute_time());
  if (st == CYW43_LINK_UP) {
    if (!sta_up) {
      sta_up = true; joining = false;
      strncpy(ip_str, ip4addr_ntoa(netif_ip4_addr(&cyw43_state.netif[CYW43_ITF_STA])), sizeof ip_str - 1);
      printf("net: %s ip %s\n", cfg.wifi[join_idx].ssid, ip_str);
    }
    return;
  }
  if (sta_up) { sta_up = false; ip_str[0] = 0; printf("net: link lost\n"); joining = false; }
  if (!joining || now - join_t0 > JOIN_TIMEOUT_MS || st < 0) join_next();
}

bool net_start_ap(void) {
  if (!chip_up) return false;
  net_stop();
  cyw43_arch_enable_ap_mode(cfg.ap_ssid, cfg.ap_pass, CYW43_AUTH_WPA2_AES_PSK);
  ip_addr_t gw, mask;
  IP4_ADDR(ip_2_ip4(&gw), 192, 168, 4, 1); IP4_ADDR(ip_2_ip4(&mask), 255, 255, 255, 0);
  dhcp_server_init(&dhcp, &cyw43_state.netif[CYW43_ITF_AP], &gw, &mask);
  strcpy(ip_str, "192.168.4.1");
  ap_up = true; printf("net: AP %s up\n", cfg.ap_ssid);
  return true;
}

void net_stop(void) {
  if (sta_wanted) { cyw43_arch_disable_sta_mode(); sta_up = false; sta_wanted = false; joining = false; }
  if (ap_up) { dhcp_server_deinit(&dhcp); cyw43_arch_disable_ap_mode(); ap_up = false; }
  ip_str[0] = 0;
}

bool net_ready(void) {
  if (ap_up) return true;
  return sta_up && cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA) == CYW43_LINK_UP;
}
int net_rssi(void) { int32_t r = 0; if (sta_up) cyw43_wifi_get_rssi(&cyw43_state, &r); return (int)r; }
const char *net_ip(void) { return ip_str; }

// ---------------------------------------------------------------- UDP
bool udp_send_json(const char *ip, uint16_t port, const char *json) {
  static struct udp_pcb *pcb;
  ip_addr_t dst; if (!ipaddr_aton(ip, &dst)) return false;
  size_t n = strlen(json);
  cyw43_arch_lwip_begin();
  if (!pcb) { pcb = udp_new(); if (!pcb) { cyw43_arch_lwip_end(); return false; } udp_bind(pcb, IP_ADDR_ANY, 0); }
  struct pbuf *p = pbuf_alloc(PBUF_TRANSPORT, n, PBUF_RAM);
  bool ok = false;
  if (p) { memcpy(p->payload, json, n); ok = udp_sendto(pcb, p, &dst, port) == ERR_OK; pbuf_free(p); }
  cyw43_arch_lwip_end();
  return ok;
}

// ---------------------------------------------------------------- HTTP client (one request in flight)
#define HTTP_BUF 1024
static struct { struct tcp_pcb *pcb; char req[HTTP_BUF]; char resp[HTTP_BUF]; int rlen; http_done_t done; void *arg;
                bool busy; uint32_t t0; } h;

static void http_finish(int status) {
  if (h.pcb) { tcp_arg(h.pcb, NULL); tcp_recv(h.pcb, NULL); tcp_err(h.pcb, NULL); tcp_sent(h.pcb, NULL);
               if (tcp_close(h.pcb) != ERR_OK) tcp_abort(h.pcb); h.pcb = NULL; }
  h.busy = false;
  if (h.done) {
    const char *body = strstr(h.resp, "\r\n\r\n"); body = body ? body + 4 : "";
    if (status == 0 && h.rlen >= 12 && !strncmp(h.resp, "HTTP/1.", 7)) status = atoi(h.resp + 9);
    h.done(status, body, h.arg);
  }
}
static err_t http_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
  (void)arg; (void)err;
  if (!p) { h.resp[h.rlen] = 0; http_finish(0); return ERR_OK; }
  int n = p->tot_len; if (h.rlen + n >= HTTP_BUF - 1) n = HTTP_BUF - 1 - h.rlen;
  pbuf_copy_partial(p, h.resp + h.rlen, n, 0); h.rlen += n; h.resp[h.rlen] = 0;
  tcp_recved(pcb, p->tot_len); pbuf_free(p);
  if (strstr(h.resp, "\r\n\r\n")) {                     // headers in; we don't wait for keep-alive closes
    const char *cl = strstr(h.resp, "Content-Length:"); const char *body = strstr(h.resp, "\r\n\r\n") + 4;
    if (!cl || (int)strlen(body) >= atoi(cl + 15)) { http_finish(0); }
  }
  return ERR_OK;
}
static void http_err(void *arg, err_t err) { (void)arg; (void)err; h.pcb = NULL; http_finish(-1); }
static err_t http_connected(void *arg, struct tcp_pcb *pcb, err_t err) {
  (void)arg;
  if (err != ERR_OK) { http_finish(-1); return err; }
  tcp_write(pcb, h.req, strlen(h.req), TCP_WRITE_FLAG_COPY); tcp_output(pcb);
  return ERR_OK;
}

bool http_post(const char *ip, uint16_t port, const char *path, const char *json, http_done_t done, void *arg) {
  if (h.busy) {
    if (to_ms_since_boot(get_absolute_time()) - h.t0 < 1500) return false;   // still in flight
    cyw43_arch_lwip_begin(); http_finish(-2); cyw43_arch_lwip_end();          // stuck: give up on it
  }
  ip_addr_t dst; if (!ipaddr_aton(ip, &dst)) return false;
  size_t n = json ? strlen(json) : 0;
  snprintf(h.req, HTTP_BUF, "POST %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %u\r\n"
           "Connection: close\r\n\r\n%s", path, ip, (unsigned)n, json ? json : "");
  h.done = done; h.arg = arg; h.rlen = 0; h.resp[0] = 0; h.busy = true; h.t0 = to_ms_since_boot(get_absolute_time());
  cyw43_arch_lwip_begin();
  h.pcb = tcp_new_ip_type(IPADDR_TYPE_V4);
  bool ok = false;
  if (h.pcb) {
    tcp_arg(h.pcb, NULL); tcp_recv(h.pcb, http_recv); tcp_err(h.pcb, http_err);
    ok = tcp_connect(h.pcb, &dst, port, http_connected) == ERR_OK;
    if (!ok) http_finish(-1);
  } else h.busy = false;
  cyw43_arch_lwip_end();
  return ok;
}
bool http_busy(void) { return h.busy; }
