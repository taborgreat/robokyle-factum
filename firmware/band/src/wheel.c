#include "wheel.h"
#include "hand.h"
#include "io.h"
#include <math.h>
#include <string.h>

// Fixed forever once chosen (changing costs relearning). Sector 0 straight ahead, going clockwise.
static const char *GRIPS[] = { "open", "fist", "pinch", "tripod", "point", "palm" };
#define N_GRIPS 6
#define DEAD_DEG 12.0f          // near-centre = no sector
#define COCON_MS 150
#define PREVIEW_MS 400
#define IDLE_CLOSE_MS 1000
#define MAX_OPEN_MS 3000

static bool open_; static float c_roll, c_pitch; static int sector = -1, prev_sector = -1;
static uint32_t cocon_since, t_open, t_last_change, t_last_preview; static const char *grip = "open";

bool wheel_open(void) { return open_; }
const char *wheel_current_grip(void) { return grip; }

void wheel_tick(intent_t intent, imu_t m, bool hand_empty, uint32_t now) {
  if (!open_) {
    if (intent == INTENT_COCON && hand_empty) {
      if (!cocon_since) cocon_since = now;
      else if (now - cocon_since >= COCON_MS) {
        open_ = true; c_roll = m.roll; c_pitch = m.pitch; sector = -1; prev_sector = -1;
        t_open = t_last_change = now; buzz_pattern(1);
      }
    } else cocon_since = 0;
    return;
  }
  // inside the wheel: roll/pitch relative to the entry orientation form a 2-D pointer
  float dx = m.roll - c_roll, dy = m.pitch - c_pitch;
  float r = sqrtf(dx * dx + dy * dy);
  int s = -1;
  if (r >= DEAD_DEG) { float a = atan2f(dx, dy) * 180.0f / (float)M_PI; if (a < 0) a += 360; s = (int)(a / (360.0f / N_GRIPS)) % N_GRIPS; }
  if (s != sector) {
    sector = s; t_last_change = now;
    if (s >= 0 && now - t_last_preview >= PREVIEW_MS) { buzz_pattern(1); hand_grip(GRIPS[s], true); t_last_preview = now; prev_sector = s; }
  }
  bool back_home = r < DEAD_DEG && sector == -1 && prev_sector >= 0;
  if (intent == INTENT_OPEN) {                                  // open burst = cancel, hand returns to the previous grip
    open_ = false; cocon_since = 0; hand_grip(grip, false); buzz_pattern(2); return;
  }
  if (back_home || now - t_last_change >= IDLE_CLOSE_MS || now - t_open >= MAX_OPEN_MS) {
    open_ = false; cocon_since = 0;
    if (prev_sector >= 0) { grip = GRIPS[prev_sector]; hand_grip(grip, false); buzz(400); }
    else buzz_pattern(2);
  }
}
