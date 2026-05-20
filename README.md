# linear-k6-ft4

## 当前阶段 / Current Stage
当前公开测试只做一件事：

- 验证 `uvk5cec-0.3q` 的 **FT4 firmware UART bench** 路径能不能在台架上工作

现在**不测试**这些内容：

- DigiManager replay
- 抓包
- `WSJT-X` 自动联动
- 上空口发射

The only public test goal right now is:

- verify that the **FT4 firmware UART bench** path in `uvk5cec-0.3q` works on the bench

We are **not** testing:

- DigiManager replay
- packet capture
- automatic `WSJT-X` integration
- on-air transmission

## 我是测试者 / I Am A Tester
如果你只是帮忙测试，**你不需要自己编译固件**。

你现在只需要做这几件事：

1. 去 Release 页面下载当前 bench 固件
2. 用你平时的 UV-K5 刷机工具把固件写入电台
3. 在项目文件夹里打开 `PowerShell`
4. 运行 `send-ft4`
5. 运行 `retune`
6. 运行 `stop-tx`
7. 按模板回传结果

If you are only helping with testing, **you do not need to compile firmware yourself**.

You only need to:

1. download the current bench firmware
2. flash it with your usual UV-K5 flashing tool
3. open `PowerShell` in the project folder
4. run `send-ft4`
5. run `retune`
6. run `stop-tx`
7. report the result with the template

测试者直接看这里：

- 固件下载 / Firmware download: [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)
- 傻瓜教程 / Simple tester guide: [docs/FT4_FIRMWARE_UART_BENCH.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_BENCH.md)
- 结果模板 / Result template: [docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

## 我是维护者 / I Am A Maintainer
如果你负责源码、构建链、GitHub Actions 或离线联调，再看这些：

- `uvk5cec-0.3q`
- `.github/workflows/firmware-build.yml`
- `scripts/build_uvk5cec_firmware.py`
- `scripts/check_uvk5cec_toolchain.py`
- `scripts/mock_uvk5cec_ft4_responder.py`

If you maintain the build chain or source code, then look at:

- `uvk5cec-0.3q`
- `.github/workflows/firmware-build.yml`
- `scripts/build_uvk5cec_firmware.py`
- `scripts/check_uvk5cec_toolchain.py`
- `scripts/mock_uvk5cec_ft4_responder.py`

## 安全要求 / Safety Rules
- 只允许接假负载，或彻底断开天线
- 不允许上空口
- 必须有人值守

- dummy load or no antenna only
- no on-air testing
- attended bench only

## 公开测试命令 / Public Test Commands
当前对测试者公开的命令只有这 3 个：

- `send-ft4`
- `retune`
- `stop-tx`

The only public tester-facing commands right now are:

- `send-ft4`
- `retune`
- `stop-tx`

## 失败时回传什么 / What To Report If Something Fails
请回传这些最基本的信息：

- 你运行的命令
- 屏幕上的完整输出
- 电台有没有进入发射
- 改频有没有生效
- 停发后有没有回到安全状态

Please report at least:

- the exact command you ran
- the full terminal output
- whether the radio entered TX
- whether retune worked
- whether stop returned to a safe state
