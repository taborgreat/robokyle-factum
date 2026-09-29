// Commands to the hand. Over Wi-Fi: HTTP POST to cfg.hand_ip. Over the cord: the same commands as JSON lines.
#pragma once
#include <stdint.h>
#include <stdbool.h>
void hand_open(void);
void hand_close(float force);            // 0..1
void hand_grip(const char *name, bool preview);
void hand_stop(void);
void hand_estop(void);
void hand_keepalive(uint32_t t_ms);      // every 250 ms; the hand opens after 500 ms without one
bool hand_link_ok(void);                 // last command was acknowledged
void hand_service(void);                    // retries the pending command; call every frame
bool hand_pending(void);

// HAND-FACTUM: the band never addresses the hand; commands are recorded and ride in the Factum frame as "h".
void hand_set_relay(bool relay);
const char *hand_last_cmd(void);   // JSON object or "null"
