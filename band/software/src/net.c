#include "net.h"
#include "config.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"
#include "lwip/udp.h"
#include "lwip/dns.h"
#include "dhcpserver.h"        // from pico-examples/pico_w/wifi/access_point (copy dhcpserver.c/h next to this file)
#include <string.h>
#include <stdio.h>

static bool ready=false, ap_mode=false; static dhcp_server_t dhcp;

bool net_init(void){ if (cyw43_arch_init()) return false; return true; }

bool net_start_sta(uint32_t timeout_ms){
  cyw43_arch_enable_sta_mode();
  ready=false; ap_mode=false;
  for (int i=0;i<4 && !ready;i++) { if (!cfg.wifi_ssid[i][0]) continue;
    ready = cyw43_arch_wifi_connect_timeout_ms(cfg.wifi_ssid[i], cfg.wifi_pass[i], CYW43_AUTH_WPA2_AES_PSK, timeout_ms)==0; }
  return ready;
}

bool net_start_ap(void){
  cyw43_arch_enable_ap_mode(cfg.ap_ssid, cfg.ap_pass, CYW43_AUTH_WPA2_AES_PSK);
  ip4_addr_t gw, mask; IP4_ADDR(&gw,192,168,4,1); IP4_ADDR(&mask,255,255,255,0);
  dhcp_server_init(&dhcp, &gw, &mask);          // hand gets 192.168.4.16 first (pico-examples dhcpserver starts at .16)
  ready=true; ap_mode=true; return true;
}

void net_stop(void){ if (ap_mode) dhcp_server_deinit(&dhcp); cyw43_arch_disable_sta_mode(); cyw43_arch_disable_ap_mode(); ready=false; }
bool net_ready(void){ return ready; }
int net_rssi(void){ int32_t r=0; cyw43_wifi_get_rssi(&cyw43_state, &r); return (int)r; }

// ---- UDP ----
bool udp_send(const char *host, uint16_t port, const char *data, uint16_t len){
  ip_addr_t ip; if (!ipaddr_aton(host, &ip)) { /* hostname: resolve with dns_gethostbyname in a real build */ return false; }
  struct udp_pcb *p = udp_new(); if(!p) return false;
  struct pbuf *b = pbuf_alloc(PBUF_TRANSPORT, len, PBUF_RAM); memcpy(b->payload, data, len);
  cyw43_arch_lwip_begin(); err_t e = udp_sendto(p, b, &ip, port); cyw43_arch_lwip_end();
  pbuf_free(b); udp_remove(p); return e==ERR_OK;
}

// ---- minimal HTTP POST (one in flight at a time) ----
typedef struct { struct tcp_pcb *pcb; char req[512]; http_cb_t cb; int status; } post_t;
static post_t P;
static err_t on_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err){
  if (!p) { tcp_close(pcb); if (P.cb) P.cb(P.status); P.pcb=NULL; return ERR_OK; }
  const char *s = (const char*)p->payload; if (p->len>12 && !strncmp(s,"HTTP/1.",7)) P.status = atoi(s+9);
  tcp_recved(pcb, p->tot_len); pbuf_free(p); return ERR_OK;
}
static err_t on_connected(void *arg, struct tcp_pcb *pcb, err_t err){
  if (err!=ERR_OK) { P.pcb=NULL; if(P.cb) P.cb(-1); return err; }
  tcp_recv(pcb, on_recv); tcp_write(pcb, P.req, strlen(P.req), TCP_WRITE_FLAG_COPY); tcp_output(pcb); return ERR_OK;
}
static void on_err(void *arg, err_t err){ P.pcb=NULL; if(P.cb) P.cb(-1); }
bool http_post(const char *host, uint16_t port, const char *path, const char *body, http_cb_t cb){
  if (P.pcb) return false;                       // busy; caller retries next frame
  ip_addr_t ip; if (!ipaddr_aton(host,&ip)) return false;
  snprintf(P.req, sizeof P.req, "POST %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s", path, host, (int)strlen(body), body);
  P.cb=cb; P.status=0;
  cyw43_arch_lwip_begin();
  P.pcb = tcp_new(); tcp_err(P.pcb, on_err); err_t e = tcp_connect(P.pcb, &ip, port, on_connected);
  cyw43_arch_lwip_end();
  return e==ERR_OK;
}
