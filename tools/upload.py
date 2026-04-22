"""上传文件到板子（不运行、不固化，仅拷贝）

用法:
  uv run tools/upload.py src/main.py          # 上传单个文件
  uv run tools/upload.py src/lib.py :lib/     # 上传到指定目录
  uv run tools/upload.py -r src/ :            # 批量上传整个项目
"""
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def upload(cfg, args: list[str]):
    port = cfg["device"]["port"]
    cmd = [sys.executable, "-m", "mpremote", "resume", "cp"]
    cmd.extend(args)
    print(f"[UPLOAD] {' '.join(args)}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("[ERROR] 上传失败")
        sys.exit(1)
    print("[OK] 上传成功")


if __name__ == "__main__":
    cfg = load_config()
    if len(sys.argv) < 2:
        print("用法: uv run tools/upload.py <本地路径> [目标路径]")
        print("      uv run tools/upload.py -r <本地目录> :")
        sys.exit(1)
    upload(cfg, sys.argv[1:])
