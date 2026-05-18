# 测试者快速上手 / Tester Quick Start

## 你要做什么 / What you need to do

如果你是第一次接触这个项目，请把任务理解成下面三步：  
If this is your first time with the project, think of your task as three steps:

1. 盘清现在机器上的 COM 口连接关系  
   Map the current COM port topology on the machine
2. 在 `WSJT-X` 和 `DigiManager` 之间插入透明代理  
   Insert a transparent proxy between `WSJT-X` and `DigiManager`
3. 抓到最小可用样本并回传  
   Capture the minimum useful sample set and send it back

你**不需要先理解协议内容**。  
You **do not need to understand the protocol first**.

## 开始前准备 / Before You Start

请确认你手上有：  
Make sure you have:

- 当前能工作的 `WSJT-X + DigiManager + CEC/K5` 环境  
  A currently working `WSJT-X + DigiManager + CEC/K5` setup
- Python 3.11 或更高版本  
  Python 3.11 or newer
- Windows 虚拟串口工具，例如 `com0com`  
  A Windows virtual COM tool such as `com0com`

## 5 分钟起步 / 5-Minute Start

### 1. 生成 COM 拓扑清单 / Generate the COM topology worksheet

```powershell
python scripts/list_serial_topology.py
```

它会生成这个文件：  
It generates this file:

[logs/serial-topology-template.csv](/F:/Codex/CEC固件改装FT4/logs/serial-topology-template.csv)

你需要把它补完整，至少填这些列：  
Fill in at least these columns:

- `COM号`
- `谁在打开`
- `用途`
- `是否为虚拟串口`
- `配对对象`
- `串口参数`
- `当前是否工作`

### 2. 看详细抓包手册 / Read the full capture guide

请打开：  
Open:

[docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)

### 3. 跑一次透明抓包代理 / Run the transparent capture proxy

把 `COM_A` 和 `COM_B` 换成你实际使用的端口：  
Replace `COM_A` and `COM_B` with your real ports:

```powershell
python scripts/serial_capture_proxy.py ^
  --wsjtx-port COM_A ^
  --digimanager-port COM_B ^
  --baudrate 9600 ^
  --scenario startup ^
  --log-path logs/serial-capture.jsonl
```

### 4. 做最小抓包场景 / Capture the minimum scenarios

至少做这些：  
At minimum, do these:

1. `startup`
2. `idle_read`
3. `set_freq`
4. `mode_change`
5. `ptt_on`
6. `ptt_off`
7. `tx_retune`

每轮抓包建议单独运行一次代理，并修改 `--scenario` 值。  
It is recommended to run the proxy separately for each scenario and change the `--scenario` value.

### 5. 对抓包结果做快速摘要 / Summarize the capture log

```powershell
python scripts/analyze_capture.py logs/serial-capture.jsonl
```

## 回传什么 / What To Send Back

请把下面三样一起回传：  
Please send back these three items together:

1. 填写后的 COM 拓扑清单  
   The completed COM topology worksheet
2. 抓包日志 `logs/serial-capture.jsonl`  
   The capture log `logs/serial-capture.jsonl`
3. 你的测试说明  
   Your test notes

测试说明请按这个模板写：  
Write your notes using this template:

[docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)

## 最常见错误 / Most Common Mistakes

- 还没盘清 COM 就开始乱插代理  
  Inserting the proxy before the COM topology is understood
- 抓包日志没有区分场景  
  Capturing logs without scenario labels
- 只抓 `PTT ON/OFF`，没抓“发射中连续改频”  
  Capturing only `PTT ON/OFF` and missing in-TX retuning
- 修改链路后没有确认原链路还能正常工作  
  Forgetting to verify that the original chain still works after rewiring

## 一句话标准 / One-Sentence Standard

你的测试是否合格，就看你能不能把：  
Your test pass/fail criterion is simple:

- 谁连哪个 COM  
  Who uses which COM
- 报文双向长什么样  
  What the bidirectional traffic looks like
- 发射中改频是怎么发生的  
  How retuning happens during TX

这三件事讲清楚。  
Explain those three things clearly.
