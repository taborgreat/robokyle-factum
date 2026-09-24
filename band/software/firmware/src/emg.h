// Two-channel EMG: 1 kHz sampling in a timer IRQ, 20 ms effort frames, thresholds with hysteresis + debounce.
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define EMG_SAMPLE_HZ 1000
#define FRAME_MS      20

typedef struct { float flex, ext; } effort_t;
typedef enum { INTENT_REST, INTENT_CLOSE, INTENT_OPEN, INTENT_COCON } intent_t;

void emg_init(void);
void emg_sample(void);                 // called at EMG_SAMPLE_HZ from a repeating timer
effort_t emg_frame(void);              // mean |v - 1.5| per channel since the last call, then resets
intent_t emg_classify(effort_t e);     // hysteresis (on/off thresholds) + debounce (3 frames on, 5 off)
float emg_force(effort_t e);           // 0..force_limit from flexor effort above flex_on
bool emg_cocon_double(intent_t cur);   // two co-contractions within 1 s -> true once

// calibration capture: phases accumulate min/max/mean of effort for ~10 s each
typedef enum { CAL_NONE, CAL_REST, CAL_CLOSE, CAL_OPEN } cal_phase_t;
void emg_cal_start(cal_phase_t p);
void emg_cal_feed(effort_t e);
bool emg_cal_apply(void);              // thresholds at 40 % (on) and 25 % (off) of the rest..active range
const char *emg_cal_json(char *buf, int n);
