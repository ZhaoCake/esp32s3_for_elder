# AGENTS.md - AI Agent 行为规范

## 项目说明

这是一个面向中老年人的 ESP32-S3 MicroPython 嵌入式开发项目。
用户群体特点：可能不熟悉命令行、不熟悉编程、需要极简的操作体验。
AI Agent 的职责：代替用户完成所有技术操作，用户只需用自然语言描述需求。

## 硬件信息

- 芯片: ESP32-S3
- 串口: COM6 (可能变动，配置在 config.toml 中)
- 固件: MicroPython v1.28.0 (ESP32_GENERIC_S3)

## 工具命令

所有命令都必须通过 `uv run` 执行：

- **刷固件**: `uv run tools/flash.py`
- **安全运行代码(开发模式)**: `uv run tools/run.py [文件名]`
- **固化代码(断电自启动)**: `uv run tools/deploy.py [文件名]`
- **解锁(回到开发模式)**: `uv run tools/unlock.py`
- **急救(板子变砖)**: `uv run tools/rescue.py`
- **上传文件**: `uv run tools/upload.py <本地路径> [目标路径]`
- **列出板子文件**: `uv run tools/list_files.py`
- **进入REPL**: `uv run tools/repl.py`

## 写代码的铁律

在编写 MicroPython 代码时必须遵守以下绝对规则：

1. **任何 `while True` 循环内部必须包含 `time.sleep()`**（推荐 0.01 秒以上），绝对不允许出现无延时的死循环，否则会触发看门狗复位导致 busy。
2. **禁止在循环内部动态创建大容量变量**（如不断 append 的列表、大字典），如需复用变量，请在循环外部初始化，循环内部只做修改。
3. **涉及网络请求时**（如 `urequests`），必须设置超时（`timeout=5`），并包裹在 `try...except` 中。
4. **涉及硬件外设时**（I2C、SPI、UART），必须包裹在 `try...except` 中，防止硬件未连接导致崩溃。
5. **不要修改 `boot.py`**——这是一个安全红线。boot.py 的写入和清空只能通过 `tools/deploy.py` 和 `tools/unlock.py` 来操作。

## 开发工作流

### 用户说"帮我跑一下看看" / "试一下"
1. 编写/修改 `src/main.py`（或其他指定文件）
2. 执行 `uv run tools/run.py`（这会自动清空 boot.py 并运行代码）
3. 观察输出结果

### 用户说"没问题，烧录进去" / "固化"
1. 执行 `uv run tools/deploy.py`
2. 告知用户：固化完成，拔掉 USB 线也能运行

### 用户说"我想改代码" / "重新调试"
1. 执行 `uv run tools/unlock.py`
2. 回到开发模式，可以安全测试

### 如果运行报错
1. 分析错误信息
2. 修改代码
3. 重新执行 `uv run tools/run.py`

### 如果板子无响应 / 变砖
1. 执行 `uv run tools/rescue.py`
2. 如果急救也失败，执行 `uv run tools/flash.py` 重刷固件

## ESP32-S3 引脚参考

当前项目使用开发板：ESP32-S3-DevKitC-1 v1.1。

在本项目当前实测环境中，板载可寻址 RGB LED 使用 **GPIO48**。

常用引脚说明（针对当前板型）：

- **GPIO48**：板载 RGB LED 数据引脚（本项目实测可用，可寻址 LED，建议用 `neopixel` 驱动）
- **GPIO19 / GPIO20**：原生 USB D- / D+
- **GPIO43 / GPIO44**：UART0 TX / RX（排针标记 TX / RX）
- **GPIO35 / GPIO36 / GPIO37**：在部分模组配置中用于内部 flash/psram 通信，外部不要占用

开发建议：

1. 如果是控制板载 RGB LED，优先使用 GPIO48，不要再使用 GPIO2 的旧示例。
2. 写灯效循环时，必须保留 `time.sleep()`，避免触发看门狗复位。
3. 涉及硬件初始化（例如 `neopixel.NeoPixel`）建议使用 `try...except` 包裹，便于排查连线或环境问题。

## 注意事项

- 使用 mpremote 前，确保 Thonny 或其他串口工具已关闭，否则串口冲突。
- 硬件复位后（flash/rescue），操作系统需要几秒重新识别 USB 设备，不要立即尝试连接。
- 运行 `run.py` 时，如果是正常的死循环代码（如 LED 闪烁），用 Ctrl+C 终止即可。
