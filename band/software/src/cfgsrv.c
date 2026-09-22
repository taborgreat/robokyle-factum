#include "cfgsrv.h"
#include "config.h"
#include "io.h"
#include "emg.h"
#include "net.h"
#include "modes.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"
#include "pico/stdlib.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
extern intent_t g_last_intent;   // set in modes.c
static float jnum(const char *b,const char *k,float dflt){ const char *p=strstr(b,k); if(!p) return dflt; p=strchr(p,':'); return p?(float)atof(p+1):dflt; }
static bool jstr(const char *b,const char *k,char *o,int n){ o[0]=0; const char *p=strstr(b,k); if(!p) return false; p=strchr(p,':'); if(!p) return false; p=strchr(p,'"'); if(!p) return false; p++; int i=0; while(*p&&*p!='"'&&i<n-1) o[i++]=*p++; o[i]=0; return true; }
static bool has_key(const char *req){ char k[80]; snprintf(k,sizeof k,"X-Factum-Key: %s",cfg.factum_key); return strstr(req,k)!=NULL; }
static void reply(struct tcp_pcb *pcb,int code,const char *body){ char h[160]; int n=snprintf(h,sizeof h,"HTTP/1.1 %d OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",code,(int)strlen(body)); tcp_write(pcb,h,n,TCP_WRITE_FLAG_COPY); tcp_write(pcb,body,strlen(body),TCP_WRITE_FLAG_COPY); tcp_output(pcb); }

// ---- calibration capture ----
static int cal_phase=-1; static uint32_t cal_t0; static float cal_f[3], cal_e[3]; static uint32_t cal_n;
static float acc_f, acc_e;
void cfgsrv_tick(uint32_t now){
  if (cal_phase<0) return;
  extern effort_t g_last_effort; acc_f+=g_last_effort.flex; acc_e+=g_last_effort.ext; cal_n++;
  if (now-cal_t0>=10000) { cal_f[cal_phase]=acc_f/cal_n; cal_e[cal_phase]=acc_e/cal_n; cal_phase=-1; buzz(200); }
}
static void cal_start(int ph, uint32_t now){ cal_phase=ph; cal_t0=now; acc_f=acc_e=0; cal_n=0; buzz(80); }
static void cal_apply(void){   // on-thresholds 40% of the way rest->active, off 25% (band/BUILD.txt)
  float rf=cal_f[0], re=cal_e[0], cf=cal_f[1], oe=cal_e[2];
  cfg.flex_on = rf + 0.40f*(cf-rf); cfg.flex_off = rf + 0.25f*(cf-rf); cfg.flex_max = cf;
  cfg.ext_on  = re + 0.40f*(oe-re); cfg.ext_off  = re + 0.25f*(oe-re); cfg.ext_max  = oe;
  config_save();
}

static int config_json(char *o,int n,bool secrets){
  int k=snprintf(o,n,"{\"band_id\":\"%s\",\"factum_host\":\"%s\",\"factum_port\":%u,\"hand_host\":\"%s\",\"hand_port\":%u,"
    "\"flex_on\":%.3f,\"flex_off\":%.3f,\"flex_max\":%.3f,\"ext_on\":%.3f,\"ext_off\":%.3f,\"ext_max\":%.3f,\"force_limit\":%.2f,"
    "\"mouse_gain\":%.3f,\"mouse_deadzone\":%.1f,\"mouse_accel\":%.2f,\"bt_slot\":%u,\"grip_count\":%u,\"wifi\":[",
    cfg.band_id,cfg.factum_host,cfg.factum_port,cfg.hand_host,cfg.hand_port,cfg.flex_on,cfg.flex_off,cfg.flex_max,cfg.ext_on,cfg.ext_off,cfg.ext_max,cfg.force_limit,
    cfg.mouse_gain,cfg.mouse_deadzone,cfg.mouse_accel,cfg.bt_slot,cfg.grip_count);
  for(int i=0;i<4;i++) k+=snprintf(o+k,n-k,"%s{\"ssid\":\"%s\"}",i?",":"",cfg.wifi_ssid[i]);
  k+=snprintf(o+k,n-k,"],\"ap_ssid\":\"%s\"}",cfg.ap_ssid);
  return k;
}
static void config_merge(const char *b){
  #define NUM(f) { const char *p=strstr(b,"\"" #f "\""); if(p) cfg.f=jnum(b,"\"" #f "\"",cfg.f); }
  NUM(flex_on) NUM(flex_off) NUM(flex_max) NUM(ext_on) NUM(ext_off) NUM(ext_max) NUM(force_limit)
  NUM(mouse_gain) NUM(mouse_deadzone) NUM(mouse_accel) NUM(grip_count) NUM(factum_port) NUM(hand_port)
  char s[65];
  if (jstr(b,"\"factum_host\"",s,sizeof s)) strncpy(cfg.factum_host,s,63);
  if (jstr(b,"\"hand_host\"",s,sizeof s))   strncpy(cfg.hand_host,s,63);
  if (jstr(b,"\"ap_ssid\"",s,sizeof s))     strncpy(cfg.ap_ssid,s,32);
  if (jstr(b,"\"ap_pass\"",s,sizeof s))     strncpy(cfg.ap_pass,s,64);
  if (jstr(b,"\"factum_key\"",s,sizeof s))  strncpy(cfg.factum_key,s,32);
  // wifi: [{"ssid":..,"pass":..}, ...] replaces profiles in order
  const char *w=strstr(b,"\"wifi\""); if (w) { const char *p=w; for(int i=0;i<4;i++){ p=strstr(p,"{"); if(!p) { cfg.wifi_ssid[i][0]=0; continue; }
      const char *e=strchr(p,'}'); char item[200]; int L=e?(int)(e-p+1):(int)strlen(p); if(L>199)L=199; memcpy(item,p,L); item[L]=0;
      if (jstr(item,"\"ssid\"",s,sizeof s)) strncpy(cfg.wifi_ssid[i],s,32); if (jstr(item,"\"pass\"",s,sizeof s)) strncpy(cfg.wifi_pass[i],s,64); p=e?e+1:p+1; } }
  config_save();
}

static err_t on_recv(void *arg,struct tcp_pcb *pcb,struct pbuf *p,err_t err){
  if(!p){ tcp_close(pcb); return ERR_OK; }
  char req[1024]; int n=p->tot_len<1023?p->tot_len:1023; pbuf_copy_partial(p,req,n,0); req[n]=0; tcp_recved(pcb,p->tot_len); pbuf_free(p);
  char method[8]={0}, path[48]={0}; sscanf(req,"%7s %47s",method,path);
  const char *body=strstr(req,"\r\n\r\n"); body=body?body+4:"";
  static char out[900];
  if (!strcmp(method,"GET") && !strcmp(path,"/status")) {
    snprintf(out,sizeof out,"{\"id\":\"%s\",\"mode\":%d,\"battery\":%.2f,\"wifi\":%d,\"intent\":%d,\"uptime\":%lu}",cfg.band_id,modes_current(),battery_volts(),net_rssi(),(int)g_last_intent,(unsigned long)to_ms_since_boot(get_absolute_time()));
    reply(pcb,200,out);
  } else if (!has_key(req)) { reply(pcb,401,"{\"error\":\"key\"}"); }
  else if (!strcmp(method,"GET") && !strcmp(path,"/config")) { config_json(out,sizeof out,false); reply(pcb,200,out); }
  else if (!strcmp(method,"POST") && !strcmp(path,"/config")) { config_merge(body); config_json(out,sizeof out,false); reply(pcb,200,out); }
  else if (!strcmp(method,"POST") && !strcmp(path,"/calibrate")) { char ph[8]; jstr(body,"\"phase\"",ph,sizeof ph); uint32_t now=to_ms_since_boot(get_absolute_time());
    if(!strcmp(ph,"rest")) cal_start(0,now); else if(!strcmp(ph,"close")) cal_start(1,now); else if(!strcmp(ph,"open")) cal_start(2,now); else if(!strcmp(ph,"apply")) cal_apply();
    reply(pcb,200,"{\"ok\":true}"); }
  else if (!strcmp(method,"POST") && !strcmp(path,"/buzz")) { buzz(150); reply(pcb,200,"{\"ok\":true}"); }
  else if (!strcmp(method,"POST") && !strcmp(path,"/mode")) { int m=(int)jnum(body,"\"mode\"",-1); if(m>=0&&m<MODE_COUNT) modes_switch((band_mode_t)m); reply(pcb,200,"{\"ok\":true}"); }
  else reply(pcb,404,"{}");
  tcp_close(pcb); return ERR_OK;
}
static err_t on_accept(void *arg,struct tcp_pcb *pcb,err_t err){ tcp_recv(pcb,on_recv); return ERR_OK; }
void cfgsrv_start(void){ struct tcp_pcb *l=tcp_new(); tcp_bind(l,IP_ADDR_ANY,cfg.cfg_port); l=tcp_listen(l); tcp_accept(l,on_accept); }
