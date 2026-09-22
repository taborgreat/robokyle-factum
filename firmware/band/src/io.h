// Button, haptic motor, WS2812 status bar, battery.
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef enum { BTN_NONE, BTN_TAP, BTN_DOUBLE, BTN_HOLD_1S, BTN_HOLD_2S, BTN_HOLD_3S } btn_event_t;

typedef struct { uint8_t r, g, b; } rgb_t;
#define RGB(r_, g_, b_) ((rgb_t){r_, g_, b_})
#define LED_OFF     RGB(0, 0, 0)
#define LED_GREEN   RGB(0, 60, 0)
#define LED_DUCK    RGB(70, 60, 0)    // Oregon yellow
#define LED_AMBER   RGB(70, 30, 0)
#define LED_RED     RGB(80, 0, 0)
#define LED_BLUE    RGB(0, 0, 70)
#define LED_CYAN    RGB(0, 50, 50)
#define LED_MAGENTA RGB(50, 0, 50)
#define LED_WHITE   RGB(45, 45, 45)

void io_init(void);
void io_tick(void);                 // call from the main loop; runs blink and buzz patterns
btn_event_t button_poll(void);      // one event per gesture, decoded in io_tick

// status bar: colour + blink cadence (on/off ms; 0 = solid)
void led_set(rgb_t c);
void led_blink(rgb_t c, uint16_t on_ms, uint16_t off_ms);
void led_pixel(uint8_t i, rgb_t c);  // direct write (used by the live EMG meter in calibration)

// haptics: 1 short = change, 1 long = set, 2 short = cancel/mode, 2 s = ESTOP
void buzz(uint16_t ms);
void buzz_pattern(uint8_t n);        // n short pulses
bool buzz_busy(void);

float battery_volts(void);           // from the divider, filtered
uint8_t battery_percent(void);
