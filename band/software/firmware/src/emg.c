#include "emg.h"
#include "config.h"
#include "pins.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/sync.h"

// Motion artefact: when the dry plate slides, the electrode-skin junction voltage jumps, and that jump is bigger
// than the muscle signal. It is slow (below ~20 Hz) while muscle is 20-500 Hz, so each channel goes through a 20 Hz
// high-pass (two cascaded first-order sections at 1 kHz, -12 dB/oct) before rectification. This also removes the
// 1.5 V centre, so no fixed centre subtraction is needed any more.
static const float HP_A = 0.8817f;          // RC / (RC + dt): RC = 1 / (2 pi 20 Hz), dt = 1 ms
typedef struct { float x1, y1, x2, y2; } hp2_t;
static hp2_t hp[2];
static volatile float acc1, acc2;           // sum of |high-passed volts| since the last frame
static volatile uint32_t n;                 // sample count

static inline float hp_run(hp2_t *h, float x) {
  float y = HP_A * (h->y1 + x - h->x1); h->x1 = x; h->y1 = y;
  float z = HP_A * (h->y2 + y - h->x2); h->x2 = y; h->y2 = z;
  return z;
}

void emg_init(void) { acc1 = acc2 = 0; n = 0; hp[0] = hp[1] = (hp2_t){0, 0, 0, 0}; }

void emg_sample(void) {
  const float scale = 3.3f / 4095.0f;
  adc_select_input(ADC_EMG1); float v1 = adc_read() * scale;
  adc_select_input(ADC_EMG2); float v2 = adc_read() * scale;
  acc1 += fabsf(hp_run(&hp[0], v1)); acc2 += fabsf(hp_run(&hp[1], v2)); n++;
}

effort_t emg_frame(void) {
  uint32_t s = save_and_disable_interrupts();
  float a1 = acc1, a2 = acc2; uint32_t k = n; acc1 = acc2 = 0; n = 0;
  restore_interrupts(s);
  effort_t e = {0, 0};
  if (k) { e.flex = a1 / k; e.ext = a2 / k; }
  return e;
}

// Jolt gate: a sudden arm movement (gyro magnitude above JOLT_DPS) marks the next JOLT_HOLD_MS of effort as
// untrusted; the last trusted effort is held instead of whatever the plates produced while they moved.
#define JOLT_DPS      250.0f
#define JOLT_HOLD_MS  150
#define BUZZ_HOLD_MS  40
effort_t emg_gate(effort_t e, float gx, float gy, float gz, bool imu_valid, bool motor_on) {
  static effort_t held; static absolute_time_t until; static bool have;
  if (imu_valid && (gx * gx + gy * gy + gz * gz) > JOLT_DPS * JOLT_DPS) until = make_timeout_time_ms(JOLT_HOLD_MS);
  if (motor_on) {                                            // the buzz itself: hold through it and 40 ms after
    absolute_time_t t = make_timeout_time_ms(BUZZ_HOLD_MS);
    if (absolute_time_diff_us(until, t) > 0) until = t;
  }
  bool blank = have && absolute_time_diff_us(get_absolute_time(), until) > 0;
  if (!blank) { held = e; have = true; return e; }
  return held;
}

intent_t emg_classify(effort_t e) {
  static intent_t cur = INTENT_REST, cand = INTENT_REST; static uint8_t run;
  bool fh = e.flex > cfg.flex_on, eh = e.ext > cfg.ext_on, fl = e.flex < cfg.flex_off, el = e.ext < cfg.ext_off;
  intent_t raw;
  if (fh && eh) raw = INTENT_COCON; else if (fh) raw = INTENT_CLOSE; else if (eh) raw = INTENT_OPEN;
  else if (fl && el) raw = INTENT_REST; else raw = cur;            // inside the hysteresis band: keep state
  if (raw == cand) { if (run < 255) run++; } else { cand = raw; run = 1; }
  if (run >= (raw == INTENT_REST ? 5 : 3)) cur = cand;
  return cur;
}

float emg_force(effort_t e) {
  float f = (e.flex - cfg.flex_on) / (cfg.flex_max - cfg.flex_on);
  if (f < 0) f = 0; if (f > 1) f = 1;
  return f * cfg.force_limit;
}

bool emg_cocon_double(intent_t cur) {
  static bool was; static absolute_time_t last; static uint8_t count;
  bool now = (cur == INTENT_COCON), fired = false;
  if (now && !was) {
    if (count && absolute_time_diff_us(last, get_absolute_time()) < 1000000) { fired = true; count = 0; }
    else { count = 1; last = get_absolute_time(); }
  }
  was = now; return fired;
}

// ---------------------------------------------------------------- calibration
static struct { cal_phase_t phase; float sum_f, sum_e, max_f, max_e; uint32_t k; } cal;
static float rest_f, rest_e, close_f, open_e; static uint8_t have;   // bit0 rest, bit1 close, bit2 open

void emg_cal_start(cal_phase_t p) { cal.phase = p; cal.sum_f = cal.sum_e = cal.max_f = cal.max_e = 0; cal.k = 0; }
void emg_cal_feed(effort_t e) {
  if (cal.phase == CAL_NONE) return;
  cal.sum_f += e.flex; cal.sum_e += e.ext; cal.k++;
  if (e.flex > cal.max_f) cal.max_f = e.flex; if (e.ext > cal.max_e) cal.max_e = e.ext;
  if (cal.k >= 10000 / FRAME_MS) {                                   // 10 s captured
    float mf = cal.sum_f / cal.k, me = cal.sum_e / cal.k;
    switch (cal.phase) {
      case CAL_REST:  rest_f = mf; rest_e = me; have |= 1; break;
      case CAL_CLOSE: close_f = mf; have |= 2; break;                 // mean of a sustained fist
      case CAL_OPEN:  open_e = me; have |= 4; break;
      default: break;
    }
    cal.phase = CAL_NONE;
  }
}
bool emg_cal_apply(void) {
  if (have != 7) return false;
  cfg.flex_on = rest_f + 0.40f * (close_f - rest_f); cfg.flex_off = rest_f + 0.25f * (close_f - rest_f);
  cfg.ext_on  = rest_e + 0.40f * (open_e - rest_e);  cfg.ext_off  = rest_e + 0.25f * (open_e - rest_e);
  cfg.flex_max = close_f;
  have = 0;
  return config_save();
}
const char *emg_cal_json(char *b, int n) {
  snprintf(b, n, "{\"phase\":%d,\"have\":%d,\"rest\":[%.3f,%.3f],\"close\":%.3f,\"open\":%.3f,\"k\":%lu}",
           cal.phase, have, rest_f, rest_e, close_f, open_e, (unsigned long)cal.k);
  return b;
}
