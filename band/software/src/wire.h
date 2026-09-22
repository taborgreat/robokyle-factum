#pragma once
#include <stdint.h>
#include <stdbool.h>
// Optional UART cord to the hand (3 wires: TX, RX, GND; JST-PH at both ends). When the hand answers hellos on the cord the
// band goes to MODE_HAND_WIRED (radios off); when hellos stop, it returns to the last wireless mode. Same hand API, one JSON
// line per command: {"cmd":"open"} {"cmd":"close","force":0.4} {"cmd":"grip","name":"pinch","preview":true} {"cmd":"stop"}
// {"cmd":"estop"} {"cmd":"keepalive","t":123} ; hello = {"hello":"band"} , hand replies {"hello":"hand"}
void wire_init(void);
void wire_poll(uint32_t now_ms);     // sends hellos, reads replies, tracks presence
bool wire_present(void);             // true while the hand is answering on the cord
void wire_send(const char *json_line);
