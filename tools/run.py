"""开发模式运行代码 - 安全执行，不怕死循环

用法: uv run tools/run.py [文件名]
默认运行 src/main.py

流程：清空 boot.py -> 运行代码
"""
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from serial_helper import serial_interrupt


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def mpremote_exec(port: str, command: str, timeout: int = 10) -> bool:
    """执行 mpremote resume exec 命令"""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "connect", f"port:{port}",
             "resume", "exec", command],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def run_file(cfg, filepath: str):
    port = cfg["device"]["port"]
    src_dir = ROOT / cfg["project"]["source_dir"]
    target = src_dir / filepath if not Path(filepath).is_absolute() else Path(filepath)

    if not target.exists():
        target = Path(filepath)
    if not target.exists():
        print(f"[ERROR] 文件不存在: {filepath}")
        sys.exit(1)

    # 清空 boot.py（开发模式安全锁）
    clear_cmd = "with open('boot.py','w') as f: f.write('')"
    if mpremote_exec(port, clear_cmd):
        print("[OK] boot.py 已清空（开发模式安全锁）")
    else:
        serial_interrupt(port)
        if mpremote_exec(port, clear_cmd):
            print("[OK] boot.py 已清空（串口中断后重试成功）")
        else:
            print("[WARN] 清空 boot.py 失败，板子可能未连接")

    print(f"\n[RUN] 运行 {target} (Ctrl+C 终止) ...")
    print("-" * 40)
    cmd = [
        sys.executable, "-m", "mpremote", "connect", f"port:{port}",
        "resume", "run", str(target),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            if r.stdout:
                print(r.stdout, end="")
            return

        error_text = (r.stdout or "") + "\n" + (r.stderr or "")
        transient_error = (
            "ClearCommError" in error_text
            or "PermissionError" in error_text
            or "拒绝访问" in error_text
            or "failed to access" in error_text
            or "no device found" in error_text
        )
        raw_repl_error = "could not enter raw repl" in error_text

        if transient_error or raw_repl_error:
            serial_interrupt(port)
            print("[WARN] 串口瞬时占用，1 秒后自动重试一次 ...")
            time.sleep(1)
            r2 = subprocess.run(cmd, capture_output=True, text=True)
            if r2.returncode != 0:
                fallback_cmd = [
                    sys.executable, "-m", "mpremote", "connect", f"port:{port}",
                    "run", str(target),
                ]
                r2 = subprocess.run(fallback_cmd, capture_output=True, text=True)
            if r2.stdout:
                print(r2.stdout, end="")
            if r2.returncode != 0 and r2.stderr:
                print(r2.stderr, end="")
            return

        if r.stderr:
            print(r.stderr, end="")
    except KeyboardInterrupt:
        print("\n[STOP] 用户中断运行")


if __name__ == "__main__":
    cfg = load_config()
    filename = sys.argv[1] if len(sys.argv) > 1 else cfg["project"]["main_file"]
    run_file(cfg, filename)
