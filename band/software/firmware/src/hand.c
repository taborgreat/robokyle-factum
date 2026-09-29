#include "hand.h"
#include "config.h"
#include "net.h"
#include "wire.h"
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"

static uint32_t last_ok;
// One pending command: a state change must never be lost behind an in-flight keepalive, and the latest state
// always wins (open after close cancels the close). Keepalives are only sent when nothing is pending.
static struct { char path[16]; char body[64]; bool pending; } cmd;
static bool relay; static char last_cmd[112] = "null";      // HAND-FACTUM: Factum relays; the frame carries the command
void hand_set_relay(bool r) { relay = r; if (!r) strcpy(last_cmd, "null"); }
const char *hand_last_cmd(void) { return last_cmd; }

static void done(int status, const char *body, void *arg) { (void)body; (void)arg; if (status == 200) last_ok = to_ms_since_boot(get_absolute_time()); }

static bool post(const char *path, const char *json) {
  if (wire_present()) {
    char line[128]; snprintf(line, sizeof line, "{\"cmd\":\"%s\",\"a\":%s}", path + 1, json ? json : "{}");
    wire_send_line(line); last_ok = to_ms_since_boot(get_absolute_time()); return true;
  }
  if (relay) {                                             // no direct path to the hand: Factum forwards it
    snprintf(last_cmd, sizeof last_cmd, "{\"cmd\":\"%s\",\"a\":%s}", path + 1, json ? json : "{}");
    last_ok = to_ms_since_boot(get_absolute_time()); return true;
  }
  if (!net_ready() || !net_ap_up()) return false;          // over the air the hand is only ever on the band's AP
  return http_post(cfg.hand_ip, cfg.hand_port, path, json, done, NULL);
}

static void send(const char *path, const char *json) {
  strncpy(cmd.path, path, sizeof cmd.path - 1); strncpy(cmd.body, json ? json : "", sizeof cmd.body - 1);
  cmd.pending = true;
  hand_service();
}

void hand_service(void) {
  if (cmd.pending && !http_busy() && post(cmd.path, cmd.body[0] ? cmd.body : NULL)) cmd.pending = false;
}
bool hand_pending(void) { return cmd.pending; }

void hand_open(void) { send("/open", NULL); }
void hand_close(float f) { char b[32]; snprintf(b, sizeof b, "{\"force\":%.2f}", f); send("/close", b); }
void hand_grip(const char *name, bool preview) { char b[64]; snprintf(b, sizeof b, "{\"name\":\"%s\",\"preview\":%s}", name, preview ? "true" : "false"); send("/grip", b); }
void hand_stop(void) { send("/stop", NULL); }
void hand_estop(void) { send("/estop", NULL); }
void hand_keepalive(uint32_t t) { if (cmd.pending) return; char b[32]; snprintf(b, sizeof b, "{\"t\":%lu}", (unsigned long)t); post("/keepalive", b); }
bool hand_link_ok(void) { return to_ms_since_boot(get_absolute_time()) - last_ok < 1500; }
