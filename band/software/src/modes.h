#pragma once
#include "config.h"
void modes_init(band_mode_t start);
void modes_switch(band_mode_t m);
band_mode_t modes_current(void);
void modes_tick(void);            // one call per 20 ms frame: does the work of the current mode
void modes_estop(void);
void modes_wire_check(void);
#include "io.h"
led_color_t slot_color(void);
bool hand_busy_guard(void);
