#include "feetech.h"
#include "config.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"
#include <string.h>
static uint8_t chk(const uint8_t *p, int n){ uint32_t s=0; for(int i=2;i<n;i++) s+=p[i]; return (uint8_t)(~s); }
static void tx(const uint8_t *p, int n){ uart_write_blocking(SERVO_UART, p, n); uart_tx_wait_blocking(SERVO_UART); }
static int rx(uint8_t *p, int max, uint32_t timeout_us){
  int n=0; absolute_time_t t=make_timeout_time_us(timeout_us);
  while(n<max && !time_reached(t)){ if(uart_is_readable(SERVO_UART)) p[n++]=uart_getc(SERVO_UART); }
  return n;
}
void ft_init(void){
  uart_init(SERVO_UART, SERVO_BAUD); gpio_set_function(PIN_SERVO_TX, GPIO_FUNC_UART); gpio_set_function(PIN_SERVO_RX, GPIO_FUNC_UART);
  uart_set_format(SERVO_UART, 8, 1, UART_PARITY_NONE);
}
static bool write_regs(uint8_t id, uint8_t reg, const uint8_t *d, uint8_t n){
  uint8_t p[16]={0xFF,0xFF,id,(uint8_t)(n+3),0x03,reg}; memcpy(p+6,d,n); p[6+n]=chk(p,6+n); tx(p,7+n);
  uint8_t r[8]; int k=rx(r,6,3000); return k>=6 && r[4]==0;             // status packet, error byte 0
}
bool ft_torque_enable(uint8_t id,bool on){ uint8_t v=on; return write_regs(id,0x28,&v,1); }
bool ft_set_torque_limit(uint8_t id,uint16_t l){ uint8_t d[2]={l&0xFF,l>>8}; return write_regs(id,0x30,d,2); }
bool ft_set_goal(uint8_t id,uint16_t pos,uint16_t speed){ uint8_t d[6]={pos&0xFF,pos>>8,0,0,speed&0xFF,speed>>8}; return write_regs(id,0x2A,d,6); }   // pos, time(0), speed
bool ft_read_u16(uint8_t id,uint8_t reg,uint16_t *out){
  uint8_t p[8]={0xFF,0xFF,id,4,0x02,reg,2}; p[7]=chk(p,7); tx(p,8);
  uint8_t r[16]; int k=rx(r,8,3000); if(k<8||r[4]!=0) return false; *out=r[5]|(r[6]<<8); return true;
}
bool ft_read_u8(uint8_t id,uint8_t reg,uint8_t *out){
  uint8_t p[8]={0xFF,0xFF,id,4,0x02,reg,1}; p[7]=chk(p,7); tx(p,8);
  uint8_t r[16]; int k=rx(r,7,3000); if(k<7||r[4]!=0) return false; *out=r[5]; return true;
}
