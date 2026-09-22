#pragma once
// Config/status HTTP server on the band. Factum calls it; nothing else has the key.
//   GET  /status                  -> mode, battery, wifi, intent, thresholds summary (no key needed)
//   GET  /config                  -> full config JSON minus secrets (key needed)
//   POST /config  {partial JSON}  -> merge into flash config; e.g. {"flex_on":0.3,"wifi":[{"ssid":"..","pass":".."}]} (key)
//   POST /calibrate {"phase":"rest"|"close"|"open"|"apply"}  -> 10 s capture per phase; apply computes thresholds (key)
//   POST /buzz {}                 -> pulse the motor (key)
//   POST /mode {"mode":0..2}      -> switch mode (key)
void cfgsrv_start(void);
void cfgsrv_tick(uint32_t now_ms);   // runs the calibration capture
