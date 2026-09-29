#include "factum.h"
#include "config.h"
#include "net.h"
#include "hand.h"
#include <stdio.h>

void factum_send_frame(uint32_t seq, uint32_t t_ms, effort_t e, imu_t m, float vbat, intent_t intent) {
  char b[320];
  snprintf(b, sizeof b, "{\"id\":\"%s\",\"seq\":%lu,\"t\":%lu,\"c\":[%.3f,%.3f],\"b\":%.2f,\"o\":[%.1f,%.1f,%.1f],\"i\":%d,\"h\":%s}",
           cfg.band_id, (unsigned long)seq, (unsigned long)t_ms, e.flex, e.ext, vbat, m.yaw, m.pitch, m.roll, intent, hand_last_cmd());
  if (net_factum_ip()[0]) udp_send_json(net_factum_ip(), cfg.factum_port, b);
}

void factum_send_estop(uint32_t seq, uint32_t t_ms) {
  char b[96];
  snprintf(b, sizeof b, "{\"id\":\"%s\",\"seq\":%lu,\"t\":%lu,\"estop\":true}", cfg.band_id, (unsigned long)seq, (unsigned long)t_ms);
  if (!net_factum_ip()[0]) return;
  for (int i = 0; i < 5; i++) udp_send_json(net_factum_ip(), cfg.factum_port, b);
  char path[48]; snprintf(path, sizeof path, "%s/estop", cfg.factum_path);
  http_post_host(net_factum_ip(), cfg.factum_http_port, cfg.factum_host, path, b, NULL, NULL);
}
