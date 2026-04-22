from machine import Pin
import neopixel
import time

RGB_LED_PIN = 48
LED_COUNT = 1
MAX_STEPS = 30

COLORS = (
    (80, 0, 0),
    (0, 80, 0),
    (0, 0, 80),
    (40, 40, 40),
    (0, 0, 0),
)

try:
    np = neopixel.NeoPixel(Pin(RGB_LED_PIN, Pin.OUT), LED_COUNT)
    color_index = 0
    print("[RGB] onboard LED pin = GPIO{}".format(RGB_LED_PIN))
    print("[RGB] running {} steps, then exit".format(MAX_STEPS))

    for _ in range(MAX_STEPS):
        np[0] = COLORS[color_index]
        np.write()

        color_index += 1
        if color_index >= len(COLORS):
            color_index = 0

        time.sleep(0.5)

    np[0] = (0, 0, 0)
    np.write()
    print("[RGB] done")
except Exception as e:
    print("[RGB] init/run error:", e)
    while True:
        time.sleep(1)
