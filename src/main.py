from machine import Pin
import neopixel
import network
import socket
import time

# Editable Wi-Fi settings.
WIFI_SSID = "zhaocake"
WIFI_PASSWORD = "cake123456"

RGB_LED_PIN = 48
LED_COUNT = 1

COLOR_MAP = {
    "red": (100, 0, 0),
    "green": (0, 100, 0),
    "blue": (0, 0, 100),
    "white": (80, 80, 80),
    "yellow": (100, 100, 0),
    "cyan": (0, 100, 100),
    "magenta": (100, 0, 100),
    "off": (0, 0, 0),
}

current_color = "off"


def set_color(np, color_name):
    global current_color
    color = COLOR_MAP.get(color_name, COLOR_MAP["off"])
    np[0] = color
    np.write()
    current_color = color_name if color_name in COLOR_MAP else "off"
    print("[RGB] color -> {} {}".format(current_color, color))


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("[WIFI] connecting to {} ...".format(WIFI_SSID))
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        retry = 0
        while (not wlan.isconnected()) and retry < 120:
            retry += 1
            time.sleep(0.25)

    if not wlan.isconnected():
        raise RuntimeError("wifi connect timeout")

    ip = wlan.ifconfig()[0]
    print("[WIFI] connected, ip={}".format(ip))
    return ip


def parse_color_from_path(path):
    # Expect path format like /set?c=red
    if not path.startswith("/set?"):
        return None

    query = path.split("?", 1)[1]
    for item in query.split("&"):
        if item.startswith("c="):
            return item[2:].lower()
    return None


def render_page(ip):
    buttons = []
    for name in ("red", "green", "blue", "white", "yellow", "cyan", "magenta", "off"):
        buttons.append('<a href="/set?c={}"><button>{}</button></a>'.format(name, name.upper()))

    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ESP32 RGB Control</title>
  <style>
        body {{ font-family: sans-serif; max-width: 720px; margin: 24px auto; padding: 0 12px; }}
        h1 {{ font-size: 22px; margin-bottom: 8px; }}
        p {{ margin: 6px 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, minmax(120px, 1fr)); gap: 10px; margin-top: 14px; }}
        button {{ width: 100%; padding: 12px; font-size: 15px; border: 1px solid #999; border-radius: 8px; background: #f3f3f3; }}
  </style>
</head>
<body>
  <h1>ESP32-S3 RGB LED</h1>
  <p>IP: <b>{ip}</b></p>
  <p>Current: <b>{current}</b></p>
  <div class="grid">{buttons}</div>
</body>
</html>
""".format(ip=ip, current=current_color.upper(), buttons="".join(buttons))


def run_http_server(np, ip):
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(2)
    print("[HTTP] open http://{}".format(ip))

    while True:
        client = None
        try:
            client, client_addr = sock.accept()
            client.settimeout(2)

            req = client.recv(1024)
            if not req:
                time.sleep(0.01)
                continue

            request_line = req.decode("utf-8", "ignore").split("\r\n", 1)[0]
            parts = request_line.split(" ")
            path = parts[1] if len(parts) >= 2 else "/"

            chosen = parse_color_from_path(path)
            if chosen is not None:
                set_color(np, chosen)

            body = render_page(ip)
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                "Connection: close\r\n\r\n"
                + body
            )
            client.send(response.encode("utf-8"))
            print("[HTTP] {} path={}".format(client_addr, path))

        except Exception as e:
            # Some clients connect and close without sending full data.
            # Suppress common timeout noise to keep serial logs readable.
            msg = str(e)
            if ("ETIMEDOUT" not in msg) and ("timed out" not in msg):
                print("[HTTP] error:", e)
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

        time.sleep(0.01)


try:
    np = neopixel.NeoPixel(Pin(RGB_LED_PIN, Pin.OUT), LED_COUNT)
    set_color(np, "off")
    print("[RGB] onboard LED pin = GPIO{}".format(RGB_LED_PIN))

    ip_addr = connect_wifi()
    run_http_server(np, ip_addr)

except Exception as e:
    print("[FATAL]", e)
    while True:
        time.sleep(1)
