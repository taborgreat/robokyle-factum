#pragma once
#include <stdint.h>
void wire_init(void);
void wire_poll(uint32_t now_ms);   // answers hellos, executes JSON-line commands; while the cord is live the hand ignores Wi-Fi
int  wire_present(void);
