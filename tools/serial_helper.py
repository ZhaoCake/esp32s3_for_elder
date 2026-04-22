"""串口底层操作 - 中断运行中的程序，让板子回到 REPL 空闲状态

当板子已部署并运行自启动程序时，mpremote connect 会触发软重启
导致程序重新运行。mpremote resume 不触发软重启，可直接中断程序
并执行命令。

此模块提供 serial_interrupt 作为兜底手段（当 resume 也失败时）
以及 serial_exec 用于极端场景。
"""
import time
import serial


def serial_interrupt(port: str, baud: int = 115200) -> bool:
    """发送 Ctrl+C 中断运行中的程序，让板子回到 REPL。

    返回 True 表示可能成功中断。
    """
    try:
        s = serial.Serial(port, baud, timeout=1, dsrdtr=False, rtscts=False)
        s.dtr = False
        s.rts = False
        time.sleep(0.05)

        for _ in range(5):
            s.write(b"\x03")
            time.sleep(0.05)
        time.sleep(0.3)

        out = s.read(s.in_waiting).decode(errors="replace")
        s.close()

        return ">>>" in out or ">" in out

    except (serial.SerialException, Exception):
        return False


def serial_exec(port: str, command: str, baud: int = 115200, timeout: float = 10) -> tuple[bool, str]:
    """通过 raw serial 中断程序后，进入 raw REPL 执行命令。

    仅用于 resume 和 connect 都无法连接的极端场景。
    正常场景优先使用 mpremote resume。

    返回 (success: bool, output: str)
    """
    try:
        s = serial.Serial(port, baud, timeout=1, dsrdtr=False, rtscts=False)
        s.dtr = False
        s.rts = False
        time.sleep(0.05)

        for _ in range(5):
            s.write(b"\x03")
            time.sleep(0.05)
        time.sleep(0.5)
        s.read(s.in_waiting)

        s.write(b"\x01")
        time.sleep(0.3)
        resp = s.read(s.in_waiting).decode(errors="replace")

        if "raw REPL" not in resp:
            s.write(b"\x01")
            time.sleep(0.3)
            resp = s.read(s.in_waiting).decode(errors="replace")

        if "raw REPL" not in resp:
            s.close()
            return False, f"Could not enter raw REPL: {resp[:100]}"

        s.write((command + "\n").encode())
        time.sleep(0.1)
        s.write(b"\x04")

        deadline = time.time() + timeout
        output = b""
        while time.time() < deadline:
            chunk = s.read(s.in_waiting or 1)
            if chunk:
                output += chunk
                if b"\x04>" in output:
                    break
            time.sleep(0.05)

        s.read(s.in_waiting)
        s.write(b"\x02")
        time.sleep(0.2)
        s.read(s.in_waiting)
        s.close()

        decoded = output.decode(errors="replace")
        success = "OK" in decoded
        return success, decoded

    except (serial.SerialException, Exception) as e:
        return False, str(e)
