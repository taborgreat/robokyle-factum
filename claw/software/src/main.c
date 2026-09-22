// Claw hand — Pico 2 W. Joins the band's network and serves the hand API; opens on lost keepalive.
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/watchdog.h"
#include "config.h"
#include "gripper.h"
#include "httpd.h"
#include "wire.h"
#include "hcfg.h"
static bool join(const char *ssid,const char *pass){ return cyw43_arch_wifi_connect_timeout_ms(ssid,pass,CYW43_AUTH_WPA2_AES_PSK,10000)==0; }
int main(void){
  stdio_init_all(); hcfg_load(); gr_init(); wire_init();
  if(cyw43_arch_init()) return 1;
  cyw43_arch_enable_sta_mode();
  // credential list: home first, then the band's hotspot; retry forever, LED blinks while trying
  bool up=false; while(!up) { for(int i=0;i<4 && !up;i++) if(hc.wifi_ssid[i][0]) up=join(hc.wifi_ssid[i],hc.wifi_pass[i]); if(up) break; cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN,1); sleep_ms(200); cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN,0); sleep_ms(200); }
  cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN,1);
  httpd_start(); watchdog_enable(4000,1);
  while(true){ uint32_t now=to_ms_since_boot(get_absolute_time()); wire_poll(now); gr_tick(now); watchdog_update(); sleep_ms(5); }
}
