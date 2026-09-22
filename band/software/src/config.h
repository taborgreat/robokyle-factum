// EMG band firmware — configuration (pins match band/BUILD.txt; runtime values persist in flash, see config.c)
#pragma once
#include <stdint.h>
#include <stdbool.h>
#define PIN_SENS1 26   // ADC0 flexor
#define PIN_SENS2 27   // ADC1 extensor
#define PIN_VBAT  28   // ADC2 battery divider (2x100k)
#define PIN_SDA    4
#define PIN_SCL    5
#define PIN_BUTTON 14  // to GND, internal pull-up
#define PIN_MOTOR  15  // 1k -> 2N2222 base
#define PIN_LED_R  16
#define PIN_LED_G  17
#define PIN_LED_B  18
#define BNO_ADDR 0x4A  // AD0 -> GND

#define FRAME_MS 20
#define EMG_SAMPLE_HZ 1000
#define KEEPALIVE_MS 250
#define WHEEL_TIMEOUT_MS 3000
#define WHEEL_STILL_MS 1000
#define COCON_MS 150
#define BTN_TAP_MS 250
#define BTN_MODE_MS 1000
#define BTN_ESTOP_MS 2000
#define BTN_PAIR_MS 3000

typedef enum { MODE_HAND_FACTUM = 0, MODE_HAND_DIRECT = 1, MODE_MOUSE = 2, MODE_COUNT, MODE_HAND_WIRED = 3 } band_mode_t;   // WIRED is entered only by the cord, never by the button

typedef struct {
  uint32_t magic;
  char wifi_ssid[4][33], wifi_pass[4][65]; // up to 4 Wi-Fi profiles, tried in order (MODE_HAND_FACTUM)
  char factum_key[33];                     // shared secret; only requests carrying X-Factum-Key: <this> may change config
  char ap_ssid[33], ap_pass[65];          // hotspot the hand joins (MODE_HAND_DIRECT)
  char factum_host[64]; uint16_t factum_port;   // UDP frames
  char hand_host[64];   uint16_t hand_port;     // HTTP to the hand
  char band_id[16];
  float flex_on, flex_off, flex_max, ext_on, ext_off, ext_max, force_limit;
  float mouse_gain, mouse_deadzone, mouse_accel;
  uint8_t bt_slot, last_mode;
  uint8_t grip_count;                     // grips on the wheel (5..8)
  uint16_t cfg_port;                      // config/status HTTP server port (default 80)
  uint32_t crc;
} band_config_t;

extern band_config_t cfg;
void config_load(void); void config_save(void); void config_defaults(void);
