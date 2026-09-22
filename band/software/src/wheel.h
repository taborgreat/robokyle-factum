#pragma once
#include <stdbool.h>
#include "emg.h"
#include "imu.h"
// Grip wheel: co-contraction opens it when the hand is empty; arm orientation points at a fixed clock sector;
// the hand previews each sector's grip live; leaving the wheel keeps what it shows.
void wheel_tick(intent_t intent, imu_t imu, bool hand_empty, uint32_t now_ms);
bool wheel_open(void);
const char *wheel_current_grip(void);
