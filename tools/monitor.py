"""串口监听 - 被动监听板子串口输出，带时间戳

用法:
  uv run tools/monitor.py        # 默认监听 5 秒
  uv run tools/monitor.py 10     # 监听 10 秒
  uv run tools/monitor.py 0      # 持续监听（Ctrl+C 停止）

注意: 此工具使用 raw serial 被动读取，不会中断板子上正在运行的程序。
"""
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def monitor(cfg, duration):
    import serial

    port = cfg["device"]["port"]
    print(f"[MONITOR] Watching {port} for {duration}s ...")
    print("[MONITOR] Press Ctrl+C to stop early")

    s = None
    line_count = 0
    start = time.time()

    try:
        s = serial.Serial(port, 115200, timeout=1, dsrdtr=False, rtscts=False)
        s.dtr = False
        s.rts = False
    except serial.SerialException as e:
        print(f"[ERROR] Cannot open {port}: {e}")
        sys.exit(1)

    try:
        buffer = ""
        while duration == 0 or (time.time() - start) < duration:
            try:
                chunk = s.read(s.in_waiting or 1)
            except Exception:
                break
            if not chunk:
                continue

            buffer += chunk.decode(errors="replace")

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line_count += 1
                ts = datetime.now().strftime("%H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}"
                print(f"[{ts}] {line}")

        # Flush remaining buffer
        if buffer.strip():
            line_count += 1
            ts = datetime.now().strftime("%H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}"
            print(f"[{ts}] {buffer.rstrip()}")
    except KeyboardInterrupt:
        print("\n[MONITOR] Stopped by user")
    finally:
        if s:
            s.close()
        elapsed = time.time() - start
        print(f"[MONITOR] Captured {line_count} lines in {elapsed:.1f}s")


if __name__ == "__main__":
    cfg = load_config()
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    monitor(cfg, duration)
