#pragma once
#include <stdint.h>
#include <stdbool.h>
// BLE HID mouse (HOGP) via BTstack. Four host slots; each slot remembers one bonded host. Switching slots disconnects and
// directed-advertises to that slot's host so only it reconnects. Pairing mode clears the active slot and advertises openly.
bool ble_mouse_start(uint8_t slot);
void ble_mouse_stop(void);
void ble_mouse_move(int8_t dx, int8_t dy, int8_t wheel, uint8_t buttons);   // buttons: bit0 L, bit1 R
void ble_mouse_pair(void);                 // forget slot's host, open advertising
void ble_mouse_set_slot(uint8_t slot);     // 0..3
bool ble_mouse_connected(void);
