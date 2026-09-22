#include "modes.h"
#include "config.h"
#include "io.h"
#include "emg.h"
#include "imu.h"
#include "net.h"
#include "factum.h"
#include "hand.h"
#include "wheel.h"
#include "ble_mouse.h"
#include "wire.h"
#include "cfgsrv.h"
#include <math.h>
#include <stdio.h>
#include "pico/stdlib.h"

#define KEEPALIVE_MS 250

static band_mode_t mode, wireless_mode = MODE_HAND_FACTUM;
static uint32_t seq, t0, last_keep, last_hand_post;
static intent_t intent = INTENT_REST, last_sent = INTENT_REST; static float last_force = -1;
static bool hand_empty = true, sta_shown; static effort_t last_effort;

static uint32_t now_ms(void) { return to_ms_since_boot(get_absolute_time()); }
static rgb_t slot_colour(void) { static const rgb_t c[4] = { LED_BLUE, LED_CYAN, LED_MAGENTA, LED_WHITE }; return c[cfg.bt_slot & 3]; }

static void enter(band_mode_t m) {
  mode = m;
  if (m != MODE_HAND_WIRED) { wireless_mode = m; if (cfg.last_mode != m) { cfg.last_mode = m; config_save(); } }
  switch (m) {
    case MODE_HAND_WIRED: ble_mouse_stop(); net_stop(); led_set(LED_AMBER); break;        // cord in: radios off
    case MODE_HAND_FACTUM: ble_mouse_stop(); led_blink(LED_GREEN, 100, 900); net_start_sta(); sta_shown = false; break;
    case MODE_HAND_DIRECT: ble_mouse_stop(); net_start_ap(); cfgsrv_start(); led_blink(LED_GREEN, 100, 100); break;
    case MODE_MOUSE: net_stop(); ble_mouse_start(cfg.bt_slot); led_blink(slot_colour(), 100, 900); break;
    default: break;
  }
  buzz_pattern(2);
}

void modes_init(band_mode_t start) { t0 = now_ms(); enter(start < MODE_COUNT ? start : MODE_HAND_FACTUM); }
void modes_switch(band_mode_t m) { if (mode == MODE_HAND_WIRED || m >= MODE_COUNT) return; enter(m); }
band_mode_t modes_current(void) { return mode; }
effort_t modes_last_effort(void) { return last_effort; }
intent_t modes_last_intent(void) { return intent; }

void modes_estop(void) {
  led_blink(LED_RED, 100, 100); buzz(2000);
  if (mode == MODE_MOUSE) return;
  hand_estop(); factum_send_estop(seq, now_ms() - t0);
}

static void wire_check(void) {
  bool w = wire_present();
  if (w && mode != MODE_HAND_WIRED) { enter(MODE_HAND_WIRED); buzz_pattern(3); }
  else if (!w && mode == MODE_HAND_WIRED) enter(wireless_mode);
}

// hand modes: the band is the only commander; Factum just listens
static void hand_tick(effort_t e, imu_t m) {
  uint32_t now = now_ms();
  intent = emg_classify(e);
  emg_cal_feed(e);
  wheel_tick(intent, m, hand_empty, now);
  if (!wheel_open()) {
    float force = emg_force(e);
    if (intent != last_sent) {
      if (intent == INTENT_CLOSE) { hand_close(force); hand_empty = false; }
      else if ((intent == INTENT_OPEN || intent == INTENT_REST) && last_sent == INTENT_CLOSE) { hand_open(); hand_empty = true; }
      last_sent = intent; last_force = force; last_hand_post = now;
    } else if (intent == INTENT_CLOSE && fabsf(force - last_force) > 0.05f && now - last_hand_post >= 100) {
      hand_close(force); last_force = force; last_hand_post = now;
    }
  }
  hand_service();
  if (now - last_keep >= KEEPALIVE_MS && !http_busy()) { hand_keepalive(now - t0); last_keep = now; }
  if (mode == MODE_HAND_FACTUM) {                                              // LED follows the link
    bool up = net_ready();
    if (up && !sta_shown) { led_set(LED_GREEN); cfgsrv_start(); sta_shown = true; }
    else if (!up && sta_shown) { led_blink(LED_GREEN, 100, 900); sta_shown = false; }
  }
  if (mode == MODE_HAND_FACTUM && net_ready()) factum_send_frame(seq, now - t0, e, m, battery_volts(), intent);
  if (mode != MODE_HAND_WIRED && emg_cocon_double(intent) && !wheel_open()) modes_switch(MODE_MOUSE);
}

// mouse: gyro rates -> cursor, EMG -> buttons. Arm relaxed at the side; tap = recenter is implicit (rate-based).
static void mouse_tick(effort_t e, imu_t m) {
  static uint32_t flex_since, ext_since, last_click; static bool dragging, clutch;
  uint32_t now = now_ms();
  intent = emg_classify(e);
  clutch = e.flex > cfg.flex_off && e.flex < cfg.flex_on;                       // light hold freezes the cursor
  float gx = m.gz, gy = m.gy;                                                    // yaw rate -> X, pitch rate -> Y
  float ax = fabsf(gx) < cfg.mouse_deadzone ? 0 : gx, ay = fabsf(gy) < cfg.mouse_deadzone ? 0 : gy;
  float dx = copysignf(powf(fabsf(ax), cfg.mouse_accel), ax) * cfg.mouse_gain;
  float dy = copysignf(powf(fabsf(ay), cfg.mouse_accel), ay) * cfg.mouse_gain;
  if (clutch || !imu_ok()) dx = dy = 0;
  uint8_t buttons = 0; int8_t wheel = 0;
  if (intent == INTENT_CLOSE) { if (!flex_since) flex_since = now; if (now - flex_since >= 400) dragging = true; }
  else if (flex_since) { uint32_t d = now - flex_since; if (!dragging && d >= 80 && now - last_click >= 250) { buttons |= 1; last_click = now; } dragging = false; flex_since = 0; }
  if (dragging) buttons |= 1;
  if (intent == INTENT_OPEN) { if (!ext_since) ext_since = now; if (now - ext_since >= 400) { wheel = (int8_t)(-ay / 20.0f); dy = 0; } }
  else if (ext_since) { uint32_t d = now - ext_since; if (d >= 80 && d < 400 && now - last_click >= 250) { buttons |= 2; last_click = now; } ext_since = 0; }
  ble_mouse_move((int8_t)dx, (int8_t)dy, wheel, buttons);
  if (ble_mouse_connected()) led_set(slot_colour()); else led_blink(slot_colour(), 100, 900);
  if (emg_cocon_double(intent)) modes_switch(MODE_HAND_DIRECT);
}

void modes_tick(void) {
  effort_t e = emg_frame(); imu_t m = imu_get(); seq++; last_effort = e;
  net_tick(); wire_check();
  if (mode == MODE_MOUSE) mouse_tick(e, m); else hand_tick(e, m);
}
