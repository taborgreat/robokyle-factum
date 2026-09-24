// The optional 3-wire cord to the hand (UART0, 115200, JSON lines). Hello every second; the hand answers.
#pragma once
#include <stdint.h>
#include <stdbool.h>
void wire_init(void);
void wire_poll(uint32_t now_ms);   // sends hellos, reads replies
bool wire_present(void);           // hand answered within the last 2.5 s
void wire_send_line(const char *json);
