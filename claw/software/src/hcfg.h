#pragma once
#include <stdint.h>
typedef struct { uint32_t magic; char wifi_ssid[4][33], wifi_pass[4][65]; char factum_key[33];
  uint16_t pos_open, pos_closed, torque_min, torque_max, speed; uint32_t crc; } hand_config_t;
extern hand_config_t hc;
void hcfg_load(void); void hcfg_save(void); void hcfg_defaults(void);
int  hcfg_json(char *o,int n); void hcfg_merge(const char *body);
