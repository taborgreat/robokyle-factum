// Grip wheel: co-contraction opens it (only when the hand is empty); arm roll/pitch points at fixed clock
// positions; the hand previews the sector's grip live; closing the wheel keeps what it shows.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "emg.h"
#include "imu.h"
void wheel_tick(intent_t intent, imu_t m, bool hand_empty, uint32_t now_ms);
bool wheel_open(void);
const char *wheel_current_grip(void);
