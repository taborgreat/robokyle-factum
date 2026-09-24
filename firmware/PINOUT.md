                                        # GPIO pinout — single source of truth

Every firmware file and the wiring page derive from this table. Change it here first.

## Band — Raspberry Pi Pico 2 W

| GPIO       | Pico pin                     | Function           | Connects to                                                                | Notes                                                                                   |
| ---------- | ---------------------------- | ------------------ | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| GP0        | 1                            | UART0 TX           | cord JST-3 pin 1                                                           | HAND-WIRED cord, 115200 8N1, JSON lines                                                 |
| GP1        | 2                            | UART0 RX           | cord JST-3 pin 2                                                           | cord GND on pin 3                                                                       |
| GP4        | 6                            | I2C0 SDA           | BNO08x SDA                                                                 | 4.7k pull-ups are on the GY board                                                       |
| GP5        | 7                            | I2C0 SCL           | BNO08x SCL                                                                 | 400 kHz                                                                                 |
| GP6        | 9                            | input, pull-up     | BNO08x INT (H_INTN)                                                        | **required**: the firmware reads the IMU only when INT is low (data ready)              |
| GP7        | 10                           | output             | BNO08x RST                                                                 | lets the firmware recover a hung IMU without a power cycle                              |
| GP14       | 19                           | input, pull-up     | yellow button → GND                                                        | tap / double / 1 s / 2 s / 3 s                                                          |
| GP15       | 20                           | output             | 1k → 2N2222 base                                                           | coin motor: 3V3 → motor → collector, emitter → GND, 1N4148 across motor (stripe to 3V3) |
| GP16       | 21                           | PIO WS2812 DIN     | 2-pixel WS2812B bar                                                        | 800 kHz; bar powered from 3V3 so 3.3 V data is always valid                             |
| GP17, GP18 | 22, 24                       | free               | —                                                                          | were the old RGB LED                                                                    |
| GP26       | 31                           | ADC0               | SEN0240 #1 signal (flexor)                                                 | 0–3 V, 1.5 V centred                                                                    |
| GP27       | 32                           | ADC1               | SEN0240 #2 signal (extensor)                                               |                                                                                         |
| GP28       | 34                           | ADC2               | battery divider midpoint                                                   | BAT+ → 100k → GP28 → 100k → GND (reads BAT/2)                                           |
| 3V3(OUT)   | 36                           | 3.3 V              | SEN0240 ×2 VCC, BNO08x VIN, WS2812 +5V pad, motor +, green LED (via 470 Ω) | 300 mA budget; total load ≈ 150 mA worst case                                           |
| VSYS       | 39                           | system 5 V/battery | charger OUT+ → slide switch → 1N5817 → VSYS                                | switch off = band dead, battery still charges                                           |
| VBUS       | 40                           | USB 5 V            | charger IN+; Qi receiver +5 V → 1N5817 → VBUS                              | USB or Qi charges the cell through the module                                           |
| GND        | 3, 8, 13, 18, 23, 28, 33, 38 | ground             | star point on the strip                                                    | one ground: sensors, IMU, motor, LEDs, charger OUT−, Qi −                               |

Power path: cell → charger module B+/B− (protection + TP4056) → OUT+ → switch → 1N5817 → VSYS. VBUS feeds the
charger IN+. The Pico's own VBUS→VSYS diode and the 1N5817 OR the two sources; USB wins when plugged in.
Green 5 mm LED: 3V3 OUT (pin 36) → 470 Ω → LED long leg → short leg → GND (lit whenever the band is on or USB is in; no GPIO).

Trunk to the forearm ring (8 wires, JST-PH 8 at the puck hub, or a 6 + a 2): 3V3, GND, EMG1, EMG2, SDA, SCL, INT, RST.
Colours: green, black, yellow, yellow, white, white, white (INT), white (RST) - mark INT/RST with tape.
Cord to the hand (3 wires, JST-PH 3): TX, RX, GND (crossed at the hand: band TX → hand RX).

## Hand / claw — Raspberry Pi Pico W (original)

| GPIO | Pico pin | Function       | Connects to                | Notes                                                               |
| ---- | -------- | -------------- | -------------------------- | ------------------------------------------------------------------- |
| GP0  | 1        | UART0 TX       | cord JST-3 → band RX       |                                                                     |
| GP1  | 2        | UART0 RX       | cord JST-3 ← band TX       |                                                                     |
| GP4  | 6        | UART1 TX       | servo driver board RX      | Feetech STS3215 bus, 1 Mbaud, via the driver board                  |
| GP5  | 7        | UART1 RX       | servo driver board TX      |                                                                     |
| GP14 | 19       | input, pull-up | local button → GND         | tap = open, 2 s = local ESTOP                                       |
| GP16 | 21       | PIO WS2812 DIN | status pixel               | powered from 3V3                                                    |
| GP26 | 31       | ADC0           | 2S pack divider            | PACK+ → 100k → GP26 → 33k → GND (8.4 V → 2.08 V)                    |
| VSYS | 39       | 5 V            | buck converter 5 V out     | buck fed from pack → BMS → kill switch                              |
| GND  | —        | ground         | driver board GND, buck GND | servo power goes pack → driver board terminal, NOT through the Pico |

## Reserved / do not use

Both boards: GP23 (wireless power), GP24 (VBUS sense), GP25 (wireless SPI), GP29 (wireless / VSYS sense). Leave unconnected.
