# EMG band firmware (Pico W, C SDK + lwIP + BTstack)

Untested skeleton: structure, state machines, pin map, and protocols are complete; API names marked VERIFY need checking
against the Pico SDK version installed (2.x). Build:

    export PICO_SDK_PATH=~/pico-sdk   # SDK 2.0+ with BTstack + cyw43 driver submodules
    cp $PICO_SDK_PATH/../pico-examples/pico_w/wifi/access_point/dhcpserver/dhcpserver.{c,h} src/
    mkdir build && cd build && cmake .. && make -j
    # copy emg_band.uf2 to the Pico in BOOTSEL

Edit src/config.c defaults (Wi-Fi, Factum IP, hand IP) or write them over USB serial later (TODO: serial config shell).

Modes (button: tap / double / 1 s / 2 s / 3 s; muscles: two co-contractions within 1 s = mode switch):
- HAND_FACTUM  green solid: joins home Wi-Fi, classifies on-board, POSTs to the hand, streams UDP frames to Factum.
- HAND_DIRECT  green fast blink: hosts AP "RoboKyle" (192.168.4.1, DHCP), hand joins, band POSTs to it. No server needed.
- MOUSE        slot color (blue/cyan/magenta/white) slow blink -> solid when connected: BLE HID mouse from gyro rates.
  Double-tap = next slot (buzz count), 3 s hold = pair (white blink), disconnected hosts reconnect via directed advertising.
- HAND_WIRED   amber solid: entered automatically when the hand answers hellos on the UART cord (GP0/GP1, 115200);
  radios off, mouse mode exited, button/muscle mode changes ignored; unplug -> back to the last wireless mode.
- 2 s hold in a hand mode = ESTOP (red blink, 2 s buzz): POST /estop to the hand and to Factum.

Files: config (flash-persisted settings), io (button/LED/motor/battery), emg (1 kHz sampling, 20 ms effort, thresholds +
hysteresis + debounce, force), imu (BNO08x Game Rotation Vector + gyro), net (STA/AP, UDP, tiny HTTP POST), factum (frame
contract), hand (HTTP API), wheel (grip wheel with live preview), ble_mouse (HOGP, 4 slots), modes (per-mode logic), main.

Known TODOs: DNS for hostnames (uses IPs now); serial config shell; store BT slot addresses in cfg (see ble_mouse.c note);
verify IMU axis mapping on the arm; calibration routine (10 s rest / close / open -> thresholds at 40% and 25% of range).

Config API (band, port 80, only Factum has the key; header X-Factum-Key):
  GET /status (no key) | GET /config | POST /config {partial} e.g. {"flex_on":0.3,"wifi":[{"ssid":"a","pass":"b"},{"ssid":"c","pass":"d"}]}
  POST /calibrate {"phase":"rest"|"close"|"open"|"apply"} (10 s captures, apply sets thresholds) | POST /buzz | POST /mode {"mode":0..2}
Up to 4 Wi-Fi profiles tried in order; ship with Tabor's and Kyle's in config.c and change everything else from Factum.
