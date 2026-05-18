# linear-k6-ft4

中文和 English 并排提供。后续项目文档默认保持中英双语。  
Chinese and English are provided side by side. Future project documentation should stay bilingual by default.

## 如果你是测试者，从这里开始 / If You Are A Tester, Start Here

如果你只是来帮忙抓包，请不要先研究代码，也不用先理解协议。你只需要按下面 3 步做。  
If you are here only to help with capture, do not start with the code and do not worry about the protocol. Just follow these 3 steps.

### 入口 1：我只是来帮忙抓包 / Path 1: I Only Want To Help Capture

1. 找到 `WSJT-X` 和 `DigiManager` 各自正在用的 `COM` 口。  
   Find which `COM` port `WSJT-X` uses and which `COM` port `DigiManager` uses.
2. 在它们中间插入抓包代理，记录双向串口数据。  
   Insert the capture proxy between them and record the traffic in both directions.
3. 把 `COM` 信息、截图和抓包日志回传。  
   Send back the `COM` info, screenshots, and capture logs.

请先看这里：  
Start here:

- 快速上手 / Quick start: [docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)
- 抓包手册 / Capture guide: [docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)
- 抓包结果模板 / Capture report template: [docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)
- 只会截图也可以 / Screenshot-only help template: [docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md)

### 入口 2：我是开发者/维护者 / Path 2: I Am A Developer Or Maintainer

如果你要看项目目标、工具和当前限制，再往下看。  
If you want the project goal, tooling, and current limitations, continue below.

## 测试者的最小成功标准 / Minimum Success Standard For Testers

第一次测试不要求你直接完成完整抓包。只要你能可靠地回传下面两行，就已经有价值：  
Your first test does not need to finish a full capture. It is already useful if you can reliably send back just these two lines:

```text
WSJT-X = COM?
DigiManager = COM?
```

如果连这两行都暂时确定不了，请直接回传 3 张截图：  
If you cannot even confirm those two lines yet, send these 3 screenshots instead:

- `WSJT-X` 设置页  
  `WSJT-X` settings page
- `DigiManager` 设置页  
  `DigiManager` settings page
- Windows 设备管理器里的 `Ports (COM & LPT)`  
  Windows Device Manager `Ports (COM & LPT)`

## 抓包前后长什么样 / What The Setup Looks Like Before And After

抓包前 / Before capture:

```text
WSJT-X -> COM? -> DigiManager
```

抓包后 / After capture:

```text
WSJT-X -> COM_A -> capture-proxy -> COM_B -> DigiManager
```

这里的重点不是改业务逻辑，只是把原来的一根线中间加一个“记录员”。  
The point is not to change the behavior. We are only inserting a “recorder” in the middle of the original link.

## 给测试者的推荐顺序 / Recommended Order For Testers

1. 打开 [docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)  
   Open [docs/TESTER_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/TESTER_QUICKSTART.md)
2. 先确认 `WSJT-X = COM?`、`DigiManager = COM?`  
   Confirm `WSJT-X = COM?` and `DigiManager = COM?`
3. 如果确认不了，直接按 [docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md) 回传截图  
   If you cannot confirm them, send screenshots using [docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md)
4. 如果确认了，再按 [docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md) 插入代理并抓包  
   If you did confirm them, continue with [docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)

## 这个仓库是做什么的 / What This Repository Is For

这个仓库的目标是保留 `CEC + DigiManager` 的洁净数字发射链，并把它推进到线性卫星上的 `FT4` 实机测试。  
This repository aims to preserve the clean `CEC + DigiManager` digital transmit chain and move it toward real-radio `FT4` testing on linear satellites.

当前仓库主要包含两类成果：  
The repository currently contains two main things:

- 一个 FT4-first 的卫星控频桥 `sat-bridge`  
  An FT4-first satellite control bridge called `sat-bridge`
- 一套给测试者使用的串口抓包工具和流程  
  A serial capture toolkit and workflow for testers

## 当前目标 / Current Goal

当前最重要的目标有两个：  
The two most important current goals are:

- 让 `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` 这条 FT4 控制链跑起来  
  Make `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` work as an FT4 control path
- 确认 `WSJT-X ↔ DigiManager` 之间实际使用的串口协议  
  Determine the actual serial protocol used between `WSJT-X` and `DigiManager`

在拿到最小抓包样本前，仓库里的串口协议实现都只是可替换假设。  
Until we have the minimum capture samples, any serial protocol implementation in this repo is still a replaceable hypothesis.

## 硬性约束 / Hard Constraints

- 不允许退回模拟音频 `SSB` 发射  
  No fallback to analog `SSB` audio injection
- 发射过程中也要连续平滑控频  
  Retuning must continue smoothly during TX
- 如果现有 DigiManager 洁净链承载不了 FT4，本项目只停在控制层打通，不做模拟音频替代  
  If the existing DigiManager clean chain cannot carry FT4, the project stops at the control layer instead of adding an analog audio workaround

## 固定拓扑 / Fixed Topology

```text
SatPC32 / Doppler software
        |
        v
  sat-bridge rig control
        |
        +--> WSJT-X control side
        |
        +--> sat-bridge serial frontend
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
- `WSJT-X` 只负责 FT4 业务、PTT、模式和状态  
  `WSJT-X` is limited to FT4 workflow, PTT, mode, and status
- `sat-bridge` 是唯一允许写 DigiManager 输入 COM 的程序  
  `sat-bridge` is the only process allowed to write to DigiManager's input COM

## 工具 / Tools

- `python scripts/list_serial_topology.py`  
  列出本机串口并生成拓扑填写表  
  List local serial ports and generate a topology worksheet
- `python scripts/serial_capture_proxy.py ...`  
  在 `WSJT-X` 和 `DigiManager` 之间做透明抓包代理  
  Run a transparent capture proxy between `WSJT-X` and `DigiManager`
- `python scripts/analyze_capture.py logs/serial-capture.jsonl`  
  对抓包结果做快速摘要  
  Produce a quick summary of the capture log

## 配置 / Configuration

配置示例见 [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)。  
See [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml) for the configuration example.

## 验证 / Validation

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```

## 当前限制 / Current Limitations

- 当前串口前端仍是最小控制语义，不是完整 CAT 设备人格  
  The current serial frontend still provides only the minimum control semantics, not a full CAT device personality
- 当前后端默认命令格式仍是可替换的假设层  
  The current backend command format is still a replaceable hypothesis layer
- 真正的协议适配要等最小抓包样本到位后再收敛  
  The real protocol adaptation will be narrowed down only after the minimum capture samples arrive
