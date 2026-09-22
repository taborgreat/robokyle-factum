#include "feetech.h"
#include "pins.h"
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

// SCS register map (STS3215)
#define REG_TORQUE_ENABLE 0x28
#define REG_GOAL_POS      0x2A
#define REG_GOAL_TIME     0x2C
#define REG_GOAL_SPEED    0x2E
#define REG_TORQUE_LIMIT  0x30
#define REG_PRESENT_POS   0x38
#define REG_PRESENT_LOAD  0x3C
#define REG_MOVING        0x42
#define INST_PING 0x01
#define INST_READ 0x02
#define INST_WRITE 0x03

void ft_init(void) {
  uart_init(SERVO_UART, SERVO_BAUD);
  gpio_set_function(PIN_SERVO_TX, GPIO_FUNC_UART); gpio_set_function(PIN_SERVO_RX, GPIO_FUNC_UART);
  uart_set_fifo_enabled(SERVO_UART, true);
}

static void flush_rx(void) { while (uart_is_readable(SERVO_UART)) uart_getc(SERVO_UART); }

static void send(uint8_t id, uint8_t inst, const uint8_t *p, uint8_t n) {
  uint8_t pkt[32]; uint8_t len = n + 2; uint8_t sum = id + len + inst;
  pkt[0] = 0xFF; pkt[1] = 0xFF; pkt[2] = id; pkt[3] = len; pkt[4] = inst;
  for (int i = 0; i < n; i++) { pkt[5 + i] = p[i]; sum += p[i]; }
  pkt[5 + n] = (uint8_t)~sum;
  flush_rx();
  uart_write_blocking(SERVO_UART, pkt, 6 + n);
  uart_tx_wait_blocking(SERVO_UART);
}

// Read a status packet: FF FF ID LEN ERR [params] CHK. Returns param count or -1 on timeout/checksum.
static int recv(uint8_t id, uint8_t *out, int max, uint32_t timeout_us) {
  absolute_time_t dl = make_timeout_time_us(timeout_us);
  int st = 0, len = 0, i = 0; uint8_t sum = 0, err = 0;
  while (!time_reached(dl)) {
    if (!uart_is_readable(SERVO_UART)) { tight_loop_contents(); continue; }
    uint8_t c = uart_getc(SERVO_UART);
    switch (st) {
      case 0: st = c == 0xFF ? 1 : 0; break;
      case 1: st = c == 0xFF ? 2 : 0; break;
      case 2: if (c == id) { sum = c; st = 3; } else st = 0; break;
      case 3: len = c; sum += c; st = 4; break;
      case 4: err = c; sum += c; i = 0; st = len > 2 ? 5 : 6; break;
      case 5: if (i < max) out[i] = c; i++; sum += c; if (i >= len - 2) st = 6; break;
      case 6: return ((uint8_t)~sum == c && !(err & 0x3F)) ? len - 2 : -1;
    }
  }
  return -1;
}

static bool read_reg(uint8_t id, uint8_t reg, uint8_t n, uint8_t *out) {
  uint8_t p[2] = { reg, n }; send(id, INST_READ, p, 2);
  return recv(id, out, n, 3000) == n;
}
static void write8(uint8_t id, uint8_t reg, uint8_t v) { uint8_t p[2] = { reg, v }; send(id, INST_WRITE, p, 2); recv(id, NULL, 0, 2000); }
static void write16(uint8_t id, uint8_t reg, uint16_t v) { uint8_t p[3] = { reg, v & 0xFF, v >> 8 }; send(id, INST_WRITE, p, 3); recv(id, NULL, 0, 2000); }

bool ft_ping(uint8_t id) { send(id, INST_PING, NULL, 0); return recv(id, NULL, 0, 3000) >= 0; }
void ft_torque_enable(uint8_t id, bool on) { write8(id, REG_TORQUE_ENABLE, on); }
void ft_set_torque_limit(uint8_t id, uint16_t l) { write16(id, REG_TORQUE_LIMIT, l > 1000 ? 1000 : l); }
void ft_set_goal(uint8_t id, uint16_t pos, uint16_t time_ms, uint16_t speed) {
  uint8_t p[7] = { REG_GOAL_POS, pos & 0xFF, pos >> 8, time_ms & 0xFF, time_ms >> 8, speed & 0xFF, speed >> 8 };
  send(id, INST_WRITE, p, 7); recv(id, NULL, 0, 2000);
}
bool ft_position(uint8_t id, uint16_t *pos) { uint8_t b[2]; if (!read_reg(id, REG_PRESENT_POS, 2, b)) return false; *pos = b[0] | (b[1] << 8); return true; }
bool ft_load(uint8_t id, uint16_t *load) { uint8_t b[2]; if (!read_reg(id, REG_PRESENT_LOAD, 2, b)) return false; *load = b[0] | (b[1] << 8); return true; }
bool ft_moving(uint8_t id, bool *m) { uint8_t b; if (!read_reg(id, REG_MOVING, 1, &b)) return false; *m = b != 0; return true; }
