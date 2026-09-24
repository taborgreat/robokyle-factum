// Hand settings in flash. Only Factum writes them (POST /config with X-Factum-Key).
#pragma once
#include <stdint.h>
#include <stdbool.h>
#define HC_MAGIC 0x524B4831u
#define HC_VERSION 1
typedef struct {
  uint32_t magic, version;
  char hand_id[16], factum_key[32];
  struct { char ssid[32], pass[64]; } wifi[4];     // home network first, the band's hotspot second
  uint16_t pos_open, pos_closed;                   // servo counts (0..4095); calibrate on the bench
  uint16_t torque_min, torque_max;                 // 0..1000; preview uses torque_min
  uint16_t speed;                                  // goal speed for open/close
  uint32_t crc;
} hcfg_t;
extern hcfg_t hc;
void hcfg_load(void);
bool hcfg_save(void);
