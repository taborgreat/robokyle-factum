#pragma once
#include <stdint.h>
#include <stdbool.h>
typedef enum { LED_OFF, LED_RED, LED_GREEN, LED_BLUE, LED_WHITE, LED_AMBER, LED_CYAN, LED_MAGENTA } led_color_t;
typedef enum { BTN_NONE, BTN_TAP, BTN_DOUBLE, BTN_HOLD_MODE, BTN_HOLD_LONG, BTN_HOLD_PAIR } btn_event_t;
void io_init(void);
void led_set(led_color_t c);
void led_blink(led_color_t c, uint16_t on_ms, uint16_t off_ms);
void buzz(uint16_t ms);
void buzz_pattern(uint8_t count);
btn_event_t button_poll(void);
void io_tick(void);
float battery_volts(void);
