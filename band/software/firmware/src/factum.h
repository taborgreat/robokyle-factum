// Frames to Factum (listener only): one UDP packet per 20 ms frame, ESTOP x5 + HTTP POST.
#pragma once
#include <stdint.h>
#include "emg.h"
#include "imu.h"
void factum_send_frame(uint32_t seq, uint32_t t_ms, effort_t e, imu_t m, float vbat, intent_t intent);
void factum_send_estop(uint32_t seq, uint32_t t_ms);
