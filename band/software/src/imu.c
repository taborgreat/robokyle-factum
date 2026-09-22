// BNO08x over I2C, SHTP framing. Trimmed from the SH-2 reference: control channel 2 (SET_FEATURE 0xFD), input reports on
// channel 3. Only Game Rotation Vector (0x08, gyro+accel, no magnetometer) and calibrated gyro (0x02), both at 50 Hz.
// VERIFY packet layouts against the SH-2 manual before trusting yaw sign conventions.
#include "imu.h"
#include "config.h"
#include "hardware/i2c.h"
#include "pico/stdlib.h"
#include <string.h>
#include <math.h>
#define CH_CONTROL 2
#define CH_REPORTS 3
#define REP_GRV 0x08
#define REP_GYRO 0x02
static imu_t st; static uint8_t seq[6];
static bool shtp_send(uint8_t ch,const uint8_t*d,uint8_t n){ uint8_t p[4+64]; uint16_t len=n+4; p[0]=len&0xFF; p[1]=len>>8; p[2]=ch; p[3]=seq[ch]++; memcpy(p+4,d,n); return i2c_write_blocking(i2c0,BNO_ADDR,p,len,false)==len; }
static int shtp_recv(uint8_t*ch,uint8_t*buf,int max){
  uint8_t h[4]; if(i2c_read_blocking(i2c0,BNO_ADDR,h,4,false)!=4) return -1;
  uint16_t len=(h[0]|(h[1]<<8))&0x7FFF; if(len<4) return 0; if(len>max+4) len=max+4;
  uint8_t t[4+256]; if(i2c_read_blocking(i2c0,BNO_ADDR,t,len,false)!=len) return -1;
  *ch=t[2]; memcpy(buf,t+4,len-4); return len-4;
}
static void set_feature(uint8_t rep,uint32_t us){ uint8_t d[17]={0}; d[0]=0xFD; d[1]=rep; d[5]=us; d[6]=us>>8; d[7]=us>>16; d[8]=us>>24; shtp_send(CH_CONTROL,d,17); }
bool imu_init(void){
  i2c_init(i2c0,400000); gpio_set_function(PIN_SDA,GPIO_FUNC_I2C); gpio_set_function(PIN_SCL,GPIO_FUNC_I2C); gpio_pull_up(PIN_SDA); gpio_pull_up(PIN_SCL);
  sleep_ms(150); uint8_t ch,b[256]; for(int i=0;i<4;i++) shtp_recv(&ch,b,sizeof b);
  set_feature(REP_GRV,20000); set_feature(REP_GYRO,20000); st.valid=false; return true;
}
static float q2f(int16_t v,int q){ return (float)v/(float)(1<<q); }
void imu_poll(void){
  uint8_t ch,b[256]; int n=shtp_recv(&ch,b,sizeof b); if(n<=0||ch!=CH_REPORTS) return;
  int i=5;
  while(i<n){
    uint8_t id=b[i];
    if(id==REP_GRV && i+14<=n){ float x=q2f((int16_t)(b[i+4]|(b[i+5]<<8)),14), y=q2f((int16_t)(b[i+6]|(b[i+7]<<8)),14), z=q2f((int16_t)(b[i+8]|(b[i+9]<<8)),14), w=q2f((int16_t)(b[i+10]|(b[i+11]<<8)),14);
      st.yaw=atan2f(2*(w*z+x*y),1-2*(y*y+z*z))*57.2958f; st.pitch=asinf(fmaxf(-1,fminf(1,2*(w*y-z*x))))*57.2958f; st.roll=atan2f(2*(w*x+y*z),1-2*(x*x+y*y))*57.2958f; st.valid=true; i+=14; }
    else if(id==REP_GYRO && i+10<=n){ st.gx=q2f((int16_t)(b[i+4]|(b[i+5]<<8)),9)*57.2958f; st.gy=q2f((int16_t)(b[i+6]|(b[i+7]<<8)),9)*57.2958f; st.gz=q2f((int16_t)(b[i+8]|(b[i+9]<<8)),9)*57.2958f; i+=10; }
    else break;
  }
}
imu_t imu_get(void){ return st; }
