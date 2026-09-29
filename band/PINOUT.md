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
| GP7        | 10                           | input, pull-up     | trunk B pin 4 → yellow button (in the forearm module) → GND                | tap / double / 1 s / 2 s / 3 s                                                          |
| GP13       | 17                           | output             | 1k → S8050 base                                                            | coin motor (in the forearm module): MOT+ (trunk A pin 5, from 3V3) → motor → MOT− (trunk A pin 6) → collector, emitter → GND; the 1N4007 sits across the motor's own tabs in the module (stripe on the 3V3 lead) |
| GP16       | 21                           | PIO WS2812 DIN     | 3-pixel WS2812B bar, lying in the middle wall's pocket                     | 800 kHz; bar powered from 3V3 so 3.3 V data is always valid                             |
| GP17, GP18 | 22, 24                       | free               | —                                                                          | were the old RGB LED                                                                    |
| GP26       | 31                           | ADC0               | SEN0240 #1 signal (flexor)                                                 | 0–3 V, 1.5 V centred                                                                    |
| GP27       | 32                           | ADC1               | SEN0240 #2 signal (extensor)                                               |                                                                                         |
| GP28       | 34                           | ADC2               | battery divider midpoint                                                   | switched BAT+ (switch output, before the 1N5817) → 100k → GP28 → 100k → GND (reads BAT/2; zero drain when off)                                           |
| 3V3(OUT)   | 36                           | 3.3 V              | SEN0240 ×2 VCC, BNO08x VIN, WS2812 +5V pad, motor +, green LED (via 470 Ω) | 300 mA budget; total load ≈ 150 mA worst case                                           |
| VSYS       | 39                           | system 5 V/battery | cell + → slide switch → 1N5817 → VSYS                                      | switch off = band dead, even on the charging pad; the cell still charges                 |
| VBUS       | 40                           | USB 5 V            | → 1N5817 → charger IN+ (meets the Qi diode there)                          | USB runs / programs the Pico AND charges the cell; the pad charges without waking it    |
| GND        | 3, 8, 13, 18, 23, 28, 33, 38 | ground             | star point on the strip                                                    | one ground: sensors, IMU, motor, LEDs, charger OUT− (IN− and Qi − stay on the charger)  |

Power path: cell → charger board B+/B− (AITRIP TP4057 with protection) → OUT+ → switch → 1N5817 → Pico VSYS;
OUT− is the ground (protection FET in it). Charging: two feeds meet at the board's IN+, each through its own 1N5817:
Qi receiver + (Qi − → IN−), and Pico VBUS (pin 40). So the pad charges the cell with the switch off and the Pico
dark (the Qi never reaches the Pico), USB charges it too but also runs the Pico (that is the programming state; the
battery reading shows 0 with the switch off), and the switch is the only thing that connects the cell to the band.
The cell's own PCM is a second protection layer.
Green 5 mm LED: 3V3 OUT (pin 36) → 470 Ω → LED long leg → short leg → GND (lit whenever the band is on or USB is in; no GPIO).
It is soldered INTO the strip (rows 21-22, chest-side outer column) and shows through a plain hole in the lid.

Every cable is plug-to-plug: JST-PH headers (the side with the pins) sit in the box walls, the forearm module and
the hand; every cable carries a housing with crimped contacts at each end. All three box headers are at the +X end
(the end opposite the USB), in the two halves of that end wall either side of the middle wall:

| socket | wall | pin 1 → n | cable to |
|---|---|---|---|
| trunk A, PH6 | battery side | 3V3, GND, EMG1, EMG2, MOT+ (from 3V3 on the strip), MOT− (to the S8050 collector) | forearm module; the motor's current stays on its own two wires |
| trunk B, PH4 | strip side, rib side | SDA, SCL, INT, BTN (GP7) | forearm module; the IMU's RST is jumpered to VCC on its board |
| cord, PH3 | strip side, next to trunk B | TX, RX, GND | hand (crossed at the hand: band TX → hand RX) |

The button and the coin motor live in the forearm module (reachable, and the motor sits
on the strap); their driver parts (1k, S8050, 1N4007) stay on the strip and the two lines ride trunk A.

Trunk colours: A = green (3V3), black (GND), yellow (EMG1), yellow (EMG2), grey (MOT+), grey (MOT−); B = white (SDA), white (SCL), white (INT), yellow (BTN) - tape-mark INT and BTN.
The sockets drop into open-top pockets behind the wall (pins pointing into the box, **clipped to 2 mm**), wires
soldered to the pins before they go in; a dab of hot glue on top keeps them seated. Trunk wires cross to the strip
through the notch in the middle wall at that end.

Nothing is mounted on the lid. The light bar lies in the middle wall's pocket (the lid closes over it, its three
leads drop through the USB-end notch to the strip: GND, 3V3, GP16), the LED stands on the strip, the button and
motor are in the forearm module. The lid lifts straight off.

The Qi board is NOT on the lid: it lies on Kapton above the charger's wires, captive under the lid.

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
