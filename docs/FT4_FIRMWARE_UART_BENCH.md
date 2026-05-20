# FT4 Firmware UART Bench

## 这份教程给谁看 / Who This Guide Is For
这份教程是给**测试者**看的。

默认前提：

- 你已经拿到了别人编译好的当前 bench 固件
- 你不需要自己编译固件
- 你只需要刷机，然后运行测试命令

This guide is for **testers**.

Assume that:

- someone already built the current bench firmware for you
- you do not need to compile the firmware yourself
- you only need to flash it and run the test commands

## 第 1 步：先下载固件 / Step 1: Download The Firmware
先打开这个页面：

- [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)

优先下载这个文件：

- `linear-k6-ft4-current-bench.packed.bin`

只有当你的刷机工具明确要求原始镜像时，才改用：

- `linear-k6-ft4-current-bench.bin`

Open this page first:

- [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)

Download this file first:

- `linear-k6-ft4-current-bench.packed.bin`

Only use this if your flasher explicitly requires a raw image:

- `linear-k6-ft4-current-bench.bin`

## 第 2 步：刷机 / Step 2: Flash The Radio
用你平时的 UV-K5 刷机网页或刷机工具就行。

通用步骤：

1. 打开刷机工具
2. 连接电台
3. 让电台进入刷机模式
4. 选择刚下载的固件文件
5. 开始写入
6. 等待完成

Use your usual UV-K5 web flasher or flashing tool.

General steps:

1. open the flasher
2. connect the radio
3. put the radio into flash mode
4. choose the firmware file
5. start flashing
6. wait until it finishes

## 第 3 步：先确认安全 / Step 3: Confirm Safety First
真实台架测试时，只允许：

- 接假负载
- 或者彻底断开天线

不允许上空口。

For real bench testing, use only:

- a dummy load
- or a fully disconnected antenna

Do not transmit on-air.

## 第 4 步：打开 PowerShell / Step 4: Open PowerShell
请在项目文件夹里打开 `PowerShell`。

最简单的方法：

1. 打开项目文件夹
2. 在空白处按住 `Shift`
3. 点击鼠标右键
4. 选择“在此处打开 PowerShell”或“在终端中打开”

Open `PowerShell` inside the project folder.

## 第 5 步：检查有没有 pyserial / Step 5: Check Whether pyserial Is Installed
先运行这一行：

```powershell
python scripts\check_uvk5cec_toolchain.py
```

你现在只需要看一项：

- `pyserial` 是不是 `true`

如果是 `false`，再运行这一行：

```powershell
python -m pip install pyserial
```

Run this first:

```powershell
python scripts\check_uvk5cec_toolchain.py
```

You only need to check one thing:

- whether `pyserial` is `true`

If it is `false`, run:

```powershell
python -m pip install pyserial
```

## 第 6 步：开始测试 / Step 6: Start The Test
下面这 3 行就是测试者真正要运行的命令：

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
python scripts\uvk5cec_ft4_cli.py retune --freq 145950100
python scripts\uvk5cec_ft4_cli.py stop-tx
```

把 `COM5` 改成你电脑上电台对应的串口号。

These are the 3 real tester commands:

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
python scripts\uvk5cec_ft4_cli.py retune --freq 145950100
python scripts\uvk5cec_ft4_cli.py stop-tx
```

Replace `COM5` with the real serial port for your radio.

## 每一行是什么意思 / What Each Command Means
第一行：

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
```

意思是：

- 通过 `COM5` 连接电台
- 发送一条 bench FT4 发射命令
- 初始发射频率是 `145950000`

第二行：

```powershell
python scripts\uvk5cec_ft4_cli.py retune --freq 145950100
```

意思是：

- 在发射过程中请求改频到 `145950100`

第三行：

```powershell
python scripts\uvk5cec_ft4_cli.py stop-tx
```

意思是：

- 停止这次 bench 发射

## 什么结果算正常 / What Counts As Normal
如果输出里出现这些，就算命令成功：

- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

同时观察：

- 电台有没有进入发射
- `retune` 后频率有没有变化
- `stop-tx` 后有没有回到安全状态

If you see these, the command worked:

- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

Also watch:

- whether the radio entered TX
- whether the frequency changed after `retune`
- whether `stop-tx` returned to a safe state

## 失败时怎么回报 / How To Report A Failure
请至少发回这些内容：

1. 你运行的完整命令
2. PowerShell 上的完整输出
3. 电台有没有进入发射
4. 改频有没有生效
5. 停发后有没有回到安全状态

请优先按这个模板回报：

[docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

Please report at least:

1. the exact command
2. the full PowerShell output
3. whether the radio entered TX
4. whether retune worked
5. whether stop returned to a safe state
