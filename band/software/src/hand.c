#include "hand.h"
#include "net.h"
#include "config.h"
#include <stdio.h>
#include "wire.h"
static void post(const char *path, const char *body){
  if (wire_present()) { char l[128]; snprintf(l,sizeof l,"{\"cmd\":\"%s\",\"body\":%s}", path+1, body); wire_send(l); return; }
  http_post(cfg.hand_host, cfg.hand_port, path, body, NULL);
}
void hand_open(void){ post("/open","{}"); }
void hand_close(float f){ char b[32]; snprintf(b,sizeof b,"{\"force\":%.2f}",f); post("/close",b); }
void hand_grip(const char *n, bool pv){ char b[64]; snprintf(b,sizeof b,"{\"name\":\"%s\",\"preview\":%s}",n,pv?"true":"false"); post("/grip",b); }
void hand_stop(void){ post("/stop","{}"); }
void hand_estop(void){ post("/estop","{}"); }
void hand_keepalive(uint32_t t){ char b[32]; snprintf(b,sizeof b,"{\"t\":%lu}",(unsigned long)t); post("/keepalive",b); }
bool hand_busy(void){ return false; }
