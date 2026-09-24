// BNO08x over I2C via CEVA's sh2 driver. Game Rotation Vector (no magnetometer) at 50 Hz + calibrated gyro.
#pragma once
#include <stdbool.h>
#include <stdint.h>

typedef struct {
  float yaw, pitch, roll;     // degrees, from the game rotation vector (relative heading, drift-free pitch/roll)
  float gx, gy, gz;           // gyro, deg/s (x = along the arm, y = across, z = normal to the box lid)
  bool valid;
  uint32_t t_ms;              // last update
} imu_t;

bool imu_init(void);          // returns false if the sensor does not answer (band runs without it)
void imu_poll(void);          // service the sensor hub; call often from the main loop
imu_t imu_get(void);
bool imu_ok(void);
