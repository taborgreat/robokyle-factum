// EMG band — Pico W, C SDK. Modes: HAND-FACTUM, HAND-DIRECT, MOUSE. See ../README.md.
#include "pico/stdlib.h"
#include "hardware/watchdog.h"
#include "config.h"
#include "io.h"
#include "emg.h"
#include "imu.h"
#include "net.h"
#include "modes.h"
#include "ble_mouse.h"
#include "wire.h"
#include "cfgsrv.h"

static bool emg_timer_cb(struct repeating_timer *t){ emg_sample(); return true; }

int main(void){
  stdio_init_all();
  config_load();
  io_init(); emg_init(); imu_init(); wire_init();
  if (!net_init()) { led_blink(LED_RED,100,100); while(1) io_tick(); }
  struct repeating_timer tmr; add_repeating_timer_us(-1000000/EMG_SAMPLE_HZ, emg_timer_cb, NULL, &tmr);
  watchdog_enable(8000, 1);
  modes_init((band_mode_t)cfg.last_mode);
  cfgsrv_start();     // listens whenever Wi-Fi is up (home or hotspot); Factum is the only caller with the key
  absolute_time_t next = make_timeout_time_ms(FRAME_MS);
  while (true) {
    imu_poll(); io_tick(); wire_poll(to_ms_since_boot(get_absolute_time())); cfgsrv_tick(to_ms_since_boot(get_absolute_time()));
    btn_event_t b = button_poll();
    band_mode_t m = modes_current();
    switch (b) {
      case BTN_TAP:       /* MOUSE: recenter is implicit with rate-based cursor; HAND: nothing */ break;
      case BTN_DOUBLE:    if (m==MODE_MOUSE) { ble_mouse_set_slot((cfg.bt_slot+1)&3); buzz_pattern(cfg.bt_slot+1); led_blink(slot_color(),100,900); } break;
      case BTN_HOLD_MODE: modes_switch((band_mode_t)((m+1)%MODE_COUNT)); break;
      case BTN_HOLD_LONG: if (m!=MODE_MOUSE) modes_estop(); break;              // works wired too              // 2 s in hand modes = ESTOP
      case BTN_HOLD_PAIR: if (m==MODE_MOUSE) { ble_mouse_pair(); led_blink(LED_WHITE,100,100); buzz(500); } break;
      default: break;
    }
    if (time_reached(next)) { next = delayed_by_ms(next, FRAME_MS); modes_tick(); watchdog_update(); }
    sleep_us(500);
  }
}
