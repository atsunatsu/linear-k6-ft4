# linear-k6-ft4 / sat-bridge

中文与 English 文档并排提供。后续项目文档默认保持中英双语。  
Chinese and English documentation are provided side by side. Future project documentation should stay bilingual by default.

## 这是什么 / What this is

这个仓库的目标是把 `CEC + DigiManager` 的洁净数字发射链，用在线性卫星上的 **FT4** 实机测试。  
This repository aims to use the clean `CEC + DigiManager` digital transmit chain for **FT4** real-radio testing on linear satellites.

它当前包含两类成果：  
It currently contains two kinds of work:

- 一个 FT4-first 的卫星控频桥 `sat-bridge`  
  An FT4-first satellite control bridge named `sat-bridge`
- 一套给测试者使用的串口抓包工具和抓包流程  
  A serial capture toolkit and workflow for testers

## 给测试者的最快入口 / Fastest Path For Testers

如果你是来帮忙测试的，请**先不要研究代码**，直接按下面顺序走：  
If you are helping with testing, **do not start by reading the code**. Follow this order instead:

1. 看快速上手：[docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)  
   Read the quick-start guide: [docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)
2. 生成 COM 拓扑表：`python scripts/list_serial_topology.py`  
   Generate the COM topology worksheet: `python scripts/list_serial_topology.py`
3. 按抓包指南操作：[docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)  
   Follow the capture guide: [docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)
4. 把结果按模板回传：[docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)  
   Send results back using the template: [docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)

如果你只记得一件事，那就是：  
If you remember only one thing, remember this:

- **先盘清 COM 拓扑，再抓包；不要先猜协议。**  
  **Map the COM topology first, then capture traffic; do not guess the protocol first.**

## 当前目标 / Current Goal

当前主目标是两件事：  
The current primary goals are:

- 让 `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` 这条 FT4 控频链跑起来  
  Make the `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` FT4 control path work
- 确认 `WSJT-X ↔ DigiManager` 之间真实使用的串口协议  
  Determine the real serial protocol used between `WSJT-X` and `DigiManager`

在拿到最小抓包样本前，仓库里的串口协议实现仍然只是一个可替换假设层。  
Until we have the minimum capture samples, the serial protocol implementation in this repository is still only a replaceable hypothesis layer.

## 硬性约束 / Hard Constraints

- 不允许退回模拟音频 SSB 发射  
  No fallback to analog SSB audio injection
- 发射过程中也要连续平滑控频  
  Doppler control must continue smoothly during TX
- 如果现有 DigiManager 洁净链承载不了 FT4，本项目止步于控制层打通，不会伪造音频发射兜底  
  If the current DigiManager clean chain cannot carry FT4, this project stops at the control layer instead of faking an audio workaround

## 固定拓扑 / Fixed Topology

首版实机链路固定如下：  
The first real-hardware topology is fixed as:

```text
SatPC32 / Doppler software
        |
        v
  sat-bridge rigctld TCP
        |
        +--> WSJT-X TCP rig control (optional)
        |
        +--> sat-bridge virtual COM frontend
                 |
                 v
             WSJT-X (FT4)

sat-bridge serial backend
        |
        v
   DigiManager input COM
        |
        v
      DigiManager
        |
        v
      CEC / K5
```

要点 / Key points:

- `SatPC32` 是上下行频率主控源  
  `SatPC32` is the uplink/downlink frequency authority
- `WSJT-X` 只负责 FT4 业务、PTT、模式和状态查询  
  `WSJT-X` is limited to FT4 workflow, PTT, mode, and status reads
- `sat-bridge` 是唯一向 DigiManager 输入口发控制命令的进程  
  `sat-bridge` is the only process allowed to drive DigiManager's input COM port

## 抓包工具 / Capture Tools

当前仓库内置了这些工具：  
The repository currently includes these tools:

- `python scripts/list_serial_topology.py`  
  列出本机串口并生成拓扑填写表  
  Lists local serial ports and generates a topology worksheet
- `python scripts/serial_capture_proxy.py ...`  
  在 `WSJT-X` 和 `DigiManager` 之间做透明抓包代理  
  Runs a transparent capture proxy between `WSJT-X` and `DigiManager`
- `python scripts/analyze_capture.py logs/serial-capture.jsonl`  
  对抓包结果做快速摘要  
  Produces a quick summary of the capture log

## 配置 / Configuration

主配置文件示例见 [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)。  
The main configuration example lives at [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml).

关键配置段 / Important sections:

- `bridge`: FT4 默认频率与 TX 平滑参数  
  FT4 default frequencies and TX smoothing parameters
- `satellite_server`: 给 `SatPC32` 的 TCP rig 控制口  
  TCP rig control for `SatPC32`
- `wsjtx_server`: 给 `WSJT-X` 的 TCP rig 控制口，可选  
  Optional TCP rig control for `WSJT-X`
- `wsjtx_serial_frontend`: 给 `WSJT-X` 的虚拟串口前端  
  Virtual COM frontend for `WSJT-X`
- `digimanager_serial_backend`: 指向 DigiManager 输入 COM 的后端串口  
  Backend COM connected to DigiManager input
- `adapter`: 当前选择 `serial` 或 `hooks`  
  Chooses either `serial` or `hooks`

## 开发与验证 / Development And Validation

运行测试 / Run the tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```

## 当前限制 / Current Limitations

- 当前串口前端实现的是最小 `rigctl` 文本语义，不模拟复杂 CAT 设备方言  
  The serial frontend currently implements a minimal text `rigctl` dialect rather than a full CAT radio personality
- 当前后端默认命令格式也是 `rigctl` 风格文本，可在配置里覆盖模板  
  The backend defaults to text `rigctl`-style commands, with configurable templates
- 如果你现有修改版 `WSJT-X` 或 DigiManager 使用不同串口方言，需要在协议层再补一层兼容  
  If your modified `WSJT-X` or DigiManager uses a different serial dialect, an additional compatibility layer will still be needed
