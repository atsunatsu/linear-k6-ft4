# 串口抓包指南 / Serial Capture Guide

## 目的 / Purpose

这份指南帮助你在**不理解协议细节**的前提下，先把 `WSJT-X ↔ DigiManager` 的双向串口数据完整记录下来。  
This guide helps you capture the full bidirectional `WSJT-X ↔ DigiManager` serial traffic **without needing to understand the protocol first**.

目标不是立即逆向协议，而是先回答这些问题：  
The goal is not to reverse-engineer the protocol immediately. The first goal is to answer:

- 哪个 COM 给 `WSJT-X` 用  
  Which COM port is used by `WSJT-X`
- 哪个 COM 给 `DigiManager` 用  
  Which COM port is used by `DigiManager`
- 它们是不是虚拟串口对  
  Whether they are a virtual COM pair
- 串口参数是什么  
  What the serial parameters are
- 发射、改频、PTT、模式切换时，双向数据长什么样  
  What the bidirectional traffic looks like during TX, retuning, PTT, and mode changes

## 第一步：盘清 COM 拓扑 / Step 1: Map the COM topology

先运行串口拓扑清单脚本：  
Run the topology worksheet script first:

```powershell
python scripts/list_serial_topology.py
```

它会：

- 枚举本机可见 COM 口
- 生成一个可手工填写的 CSV 模板

It will:

- enumerate visible local COM ports
- generate a CSV worksheet you can fill in manually

默认输出文件：  
Default output file:

[logs/serial-topology-template.csv](/F:/Codex/CEC固件改装FT4/logs/serial-topology-template.csv)

你需要结合这些地方把表补完整：  
Complete the worksheet using:

- `WSJT-X` 的 CAT / rig 设置界面  
  `WSJT-X` CAT / rig settings
- `DigiManager` 的串口设置界面  
  `DigiManager` serial settings
- Windows 设备管理器里的 `Ports (COM & LPT)`  
  Windows Device Manager `Ports (COM & LPT)`
- 你当前使用的虚拟串口工具  
  Your current virtual COM utility

## 第二步：插入串口代理 / Step 2: Insert the capture proxy

当你知道 `WSJT-X` 和 `DigiManager` 原本各自连接的 COM 口后，把中间链路改成：  
Once you know the original COM ports used by `WSJT-X` and `DigiManager`, change the wiring to:

```text
WSJT-X -> COM_A -> capture-proxy -> COM_B -> DigiManager
```

然后运行抓包代理：  
Then run the capture proxy:

```powershell
python scripts/serial_capture_proxy.py ^
  --wsjtx-port COM_A ^
  --digimanager-port COM_B ^
  --baudrate 9600 ^
  --scenario startup ^
  --log-path logs/serial-capture.jsonl
```

常用参数：  
Common parameters:

- `--wsjtx-port`：代理面向 `WSJT-X` 的 COM  
  The COM facing `WSJT-X`
- `--digimanager-port`：代理面向 `DigiManager` 的 COM  
  The COM facing `DigiManager`
- `--baudrate`：串口波特率  
  Serial baud rate
- `--scenario`：本轮抓包的人类标签，例如 `startup`、`ptt_on`、`tx_retune`  
  Human-readable label for this run, for example `startup`, `ptt_on`, or `tx_retune`
- `--log-path`：JSONL 日志输出文件  
  JSONL output file

## 第三步：按场景抓最小样本 / Step 3: Capture the minimum useful scenarios

第一次抓包按这个顺序来：  
For the first capture pass, use this order:

1. 软件启动并建立连接  
   Startup and initial connection
2. 空闲状态读频率或状态  
   Idle state frequency/status reads
3. 手工改一次频率  
   One manual frequency change
4. 切一次模式  
   One mode change
5. `PTT ON`  
   `PTT ON`
6. `PTT OFF`  
   `PTT OFF`
7. 发射过程中连续改几次频率  
   Several retunes while transmitting
8. 关闭软件或断开串口  
   Shutdown or disconnect
9. 故意做一个错误动作  
   One intentional error case

建议每个场景单独跑一轮，并修改 `--scenario` 标签。  
It is recommended to run each scenario separately and change the `--scenario` label each time.

## 第四步：快速看抓包是不是像文本协议 / Step 4: Quickly inspect whether it looks text-based

抓完以后先跑分析脚本：  
After capturing, run the analyzer:

```powershell
python scripts/analyze_capture.py logs/serial-capture.jsonl
```

它会输出：  
It prints:

- 记录数  
  number of records
- 双向方向统计  
  direction counts
- 场景统计  
  scenario counts
- 一个粗略的 `ascii_like_ratio`  
  a rough `ascii_like_ratio`
- 前几条样本  
  the first sample records

如果 `ascii_like_ratio` 很高，并且样本里能看出像 `F 145950000` 这种可读文本，就优先按文本协议分析。  
If `ascii_like_ratio` is high and the samples look like readable commands such as `F 145950000`, start with a text-protocol hypothesis.

## 日志格式 / Log Format

每条 JSONL 记录固定包含：  
Each JSONL record contains:

- `timestamp_ms`
- `direction`
- `bytes_hex`
- `bytes_ascii`
- `scenario`
- `port_name`

这意味着抓包完成后，你可以先不懂协议，但已经拥有：

- 可回放样本
- 可检索样本
- 可对照场景的样本

This means that even before understanding the protocol, you already have:

- replayable samples
- searchable samples
- scenario-tagged samples

## 抓包后再做什么 / What comes next after capture

拿到最小样本后，再回答这些问题：  
After the minimum sample set is captured, answer:

- 它是文本协议还是二进制协议  
  Is it text or binary?
- 报文是不是按行分隔  
  Is it line-delimited?
- 改频命令是什么  
  What is the retune command?
- PTT 命令是什么  
  What is the PTT command?
- 模式切换命令是什么  
  What is the mode-switch command?
- 发射中连续改频是如何体现的  
  How is in-TX retuning represented?

在这一步之前，不要写死 `sat-bridge` 的串口协议实现。  
Do not hardcode the `sat-bridge` serial protocol implementation before this step.
