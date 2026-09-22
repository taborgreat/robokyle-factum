#pragma once
#include <stdbool.h>
typedef enum { INTENT_REST, INTENT_CLOSE, INTENT_OPEN, INTENT_COCON } intent_t;
typedef struct { float flex, ext; } effort_t;
void emg_init(void);
void emg_sample(void);            // ~1 kHz from a repeating timer
effort_t emg_frame(void);         // mean |v-1.5| over the frame, then reset
intent_t emg_classify(effort_t e);
float emg_force(effort_t e);      // 0..cfg.force_limit from flexor effort
bool emg_cocon_double(intent_t cur);  // two co-contractions within 1 s
