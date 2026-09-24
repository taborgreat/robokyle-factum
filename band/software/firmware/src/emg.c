#include "emg.h"
#include "config.h"
#include "pins.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/sync.h"

static const float CENTER = 1.5f;
static volatile uint32_t acc1, acc2, n;     // sum of |code - center| in ADC codes, sample count

void emg_init(void) { acc1 = acc2 = 0; n = 0; }

void emg_sample(void) {
  adc_select_input(ADC_EMG1); int c1 = adc_read();
  adc_select_input(ADC_EMG2); int c2 = adc_read();
  const int center = (int)(CENTER / 3.3f * 4095.0f);
  acc1 += (uint32_t)abs(c1 - center); acc2 += (uint32_t)abs(c2 - center); n++;
}

effort_t emg_frame(void) {
  uint32_t s = save_and_disable_interrupts();
  uint32_t a1 = acc1, a2 = acc2, k = n; acc1 = acc2 = 0; n = 0;
  restore_interrupts(s);
  effort_t e = {0, 0};
  if (k) { const float scale = 3.3f / 4095.0f; e.flex = a1 * scale / k; e.ext = a2 * scale / k; }
  return e;
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
