#include "imu.h"
#include "pins.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "sh2.h"
#include "sh2_SensorValue.h"
#include "sh2_err.h"

// ---------------------------------------------------------------- SH-2 HAL over I2C (SHTP framing)
// SHTP over I2C: every transfer starts with a 4-byte header (length LSB/MSB, channel, seqnum). A read fetches
// the header, then the rest of the packet. The BNO08x pulls INT low when it has data.
static bool hub_present;

static int hal_open(sh2_Hal_t *self) {
  (void)self;
  // Reset the hub; sh2_open() then waits for its reset/advertisement packets through hal_read, so do NOT
  // read anything here.
  gpio_put(PIN_IMU_RST, 0); sleep_ms(10); gpio_put(PIN_IMU_RST, 1); sleep_ms(50);
  return SH2_OK;
}
static void hal_close(sh2_Hal_t *self) { (void)self; }

static int hal_read(sh2_Hal_t *self, uint8_t *pBuffer, unsigned len, uint32_t *t_us) {
  (void)self;
  if (gpio_get(PIN_IMU_INT)) return 0;                     // INT idle high: nothing waiting
  uint8_t hdr[4];
  if (i2c_read_timeout_us(IMU_I2C, IMU_I2C_ADDR, hdr, 4, false, 20000) != 4) return 0;
  uint16_t packet_len = ((hdr[1] << 8) | hdr[0]) & 0x7FFF;
  if (packet_len == 0 || packet_len > len) return 0;
  *t_us = to_us_since_boot(get_absolute_time());
  // the hub re-sends the header with the body; read the whole packet in one go
  if (i2c_read_timeout_us(IMU_I2C, IMU_I2C_ADDR, pBuffer, packet_len, false, 50000) != packet_len) return 0;
  return packet_len;
}

static int hal_write(sh2_Hal_t *self, uint8_t *pBuffer, unsigned len) {
  (void)self;
  if (len > SH2_HAL_MAX_TRANSFER_OUT) len = SH2_HAL_MAX_TRANSFER_OUT;
  int w = i2c_write_timeout_us(IMU_I2C, IMU_I2C_ADDR, pBuffer, len, false, 50000);
  return w < 0 ? 0 : w;
}
static uint32_t hal_time_us(sh2_Hal_t *self) { (void)self; return to_us_since_boot(get_absolute_time()); }

static sh2_Hal_t hal = { hal_open, hal_close, hal_read, hal_write, hal_time_us };

// ---------------------------------------------------------------- sensor events
static imu_t state;

static void quat_to_euler(float qi, float qj, float qk, float qr, float *yaw, float *pitch, float *roll) {
  float sqi = qi * qi, sqj = qj * qj, sqk = qk * qk, sqr = qr * qr;
  *yaw   = atan2f(2.0f * (qi * qj + qk * qr), sqi - sqj - sqk + sqr) * 180.0f / (float)M_PI;
  float s = -2.0f * (qi * qk - qj * qr); if (s > 1) s = 1; if (s < -1) s = -1;
  *pitch = asinf(s) * 180.0f / (float)M_PI;
  *roll  = atan2f(2.0f * (qj * qk + qi * qr), -sqi - sqj + sqk + sqr) * 180.0f / (float)M_PI;
}

static void sensor_cb(void *cookie, sh2_SensorEvent_t *ev) {
  (void)cookie;
  sh2_SensorValue_t v;
  if (sh2_decodeSensorEvent(&v, ev) != SH2_OK) return;
  switch (v.sensorId) {
    case SH2_GAME_ROTATION_VECTOR:
      quat_to_euler(v.un.gameRotationVector.i, v.un.gameRotationVector.j, v.un.gameRotationVector.k,
                    v.un.gameRotationVector.real, &state.yaw, &state.pitch, &state.roll);
      state.valid = true; state.t_ms = to_ms_since_boot(get_absolute_time());
      break;
    case SH2_GYROSCOPE_CALIBRATED:
      state.gx = v.un.gyroscope.x * 180.0f / (float)M_PI;
      state.gy = v.un.gyroscope.y * 180.0f / (float)M_PI;
      state.gz = v.un.gyroscope.z * 180.0f / (float)M_PI;
      break;
    default: break;
  }
}

static bool enable_reports(void) {
  sh2_SensorConfig_t c; memset(&c, 0, sizeof c);
  c.reportInterval_us = 20000;                             // 50 Hz
  if (sh2_setSensorConfig(SH2_GAME_ROTATION_VECTOR, &c) != SH2_OK) return false;
  c.reportInterval_us = 10000;                             // 100 Hz gyro for the mouse
  return sh2_setSensorConfig(SH2_GYROSCOPE_CALIBRATED, &c) == SH2_OK;
}

static void async_cb(void *cookie, sh2_AsyncEvent_t *ev) {
  (void)cookie;
  if (ev->eventId == SH2_RESET) { printf("imu: hub reset, re-enabling reports\n"); enable_reports(); }
}

bool imu_init(void) {
  i2c_init(IMU_I2C, 400000);
  gpio_set_function(PIN_IMU_SDA, GPIO_FUNC_I2C); gpio_set_function(PIN_IMU_SCL, GPIO_FUNC_I2C);
  gpio_pull_up(PIN_IMU_SDA); gpio_pull_up(PIN_IMU_SCL);
  gpio_init(PIN_IMU_INT); gpio_set_dir(PIN_IMU_INT, GPIO_IN); gpio_pull_up(PIN_IMU_INT);
  gpio_init(PIN_IMU_RST); gpio_set_dir(PIN_IMU_RST, GPIO_OUT); gpio_put(PIN_IMU_RST, 1);
  uint8_t probe;
  if (i2c_read_timeout_us(IMU_I2C, IMU_I2C_ADDR, &probe, 1, false, 10000) < 0) {
    printf("imu: no device at 0x%02x\n", IMU_I2C_ADDR); hub_present = false; return false;
  }
  if (sh2_open(&hal, async_cb, NULL) != SH2_OK) { printf("imu: sh2_open failed\n"); return false; }
  sh2_ProductIds_t ids; memset(&ids, 0, sizeof ids);
  if (sh2_getProdIds(&ids) == SH2_OK && ids.numEntries)
    printf("imu: BNO08x fw %lu.%lu.%lu\n", (unsigned long)ids.entry[0].swVersionMajor,
           (unsigned long)ids.entry[0].swVersionMinor, (unsigned long)ids.entry[0].swVersionPatch);
  sh2_setSensorCallback(sensor_cb, NULL);
  hub_present = enable_reports();
  if (!hub_present) printf("imu: enabling reports failed\n");
  return hub_present;
}

void imu_poll(void) { if (hub_present) sh2_service(); }
imu_t imu_get(void) { return state; }
bool imu_ok(void) { return hub_present && state.valid && to_ms_since_boot(get_absolute_time()) - state.t_ms < 500; }
