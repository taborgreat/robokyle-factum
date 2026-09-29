#include "feedback.h"
#include "io.h"
#include "config.h"
#include "pins.h"
#include <math.h>
#include "pico/stdlib.h"

#define FB_MAX   80          // never above this per channel: the 3V3 rail budget (3 pixels, ~40 mA total at 80)
#define FB_MIN   28          // visible floor once a side is active

static rgb_t scale(rgb_t c, float k) {
  if (k < 0) k = 0; if (k > 1) k = 1;
  return RGB((uint8_t)(c.r * k), (uint8_t)(c.g * k), (uint8_t)(c.b * k));
}
static float level(float effort, float on, float max) {          // 0 at the on-threshold .. 1 at the calibrated max
  float d = max - on; if (d < 0.01f) d = 0.01f;
  float k = (effort - on) / d; return k < 0 ? 0 : (k > 1 ? 1 : k);
}

void feedback_tick(effort_t e, intent_t cur, bool wheel_is_open, uint32_t now) {
  static intent_t prev = INTENT_REST; static bool owning;
  uint8_t lvl = cfg.feedback;
  if (!lvl) { if (owning) { led_override(false); owning = false; } prev = cur; return; }

  // haptics on onsets; the wheel has its own cues, and never on top of a running buzz
  if (lvl >= 2 && cur != prev && !wheel_is_open && !buzz_busy()) {
    if (cur == INTENT_CLOSE || cur == INTENT_OPEN) buzz(30);
    else if (cur == INTENT_COCON) buzz(90);
  }
  prev = cur;

  rgb_t px[N_PIXELS]; bool show = true;
  if (cur == INTENT_CLOSE || cur == INTENT_OPEN || cur == INTENT_COCON) {
    float kf = level(e.flex, cfg.flex_on, cfg.flex_max), ke = level(e.ext, cfg.ext_on, cfg.flex_max);
    float k = (FB_MIN + (FB_MAX - FB_MIN) * fmaxf(kf, ke)) / 255.0f;
    rgb_t base = cur == INTENT_CLOSE ? RGB(255, 200, 0) : (cur == INTENT_OPEN ? RGB(0, 90, 255) : RGB(0, 255, 40));
    rgb_t c = scale(base, k);
    for (int i = 0; i < N_PIXELS; i++) px[i] = c;
  } else if (vbus_present()) {                                   // USB in, nothing happening: battery gauge
    float vb = battery_volts();
    float breathe = 0.55f + 0.45f * sinf(now * 6.2832f / 2400.0f);
    if (vb < 2.5f) {                                             // switch off: the divider reads nothing
      for (int i = 0; i < N_PIXELS; i++) px[i] = LED_OFF;
      px[0] = scale(RGB(255, 110, 0), 0.22f * breathe);          // amber breathing = on USB, switch off
    } else {
      uint8_t p = battery_percent(); int lit = p > 66 ? 3 : (p > 33 ? 2 : 1);
      for (int i = 0; i < N_PIXELS; i++) px[i] = i < lit ? scale(RGB(0, 255, 30), 0.16f) : LED_OFF;
      px[lit - 1] = scale(RGB(0, 255, 30), 0.16f * breathe);     // the top lit pixel breathes: charging
    }
  } else show = false;

  if (show) { if (!owning) { led_override(true); owning = true; } led_pixels(px); }
  else if (owning) { led_override(false); owning = false; }
}
