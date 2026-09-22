#include "config.h"
#include <string.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/flash.h"
#include "hardware/flash.h"
#include "hardware/sync.h"

config_t cfg;

// BTstack keeps its bond database in the LAST TWO sectors (pico_btstack_flash_bank); we take the third from the end.
#define CFG_FLASH_OFFSET (PICO_FLASH_SIZE_BYTES - 3 * FLASH_SECTOR_SIZE)
#define CFG_FLASH_ADDR   ((const uint8_t *)(XIP_BASE + CFG_FLASH_OFFSET))

static uint32_t crc32(const uint8_t *p, size_t n) {
  uint32_t c = 0xFFFFFFFFu;
  while (n--) { c ^= *p++; for (int i = 0; i < 8; i++) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u))); }
  return ~c;
}

void config_defaults(config_t *c) {
  memset(c, 0, sizeof *c);
  c->magic = CFG_MAGIC; c->version = CFG_VERSION;
  strcpy(c->band_id, "band1");
  strcpy(c->factum_key, "change-me-on-first-setup");
  // Ship with Tabor's and Kyle's networks here; everything else is set from Factum.
  strcpy(c->wifi[0].ssid, "TABOR_WIFI"); strcpy(c->wifi[0].pass, "password");
  strcpy(c->wifi[1].ssid, "KYLE_WIFI");  strcpy(c->wifi[1].pass, "password");
  strcpy(c->factum_ip, "192.168.1.10"); c->factum_port = 5005;
  strcpy(c->hand_ip, "192.168.1.11");   c->hand_port = 80;
  strcpy(c->ap_ssid, "RoboKyle"); strcpy(c->ap_pass, "robokyle");
  c->flex_on = 0.30f; c->flex_off = 0.18f; c->ext_on = 0.30f; c->ext_off = 0.18f;
  c->flex_max = 0.90f; c->force_limit = 0.6f;
  c->mouse_gain = 0.08f; c->mouse_deadzone = 3.0f; c->mouse_accel = 1.4f;
  c->last_mode = 0; c->bt_slot = 0;
}

void config_load(void) {
  const config_t *f = (const config_t *)CFG_FLASH_ADDR;
  if (f->magic == CFG_MAGIC && f->version == CFG_VERSION &&
      f->crc == crc32((const uint8_t *)f, offsetof(config_t, crc))) {
    memcpy(&cfg, f, sizeof cfg);
    printf("config: loaded from flash\n");
    return;
  }
  config_defaults(&cfg);
  printf("config: defaults (flash empty or version mismatch)\n");
}

typedef struct { const uint8_t *data; } prog_arg_t;
static void do_program(void *p) {
  flash_range_erase(CFG_FLASH_OFFSET, FLASH_SECTOR_SIZE);
  flash_range_program(CFG_FLASH_OFFSET, ((prog_arg_t *)p)->data, FLASH_PAGE_SIZE * ((sizeof(config_t) + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE));
}

bool config_save(void) {
  static uint8_t buf[FLASH_PAGE_SIZE * ((sizeof(config_t) + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE)];
  cfg.magic = CFG_MAGIC; cfg.version = CFG_VERSION;
  cfg.crc = crc32((const uint8_t *)&cfg, offsetof(config_t, crc));
  memset(buf, 0xFF, sizeof buf);
  memcpy(buf, &cfg, sizeof cfg);
  prog_arg_t a = { buf };
  int rc = flash_safe_execute(do_program, &a, 200);
  if (rc != PICO_OK) { printf("config: save failed %d\n", rc); return false; }
  return true;
}
