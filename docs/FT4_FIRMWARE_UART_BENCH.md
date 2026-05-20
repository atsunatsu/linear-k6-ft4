# FT4 Firmware UART Bench

## 这份文档给谁看 / Who Should Read This
这份文档是给测试者的。

如果你不想研究代码，只想知道“现在怎么测”，就看这一份。

This document is for testers.

If you do not want to study the code and only want to know “how do I test now”, read this file only.

## 你现在在测什么 / What You Are Testing
你现在测试的是：

- `uvk5cec-0.3q` 固件里的新 `FT4 clean TX UART bench` 路径

你现在**不是**在测试：

- DigiManager 的 FT4 发射
- 现场抓包
- `WSJT-X` 自动联动

You are testing:

- the new `FT4 clean TX UART bench` path inside `uvk5cec-0.3q`

You are **not** testing:

- DigiManager FT4 transmit
- live packet capture
- automatic `WSJT-X` integration

## 第 0 步：先确认安全 / Step 0: Confirm Safety First
真机 bench 时只允许下面两种情况：

- 接假负载
- 或者彻底断开天线

不允许上空口。

For real bench, use only:

- a dummy load
- or a fully disconnected antenna

Do not transmit on-air.

## 第 1 步：打开 PowerShell / Step 1: Open PowerShell
请在项目文件夹里打开 `PowerShell`。

最简单的方法：

1. 打开项目文件夹 `CEC固件改装FT4`
2. 在空白处按住 `Shift`
3. 点击鼠标右键
4. 选择“在此处打开 PowerShell”或“在终端中打开”

Open `PowerShell` inside the project folder.

The easiest way:

1. open the project folder `CEC固件改装FT4`
2. hold `Shift`
3. right-click on empty space
4. choose “Open PowerShell here” or “Open in Terminal”

## 第 2 步：先检查工具 / Step 2: Check Tools First
先运行这一行：

Run this first:

```powershell
python scripts\check_uvk5cec_toolchain.py
```

你现在只需要看 4 件事：

- 有没有 `python`
- 有没有 `arm-none-eabi-gcc`
- 有没有 `make`
- `pyserial` 有没有安装

You only need to check 4 things:

- whether `python` exists
- whether `arm-none-eabi-gcc` exists
- whether `make` exists
- whether `pyserial` is installed

如果结果里显示 `pyserial` 没装，请先运行这一行：

If the result says `pyserial` is missing, run this first:

```powershell
python -m pip install pyserial
```

如果这一步已经报错，就先停下，把输出发回来。

If this step already fails, stop here and send back the output.

## 第 3 步：先尝试编译固件 / Step 3: Try Building The Firmware
运行这一行：

Run this:

```powershell
python scripts\build_uvk5cec_firmware.py --target auto
```

这一行会自动尝试：

- 优先走 Windows 本机构建
- 如果本机构建条件不够，再尝试 Docker 路线

This command will:

- try a Windows local build first
- then try the Docker route if local build tools are not available

你现在要看的是：

- 有没有生成固件文件
- 有没有明确写出失败原因

What to check:

- whether a firmware file was generated
- whether the failure reason is clearly printed

如果固件都编不过，先不要碰电台。

If the firmware does not build, do not touch the radio yet.

## 第 4 步：先做离线检查，不接电台 / Step 4: Do Offline Check First
这一步**不接电台**。

This step is **without the radio**.

### 4.1 先开一个假响应器 / 4.1 Start The Mock Responder
先在第一个 `PowerShell` 窗口里运行：

In the first `PowerShell` window, run:

```powershell
python scripts\mock_uvk5cec_ft4_responder.py --port 7001
```

正常情况下，你会看到：

```text
mock_responder_ready=socket://127.0.0.1:7001
```

If it works, you should see:

```text
mock_responder_ready=socket://127.0.0.1:7001
```

### 4.2 再开第二个 PowerShell / 4.2 Open A Second PowerShell
再打开第二个 `PowerShell` 窗口，运行：

Open a second `PowerShell` window and run:

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port socket://127.0.0.1:7001 --text "CQ TEST OO00" --freq 145950000 --retune 145950100@1200 --stop-when-done
```

这一行命令的意思很简单：

- 发送一个 FT4 bench 发射请求
- 初始频率是 `145950000`
- `1200 ms` 后改频到 `145950100`
- 最后自动停发

This means:

- send one FT4 bench transmit request
- start at `145950000`
- retune to `145950100` after `1200 ms`
- stop automatically at the end

### 4.3 什么结果算正常 / 4.3 What Counts As Normal
如果屏幕上出现类似这些结果，就算正常：

- `session_version=...`
- `config_version=...`
- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

If you see output like this, it is normal:

- `session_version=...`
- `config_version=...`
- `start_ft4_tx status=0(OK)`
- `retune status=0(OK)`
- `stop_tx status=0(OK)`

这说明：

- 主机侧协议封包是通的
- 会话流程是通的
- 基本错误处理是通的

This proves:

- PC-side framing works
- the session flow works
- the basic error-handling path works

## 第 5 步：离线检查通过后，才开始真机 / Step 5: Real Bench Starts Only After Offline Passes
只有上面的离线检查通过后，才开始下一步：

- 编译并烧录固件
- 连接电台串口
- 把 `socket://127.0.0.1:7001` 换成真实串口，例如 `COM5`

Only after the offline check passes should you:

- build and flash the firmware
- connect the radio serial port
- replace `socket://127.0.0.1:7001` with a real port such as `COM5`

## 第 6 步：真机 bench 命令 / Step 6: Real Bench Commands
烧录完成后，用真实串口运行：

After flashing, run with the real serial port:

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 --text "CQ TEST OO00" --freq 145950000
python scripts\uvk5cec_ft4_cli.py retune --freq 145950100
python scripts\uvk5cec_ft4_cli.py stop-tx
```

## 真机时看什么 / What To Watch During Real Bench
请记录这几件事：

- 电台有没有进入发射
- `retune` 后频率有没有变化
- `stop-tx` 后有没有回到安全状态
- 频谱有没有明显异常

Record these:

- whether the radio enters transmit
- whether frequency changes after `retune`
- whether `stop-tx` returns to a safe state
- whether the spectrum looks obviously wrong

## 如果失败了，怎么回报 / How To Report A Failure
请至少发回来：

1. 你运行的命令
2. 屏幕上的完整输出
3. 失败发生在第几步
4. 你是不是已经接了假负载或断开天线

Please send back at least:

1. the exact command
2. the full output
3. which step failed
4. whether you used a dummy load or disconnected antenna

请优先按这个模板回报：

Please use this template if possible:

[docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

