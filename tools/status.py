"""板子状态报告 - 一键获取 ESP32-S3 健康信息

用法: uv run tools/status.py

输出内存、WiFi、运行时间、文件列表等信息。
部分查询失败时会显示 [N/A]，不影响其他查询。
"""
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 一次性在板子上执行所有查询的 MicroPython 脚本
# 输出格式: KEY=VALUE，每个查询一行，失败输出 KEY=[N/A]
BOARD_STATUS_SCRIPT = r"""
import sys, gc, time, os
try:
    import network
except ImportError:
    network = None

def _v(label, expr_fn):
    try:
        print("{}={}".format(label, expr_fn()))
    except Exception:
        print("{}=[N/A]".format(label))

_v("platform", lambda: sys.platform)
_v("impl", lambda: str(sys.implementation.name) + ' v' + '.'.join(str(x) for x in sys.implementation.version))
_v("uptime", lambda: str(time.ticks_ms()))
_v("mem_free", lambda: str(gc.mem_free()))
_v("mem_alloc", lambda: str(gc.mem_alloc()))
_v("wifi_conn", lambda: str(network.WLAN(network.STA_IF).isconnected()) if network else "[N/A]")
_v("wifi_ip", lambda: network.WLAN(network.STA_IF).ifconfig()[0] if network and network.WLAN(network.STA_IF).isconnected() else "[N/A]")
_v("files", lambda: str(os.listdir()))
_v("last_error", lambda: last_error if 'last_error' in dir() else "[N/A]")
"""


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def fetch_status(port: str) -> dict[str, str]:
    """在板子上执行状态查询脚本，解析 KEY=VALUE 输出返回字典。"""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "connect", f"port:{port}",
             "resume", "exec", BOARD_STATUS_SCRIPT],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        return {}

    if r.returncode != 0:
        return {}

    result = {}
    for line in r.stdout.strip().splitlines():
        if "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip()
    return result


def print_status(cfg):
    port = cfg["device"]["port"]

    print("[STATUS] ESP32-S3 Board Report")
    print("[STATUS] ========================")

    data = fetch_status(port)

    def get(key: str) -> str:
        return data.get(key, "[N/A]")

    # 1. Platform
    print(f"[STATUS] Platform: {get('platform')}")

    # 2. MicroPython version
    print(f"[STATUS] MicroPython: {get('impl')}")

    # 3. Uptime
    ticks = get("uptime")
    if ticks not in ("[N/A]", "") and ticks.lstrip("-").isdigit():
        print(f"[STATUS] Uptime: {int(ticks) // 1000}s")
    else:
        print("[STATUS] Uptime: [N/A]")

    # 4. Memory
    mem_free = get("mem_free")
    mem_alloc = get("mem_alloc")
    if mem_free != "[N/A]" and mem_alloc != "[N/A]":
        print(f"[STATUS] Memory: {mem_free} free / {mem_alloc} allocated")
    else:
        print("[STATUS] Memory: [N/A]")

    # 5. WiFi
    wifi_conn = get("wifi_conn")
    if wifi_conn == "True":
        wifi_ip = get("wifi_ip")
        if wifi_ip == "[N/A]":
            wifi_ip = "?"
        print(f"[STATUS] WiFi: connected ({wifi_ip})")
    elif wifi_conn == "False":
        print("[STATUS] WiFi: disconnected")
    else:
        print("[STATUS] WiFi: [N/A]")

    # 6. Files
    print(f"[STATUS] Files: {get('files')}")

    # 7. Last error
    last_err = get("last_error")
    if last_err not in ("[N/A]", "None", ""):
        print(f"[STATUS] Last error: {last_err}")

    print("[STATUS] ========================")


if __name__ == "__main__":
    cfg = load_config()
    print_status(cfg)
