#include "wire.h"
#include "config.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"
#include <string.h>
#define WIRE_UART uart0
#define PIN_WIRE_TX 0
#define PIN_WIRE_RX 1
#define WIRE_BAUD 115200
#define HELLO_MS 1000
#define LOST_MS 2500
static uint32_t last_hello=0, last_reply=0; static char line[128]; static int li=0; static bool present=false;
void wire_init(void){ uart_init(WIRE_UART,WIRE_BAUD); gpio_set_function(PIN_WIRE_TX,GPIO_FUNC_UART); gpio_set_function(PIN_WIRE_RX,GPIO_FUNC_UART); gpio_pull_up(PIN_WIRE_RX); }
void wire_send(const char *s){ uart_puts(WIRE_UART,s); uart_putc_raw(WIRE_UART,'\n'); }
void wire_poll(uint32_t now){
  if(now-last_hello>=HELLO_MS){ wire_send("{\"hello\":\"band\"}"); last_hello=now; }
  while(uart_is_readable(WIRE_UART)){ char c=uart_getc(WIRE_UART); if(c=='\n'){ line[li]=0; if(strstr(line,"\"hello\":\"hand\"")||strstr(line,"\"ok\"")) last_reply=now; li=0; } else if(li<127) line[li++]=c; }
  present = last_reply && (now-last_reply<LOST_MS);
}
bool wire_present(void){ return present; }
