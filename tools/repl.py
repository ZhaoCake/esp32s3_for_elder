"""进入 REPL 交互模式

用法: uv run tools/repl.py
"""
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def repl(cfg):
    port = cfg["device"]["port"]
    print(f"[REPL] 连接 {port}，按 Ctrl+] 退出 ...")
    print("-" * 40)
    subprocess.run(
        [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "resume", "repl"],
    )


if __name__ == "__main__":
    cfg = load_config()
    repl(cfg)
