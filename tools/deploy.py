"""固化模式 - 将代码部署到板子，断电也能自启动

用法: uv run tools/deploy.py [文件名]
默认部署 src/main.py

流程：清空 boot.py -> 上传文件 -> 写入 boot.py -> 软重启验证
"""
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def mpremote_exec(port: str, command: str, timeout: int = 10) -> bool:
    """执行 mpremote resume exec 命令"""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "resume",
             "exec", command],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def deploy(cfg, filepath: str):
    port = cfg["device"]["port"]
    src_dir = ROOT / cfg["project"]["source_dir"]
    target = src_dir / filepath if not Path(filepath).is_absolute() else Path(filepath)

    if not target.exists():
        target = Path(filepath)
    if not target.exists():
        print(f"[ERROR] 文件不存在: {filepath}")
        sys.exit(1)

    main_name = target.stem

    # 步骤1：清空 boot.py，防止串口重连时触发自启动
    print("[1/4] 清空 boot.py ...")
    if mpremote_exec(port, "with open('boot.py','w') as f: f.write('')"):
        print("[OK] boot.py 已清空")
    else:
        print("[WARN] 清空失败，继续 ...")

    # 步骤2：上传文件
    print(f"[2/4] 上传 {target.name} ...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "mpremote", "resume",
             "cp", str(target), f":{target.name}"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            print(f"[ERROR] 上传失败: {r.stderr.strip()}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("[ERROR] 上传超时")
        sys.exit(1)
    print("[OK] 上传成功")

    # 步骤3：写入 boot.py
    print(f"[3/4] 写入 boot.py (上电自动运行 {target.name}) ...")
    boot_code = f"import {main_name}\n"
    cmd = f"with open('boot.py','w') as f: f.write({repr(boot_code)})"
    if not mpremote_exec(port, cmd):
        print("[ERROR] 写入 boot.py 失败")
        sys.exit(1)
    print("[OK] boot.py 已写入")

    # 步骤4：软重启验证自启动
    print("[4/4] 软重启验证自启动 ...")
    try:
        subprocess.run(
            [sys.executable, "-m", "mpremote", "resume",
             "soft-reset"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        pass

    print("\n[OK] 固化完成！拔掉 USB 线独立供电也能运行。")


if __name__ == "__main__":
    cfg = load_config()
    filename = sys.argv[1] if len(sys.argv) > 1 else cfg["project"]["main_file"]
    deploy(cfg, filename)
