#include "gripper.h"
#include "feetech.h"
#include "hcfg.h"
#include "pins.h"
#include <stdio.h>
#include <string.h>

static uint32_t last_keep, last_poll; static bool estopped, closing, servo_ok;
static float cur_force; static uint16_t pos, load; static const char *cur_grip = "open";

static void goto_pos(uint16_t p, uint16_t torque) { ft_set_torque_limit(SERVO_ID, torque); ft_set_goal(SERVO_ID, p, 0, hc.speed); }

void gr_init(void) {
  ft_init(); servo_ok = ft_ping(SERVO_ID);
  printf("gripper: servo %s\n", servo_ok ? "ok" : "NOT FOUND");
  ft_torque_enable(SERVO_ID, true); goto_pos(hc.pos_open, hc.torque_min);
}
void gr_open(void) { if (estopped) return; closing = false; cur_force = 0; cur_grip = "open"; goto_pos(hc.pos_open, hc.torque_max); }
void gr_close(float f) {
  if (estopped) return; if (f < 0) f = 0; if (f > 1) f = 1; cur_force = f; closing = true;
  goto_pos(hc.pos_closed, hc.torque_min + (uint16_t)((hc.torque_max - hc.torque_min) * f));
}
void gr_grip(const char *name, bool preview) {
  // a two-jaw claw has three useful postures: open, half (pinch/tripod/point preview), closed (fist/palm)
  if (estopped) return; cur_grip = name;
  if (!strcmp(name, "open")) { gr_open(); return; }
  uint16_t half = (hc.pos_open + hc.pos_closed) / 2;
  uint16_t target = (!strcmp(name, "pinch") || !strcmp(name, "tripod") || !strcmp(name, "point")) ? half : hc.pos_closed - 200;
  closing = !preview; goto_pos(target, preview ? hc.torque_min : hc.torque_max / 2);
}
void gr_stop(void) { uint16_t p; if (ft_position(SERVO_ID, &p)) ft_set_goal(SERVO_ID, p, 0, hc.speed); closing = false; }
void gr_estop(void) { estopped = true; closing = false; goto_pos(hc.pos_open, hc.torque_max); }
void gr_keepalive(uint32_t now) { last_keep = now; }
bool gr_servo_ok(void) { return servo_ok; }

void gr_tick(uint32_t now) {
  if (now - last_poll < 50) return; last_poll = now;
  servo_ok = ft_position(SERVO_ID, &pos); ft_load(SERVO_ID, &load);
  if (last_keep && now - last_keep > KEEPALIVE_TIMEOUT_MS && !estopped && closing) {   // band gone: never hold a grip on a dead link
    printf("gripper: keepalive lost, opening\n"); gr_stop(); gr_open(); last_keep = 0;
  }
}
int gr_status_json(char *b, int n) {
  return snprintf(b, n, "{\"id\":\"%s\",\"pos\":%u,\"load\":%u,\"force\":%.2f,\"grip\":\"%s\",\"estop\":%s,\"closing\":%s,\"servo\":%s}",
                  hc.hand_id, pos, load & 0x3FF, cur_force, cur_grip, estopped ? "true" : "false", closing ? "true" : "false", servo_ok ? "true" : "false");
}
