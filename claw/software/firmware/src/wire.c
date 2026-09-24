#include "wire.h"
#include "pins.h"
#include "gripper.h"
#include "json.h"
#include <string.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
static char rx[160]; static int rxn;
void wire_init(void) {
  uart_init(CORD_UART, CORD_BAUD);
  gpio_set_function(PIN_CORD_TX, GPIO_FUNC_UART); gpio_set_function(PIN_CORD_RX, GPIO_FUNC_UART); gpio_pull_up(PIN_CORD_RX);
}
static void handle(const char *line, uint32_t now) {
  char cmd[16] = {0}; json_get_str(line, "cmd", cmd, sizeof cmd);
  char args[96] = {0}; const char *a = strstr(line, "\"a\":"); if (a) { strncpy(args, a + 4, sizeof args - 1); }
  if (!strcmp(cmd, "hello")) { char b[160]; int n = snprintf(b, sizeof b, "{\"hand\":true,\"s\":"); gr_status_json(b + n, sizeof b - n - 2); strcat(b, "}\n"); uart_puts(CORD_UART, b); return; }
  if (!strcmp(cmd, "open")) gr_open();
  else if (!strcmp(cmd, "close")) { float f = 0.5f; json_get_num(args, "force", &f); gr_close(f); }
  else if (!strcmp(cmd, "grip")) { char name[16] = "open"; bool pv = false; json_get_str(args, "name", name, sizeof name); json_get_bool(args, "preview", &pv); gr_grip(name, pv); }
  else if (!strcmp(cmd, "stop")) gr_stop();
  else if (!strcmp(cmd, "estop")) gr_estop();
  else if (!strcmp(cmd, "keepalive")) { }
  gr_keepalive(now);                                  // any command on the cord counts as a keepalive
}
void wire_poll(uint32_t now) {
  while (uart_is_readable(CORD_UART)) {
    char c = uart_getc(CORD_UART);
    if (c == '\n') { rx[rxn] = 0; if (rxn) handle(rx, now); rxn = 0; }
    else if (rxn < (int)sizeof rx - 1) rx[rxn++] = c; else rxn = 0;
  }
}
