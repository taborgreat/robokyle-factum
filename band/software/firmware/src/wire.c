#include "wire.h"
#include "pins.h"
#include <string.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

static uint32_t last_hello, last_reply; static char rx[128]; static int rxn;

void wire_init(void) {
  uart_init(CORD_UART, CORD_BAUD);
  gpio_set_function(PIN_CORD_TX, GPIO_FUNC_UART); gpio_set_function(PIN_CORD_RX, GPIO_FUNC_UART);
  gpio_pull_up(PIN_CORD_RX);                    // idle high when nothing is plugged in: no phantom bytes
  uart_set_fifo_enabled(CORD_UART, true);
}
void wire_send_line(const char *json) { uart_puts(CORD_UART, json); uart_puts(CORD_UART, "\n"); }

void wire_poll(uint32_t now) {
  if (now - last_hello >= 1000) { last_hello = now; wire_send_line("{\"cmd\":\"hello\"}"); }
  while (uart_is_readable(CORD_UART)) {
    char c = uart_getc(CORD_UART);
    if (c == '\n') { rx[rxn] = 0; if (strstr(rx, "\"hand\"")) last_reply = now; rxn = 0; }
    else if (rxn < (int)sizeof rx - 1) rx[rxn++] = c; else rxn = 0;
  }
}
bool wire_present(void) { return last_reply && to_ms_since_boot(get_absolute_time()) - last_reply < 2500; }
