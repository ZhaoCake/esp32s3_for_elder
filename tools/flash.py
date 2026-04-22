"""刷入 MicroPython 固件到 ESP32-S3

用法: uv run tools/flash.py
"""
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def flash_firmware(cfg):
    port = cfg["device"]["port"]
    chip = cfg["device"]["chip"]
    baud = cfg["firmware"]["baud_rate"]
    fw_path = ROOT / cfg["firmware"]["path"]
    addr = cfg["firmware"]["flash_address"]

    if not fw_path.exists():
        print(f"[ERROR] 固件文件不存在: {fw_path}")
        sys.exit(1)

    print(f"[1/2] 擦除 Flash ({port} / {chip}) ...")
    r = subprocess.run(
        [
            sys.executable, "-m", "esptool",
            "--chip", chip, "--port", port,
            "--baud", str(baud), "erase-flash",
        ],
    )
    if r.returncode != 0:
        print("[ERROR] 擦除失败，请检查板子是否已进入下载模式。")
        sys.exit(1)

    print(f"[2/2] 写入固件 {fw_path.name} ...")
    r = subprocess.run(
        [
            sys.executable, "-m", "esptool",
            "--chip", chip, "--port", port,
            "--baud", str(baud), "write-flash", "-z", addr, str(fw_path),
        ],
    )
    if r.returncode != 0:
        print("[ERROR] 写入失败。")
        sys.exit(1)

    print("[OK] 固件刷入完成！板子正在重启...")


if __name__ == "__main__":
    cfg = load_config()
    flash_firmware(cfg)
