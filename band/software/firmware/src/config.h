// Persistent settings: one struct in the last flash sector. Factum is the only writer (POST /config with the key).
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define CFG_MAGIC      0x524B4231u   // "RKB1"
#define CFG_VERSION    6
#define CFG_N_WIFI     4
#define CFG_N_BT       4
#define CFG_STR        32
#define CFG_KEY_LEN    32

typedef struct { char ssid[CFG_STR]; char pass[CFG_STR + 32]; } wifi_profile_t;

typedef struct {
  uint32_t magic, version;
  char band_id[16];
  char factum_key[CFG_KEY_LEN];          // shared secret; header X-Factum-Key
  wifi_profile_t wifi[CFG_N_WIFI];       // tried in order
  char factum_host[48]; uint16_t factum_port;        // host name or IP; UDP frames go to factum_port (5005)
  char factum_path[24]; uint16_t factum_http_port;   // HTTP prefix ("/band") and port for the estop POST
  char hand_ip[16];   uint16_t hand_port;            // the hand on the band's own AP (HAND-DIRECT); no other network ever carries band -> hand
  char ap_ssid[CFG_STR], ap_pass[CFG_STR];
  // EMG thresholds (volts of mean |v-1.5| per 20 ms frame)
  float flex_on, flex_off, ext_on, ext_off, flex_max, force_limit;
  // mouse
  float mouse_gain, mouse_deadzone, mouse_accel;
  uint8_t last_mode, bt_slot;
  uint8_t feedback;                      // 0 off, 1 bar colours only, 2 bar + buzz on every onset (default)
  uint8_t bt_addr[CFG_N_BT][6];          // bonded host per slot (all zero = empty)
  uint8_t bt_addr_type[CFG_N_BT];
  uint32_t crc;
} config_t;

extern config_t cfg;

void config_load(void);      // flash -> cfg, defaults if the sector is empty or wrong version
bool config_save(void);      // cfg -> flash (erases + programs one sector; ~50 ms)
void config_defaults(config_t *c);
