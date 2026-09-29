// GPIO map for the band. Mirrors band/PINOUT.md - change there first.
#pragma once

#define PIN_CORD_TX     0   // UART0 -> hand (HAND-WIRED cord)
#define PIN_CORD_RX     1
#define PIN_IMU_SDA     4   // I2C0 -> BNO08x
#define PIN_IMU_SCL     5
#define PIN_IMU_INT     6   // BNO08x H_INTN (active low)
#define PIN_IMU_RST     7   // BNO08x reset (active low); harmless if RST is tied to 3V3 instead
#define PIN_BUTTON      14  // to GND, internal pull-up
#define PIN_MOTOR       13  // 1k -> S8050 base (low-side switch for the coin motor); GP13 = pin 17, strip hole (17,2), next to the 1k at (17,1)
#define PIN_WS2812      16  // 3-pixel WS2812B bar, PIO
#define PIN_EMG1        26  // ADC0 flexor
#define PIN_EMG2        27  // ADC1 extensor
#define PIN_VBAT        28  // ADC2 battery divider (2 x 100k)

#define ADC_EMG1        0
#define ADC_EMG2        1
#define ADC_VBAT        2

#define N_PIXELS        3
#define CORD_UART       uart0
#define CORD_BAUD       115200
#define IMU_I2C         i2c0
#define IMU_I2C_ADDR    0x4A    // BNO08x with SA0/AD0 low; 0x4B with it high. imu_init() probes both and keeps the one that answers.
