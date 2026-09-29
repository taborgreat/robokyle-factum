// Feedback layer: what Kyle sees and feels while he uses the band, on top of the mode cues.
// Bar: flexor effort = yellow, extensor = blue, both together = green (the co-contraction he needs for the wheel),
// brightness follows effort. Buzz: one tick on a close/open onset, a longer one on co-contraction. With USB in and
// nothing happening, the bar is a battery gauge. cfg.feedback: 0 off, 1 bar only, 2 bar + buzz.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "emg.h"

void feedback_tick(effort_t e, intent_t cur, bool wheel_is_open, uint32_t now_ms);
