"""Band bench test - MicroPython on the Pico 2 W. Flash MicroPython (Pico 2 W build), copy this file as main.py
(or run it from MicroPico), open the serial console.

Pins follow firmware/PINOUT.md exactly. It prints one status line per 200 ms and runs an actuator self-test on
the button. Nothing here is the real firmware; it is the "is every wire right" tool.

  EMG   flex=0.031 ext=0.027 V        mean |v - 1.5| over the last 20 ms, per channel (rest ~0.02, fist ~0.3+)
  BAT   3.98 V                        from the divider on GP28 (x2)
  BTN   0 / 1                         1 while pressed
  IMU   ok 0x4b / -- missing           I2C scan for the BNO08x (0x4A or 0x4B)
  WIFI  <rssi>                        if WIFI_SSID is set: joins and sends UDP frames to UDP_HOST:5005

Button: tap = buzz + LED chase, hold 1 s = white flash. Ctrl-C stops.
"""
import machine, time, sys
from machine import Pin, ADC, I2C
import neopixel

# ---------------------------------------------------------------- PINOUT.md
PIN_EMG1, PIN_EMG2, PIN_VBAT = 26, 27, 28
PIN_SDA, PIN_SCL, PIN_IMU_INT, PIN_IMU_RST = 4, 5, 6, 7
PIN_BTN, PIN_MOTOR, PIN_WS2812 = 14, 15, 16
N_PIXELS = 3

# optional Wi-Fi UDP stream (fill in to test level 1 of the build order)
WIFI_SSID = ""
WIFI_PASS = ""
UDP_HOST, UDP_PORT = "192.168.1.10", 5005

emg1, emg2, vbat = ADC(PIN_EMG1), ADC(PIN_EMG2), ADC(PIN_VBAT)
btn = Pin(PIN_BTN, Pin.IN, Pin.PULL_UP)
motor = Pin(PIN_MOTOR, Pin.OUT, value=0)
imu_rst = Pin(PIN_IMU_RST, Pin.OUT, value=1)
px = neopixel.NeoPixel(Pin(PIN_WS2812), N_PIXELS)
i2c = I2C(0, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=400_000)
led = Pin("LED", Pin.OUT)


def volts(adc):
    return adc.read_u16() * 3.3 / 65535


def effort(adc, n=20):
    """Mean |v - 1.5| over n samples ~1 ms apart (what the real firmware does over 20 ms)."""
    acc = 0.0
    for _ in range(n):
        acc += abs(volts(adc) - 1.5)
        time.sleep_us(900)
    return acc / n


def fill(rgb):
    for i in range(N_PIXELS):
        px[i] = rgb
    px.write()


def buzz(ms):
    motor.value(1); time.sleep_ms(ms); motor.value(0)


def selftest():
    print("SELFTEST: motor 150 ms, pixels R G B W")
    buzz(150)
    for c in ((40, 0, 0), (0, 40, 0), (0, 0, 40), (40, 40, 40), (0, 0, 0)):
        fill(c); time.sleep_ms(200)


def imu_status():
    found = [a for a in i2c.scan() if a in (0x4A, 0x4B)]
    return "ok 0x%02x" % found[0] if found else "-- missing"


def wifi_up():
    if not WIFI_SSID:
        return None
    import network, socket
    wlan = network.WLAN(network.STA_IF); wlan.active(True); wlan.connect(WIFI_SSID, WIFI_PASS)
    for _ in range(100):
        if wlan.isconnected():
            break
        time.sleep_ms(100)
    if not wlan.isconnected():
        print("WIFI: failed"); return None
    print("WIFI:", wlan.ifconfig()[0])
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return (wlan, s)


print("band bench - PINOUT.md pins. IMU:", imu_status())
selftest()
net = wifi_up()
seq = 0; t0 = time.ticks_ms(); pressed_at = None; held_done = False
while True:
    f, e = effort(emg1), effort(emg2)
    vb = volts(vbat) * 2
    b = 0 if btn.value() else 1
    now = time.ticks_ms()
    if b and pressed_at is None:
        pressed_at = now; held_done = False
    if b and pressed_at is not None and not held_done and time.ticks_diff(now, pressed_at) > 1000:
        fill((60, 60, 60)); buzz(300); fill((0, 0, 0)); held_done = True
    if not b and pressed_at is not None:
        if not held_done:
            buzz(60)
            for i in range(N_PIXELS):
                fill((0, 0, 0)); px[i] = (0, 50, 0); px.write(); time.sleep_ms(80)
            fill((0, 0, 0))
        pressed_at = None
    # live EMG on the pixels: green = flexor, red = extensor
    px[0] = (0, min(255, int(f * 600)), 0); px[1] = (min(255, int(e * 600)), 0, 0); px.write()
    led.toggle()
    line = "EMG flex=%.3f ext=%.3f V  BAT %.2f V  BTN %d  IMU %s" % (f, e, vb, b, imu_status())
    if net:
        wlan, s = net
        seq += 1
        msg = '{"id":"band1","seq":%d,"t":%d,"c":[%.3f,%.3f],"b":%.2f}' % (seq, time.ticks_diff(now, t0), f, e, vb)
        try:
            s.sendto(msg, (UDP_HOST, UDP_PORT)); line += "  WIFI %d" % wlan.status("rssi")
        except Exception as ex:
            line += "  WIFI err %s" % ex
    print(line)
    time.sleep_ms(150)
