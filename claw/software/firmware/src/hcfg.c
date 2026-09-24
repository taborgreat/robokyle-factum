#include "hcfg.h"
#include <string.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/flash.h"
#include "hardware/flash.h"
hcfg_t hc;
#define OFF (PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE)
static uint32_t crc32(const uint8_t *p, size_t n) { uint32_t c = 0xFFFFFFFFu; while (n--) { c ^= *p++; for (int i = 0; i < 8; i++) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u))); } return ~c; }
static void defaults(void) {
  memset(&hc, 0, sizeof hc); hc.magic = HC_MAGIC; hc.version = HC_VERSION;
  strcpy(hc.hand_id, "claw1"); strcpy(hc.factum_key, "change-me-on-first-setup");
  strcpy(hc.wifi[0].ssid, "TABOR_WIFI"); strcpy(hc.wifi[0].pass, "password");
  strcpy(hc.wifi[1].ssid, "RoboKyle"); strcpy(hc.wifi[1].pass, "robokyle");      // the band's hotspot
  hc.pos_open = 1000; hc.pos_closed = 2600; hc.torque_min = 150; hc.torque_max = 700; hc.speed = 1500;
}
void hcfg_load(void) {
  const hcfg_t *f = (const hcfg_t *)(XIP_BASE + OFF);
  if (f->magic == HC_MAGIC && f->version == HC_VERSION && f->crc == crc32((const uint8_t *)f, offsetof(hcfg_t, crc))) { memcpy(&hc, f, sizeof hc); printf("hcfg: flash\n"); return; }
  defaults(); printf("hcfg: defaults\n");
}
static void prog(void *p) { flash_range_erase(OFF, FLASH_SECTOR_SIZE); flash_range_program(OFF, p, FLASH_PAGE_SIZE * ((sizeof(hcfg_t) + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE)); }
bool hcfg_save(void) {
  static uint8_t buf[FLASH_PAGE_SIZE * ((sizeof(hcfg_t) + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE)];
  hc.crc = crc32((const uint8_t *)&hc, offsetof(hcfg_t, crc)); memset(buf, 0xFF, sizeof buf); memcpy(buf, &hc, sizeof hc);
  return flash_safe_execute(prog, buf, 200) == PICO_OK;
}
