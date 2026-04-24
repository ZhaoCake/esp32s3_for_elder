"""远程求值 - 在板子上执行 MicroPython 表达式并返回结果

用法: uv run tools/eval.py "<expression>"
  uv run tools/eval.py "1+1"
  uv run tools/eval.py "gc.mem_free()"
  uv run tools/eval.py "machine.Pin(48).value()"

注意:
- mpremote eval 在 REPL 空闲作用域中执行，不自动导入模块
- 需要 __import__() 访问标准库: __import__('sys').platform, __import__('os').listdir()
- gc 在 REPL 中默认可用: gc.mem_free(), gc.mem_alloc()
- 无法直接访问运行中程序的局部变量（如 current_color）
- 如果运行中程序未阻塞 REPL（无 while True 循环），可用 __import__('模块').变量名 访问
"""
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from serial_helper import mpremote_eval, serial_interrupt


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def eval_expr(cfg, expr):
    port = cfg["device"]["port"]
    print(f"[EVAL] {expr}")

    ok, output = mpremote_eval(port, expr)

    if ok:
        print(f"[RESULT] {output}")
        return

    # 检查是否为超时
    if output == "timeout":
        print("[ERROR] eval timeout")
        return

    # 检查瞬时错误
    ok_stdout = ""
    error_detail = output
    error_text = (ok_stdout + "\n" + error_detail).lower()
    transient = (
        "clearcommerror" in error_text
        or "permissionerror" in error_text
        or "拒绝访问" in error_text
        or "failed to access" in error_text
        or "no device found" in error_text
    )
    raw_repl = "could not enter raw repl" in error_text

    if transient or raw_repl:
        serial_interrupt(port)
        time.sleep(1)
        ok2, output2 = mpremote_eval(port, expr)
        if ok2:
            print(f"[RESULT] {output2}")
            return
        print("[WARN] 串口瞬时占用，重试后仍失败")
        print(f"[ERROR] {output2}")
        return

    print(f"[ERROR] {error_detail}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: uv run tools/eval.py <expression>")
        print('  uv run tools/eval.py "1+1"')
        print('  uv run tools/eval.py "gc.mem_free()"')
        print('  uv run tools/eval.py "__import__(\'sys\').platform"')
        sys.exit(1)
    cfg = load_config()
    eval_expr(cfg, sys.argv[1])
