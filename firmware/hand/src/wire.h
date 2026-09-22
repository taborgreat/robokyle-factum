// Cord side: answer the band's hellos and run the same commands from JSON lines.
#pragma once
#include <stdint.h>
void wire_init(void);
void wire_poll(uint32_t now_ms);
