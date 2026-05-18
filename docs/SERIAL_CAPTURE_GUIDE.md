# 串口抓包手册 / Serial Capture Guide

## 这份手册是给谁的 / Who This Guide Is For

这份手册写给“会操作 Windows 软件，但不懂串口协议”的测试者。  
This guide is written for testers who can operate Windows software but do not understand serial protocols.

你不需要先搞懂协议细节。  
You do not need to understand the protocol details first.

## 最小成功标准 / Minimum Success Standard

请先记住一件事：  
Please remember one thing first:

**如果你只完成了“找到 `WSJT-X` 的 COM 和 `DigiManager` 的 COM，并把它们回传”，这已经是有价值的结果。**  
**If all you complete is finding the `WSJT-X` COM and the `DigiManager` COM and sending them back, that is already valuable.**

第一次测试不要求你必须完成完整抓包。  
Your first test does not have to finish a full capture.

## 阶段 A：先不要抓包，只确认 COM / Phase A: Do Not Capture Yet, Confirm The COM Ports First

### A1. 你现在要确认什么 / What You Need To Confirm

你现在只需要确认这两行：  
Right now you only need to confirm these two lines:

```text
WSJT-X = COM?
DigiManager = COM?
```

### A2. 去哪里看 / Where To Look

请按这个顺序看：  
Please check in this order:

1. `WSJT-X` 设置页  
   `WSJT-X` settings page
2. `DigiManager` 设置页  
   `DigiManager` settings page
3. Windows `设备管理器 -> Ports (COM & LPT)`  
   Windows `Device Manager -> Ports (COM & LPT)`

详细动作已经写在这里：  
The detailed click-by-click actions are here:

[docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)

### A3. 什么时候先停住 / When You Should Stop Here

如果出现下面任意一种情况，请先停住，不要继续插代理：  
If any of the following is true, stop here and do not insert the proxy yet:

- 你不知道 `WSJT-X` 正在用哪个 `COM`  
  You do not know which `COM` `WSJT-X` is using
- 你不知道 `DigiManager` 正在用哪个 `COM`  
  You do not know which `COM` `DigiManager` is using
- 你分不清哪个是虚拟串口，哪个是别的设备  
  You cannot tell which ports are virtual COM ports and which belong to something else
- 你不确定当前固定频点链路是不是本来就能正常工作  
  You are not sure whether the original fixed-frequency chain already works

### A4. 阶段 A 可以回传什么 / What You Can Send Back In Phase A

如果你只能做到阶段 A，请回传下面任意一种：  
If you can only reach Phase A, send back either of these:

1. 两行文字  
   Two text lines

```text
WSJT-X = COM?
DigiManager = COM?
```

2. 三张截图  
   Three screenshots

- `WSJT-X` 设置页  
  `WSJT-X` settings page
- `DigiManager` 设置页  
  `DigiManager` settings page
- `设备管理器 -> Ports (COM & LPT)`  
  `Device Manager -> Ports (COM & LPT)`

你也可以直接使用这个模板：  
You can also use this template directly:

[docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md)

## 阶段 B：确认 COM 后再抓包 / Phase B: Capture Only After COM Is Confirmed

### B1. 先理解这 2 个名字 / First Understand These 2 Names

- `COM_A`：代理靠近 `WSJT-X` 的那一侧  
  `COM_A`: the side of the proxy that faces `WSJT-X`
- `COM_B`：代理靠近 `DigiManager` 的那一侧  
  `COM_B`: the side of the proxy that faces `DigiManager`

你不需要先理解更深的拓扑，只要知道：  
You do not need deeper topology knowledge yet. Just remember:

```text
WSJT-X -> COM_A -> capture-proxy -> COM_B -> DigiManager
```

### B2. 为什么代理要插在中间 / Why The Proxy Goes In The Middle

我们不是要改业务逻辑。  
We are not trying to change the behavior.

我们只是把原来的一根线中间加一个“记录员”，把双向串口数据记下来。  
We are only adding a “recorder” in the middle of the original link so both directions are logged.

### B3. 抓包前先做一个表 / Generate The Topology Worksheet First

```powershell
python scripts/list_serial_topology.py
```

它会生成：  
It will generate:

[logs/serial-topology-template.csv](/F:/Codex/CEC固件改装FT4/logs/serial-topology-template.csv)

如果你愿意，先把它填一部分再抓包会更好。  
If you can, filling part of it before capture is even better.

### B4. 抓包命令怎么换成真实 COM / Replace The Example Ports With Real COM Ports

命令示例：  
Example command:

```powershell
python scripts/serial_capture_proxy.py ^
  --wsjtx-port COM_A ^
  --digimanager-port COM_B ^
  --baudrate 9600 ^
  --scenario startup ^
  --log-path logs/serial-capture.jsonl
```

你要改的只是这几项：  
You only need to replace these parts:

- `COM_A` 改成真实的前端 COM  
  Replace `COM_A` with the real frontend COM
- `COM_B` 改成真实的后端 COM  
  Replace `COM_B` with the real backend COM
- `9600` 改成你的实际波特率  
  Replace `9600` with your actual baud rate
- `startup` 改成当前场景名  
  Replace `startup` with the scenario name you are capturing now

### B5. 每个 `--scenario` 什么时候用 / When To Use Each `--scenario`

第一次抓包，只抓最小场景集就够了：  
For the first capture, only the minimum scenario set is needed:

1. `startup`  
   软件启动并连上串口  
   Software starts and connects to the serial link
2. `idle_read`  
   空闲时读取频率或状态  
   Idle frequency or status reads
3. `set_freq`  
   手工改一次频率  
   One manual frequency change
4. `mode_change`  
   切一次模式  
   One mode change
5. `ptt_on`  
   按下发射  
   Start transmit
6. `ptt_off`  
   停止发射  
   Stop transmit
7. `tx_retune`  
   发射过程中连续改几次频率  
   Retune several times while transmitting

### B6. 每跑完一轮要检查什么 / What To Check After Each Run

每跑完一轮，请至少确认：  
After each run, at minimum confirm:

- `logs/serial-capture.jsonl` 已经生成  
  `logs/serial-capture.jsonl` exists
- 这个文件不是空的  
  The file is not empty
- 这轮抓包用的 `--scenario` 是你当前实际做的动作  
  The `--scenario` label matches what you actually did

### B7. 抓完后看一下摘要 / Read A Quick Summary After Capture

```powershell
python scripts/analyze_capture.py logs/serial-capture.jsonl
```

这一步不用你理解协议，只是帮你确认日志确实抓到了东西。  
This step does not require protocol knowledge. It only helps confirm that the log actually captured something.

## 结果怎么回传 / How To Send Back The Results

### 只做到阶段 A / If You Only Reached Phase A

请提交：  
Please submit:

- `WSJT-X = COM?`
- `DigiManager = COM?`
- 或者 3 张截图  
  Or 3 screenshots

### 完成了阶段 B / If You Completed Phase B

请提交：  
Please submit:

- `serial-topology-template.csv`
- `serial-capture.jsonl`
- 分析脚本输出  
  Analyzer output
- 你的观察说明  
  Your notes

完整汇报模板在这里：  
The full report template is here:

[docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)

## 常见错误 / Common Mistakes

- 还没确认两个 `COM` 就急着插代理  
  Inserting the proxy before confirming the two `COM` ports
- 不确定原本链路是否工作就开始改线  
  Rewiring before confirming the original chain works
- 抓了很多动作，但没有换 `--scenario`  
  Capturing many actions without changing `--scenario`
- 只抓 `PTT ON/OFF`，没抓发射中的改频  
  Capturing only `PTT ON/OFF` and missing retuning during TX

## 一句话总结 / One-Sentence Summary

**先确认两个 COM；确认后再把代理插在中间抓包。**  
**Confirm the two COM ports first; only then insert the proxy in the middle and capture.**
