# linear-k6-ft4

## 当前阶段 / Current Stage
当前公开测试阶段只有一个目标：

- 验证 `uvk5cec-0.3q` 的 **FT4 firmware UART bench** 路径能不能在台架上跑通

现在**不是**在测试：

- DigiManager replay
- 抓包
- `WSJT-X` 自动联动
- 上空口发射

The only public test goal right now is:

- verify that the **FT4 firmware UART bench** path in `uvk5cec-0.3q` works on the bench

We are **not** currently testing:

- DigiManager replay
- packet capture
- automatic `WSJT-X` integration
- on-air transmission

## 先分清角色 / First Pick Your Role

### 1. 我是测试者 / I Am A Tester
如果你只是帮忙测试，请**不要自己编译固件**。

你只需要：

1. 去 GitHub Releases 下载当前 bench 固件
2. 用你常用的 UV-K5 刷机工具把固件写进去
3. 在项目目录里打开 `PowerShell`
4. 运行 `send-ft4 / retune / stop-tx`
5. 把结果按模板回传

测试者只需要看：

- 当前 bench 固件下载页 / Current bench firmware release: [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)
- 测试教程 / Tester guide: [docs/FT4_FIRMWARE_UART_BENCH.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_BENCH.md)
- 结果模板 / Result template: [docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

If you are only helping with testing, **do not compile firmware yourself**.

You only need to:

1. download the current bench firmware from GitHub Releases
2. flash it with your usual UV-K5 flashing tool
3. open `PowerShell` in the project folder
4. run `send-ft4 / retune / stop-tx`
5. report the result

Tester entry points:

- Current bench firmware release: [Current Bench Release](https://github.com/atsunatsu/linear-k6-ft4/releases/tag/current-bench)
- Tester guide: [docs/FT4_FIRMWARE_UART_BENCH.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_BENCH.md)
- Result template: [docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

### 2. 我是维护者 / I Am A Maintainer
如果你负责编译、看源码、排查构建链，才需要：

- 本地工具链
- Docker 构建
- mock responder
- GitHub Actions

If you are maintaining the firmware or build chain, then you need:

- local toolchains
- Docker build flow
- the mock responder
- GitHub Actions

## 给测试者的最短说明 / Shortest Message For Testers
测试者现在不需要：

- 装编译工具
- 本地编译固件
- 改代码

测试者现在只需要：

1. 下载当前 Release 固件
2. 刷机
3. 安装 `pyserial`（如果缺少）
4. 跑测试命令
5. 回传结果

Testers do not need to:

- install build tools
- compile firmware locally
- change code

Testers only need to:

1. download the current release firmware
2. flash the radio
3. install `pyserial` if missing
4. run the test commands
5. report the result

## 真机阶段不变的安全要求 / Safety Rules For Real Bench
- 只允许 `假负载` 或 `断开天线`
- 不允许上空口
- 必须有人值守

- `dummy load` or `no antenna` only
- no on-air testing
- attended bench only

## 当前公开接口 / Public Interfaces
当前对测试者公开的命令只有这 3 个：

- `send-ft4`
- `retune`
- `stop-tx`

The only public tester-facing commands right now are:

- `send-ft4`
- `retune`
- `stop-tx`

## 如果失败了，回传什么 / What To Report If Something Fails
请优先把下面这些发回来：

- 你运行的命令
- 屏幕上的完整输出
- 电台有没有进入发射
- 改频有没有生效
- 停发有没有恢复安全状态

Please send back:

- the exact command you ran
- the full output
- whether the radio entered TX
- whether retune worked
- whether stop returned to a safe state
