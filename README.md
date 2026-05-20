# linear-k6-ft4

## 当前阶段 / Current Stage
当前公开测试阶段只有一个目标：

- 验证 `uvk5cec-0.3q` 的 **FT4 firmware UART bench** 路径能不能先在离线和台架环境中跑通

现在**不是**在测试：

- DigiManager replay
- 抓包
- `WSJT-X` 自动联动
- 上空口发射

The only public test goal right now is:

- verify that the **FT4 firmware UART bench** path in `uvk5cec-0.3q` works in offline and bench testing

We are **not** currently testing:

- DigiManager replay
- packet capture
- automatic `WSJT-X` integration
- on-air transmission

## 测试者先看这里 / Tester Start Here
如果你是来帮忙测试的，只看这 2 份文档就够了：

- 快速上手 / Quick start: [docs/FT4_FIRMWARE_UART_BENCH.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_BENCH.md)
- 结果模板 / Result template: [docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

If you are helping with testing, you only need these 2 documents:

- Quick start: [docs/FT4_FIRMWARE_UART_BENCH.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_BENCH.md)
- Result template: [docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/FT4_FIRMWARE_UART_RESULT_TEMPLATE.md)

## 测试者现在到底要做什么 / What Testers Actually Do
按顺序只做下面 4 件事：

1. 检查电脑上有没有编译工具
2. 尝试编译固件
3. 先做一次**不接电台**的离线协议检查
4. 只有前 3 步都过了，才进入真实 bench 测试

Only do these 4 things, in order:

1. check whether the build tools exist
2. try to build the firmware
3. do one **offline, no-radio** protocol check
4. only then move to the real bench test

## 现在最短的测试流程 / Shortest Test Flow
在项目目录里打开 `PowerShell`，然后按顺序运行：

Open `PowerShell` in the project folder, then run these in order:

```powershell
python scripts\check_uvk5cec_toolchain.py
python scripts\build_uvk5cec_firmware.py --target auto
python scripts\mock_uvk5cec_ft4_responder.py --port 7001
```

如果第一步的输出里显示 `pyserial` 没装，请先运行：

If the first step says `pyserial` is missing, run this first:

```powershell
python -m pip install pyserial
```

再打开**第二个** `PowerShell` 窗口，运行：

Then open a **second** `PowerShell` window and run:

```powershell
python scripts\uvk5cec_ft4_cli.py send-ft4 --port socket://127.0.0.1:7001 --text "CQ TEST OO00" --freq 145950000 --retune 145950100@1200 --stop-when-done
```

如果你能看到 `status=0(OK)`，说明：

- 主机侧命令封包是通的
- 会话流程是通的
- `send-ft4 / retune / stop-tx` 这条离线路径是通的

If you can see `status=0(OK)`, it means:

- PC-side command framing works
- the session flow works
- the offline `send-ft4 / retune / stop-tx` path works

## 什么时候才开始碰真机 / When Real Bench Starts
只有在下面都通过后，才开始连电台：

- 工具检查完成
- 固件编译完成
- 离线假响应器检查完成

Only connect the radio after all of these pass:

- tool check
- firmware build
- offline mock-responder check

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
- 是卡在“工具检查 / 编译 / 离线检查 / 真机 bench”的哪一步

Please send back:

- the exact command you ran
- the full output
- which stage failed: tool check, build, offline check, or real bench

## 给开发者的话 / For Developers
当前仓库已经包含：

- `uvk5cec-0.3q` 固件源码和 FT4 UART bench 改动
- UART 主机 CLI
- mock responder
- 构建检查脚本
- bench 结果模板

The repository now includes:

- the `uvk5cec-0.3q` firmware tree plus FT4 UART bench changes
- the UART host CLI
- a mock responder
- build-check scripts
- the bench result template

