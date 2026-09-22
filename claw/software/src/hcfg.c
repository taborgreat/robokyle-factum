#include "hcfg.h"
#include "config.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "pico/stdlib.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#define OFF (PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE)
#define MAGIC 0x48414E44u
hand_config_t hc;
static uint32_t crc32(const uint8_t*p,size_t n){ uint32_t c=0xFFFFFFFFu; for(size_t i=0;i<n;i++){ c^=p[i]; for(int k=0;k<8;k++) c=(c>>1)^(0xEDB88320u&(0u-(c&1u))); } return ~c; }
void hcfg_defaults(void){ memset(&hc,0,sizeof hc); hc.magic=MAGIC; strcpy(hc.wifi_ssid[0],WIFI_HOME_SSID); strcpy(hc.wifi_pass[0],WIFI_HOME_PASS); strcpy(hc.wifi_ssid[1],WIFI_BAND_SSID); strcpy(hc.wifi_pass[1],WIFI_BAND_PASS); strcpy(hc.factum_key,"change-me-to-a-long-random-string"); hc.pos_open=POS_OPEN; hc.pos_closed=POS_CLOSED; hc.torque_min=TORQUE_MIN; hc.torque_max=TORQUE_MAX; hc.speed=600; }
void hcfg_load(void){ const hand_config_t *f=(const hand_config_t*)(XIP_BASE+OFF); if(f->magic==MAGIC && f->crc==crc32((const uint8_t*)f,sizeof(*f)-4)){ hc=*f; return; } hcfg_defaults(); hcfg_save(); }
void hcfg_save(void){ hc.crc=crc32((const uint8_t*)&hc,sizeof(hc)-4); static uint8_t page[FLASH_PAGE_SIZE*2]; memset(page,0xFF,sizeof page); memcpy(page,&hc,sizeof hc); uint32_t i=save_and_disable_interrupts(); flash_range_erase(OFF,FLASH_SECTOR_SIZE); flash_range_program(OFF,page,sizeof page); restore_interrupts(i); }
static float jnum(const char*b,const char*k,float d){ const char*p=strstr(b,k); if(!p) return d; p=strchr(p,':'); return p?(float)atof(p+1):d; }
static int jstr(const char*b,const char*k,char*o,int n){ o[0]=0; const char*p=strstr(b,k); if(!p) return 0; p=strchr(p,':'); if(!p) return 0; p=strchr(p,'"'); if(!p) return 0; p++; int i=0; while(*p&&*p!='"'&&i<n-1) o[i++]=*p++; o[i]=0; return 1; }
int hcfg_json(char*o,int n){ int k=snprintf(o,n,"{\"pos_open\":%u,\"pos_closed\":%u,\"torque_min\":%u,\"torque_max\":%u,\"speed\":%u,\"wifi\":[",hc.pos_open,hc.pos_closed,hc.torque_min,hc.torque_max,hc.speed); for(int i=0;i<4;i++) k+=snprintf(o+k,n-k,"%s{\"ssid\":\"%s\"}",i?",":"",hc.wifi_ssid[i]); k+=snprintf(o+k,n-k,"]}"); return k; }
void hcfg_merge(const char*b){
  if(strstr(b,"\"pos_open\"")) hc.pos_open=(uint16_t)jnum(b,"\"pos_open\"",hc.pos_open); if(strstr(b,"\"pos_closed\"")) hc.pos_closed=(uint16_t)jnum(b,"\"pos_closed\"",hc.pos_closed);
  if(strstr(b,"\"torque_min\"")) hc.torque_min=(uint16_t)jnum(b,"\"torque_min\"",hc.torque_min); if(strstr(b,"\"torque_max\"")) hc.torque_max=(uint16_t)jnum(b,"\"torque_max\"",hc.torque_max);
  if(strstr(b,"\"speed\"")) hc.speed=(uint16_t)jnum(b,"\"speed\"",hc.speed);
  char s[65]; if(jstr(b,"\"factum_key\"",s,sizeof s)) strncpy(hc.factum_key,s,32);
  const char*w=strstr(b,"\"wifi\""); if(w){ const char*p=w; for(int i=0;i<4;i++){ p=strstr(p,"{"); if(!p){ hc.wifi_ssid[i][0]=0; continue; } const char*e=strchr(p,'}'); char it[200]; int L=e?(int)(e-p+1):(int)strlen(p); if(L>199)L=199; memcpy(it,p,L); it[L]=0; if(jstr(it,"\"ssid\"",s,sizeof s)) strncpy(hc.wifi_ssid[i],s,32); if(jstr(it,"\"pass\"",s,sizeof s)) strncpy(hc.wifi_pass[i],s,64); p=e?e+1:p+1; } }
  hcfg_save();
}
