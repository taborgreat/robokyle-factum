#pragma once
#include <stdint.h>
#include <stdbool.h>
// Feetech STS3215 serial bus servo, protocol like Dynamixel 1.0. Registers (SMS/STS map):
//   0x28 TORQUE_ENABLE(1) 0x2A GOAL_POSITION(2) 0x2E GOAL_SPEED(2) 0x30 TORQUE_LIMIT(2) 0x38 PRESENT_POSITION(2)
//   0x3C PRESENT_LOAD(2) 0x3E PRESENT_VOLTAGE(1) 0x3F PRESENT_TEMP(1) 0x42 MOVING(1)
// VERIFY against the STS3215 memory table for your firmware version.
void   ft_init(void);
bool   ft_torque_enable(uint8_t id, bool on);
bool   ft_set_torque_limit(uint8_t id, uint16_t limit);   // 0..1000
bool   ft_set_goal(uint8_t id, uint16_t pos, uint16_t speed);
bool   ft_read_u16(uint8_t id, uint8_t reg, uint16_t *out);
bool   ft_read_u8(uint8_t id, uint8_t reg, uint8_t *out);
static inline bool ft_position(uint8_t id, uint16_t *p){ return ft_read_u16(id, 0x38, p); }
static inline bool ft_load(uint8_t id, uint16_t *l){ return ft_read_u16(id, 0x3C, l); }   // bit10 = direction, low 10 bits = magnitude
static inline bool ft_moving(uint8_t id, uint8_t *m){ return ft_read_u8(id, 0x42, m); }
