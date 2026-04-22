# ESP32-S3 适老型嵌入式开发模板 (AI Agent 驱动)

## 项目概述

面向中老年人的零门槛嵌入式开发环境。使用 MicroPython + mpremote + AI Agent 黄金三角，摒弃沉重 IDE，用最简单的命令行工具组合出最安全的开发体验。

## 环境要求

- Python 3.10+ (通过 uv 管理)
- ESP32-S3 开发板 (通过 USB 连接)
- Windows / macOS / Linux

## 快速开始

### 1. 刷入固件（仅首次或需要重置时）

```bash
uv run tools/flash.py
```

### 2. 开发模式运行代码（安全，不怕死循环）

```bash
uv run tools/run.py              # 运行 src/main.py
uv run tools/run.py my_test.py   # 运行 src/my_test.py
```

### 3. 固化代码（断电也能自启动）

```bash
uv run tools/deploy.py              # 固化 src/main.py
uv run tools/deploy.py my_app.py    # 固化 src/my_app.py
```

### 4. 解锁（从固化模式切回开发模式）

```bash
uv run tools/unlock.py
```

### 5. 急救（板子变砖时使用）

```bash
uv run tools/rescue.py
```

## 其他工具

| 命令 | 用途 |
|------|------|
| `uv run tools/upload.py <文件>` | 上传单个/多个文件到板子 |
| `uv run tools/upload.py -r src/ :` | 批量上传整个目录 |
| `uv run tools/list_files.py` | 列出板子上的文件 |
| `uv run tools/repl.py` | 进入 REPL 交互模式 |

## 配置

编辑 `config.toml` 修改串口、芯片类型、固件路径等：

```toml
[device]
port = "COM6"         # Windows: COMx, Mac: /dev/tty.usbmodemxxx
chip = "esp32s3"

[firmware]
path = "firmware/ESP32_GENERIC_S3-20260406-v1.28.0.bin"
flash_address = "0x0"
baud_rate = 460800

[project]
source_dir = "src"
main_file = "main.py"
```

## 项目结构

```
esp32s3_for_elder/
├── config.toml          # 项目配置（串口、固件等）
├── AGENTS.md            # AI Agent 行为规范
├── firmware/            # MicroPython 固件
│   └── ESP32_GENERIC_S3-20260406-v1.28.0.bin
├── src/                 # 你的 MicroPython 源代码
│   └── main.py
├── tools/               # 工具脚本
│   ├── flash.py         # 刷固件
│   ├── run.py           # 开发模式运行
│   ├── deploy.py        # 固化部署
│   ├── unlock.py        # 解锁回开发模式
│   ├── rescue.py        # 急救恢复
│   ├── upload.py        # 上传文件
│   ├── list_files.py    # 列出板子文件
│   └── repl.py          # REPL 交互
├── pyproject.toml       # uv 项目配置
└── .python-version      # Python 版本
```

## 核心设计原则

1. **开发/固化双模式**：开发时 boot.py 为空，代码不自动运行，看门狗能自动救活；固化时写 boot.py 实现自启动。
2. **防卡死机制**：`run.py` 自动清空 boot.py，确保即使代码有死循环，板子看门狗复位后也不会无限重启。
3. **急救兜底**：`rescue.py` 通过硬件复位 + 重试窗口期清空 boot.py，作为最后手段。如果连急救也不行，用 `flash.py` 重刷固件。
4. **AI Agent 友好**：所有工具都是命令行脚本，Agent 可以直接调用，输出有明确的 [OK]/[ERROR] 标记。
