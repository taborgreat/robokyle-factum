#include "factum.h"
#include "net.h"
#include "config.h"
#include <stdio.h>
#include <string.h>
// Frame contract (band/BUILD.txt): one UDP datagram per 20 ms
void factum_send_frame(uint32_t seq, uint32_t t, effort_t e, imu_t m, float vbat, int intent){
  char b[200];
  int n = snprintf(b, sizeof b, "{\"id\":\"%s\",\"seq\":%lu,\"t\":%lu,\"c\":[%.3f,%.3f],\"b\":%.2f,\"o\":[%.1f,%.1f,%.1f],\"i\":%d}",
                   cfg.band_id, (unsigned long)seq, (unsigned long)t, e.flex, e.ext, vbat, m.yaw, m.pitch, m.roll, intent);
  udp_send(cfg.factum_host, cfg.factum_port, b, n);
}
void factum_send_estop(uint32_t seq, uint32_t t){
  char b[96]; int n = snprintf(b, sizeof b, "{\"id\":\"%s\",\"seq\":%lu,\"t\":%lu,\"estop\":true}", cfg.band_id, (unsigned long)seq, (unsigned long)t);
  for (int i=0;i<5;i++) udp_send(cfg.factum_host, cfg.factum_port, b, n);
  http_post(cfg.factum_host, 80, "/estop", b, NULL);
}
