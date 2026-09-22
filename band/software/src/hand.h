#pragma once
#include <stdint.h>
#include <stdbool.h>
// Hand API (shared by the Brunel server and the claw): all POST, JSON body, hand replies 200 before it moves.
//   /open            {}                   open fully
//   /close           {"force":0..1}       close until load reaches force
//   /grip            {"name":"pinch","preview":true|false}
//   /stop            {}
//   /estop           {}                   open + disable, bypasses everything
//   /keepalive       {"t":ms}             hand opens if none for 500 ms
void hand_open(void);
void hand_close(float force);
void hand_grip(const char *name, bool preview);
void hand_stop(void);
void hand_estop(void);
void hand_keepalive(uint32_t t_ms);
bool hand_busy(void);
