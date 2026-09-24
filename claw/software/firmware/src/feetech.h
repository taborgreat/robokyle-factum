// Feetech STS3215 serial bus (SCS protocol) through the driver board on UART1. Half-duplex is handled by the board.
#pragma once
#include <stdint.h>
#include <stdbool.h>
void ft_init(void);
bool ft_ping(uint8_t id);
void ft_torque_enable(uint8_t id, bool on);
void ft_set_torque_limit(uint8_t id, uint16_t limit);       // 0..1000
void ft_set_goal(uint8_t id, uint16_t pos, uint16_t time_ms, uint16_t speed); // pos 0..4095
bool ft_position(uint8_t id, uint16_t *pos);
bool ft_load(uint8_t id, uint16_t *load);                    // bit 10 = direction, low 10 bits magnitude
bool ft_moving(uint8_t id, bool *moving);
