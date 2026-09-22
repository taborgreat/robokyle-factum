#include "wheel.h"
#include "hand.h"
#include "io.h"
#include "config.h"
#include <math.h>
static const char *GRIPS[8] = {"open","fist","pinch","tripod","point","lateral","hook","flat"};
static bool open_=false; static float cy,cp; static int sector=-1, cur=0; static uint32_t t_open, t_last_change, t_last_send;
static uint32_t cocon_since=0;
bool wheel_open(void){ return open_; }
const char *wheel_current_grip(void){ return GRIPS[cur]; }
void wheel_tick(intent_t intent, imu_t m, bool hand_empty, uint32_t now){
  if (!open_) {
    if (intent==INTENT_COCON) { if(!cocon_since) cocon_since=now; }
    else cocon_since=0;
    if (cocon_since && now-cocon_since>=COCON_MS && hand_empty && m.valid) {
      open_=true; cy=m.yaw; cp=m.pitch; sector=-1; t_open=now; t_last_change=now; t_last_send=0; buzz(80); cocon_since=0;
    }
    return;
  }
  // inside the wheel: angle of (dyaw, dpitch) from the entry orientation, sector = angle / (360/N); near center = none
  float dy=m.yaw-cy, dp=m.pitch-cp; if(dy>180)dy-=360; if(dy<-180)dy+=360;
  float r=sqrtf(dy*dy+dp*dp);
  int s=-1;
  if (r > 12.0f) { float a=atan2f(dp,dy)*57.2958f; if(a<0)a+=360; s=(int)(a/(360.0f/cfg.grip_count)) % cfg.grip_count; }
  if (s!=sector) { sector=s; t_last_change=now; if (s>=0 && now-t_last_send>=400) { cur=s; hand_grip(GRIPS[cur], true); t_last_send=now; buzz(60); } }
  bool close = (intent==INTENT_OPEN) || (now-t_last_change>=WHEEL_STILL_MS && sector==-1) || (now-t_open>=WHEEL_TIMEOUT_MS && now-t_last_change>=WHEEL_STILL_MS);
  if (intent==INTENT_OPEN) { /* cancel */ hand_open(); buzz_pattern(2); open_=false; return; }
  if (close) { hand_grip(GRIPS[cur], false); buzz(300); open_=false; }
}
