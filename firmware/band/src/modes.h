#pragma once
#include <stdint.h>
#include "emg.h"
typedef enum { MODE_HAND_FACTUM = 0, MODE_HAND_DIRECT = 1, MODE_MOUSE = 2, MODE_COUNT = 3, MODE_HAND_WIRED = 3 } band_mode_t;
void modes_init(band_mode_t start);
void modes_tick(void);                 // every FRAME_MS
void modes_switch(band_mode_t m);      // ignored while the cord is in
band_mode_t modes_current(void);
void modes_estop(void);
effort_t modes_last_effort(void);
intent_t modes_last_intent(void);
