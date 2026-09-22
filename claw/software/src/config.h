#pragma once
// Claw hand — Pico 2 W. Joins the band's network (home Wi-Fi first, then the band's hotspot) and serves the hand API.
#define WIFI_HOME_SSID "HOME_SSID"
#define WIFI_HOME_PASS "HOME_PASS"
#define WIFI_BAND_SSID "RoboKyle"
#define WIFI_BAND_PASS "robokyle1"
#define HTTP_PORT 80
#define KEEPALIVE_TIMEOUT_MS 500      // no keepalive -> open + disable torque
#define SERVO_ID 1
#define SERVO_UART uart1
#define PIN_SERVO_TX 8                // Pico -> driver board RX
#define PIN_SERVO_RX 9                // driver board TX -> Pico
#define SERVO_BAUD 1000000
#define PIN_VBAT 26                   // optional pack divider
// gripper geometry, in servo ticks (0..4095 = 360 deg). Set with the Feetech tool, then copy here.
#define POS_OPEN   1400
#define POS_CLOSED 2300
#define TORQUE_MIN  150               // 0..1000; force 0..1 maps between these
#define TORQUE_MAX  600
