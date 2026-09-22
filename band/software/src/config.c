#include "config.h"
#include <string.h>
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "pico/stdlib.h"
#define CFG_FLASH_OFFSET (PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE)
#define CFG_MAGIC 0x42414E44u
band_config_t cfg;
static uint32_t crc32(const uint8_t *p, size_t n){ uint32_t c=0xFFFFFFFFu; for(size_t i=0;i<n;i++){ c^=p[i]; for(int k=0;k<8;k++) c=(c>>1)^(0xEDB88320u & (0u-(c&1u))); } return ~c; }
void config_defaults(void){
  memset(&cfg,0,sizeof cfg); cfg.magic=CFG_MAGIC;
  strcpy(cfg.wifi_ssid[0],"TABOR_SSID"); strcpy(cfg.wifi_pass[0],"TABOR_PASS");   // profile 0: Tabor's
  strcpy(cfg.wifi_ssid[1],"KYLE_SSID");  strcpy(cfg.wifi_pass[1],"KYLE_PASS");    // profile 1: Kyle's
  strcpy(cfg.factum_key,"change-me-to-a-long-random-string"); cfg.cfg_port=80;
  strcpy(cfg.ap_ssid,"RoboKyle"); strcpy(cfg.ap_pass,"robokyle1");
  strcpy(cfg.factum_host,"192.168.1.10"); cfg.factum_port=5005;
  strcpy(cfg.hand_host,"192.168.4.16"); cfg.hand_port=80;      // AP mode: first DHCP lease from the Pico's dhcp server
  strcpy(cfg.band_id,"band1");
  cfg.flex_on=0.25f; cfg.flex_off=0.15f; cfg.flex_max=0.9f; cfg.ext_on=0.25f; cfg.ext_off=0.15f; cfg.ext_max=0.9f; cfg.force_limit=0.4f;
  cfg.mouse_gain=0.08f; cfg.mouse_deadzone=3.0f; cfg.mouse_accel=1.4f;
  cfg.bt_slot=0; cfg.last_mode=MODE_HAND_DIRECT; cfg.grip_count=6;
}
void config_load(void){
  const band_config_t *f=(const band_config_t*)(XIP_BASE+CFG_FLASH_OFFSET);
  if (f->magic==CFG_MAGIC && f->crc==crc32((const uint8_t*)f,sizeof(*f)-4)) { cfg=*f; return; }
  config_defaults(); config_save();
}
void config_save(void){
  cfg.crc=crc32((const uint8_t*)&cfg,sizeof(cfg)-4);
  static uint8_t page[FLASH_PAGE_SIZE*2]; memset(page,0xFF,sizeof page); memcpy(page,&cfg,sizeof cfg);
  uint32_t ints=save_and_disable_interrupts(); flash_range_erase(CFG_FLASH_OFFSET,FLASH_SECTOR_SIZE); flash_range_program(CFG_FLASH_OFFSET,page,sizeof page); restore_interrupts(ints);
}
