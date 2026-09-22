// Gripper logic: force -> torque limit, keepalive watchdog (500 ms without one -> stop then open), ESTOP latches.
#pragma once
#include <stdint.h>
#include <stdbool.h>
void gr_init(void);
void gr_tick(uint32_t now_ms);
void gr_open(void);
void gr_close(float force);                 // 0..1
void gr_grip(const char *name, bool preview);
void gr_stop(void);
void gr_estop(void);                        // opens at full torque, then ignores everything until power-cycle
void gr_keepalive(uint32_t now_ms);
bool gr_servo_ok(void);
int gr_status_json(char *b, int n);
