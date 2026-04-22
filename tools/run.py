"""开发模式运行代码 - 安全执行，不怕死循环

用法: uv run tools/run.py [文件名]
默认运行 src/main.py

流程：清空 boot.py -> 运行代码
"""
import subprocess
import sys
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
    if mpremote_exec(port, "with open('boot.py','w') as f: f.write('')"):
        print("[OK] boot.py 已清空（开发模式安全锁）")
    else:
        print("[WARN] 清空 boot.py 失败，板子可能未连接")

    print(f"\n[RUN] 运行 {target} (Ctrl+C 终止) ...")
    print("-" * 40)
    try:
        subprocess.run(
            [sys.executable, "-m", "mpremote", "resume",
             "run", str(target)],
        )
    except KeyboardInterrupt:
        print("\n[STOP] 用户中断运行")


if __name__ == "__main__":
    cfg = load_config()
    filename = sys.argv[1] if len(sys.argv) > 1 else cfg["project"]["main_file"]
    run_file(cfg, filename)
