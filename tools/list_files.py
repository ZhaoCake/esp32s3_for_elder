"""列出板子上的文件

用法: uv run tools/list_files.py [目录]
默认列出根目录
"""
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def list_files(cfg, directory: str = ":"):
    port = cfg["device"]["port"]
    r = subprocess.run(
        [sys.executable, "-m", "mpremote", "resume", "ls", directory],
    )
    if r.returncode != 0:
        print("[ERROR] 列出文件失败，板子可能未连接")
        sys.exit(1)


if __name__ == "__main__":
    cfg = load_config()
    directory = sys.argv[1] if len(sys.argv) > 1 else ":"
    list_files(cfg, directory)
