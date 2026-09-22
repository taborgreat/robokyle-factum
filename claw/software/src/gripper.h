#pragma once
#include <stdint.h>
#include <stdbool.h>
// Gripper behaviour on top of the servo. "close(force)" = set torque limit from force, drive toward POS_CLOSED, and stop
// where the load reaches the limit (the servo does this itself once torque-limited; we also stop commanding on stall).
void gr_init(void);
void gr_open(void);
void gr_close(float force);           // 0..1
void gr_grip(const char *name, bool preview);   // claw maps every grip to open/close widths; preview uses low torque
void gr_stop(void);
void gr_estop(void);
void gr_keepalive(uint32_t now_ms);
void gr_tick(uint32_t now_ms);        // watchdog on keepalive, stall detection, status
int  gr_status_json(char *buf, int n);
