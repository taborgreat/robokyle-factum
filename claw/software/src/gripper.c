#include "gripper.h"
#include "feetech.h"
#include "config.h"
#include "hcfg.h"
#include <string.h>
#include <stdio.h>
static uint32_t last_keep=0; static bool estopped=false, closing=false; static float cur_force=0; static uint16_t pos=0, load=0;
static const char *cur_grip="open";
void gr_init(void){ ft_init(); ft_torque_enable(SERVO_ID,true); ft_set_torque_limit(SERVO_ID,hc.torque_min); ft_set_goal(SERVO_ID,hc.pos_open,800); }
void gr_open(void){ if(estopped) return; closing=false; cur_force=0; ft_set_torque_limit(SERVO_ID,hc.torque_max); ft_set_goal(SERVO_ID,hc.pos_open,800); cur_grip="open"; }
void gr_close(float f){ if(estopped) return; if(f<0)f=0; if(f>1)f=1; cur_force=f; uint16_t tl=hc.torque_min+(uint16_t)((hc.torque_max-hc.torque_min)*f); ft_set_torque_limit(SERVO_ID,tl); ft_set_goal(SERVO_ID,hc.pos_closed,600); closing=true; }
void gr_grip(const char *name,bool preview){
  // two-jaw claw: "open" -> open; anything else -> a partial close as a preview posture, full torque only when not preview
  cur_grip=name;
  if(!strcmp(name,"open")){ gr_open(); return; }
  uint16_t target = !strcmp(name,"pinch")? (hc.pos_open+hc.pos_closed)/2+150 : !strcmp(name,"point")? hc.pos_open+100 : (hc.pos_open+hc.pos_closed)/2;
  ft_set_torque_limit(SERVO_ID, preview? hc.torque_min : hc.torque_max/2); ft_set_goal(SERVO_ID,target,500); closing=!preview;
}
void gr_stop(void){ uint16_t p; if(ft_position(SERVO_ID,&p)) ft_set_goal(SERVO_ID,p,0); closing=false; }
void gr_estop(void){ estopped=true; ft_set_torque_limit(SERVO_ID,hc.torque_max); ft_set_goal(SERVO_ID,hc.pos_open,1000); closing=false; }   // open then hold open; power-cycle clears
void gr_keepalive(uint32_t now){ last_keep=now; if(estopped && false) estopped=false; }
void gr_tick(uint32_t now){
  static uint32_t last_poll=0; if(now-last_poll<50) return; last_poll=now;
  ft_position(SERVO_ID,&pos); ft_load(SERVO_ID,&load);
  if(last_keep && now-last_keep>KEEPALIVE_TIMEOUT_MS && !estopped){ gr_open(); last_keep=0; }   // band gone: open, never hold a grip on a dead link
}
int gr_status_json(char *b,int n){ return snprintf(b,n,"{\"pos\":%u,\"load\":%u,\"force\":%.2f,\"grip\":\"%s\",\"estop\":%s,\"closing\":%s}",pos,load&0x3FF,cur_force,cur_grip,estopped?"true":"false",closing?"true":"false"); }
