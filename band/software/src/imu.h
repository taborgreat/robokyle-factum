#pragma once
#include <stdbool.h>
typedef struct { float yaw, pitch, roll, gx, gy, gz; bool valid; } imu_t;   // deg, deg/s
bool imu_init(void);
void imu_poll(void);
imu_t imu_get(void);
