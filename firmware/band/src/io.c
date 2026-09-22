#include "io.h"
#include "pins.h"
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/pio.h"
#include "ws2812.pio.h"

static PIO ws_pio; static uint ws_sm;
static uint32_t now_ms(void) { return to_ms_since_boot(get_absolute_time()); }

// ---------------------------------------------------------------- WS2812
static rgb_t led_colour, led_shown[N_PIXELS];
static uint16_t blink_on, blink_off; static bool blink_phase; static uint32_t blink_t;

static void ws_write(void) {
  for (int i = 0; i < N_PIXELS; i++) {
    rgb_t c = led_shown[i];
    pio_sm_put_blocking(ws_pio, ws_sm, ((uint32_t)c.g << 24) | ((uint32_t)c.r << 16) | ((uint32_t)c.b << 8));
  }
}
static void show_all(rgb_t c) { for (int i = 0; i < N_PIXELS; i++) led_shown[i] = c; ws_write(); }

void led_set(rgb_t c) { led_colour = c; blink_on = blink_off = 0; show_all(c); }
void led_blink(rgb_t c, uint16_t on_ms, uint16_t off_ms) {
  led_colour = c; blink_on = on_ms; blink_off = off_ms; blink_phase = true; blink_t = now_ms(); show_all(c);
}
void led_pixel(uint8_t i, rgb_t c) { if (i < N_PIXELS) { led_shown[i] = c; ws_write(); } }

static void led_tick(void) {
  if (!blink_on) return;
  uint32_t t = now_ms();
  if (blink_phase && t - blink_t >= blink_on) { blink_phase = false; blink_t = t; show_all(LED_OFF); }
  else if (!blink_phase && t - blink_t >= blink_off) { blink_phase = true; blink_t = t; show_all(led_colour); }
}

// ---------------------------------------------------------------- motor
static uint32_t buzz_until; static uint8_t buzz_left; static uint32_t buzz_next;
#define BUZZ_SHORT 80
#define BUZZ_GAP   120

void buzz(uint16_t ms) { gpio_put(PIN_MOTOR, 1); buzz_until = now_ms() + ms; buzz_left = 0; }
void buzz_pattern(uint8_t n) { if (!n) return; buzz(BUZZ_SHORT); buzz_left = n - 1; buzz_next = buzz_until + BUZZ_GAP; }
bool buzz_busy(void) { return gpio_get(PIN_MOTOR) || buzz_left; }

static void buzz_tick(void) {
  uint32_t t = now_ms();
  if (gpio_get(PIN_MOTOR) && (int32_t)(t - buzz_until) >= 0) gpio_put(PIN_MOTOR, 0);
  if (buzz_left && !gpio_get(PIN_MOTOR) && (int32_t)(t - buzz_next) >= 0) {
    buzz_left--; gpio_put(PIN_MOTOR, 1); buzz_until = t + BUZZ_SHORT; buzz_next = buzz_until + BUZZ_GAP;
  }
}

// ---------------------------------------------------------------- button
// Gestures: tap (press+release, no second press within 350 ms), double (second press starts within 350 ms of
// the first release), holds fire ONCE when 1 s / 2 s / 3 s is crossed, while still held, so the buzz cue lands
// during the hold. Releasing after a hold produces nothing.
static bool btn_down, btn_raw_last, second; static uint32_t btn_t_down, btn_t_up, btn_debounce;
static uint8_t hold_stage; static bool tap_pending; static btn_event_t pending;

static void button_tick(void) {
  uint32_t t = now_ms();
  bool raw = !gpio_get(PIN_BUTTON);
  if (raw != btn_raw_last) { btn_raw_last = raw; btn_debounce = t; }
  if (t - btn_debounce < 20) return;
  if (raw && !btn_down) {                                  // press
    btn_down = true; btn_t_down = t; hold_stage = 0;
    second = tap_pending; tap_pending = false;
  }
  if (!raw && btn_down) {                                  // release
    btn_down = false; btn_t_up = t;
    if (hold_stage == 0) { if (second) pending = BTN_DOUBLE; else tap_pending = true; }
    second = false;
  }
  if (btn_down) {
    uint32_t held = t - btn_t_down;
    if (hold_stage == 0 && held >= 1000) { hold_stage = 1; pending = BTN_HOLD_1S; second = false; }
    else if (hold_stage == 1 && held >= 2000) { hold_stage = 2; pending = BTN_HOLD_2S; }
    else if (hold_stage == 2 && held >= 3000) { hold_stage = 3; pending = BTN_HOLD_3S; }
  }
  if (tap_pending && !btn_down && t - btn_t_up >= 350) { tap_pending = false; pending = BTN_TAP; }
}

btn_event_t button_poll(void) { btn_event_t e = pending; pending = BTN_NONE; return e; }

// ---------------------------------------------------------------- battery
static float vbat_filt = 3.9f;
float battery_volts(void) { return vbat_filt; }
uint8_t battery_percent(void) {
  // LiPo open-circuit curve, coarse
  float v = vbat_filt, p;
  if (v >= 4.15f) p = 100; else if (v >= 3.95f) p = 80 + (v - 3.95f) * 100; else if (v >= 3.80f) p = 50 + (v - 3.80f) * 200;
  else if (v >= 3.70f) p = 25 + (v - 3.70f) * 250; else if (v >= 3.50f) p = 5 + (v - 3.50f) * 100; else p = 0;
  return (uint8_t)(p > 100 ? 100 : p);
}
static void battery_tick(void) {
  static uint32_t last; uint32_t t = now_ms();
  if (t - last < 500) return; last = t;
  adc_select_input(ADC_VBAT);
  float v = adc_read() * 3.3f / 4095.0f * 2.0f;
  vbat_filt += (v - vbat_filt) * 0.1f;
}

// ---------------------------------------------------------------- init / tick
void io_init(void) {
  gpio_init(PIN_BUTTON); gpio_set_dir(PIN_BUTTON, GPIO_IN); gpio_pull_up(PIN_BUTTON);
  gpio_init(PIN_MOTOR); gpio_set_dir(PIN_MOTOR, GPIO_OUT); gpio_put(PIN_MOTOR, 0);
  adc_init(); adc_gpio_init(PIN_EMG1); adc_gpio_init(PIN_EMG2); adc_gpio_init(PIN_VBAT);
  ws_pio = pio0; ws_sm = pio_claim_unused_sm(ws_pio, true);
  uint offset = pio_add_program(ws_pio, &ws2812_program);
  ws2812_program_init(ws_pio, ws_sm, offset, PIN_WS2812, 800000);
  show_all(LED_OFF);
  adc_select_input(ADC_VBAT); vbat_filt = adc_read() * 3.3f / 4095.0f * 2.0f;
}

void io_tick(void) { button_tick(); buzz_tick(); led_tick(); battery_tick(); }
