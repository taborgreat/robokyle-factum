// EMG band - Pico W. Modes: HAND-FACTUM, HAND-DIRECT, MOUSE, HAND-WIRED (automatic). See ../README.md.
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/watchdog.h"
#include "config.h"
#include "pins.h"
#include "io.h"
#include "emg.h"
#include "imu.h"
#include "net.h"
#include "modes.h"
#include "ble_mouse.h"
#include "wire.h"

static bool emg_timer_cb(struct repeating_timer *t) { (void)t; emg_sample(); return true; }

int main(void) {
  stdio_init_all();
  sleep_ms(300);
  printf("\nrobokyle band %s\n", __DATE__);
  config_load();
  io_init(); emg_init(); wire_init();
  if (!imu_init()) led_blink(LED_AMBER, 50, 50);     // runs without the IMU; wheel and mouse degrade
  if (!net_init()) { led_blink(LED_RED, 100, 100); while (1) { io_tick(); sleep_ms(5); } }
  struct repeating_timer tmr;
  add_repeating_timer_us(-1000000 / EMG_SAMPLE_HZ, emg_timer_cb, NULL, &tmr);
  watchdog_enable(8000, 1);
  modes_init((band_mode_t)cfg.last_mode);
  absolute_time_t next = make_timeout_time_ms(FRAME_MS);
  while (true) {
    imu_poll(); io_tick(); wire_poll(to_ms_since_boot(get_absolute_time()));
    band_mode_t m = modes_current();
    switch (button_poll()) {
      case BTN_TAP:      break;                                                     // recentre is implicit (rate cursor)
      case BTN_DOUBLE:   if (m == MODE_MOUSE) { uint8_t s = (cfg.bt_slot + 1) & 3; ble_mouse_set_slot(s); config_save(); buzz_pattern(s + 1); } break;
      case BTN_HOLD_1S:  modes_switch((band_mode_t)((m + 1) % MODE_COUNT)); break;
      case BTN_HOLD_2S:  if (m != MODE_MOUSE) modes_estop(); break;
      case BTN_HOLD_3S:  if (m == MODE_MOUSE) { ble_mouse_pair(); led_blink(LED_WHITE, 100, 100); buzz(500); } break;
      default: break;
    }
    if (time_reached(next)) { next = delayed_by_ms(next, FRAME_MS); modes_tick(); watchdog_update(); }
    sleep_us(500);
  }
}
