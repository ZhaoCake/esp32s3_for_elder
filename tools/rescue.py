"""急救脚本 - 板子变砖时的终极恢复手段

用法: uv run tools/rescue.py

适用场景：板子无限重启，mpremote resume 也连不上。
原理：
  1. 硬件复位板子
  2. 等待 USB 重新识别
  3. 用 mpremote resume 在窗口期中断并清空 boot.py
  4. 如果全部失败，用 flash.py 重刷固件
"""
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from serial_helper import serial_exec

MAX_RETRIES = 5
RETRY_INTERVAL = 3


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def rescue(cfg):
    port = cfg["device"]["port"]
    chip = cfg["device"]["chip"]
    clear_cmd = "with open('boot.py','w') as f: f.write('')"

    print("=" * 50)
    print("  ESP32-S3 急救模式")
    print("=" * 50)
    print(f"  串口: {port}")
    print(f"  芯片: {chip}")
    print(f"  最大重试: {MAX_RETRIES} 次")
    print()

    # 先试 mpremote resume（如果板子还活着）
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "resume", "exec", clear_cmd],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            print("[OK] board.py 已清空，板子已恢复！")
            print("[OK] 现在可以安全地使用 uv run tools/run.py 测试代码了。")
            return
    except subprocess.TimeoutExpired:
        pass

    # resume 不行，触发硬件复位
    print("[1/3] 硬件复位板子 ...")
    import serial
    try:
        s = serial.Serial(port, 115200, timeout=1)
        s.dtr = True
        s.rts = True
        time.sleep(0.1)
        s.dtr = False
        s.rts = False
        s.close()
    except Exception:
        pass

    print(f"[2/3] 等待 USB 重新识别 ({RETRY_INTERVAL}秒) ...")
    time.sleep(RETRY_INTERVAL)

    print("[3/3] 尝试清空 boot.py ...")
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"   第 {attempt}/{MAX_RETRIES} 次尝试 ...")

        # 先试 mpremote resume
        try:
            r = subprocess.run(
                [sys.executable, "-m", "mpremote", "resume", "exec", clear_cmd],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                print(f"\n[OK] 第 {attempt} 次尝试成功 (mpremote resume)！")
                print("[OK] boot.py 已清空，板子已恢复。")
                return
        except subprocess.TimeoutExpired:
            pass

        # 再试 raw serial
        ok, _ = serial_exec(port, clear_cmd)
        if ok:
            print(f"\n[OK] 第 {attempt} 次尝试成功 (raw serial)！")
            print("[OK] boot.py 已清空，板子已恢复。")
            return

        if attempt < MAX_RETRIES:
            print(f"   {RETRY_INTERVAL}秒后重试 ...")
            time.sleep(RETRY_INTERVAL)

    print("\n[FAIL] 所有尝试均失败。")
    print("最后手段：刷入新固件（会清除板子上所有文件）:")
    print(f"  uv run tools/flash.py")


if __name__ == "__main__":
    cfg = load_config()
    rescue(cfg)
