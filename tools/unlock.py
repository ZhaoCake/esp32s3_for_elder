"""解锁 - 从固化模式切回开发模式（清空自启动）

用法: uv run tools/unlock.py

适用于板子正在运行自启动程序的场景。
使用 mpremote resume 中断运行程序并清空 boot.py。
"""
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from serial_helper import serial_exec


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def unlock(cfg):
    port = cfg["device"]["port"]
    clear_cmd = "with open('boot.py','w') as f: f.write('')"

    print("[1/2] 清空 boot.py (禁止自启动) ...")

    # 优先使用 mpremote resume（不触发软重启，可直接中断运行程序）
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "exec", clear_cmd],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            print("[OK] boot.py 已清空")
            print("[2/2] 软重启板子 ...")
            subprocess.run(
                [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "soft-reset"],
                capture_output=True, text=True, timeout=10,
            )
            print("\n[OK] 已恢复开发模式，可以放心测试代码了。")
            return
    except subprocess.TimeoutExpired:
        pass

    # resume 失败，尝试 raw serial 方式
    print("[1/2] mpremote resume 失败，尝试 raw serial ...")
    ok, _ = serial_exec(port, clear_cmd)
    if ok:
        print("[OK] boot.py 已清空 (serial 方式)")
        time.sleep(2)
        try:
            subprocess.run(
                [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "soft-reset"],
                capture_output=True, text=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            pass
        print("\n[OK] 已恢复开发模式。")
        return

    # 硬件复位兜底
    print("[WARN] 所有方式均失败，尝试硬件复位 ...")
    import serial as pyserial
    try:
        s = pyserial.Serial(port, 115200, timeout=1)
        s.dtr = True
        s.rts = True
        time.sleep(0.1)
        s.dtr = False
        s.rts = False
        s.close()
    except Exception:
        pass

    time.sleep(5)

    for attempt in range(3):
        try:
            r = subprocess.run(
                [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "exec", clear_cmd],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                print(f"[OK] 第 {attempt+1} 次尝试成功！")
                subprocess.run(
                    [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "soft-reset"],
                    capture_output=True, text=True, timeout=10,
                )
                print("\n[OK] 已恢复开发模式。")
                return
        except subprocess.TimeoutExpired:
            pass
        time.sleep(3)

    print("[ERROR] 解锁失败，请尝试: uv run tools/rescue.py")
    sys.exit(1)


if __name__ == "__main__":
    cfg = load_config()
    unlock(cfg)
