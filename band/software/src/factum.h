#pragma once
#include "emg.h"
#include "imu.h"
void factum_send_frame(uint32_t seq, uint32_t t_ms, effort_t e, imu_t imu, float vbat, int intent);
void factum_send_estop(uint32_t seq, uint32_t t_ms);
