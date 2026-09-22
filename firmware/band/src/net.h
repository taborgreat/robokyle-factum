// Wi-Fi (STA joins a profile list, AP hosts "RoboKyle"), UDP send, and a tiny non-blocking HTTP/1.1 client.
#pragma once
#include <stdbool.h>
#include <stdint.h>

bool net_init(void);                       // cyw43 up; radios idle
void net_start_sta(void);                  // non-blocking: tries cfg.wifi[] in order; poll net_ready()
void net_tick(void);                       // advances the join state machine; call from the main loop
bool net_start_ap(void);                   // 192.168.4.1/24 with DHCP
void net_stop(void);                       // leave / stop AP; keeps the chip up for BLE
bool net_ready(void);
int  net_rssi(void);
const char *net_ip(void);

bool udp_send_json(const char *ip, uint16_t port, const char *json);

// One in-flight HTTP request at a time (raw lwIP TCP). done(status, body) is called from the lwIP context.
typedef void (*http_done_t)(int status, const char *body, void *arg);
bool http_post(const char *ip, uint16_t port, const char *path, const char *json, http_done_t done, void *arg);
bool http_busy(void);
