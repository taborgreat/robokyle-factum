// Robo Kyle hand / claw - Pico 2 W. Joins the home network, then the band's hotspot; serves the hand API on :80;
// answers the cord. The band commands; the keepalive watchdog opens the claw if the band goes quiet.
#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/watchdog.h"
#include "hardware/adc.h"
#include "pins.h"
#include "hcfg.h"
#include "gripper.h"
#include "httpd.h"
#include "wire.h"
#include "status_led.h"

static bool wifi_join(void) {
  for (int i = 0; i < 4; i++) {
    if (!hc.wifi[i].ssid[0]) continue;
    printf("wifi: joining %s\n", hc.wifi[i].ssid);
    if (cyw43_arch_wifi_connect_timeout_ms(hc.wifi[i].ssid, hc.wifi[i].pass, CYW43_AUTH_WPA2_AES_PSK, 8000) == 0) {
      printf("wifi: joined %s\n", hc.wifi[i].ssid); return true;
    }
  }
  return false;
}

int main(void) {
  stdio_init_all(); sleep_ms(300);
  printf("\nrobokyle hand %s\n", __DATE__);
  hcfg_load(); led_init(); led_rgb(40, 20, 0);
  adc_init(); adc_gpio_init(PIN_VPACK);
  gpio_init(PIN_BUTTON); gpio_set_dir(PIN_BUTTON, GPIO_IN); gpio_pull_up(PIN_BUTTON);
  gr_init(); wire_init();
  if (cyw43_arch_init_with_country(CYW43_COUNTRY_USA)) { printf("wifi: init failed\n"); }
  else { cyw43_arch_enable_sta_mode(); if (wifi_join()) { httpd_start(); led_rgb(0, 40, 0); } else led_rgb(40, 0, 0); }
  watchdog_enable(8000, 1);
  uint32_t last_retry = 0, btn_down_at = 0; bool btn_was = false;
  while (true) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    wire_poll(now); gr_tick(now); watchdog_update();
    bool btn = !gpio_get(PIN_BUTTON);
    if (btn && !btn_was) btn_down_at = now;
    if (!btn && btn_was && now - btn_down_at < 600) gr_open();                 // tap = open
    if (btn && now - btn_down_at >= 2000 && btn_was) { gr_estop(); led_rgb(80, 0, 0); }
    btn_was = btn;
    if (cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA) != CYW43_LINK_UP && now - last_retry > 10000) {
      last_retry = now; if (wifi_join()) { httpd_start(); led_rgb(0, 40, 0); }
    }
    sleep_ms(2);
  }
}
