#include "wire.h"
#include "gripper.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"
#include <string.h>
#include <stdlib.h>
#define WIRE_UART uart0
#define PIN_WIRE_TX 0
#define PIN_WIRE_RX 1
static char line[160]; static int li=0; static uint32_t last_hello=0;
static float num(const char *s,const char *k){ const char *p=strstr(s,k); if(!p) return 0; p=strchr(p,':'); return p?(float)atof(p+1):0; }
static void str(const char *s,const char *k,char *o,int n){ o[0]=0; const char *p=strstr(s,k); if(!p) return; p=strchr(p,':'); if(!p) return; p=strchr(p,'"'); if(!p) return; p++; int i=0; while(*p&&*p!='"'&&i<n-1) o[i++]=*p++; o[i]=0; }
void wire_init(void){ uart_init(WIRE_UART,115200); gpio_set_function(PIN_WIRE_TX,GPIO_FUNC_UART); gpio_set_function(PIN_WIRE_RX,GPIO_FUNC_UART); gpio_pull_up(PIN_WIRE_RX); }
static void handle(const char *l, uint32_t now){
  if(strstr(l,"\"hello\":\"band\"")){ uart_puts(WIRE_UART,"{\"hello\":\"hand\"}\n"); last_hello=now; return; }
  char cmd[16]; str(l,"\"cmd\"",cmd,sizeof cmd); last_hello=now;
  if(!strcmp(cmd,"open")) gr_open();
  else if(!strcmp(cmd,"close")) gr_close(num(l,"\"force\""));
  else if(!strcmp(cmd,"grip")){ char nm[24]; str(l,"\"name\"",nm,sizeof nm); gr_grip(nm, strstr(l,"\"preview\":true")!=NULL); }
  else if(!strcmp(cmd,"stop")) gr_stop();
  else if(!strcmp(cmd,"estop")) gr_estop();
  else if(!strcmp(cmd,"keepalive")) gr_keepalive(now);
  uart_puts(WIRE_UART,"{\"ok\":true}\n");
}
void wire_poll(uint32_t now){ while(uart_is_readable(WIRE_UART)){ char c=uart_getc(WIRE_UART); if(c=='\n'){ line[li]=0; handle(line,now); li=0; } else if(li<159) line[li++]=c; } }
int wire_present(void){ return last_hello && (to_ms_since_boot(get_absolute_time())-last_hello<2500); }
