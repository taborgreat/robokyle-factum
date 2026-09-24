// Hand / claw GPIO map (Pico 2 W). Mirrors firmware/PINOUT.md.
#pragma once
#define PIN_CORD_TX   0    // UART0 <-> band cord
#define PIN_CORD_RX   1
#define PIN_SERVO_TX  4    // UART1 -> servo driver board
#define PIN_SERVO_RX  5
#define PIN_BUTTON    14
#define PIN_WS2812    16
#define PIN_VPACK     26   // ADC0: PACK+ -> 100k -> GP26 -> 33k -> GND
#define CORD_UART     uart0
#define CORD_BAUD     115200
#define SERVO_UART    uart1
#define SERVO_BAUD    1000000
#define SERVO_ID      1
#define KEEPALIVE_TIMEOUT_MS 500
