# Claw hand firmware (Pico 2 W)

Serves the hand API the band expects. Build like the band (PICO_SDK_PATH, cmake, make); no BTstack needed.

Endpoints (JSON, reply 200 before acting):
  POST /open {}   POST /close {"force":0..1}   POST /grip {"name":"pinch","preview":true}   POST /stop {}
  POST /estop {}   POST /keepalive {"t":ms}   GET /status -> {pos,load,force,grip,estop,closing}

Safety: no keepalive for 500 ms -> open. ESTOP -> open at full torque and refuse commands until power-cycle.
Force 0..1 -> servo torque limit TORQUE_MIN..TORQUE_MAX; the servo stops where load meets the limit (holding, not crushing).

Before first run: set the servo ID to 1 and its angle limits with the Feetech PC tool over the driver board's USB, then
measure POS_OPEN/POS_CLOSED ticks and put them in config.h. Start TORQUE_MAX low and raise until a sock is held.
Wiring: driver board TX/RX/GND -> Pico GP9/GP8/GND (VERIFY the board's UART direction labels), pack -> BMS -> switch ->
driver power + buck (5 V -> VSYS) + charger BAT.

Cord (optional): UART on GP0/GP1 at 115200, 3-wire JST to the band. The band sends {"hello":"band"} every second; the hand
replies {"hello":"hand"} and then accepts the same commands as JSON lines ({"cmd":"close","force":0.4}). Keepalive rule
still applies over the wire. HTTP keeps working alongside; the band simply stops using Wi-Fi while the cord is live.

Config API (Factum only, header X-Factum-Key): GET /config | POST /config {"torque_max":500,"pos_open":1400,"wifi":[{"ssid":..,"pass":..}]}
Up to 4 Wi-Fi profiles (home, Kyle's, the band's hotspot, spare) tried in order on boot; all persisted in flash.
