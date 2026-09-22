#include "modes.h"
#include "io.h"
#include "emg.h"
#include "imu.h"
#include "net.h"
#include "factum.h"
#include "hand.h"
#include "wheel.h"
#include "ble_mouse.h"
#include "wire.h"
#include "pico/stdlib.h"
#include <math.h>

static band_mode_t mode, wireless_mode; static uint32_t seq=0, t0, last_keep=0, last_hand_post=0;
static intent_t intent=INTENT_REST, last_sent=INTENT_REST; static float last_force=-1;
static bool hand_empty=true;
intent_t g_last_intent=INTENT_REST; effort_t g_last_effort;

static uint32_t now_ms(void){ return to_ms_since_boot(get_absolute_time()); }

static void enter(band_mode_t m){
  mode=m;
  if (m!=MODE_HAND_WIRED) { wireless_mode=m; cfg.last_mode=m; config_save(); }
  switch(m){
    case MODE_HAND_WIRED:  ble_mouse_stop(); net_stop(); led_set(LED_AMBER); break;   // cord in: radios off, hand only
    case MODE_HAND_FACTUM: ble_mouse_stop(); led_blink(LED_GREEN,100,900); if(!net_start_sta(8000)) { led_blink(LED_RED,200,200); } else led_set(LED_GREEN); break;
    case MODE_HAND_DIRECT: ble_mouse_stop(); net_stop(); net_start_ap(); led_blink(LED_GREEN,100,100); break;
    case MODE_MOUSE:       net_stop(); ble_mouse_start(cfg.bt_slot); led_blink(slot_color(), 100, 900); break;
    default: break;
  }
  buzz_pattern(2);
}
led_color_t slot_color(void){ static const led_color_t c[4]={LED_BLUE,LED_CYAN,LED_MAGENTA,LED_WHITE}; return c[cfg.bt_slot&3]; }

void modes_init(band_mode_t start){ t0=now_ms(); enter(start); }
void modes_switch(band_mode_t m){ if (mode==MODE_HAND_WIRED) return; enter(m); }   // button/muscle mode changes are ignored while the cord is in
void modes_wire_check(void){
  bool w = wire_present();
  if (w && mode!=MODE_HAND_WIRED) { enter(MODE_HAND_WIRED); buzz_pattern(3); }
  else if (!w && mode==MODE_HAND_WIRED) { enter(wireless_mode); }
}
band_mode_t modes_current(void){ return mode; }

void modes_estop(void){
  led_blink(LED_RED,100,100); buzz(2000);
  if (mode==MODE_MOUSE) return;
  hand_estop(); factum_send_estop(seq, now_ms()-t0);
}

// --- hand modes: band is the sole commander; Factum only listens (in HAND_FACTUM) ---
static void hand_tick(effort_t e, imu_t m){
  uint32_t now = now_ms();
  intent = emg_classify(e); g_last_intent=intent;
  wheel_tick(intent, m, hand_empty, now);
  if (!wheel_open()) {
    float force = emg_force(e);
    if (intent!=last_sent) {
      if (intent==INTENT_CLOSE) { hand_close(force); hand_empty=false; }
      else if (intent==INTENT_OPEN || intent==INTENT_REST) { if (last_sent==INTENT_CLOSE) { hand_open(); hand_empty=true; } }
      last_sent=intent; last_force=force; last_hand_post=now;
    } else if (intent==INTENT_CLOSE && fabsf(force-last_force)>0.05f && now-last_hand_post>=100) { hand_close(force); last_force=force; last_hand_post=now; }
  }
  if (now-last_keep>=KEEPALIVE_MS && !hand_busy_guard()) { hand_keepalive(now-t0); last_keep=now; }
  if (mode==MODE_HAND_FACTUM && net_ready()) factum_send_frame(seq, now-t0, e, m, battery_volts(), intent);
  if (emg_cocon_double(intent) && !wheel_open()) modes_switch(MODE_MOUSE);   // hands-free mode switch (ignored when wired)
}
bool hand_busy_guard(void){ return false; }   // http_post refuses when busy; keepalive simply retries next frame

// --- mouse: gyro rates -> cursor deltas, EMG -> buttons ---
static void mouse_tick(effort_t e, imu_t m){
  static uint32_t flex_since=0, ext_since=0, last_click=0, last_lclick=0; static bool dragging=false, clutch=false;
  uint32_t now=now_ms();
  intent = emg_classify(e);
  // clutch: light flexor hold (above off, below on) freezes the cursor
  clutch = (e.flex > cfg.flex_off && e.flex < cfg.flex_on);
  float gx = m.gz, gy = m.gy;                              // VERIFY axis mapping on the arm: yaw rate -> X, pitch rate -> Y
  float ax=fabsf(gx)<cfg.mouse_deadzone?0:gx, ay=fabsf(gy)<cfg.mouse_deadzone?0:gy;
  float dx = copysignf(powf(fabsf(ax), cfg.mouse_accel), ax) * cfg.mouse_gain;
  float dy = copysignf(powf(fabsf(ay), cfg.mouse_accel), ay) * cfg.mouse_gain;
  if (clutch) dx=dy=0;
  if (dx>127) dx=127; if (dx<-127) dx=-127; if (dy>127) dy=127; if (dy<-127) dy=-127;
  uint8_t buttons=0; int8_t wheel=0;
  // left: flexor burst >=80 ms then release (refractory 250 ms); hold >400 ms = drag
  if (intent==INTENT_CLOSE) { if(!flex_since) flex_since=now; if (now-flex_since>=400) { dragging=true; } }
  else { if (flex_since) { uint32_t dur=now-flex_since; if (!dragging && dur>=80 && now-last_click>=250) { buttons|=1; last_click=now; last_lclick=now; } dragging=false; flex_since=0; } }
  if (dragging) buttons|=1;
  // right: extensor burst; extensor hold + tilt = scroll
  if (intent==INTENT_OPEN) { if(!ext_since) ext_since=now; if (now-ext_since>=400) { wheel = (int8_t)(-ay/20.0f); dy=0; } }
  else { if (ext_since) { uint32_t dur=now-ext_since; if (dur>=80 && dur<400 && now-last_click>=250) { buttons|=2; last_click=now; } ext_since=0; } }
  ble_mouse_move((int8_t)dx,(int8_t)dy,wheel,buttons);
  if (emg_cocon_double(intent)) modes_switch(MODE_HAND_DIRECT);
}

void modes_tick(void){
  effort_t e = emg_frame(); imu_t m = imu_get(); seq++; g_last_effort=e;
  modes_wire_check();
  if (mode==MODE_MOUSE) mouse_tick(e,m); else hand_tick(e,m);   // HAND_WIRED uses hand_tick; hand.c routes over the cord
}
