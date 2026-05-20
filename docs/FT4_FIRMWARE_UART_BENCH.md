# FT4 Firmware UART Bench

## 这份文档给谁看 / Who This Is For
这份文档是给**测试者**的。

默认前提是：

- 电台已经刷好指定固件
- 你不需要自己编译固件
- 你不需要自己烧录固件

This document is for **testers**.

Assume that:

- the radio already has the required firmware flashed
- you do not need to build the firmware yourself
- you do not need to flash the firmware yourself

## 第 1 步：先下载固件 / Step 1: Download The Firmware First
先打开这个页面：

Open this page first:

- [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)

你会看到至少这几个文件：

- `linear-k6-ft4-current-bench.packed.bin`
- `linear-k6-ft4-current-bench.bin`
- `build-summary.txt`

You should see at least:

- `linear-k6-ft4-current-bench.packed.bin`
- `linear-k6-ft4-current-bench.bin`
- `build-summary.txt`

默认先下载：

- `linear-k6-ft4-current-bench.packed.bin`

By default, download:

- `linear-k6-ft4-current-bench.packed.bin`

只有在你的刷机工具明确要求原始镜像时，才改用：

- `linear-k6-ft4-current-bench.bin`

Only use this if your flashing tool explicitly needs a raw image:

- `linear-k6-ft4-current-bench.bin`

## 第 2 步：刷机 / Step 2: Flash The Radio
用你平时给 UV-K5 刷机的网页或工具，按通用步骤操作：

1. 打开刷机工具
2. 连接电台
3. 让电台进入刷机模式
4. 选择刚下载的固件文件
5. 开始写入
6. 等待刷机完成

Use your usual UV-K5 web flasher or flashing tool:

1. open the flasher
2. connect the radio
3. put the radio into flash mode
4. choose the firmware file you downloaded
5. start flashing
6. wait until flashing finishes

如果你平时就是在某个网页里刷机，这一步继续用你原来的方式就行。

If you already use a specific web flasher, keep using it here.

## 第 3 步：先确认安全 / Step 3: Confirm Safety First
真机 bench 时只允许下面两种情况：

- 接假负载
- 或者彻底断开天线

不允许上空口。

For real bench, use only:

- a dummy load
- or a fully disconnected antenna

Do not transmit on-air.

## 第 4 步：打开 PowerShell / Step 4: Open PowerShell
请在项目文件夹里打开 `PowerShell`。

最简单的方法：

1. 打开项目文件夹 `CEC固件改装FT4`
2. 在空白处按住 `Shift`
3. 点击鼠标右键
4. 选择“在此处打开 PowerShell”或“在终端中打开”

Open `PowerShell` inside the project folder.

## 第 5 步：如果缺 pyserial，就先安装 / Step 5: Install pyserial If Missing
先运行这一行：

Run this first:

```powershell
python scripts\check_uvk5cec_toolchain.py
```

你现在只需要看一件事：

- `pyserial` 是不是 `true`

You only need to check one thing:

- whether `pyserial` is `true`

如果它是 `false`，就先运行这一行：

If it is `false`, run this:

```powershell
python -m pip install pyserial
```

## 第 6 步：开始真实测试 / Step 6: Start The Real Bench Test
下面这 3 行就是测试者真正要用的命令：

These 3 lines are the real tester commands:

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
python scripts\uvk5cec_ft4_cli.py retune --freq 145950100
python scripts\uvk5cec_ft4_cli.py stop-tx
```

把 `COM5` 改成你电脑上真正的电台串口。

Replace `COM5` with the real serial port for your radio.

## 每一行是什么意思 / What Each Command Means
第一行：

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
```

意思是：

- 通过 `COM5` 连接电台
- 发送一条 bench FT4 发射命令
- 初始频率是 `145950000`

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
如果输出里出现这些，就算正常：

- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

同时请观察：

- 电台有没有进入发射
- `retune` 后频率有没有变化
- `stop-tx` 后有没有回到安全状态

If you see these, that is normal:

- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

Also watch:

- whether the radio enters TX
- whether the frequency changes after `retune`
- whether `stop-tx` returns to a safe state

## 如果失败了，怎么回报 / How To Report A Failure
请至少发回来：

1. 你运行的命令
2. 屏幕上的完整输出
3. 电台有没有进入发射
4. 改频有没有生效
5. 停发有没有恢复安全状态

Please send back at least:

1. the exact command
2. the full output
3. whether the radio entered TX
4. whether retune worked
5. whether stop returned to a safe state

请优先按这个模板回报：

[docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)
