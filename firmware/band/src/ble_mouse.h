// BLE HID mouse (HOGP) with 4 bonded host slots. One slot is active; switching slots re-targets advertising
// (directed to the bonded host when known, undirected while pairing).
#pragma once
#include <stdint.h>
#include <stdbool.h>
void ble_mouse_start(uint8_t slot);
void ble_mouse_stop(void);
void ble_mouse_set_slot(uint8_t slot);    // disconnects and advertises for the new slot's host
void ble_mouse_pair(void);                // 3 s hold: forget this slot's bond, advertise undirected for a new host
bool ble_mouse_connected(void);
void ble_mouse_move(int8_t dx, int8_t dy, int8_t wheel, uint8_t buttons);   // called every 10 ms; coalesced
