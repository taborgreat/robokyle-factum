#pragma once
#include <stdbool.h>
#include <stdint.h>
bool net_init(void);                       // cyw43 up, no radio mode yet
bool net_start_sta(uint32_t timeout_ms);   // join home Wi-Fi (MODE_HAND_FACTUM)
bool net_start_ap(void);                   // host the RoboKyle hotspot with DHCP (MODE_HAND_DIRECT)
void net_stop(void);                       // radio off (before MOUSE mode)
bool net_ready(void);
int  net_rssi(void);
// tiny HTTP POST over lwIP raw TCP: fire-and-forget, callback optional
typedef void (*http_cb_t)(int status);
bool http_post(const char *host, uint16_t port, const char *path, const char *body, http_cb_t cb);
bool udp_send(const char *host, uint16_t port, const char *data, uint16_t len);
