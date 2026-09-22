#include "io.h"
#include "config.h"
#include "pico/stdlib.h"
#include "hardware/adc.h"
static led_color_t blink_c; static uint16_t blink_on, blink_off; static bool blinking, blink_state; static absolute_time_t blink_t;
static uint16_t bq[8]; static uint8_t bn, bi; static absolute_time_t bt; static bool bon;
void io_init(void){
  gpio_init(PIN_BUTTON); gpio_set_dir(PIN_BUTTON,GPIO_IN); gpio_pull_up(PIN_BUTTON);
  gpio_init(PIN_MOTOR); gpio_set_dir(PIN_MOTOR,GPIO_OUT); gpio_put(PIN_MOTOR,0);
  int leds[3]={PIN_LED_R,PIN_LED_G,PIN_LED_B}; for(int i=0;i<3;i++){ gpio_init(leds[i]); gpio_set_dir(leds[i],GPIO_OUT); gpio_put(leds[i],0); }
  adc_init(); adc_gpio_init(PIN_SENS1); adc_gpio_init(PIN_SENS2); adc_gpio_init(PIN_VBAT);
}
static void led_raw(led_color_t c){ bool r=0,g=0,b=0; switch(c){case LED_RED:r=1;break;case LED_GREEN:g=1;break;case LED_BLUE:b=1;break;case LED_WHITE:r=g=b=1;break;case LED_AMBER:r=g=1;break;case LED_CYAN:g=b=1;break;case LED_MAGENTA:r=b=1;break;default:break;} gpio_put(PIN_LED_R,r); gpio_put(PIN_LED_G,g); gpio_put(PIN_LED_B,b); }  // common-cathode; invert if common-anode
void led_set(led_color_t c){ blinking=false; led_raw(c); }
void led_blink(led_color_t c,uint16_t on,uint16_t off){ blink_c=c; blink_on=on; blink_off=off; blinking=true; blink_state=true; led_raw(c); blink_t=make_timeout_time_ms(on); }
void buzz(uint16_t ms){ if(bn<8) bq[bn++]=ms; }
void buzz_pattern(uint8_t n){ for(uint8_t i=0;i<n&&bn<7;i++){ bq[bn++]=80; if(i+1<n) bq[bn++]=0x8000|120; } }
void io_tick(void){
  if(blinking && time_reached(blink_t)){ blink_state=!blink_state; led_raw(blink_state?blink_c:LED_OFF); blink_t=make_timeout_time_ms(blink_state?blink_on:blink_off); }
  if(bn){
    if(!bon){ uint16_t v=bq[bi]; gpio_put(PIN_MOTOR,!(v&0x8000)); bon=true; bt=make_timeout_time_ms(v&0x7FFF); }
    else if(time_reached(bt)){ gpio_put(PIN_MOTOR,0); bon=false; if(++bi>=bn){ bn=bi=0; } }
  }
}
btn_event_t button_poll(void){
  static bool was=false,fired=false; static absolute_time_t down_t,up_t; static uint8_t taps=0;
  bool down=!gpio_get(PIN_BUTTON); btn_event_t ev=BTN_NONE;
  if(down&&!was){ down_t=get_absolute_time(); fired=false; }
  if(down&&was&&!fired){ int64_t held=absolute_time_diff_us(down_t,get_absolute_time())/1000;
    if(held>=BTN_PAIR_MS){ ev=BTN_HOLD_PAIR; fired=true; } else if(held>=BTN_ESTOP_MS){ ev=BTN_HOLD_LONG; fired=true; } }
  if(!down&&was&&!fired){ int64_t held=absolute_time_diff_us(down_t,get_absolute_time())/1000; if(held>=BTN_MODE_MS) ev=BTN_HOLD_MODE; else { taps++; up_t=get_absolute_time(); } }
  if(taps && absolute_time_diff_us(up_t,get_absolute_time())/1000>BTN_TAP_MS){ ev=(taps>=2)?BTN_DOUBLE:BTN_TAP; taps=0; }
  was=down; return ev;
}
float battery_volts(void){ adc_select_input(2); return adc_read()*3.3f/4095.0f*2.0f; }
