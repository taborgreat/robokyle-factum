#include "emg.h"
#include "config.h"
#include "hardware/adc.h"
#include "pico/stdlib.h"
static volatile float a1,a2; static volatile uint32_t n; static const float CENTER=1.5f;
void emg_init(void){ a1=a2=0; n=0; }
void emg_sample(void){
  adc_select_input(0); float v1=adc_read()*3.3f/4095.0f; adc_select_input(1); float v2=adc_read()*3.3f/4095.0f;
  float d1=v1-CENTER; if(d1<0)d1=-d1; float d2=v2-CENTER; if(d2<0)d2=-d2; a1+=d1; a2+=d2; n++;
}
effort_t emg_frame(void){ effort_t e={0,0}; uint32_t k=n; if(k){ e.flex=a1/k; e.ext=a2/k; } a1=a2=0; n=0; return e; }
intent_t emg_classify(effort_t e){
  static intent_t cur=INTENT_REST,cand=INTENT_REST; static uint8_t run=0; intent_t raw;
  bool fh=e.flex>cfg.flex_on, eh=e.ext>cfg.ext_on, fl=e.flex<cfg.flex_off, el=e.ext<cfg.ext_off;
  if(fh&&eh) raw=INTENT_COCON; else if(fh) raw=INTENT_CLOSE; else if(eh) raw=INTENT_OPEN; else if(fl&&el) raw=INTENT_REST; else raw=cur;
  if(raw==cand) run++; else { cand=raw; run=1; }
  if(run >= ((raw==INTENT_REST)?5:3)) cur=cand;
  return cur;
}
float emg_force(effort_t e){ float f=(e.flex-cfg.flex_on)/(cfg.flex_max-cfg.flex_on); if(f<0)f=0; if(f>1)f=1; return f*cfg.force_limit; }
bool emg_cocon_double(intent_t cur){
  static bool was=false; static absolute_time_t last; static uint8_t count=0; bool now=(cur==INTENT_COCON), fired=false;
  if(now&&!was){ if(count && absolute_time_diff_us(last,get_absolute_time())<1000000){ fired=true; count=0; } else { count=1; last=get_absolute_time(); } }
  was=now; return fired;
}
