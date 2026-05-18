# linear-k6-ft4

中文和 English 并排提供。后续项目文档默认保持中英双语。  
Chinese and English are provided side by side. Future project documentation should stay bilingual by default.

## 如果你是测试者，从这里开始 / If You Are A Tester, Start Here

如果你只是来帮忙抓包，请先按 **UDP 路线** 走，不要默认自己需要串口代理。  
If you are here only to help with capture, start with the **UDP path** and do not assume you need a serial proxy.

### 入口 1：我只是来帮忙抓包 / Path 1: I Only Want To Help Capture

1. 先确认 `WSJT-X` 和 `DigiManager` 当前用的是不是本机 `UDP`。  
   First confirm whether `WSJT-X` and `DigiManager` are using local `UDP`.
2. 观察 `2237 / 4532 / 5957` 这几个关键端口。  
   Observe the key ports `2237 / 4532 / 5957`.
3. 用 Windows loopback capture 抓 `WSJT-X ↔ DigiManager` 的本机 `UDP`。  
   Use Windows loopback capture to record the local `UDP` traffic between `WSJT-X` and `DigiManager`.
4. 只有在 UDP 不足以解释行为时，才回头看设备侧串口控制面。  
   Only fall back to the device-side serial control path if the UDP traffic is not enough to explain the behavior.

请先看这里：  
Start here:

- UDP 快速上手 / UDP quick start: [docs/UDP_CAPTURE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_QUICKSTART.md)
- UDP 抓包手册 / UDP capture guide: [docs/UDP_LOOPBACK_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_LOOPBACK_CAPTURE_GUIDE.md)
- 端口观察模板 / Port observation template: [docs/UDP_PORT_OBSERVATION_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_PORT_OBSERVATION_TEMPLATE.md)
- UDP 抓包结果模板 / UDP capture report template: [docs/UDP_CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_REPORT_TEMPLATE.md)

### 入口 2：串口抓包是第二阶段 / Path 2: Serial Capture Is Phase Two

如果第一轮 UDP 抓包已经能解释 `FT4` 行为，就不要再继续设备侧串口抓包。  
If the first round of UDP capture already explains the `FT4` behavior, do not continue to device-side serial capture.

只有在这些情况出现时，才继续看串口路线：  
Only use the serial path if one of these becomes true:

- `UDP` 流量不足以解释 DigiManager 如何驱动洁净发射  
  The `UDP` traffic is not enough to explain how DigiManager drives the clean transmit path
- `FT4` 发射关键行为没有体现在 `UDP` 面  
  The key `FT4` transmit behavior does not appear in the `UDP` layer
- 必须进一步观察 `DigiManager ↔ CEC/K5` 的设备控制流  
  You must go deeper into the `DigiManager ↔ CEC/K5` device-side control flow

串口路线保留在这里：  
The serial fallback documents remain here:

- [docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)
- [docs/CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/CAPTURE_REPORT_TEMPLATE.md)
- [docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md)

## 测试者的最小成功标准 / Minimum Success Standard For Testers

第一次测试不要求你立刻提交完整 `pcapng`。只要你能确认并回传下面这些信息，就已经有价值：  
Your first test does not need to produce a complete `pcapng` immediately. It is already useful if you can send back these facts:

```text
WSJT-X PTT = VOX?
WSJT-X UDPServerPort = ?
WSJT-X SendSymPort = ?
DigiManager UDP port = ?
wsjtx.exe live UDP port = ?
```

如果你还没装抓包工具，也没有关系，先回传端口观察结果即可。  
If you have not installed the capture tool yet, that is fine. The port-observation result is already useful.

## 抓包前后长什么样 / What The Setup Looks Like Before And After

抓包前 / Before capture:

```text
WSJT-X -> local UDP -> DigiManager
```

抓包时 / During capture:

```text
WSJT-X -> local UDP -> DigiManager
           ^
           |
   loopback packet capture
```

这里的重点不是改业务逻辑，而是在原链路上做**无侵入观察**。  
The point is not to change the behavior. We are doing **non-invasive observation** on the original link.

## 给测试者的推荐顺序 / Recommended Order For Testers

1. 打开 [docs/UDP_CAPTURE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_QUICKSTART.md)  
   Open [docs/UDP_CAPTURE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_QUICKSTART.md)
2. 运行 `python scripts/observe_udp_ports.py`  
   Run `python scripts/observe_udp_ports.py`
3. 回传端口观察结果，确认 `2237 / 4532 / 5957` 的现场关系  
   Send back the port-observation result and confirm the live relationship between `2237 / 4532 / 5957`
4. 安装 `Npcap` / `Wireshark` 或 `tshark`  
   Install `Npcap` / `Wireshark` or `tshark`
5. 按 [docs/UDP_LOOPBACK_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_LOOPBACK_CAPTURE_GUIDE.md) 抓 `startup / idle / decode / vox_tx_start / tx_symbols / tx_end`  
   Follow [docs/UDP_LOOPBACK_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_LOOPBACK_CAPTURE_GUIDE.md) to capture `startup / idle / decode / vox_tx_start / tx_symbols / tx_end`

## 这个仓库是做什么的 / What This Repository Is For

这个仓库的目标是保留 `CEC + DigiManager` 的洁净数字发射链，并把它推进到线性卫星上的 `FT4` 实机测试。  
This repository aims to preserve the clean `CEC + DigiManager` digital transmit chain and move it toward real-radio `FT4` testing on linear satellites.

当前仓库主要包含两类成果：  
The repository currently contains two main things:

- 一个 FT4-first 的卫星控频桥 `sat-bridge`  
  An FT4-first satellite control bridge called `sat-bridge`
- 一套给测试者使用的抓包和观察工具  
  A set of capture and observation tools for testers

## 当前目标 / Current Goal

当前最重要的目标有两个：  
The two most important current goals are:

- 让 `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` 这条 FT4 控制链跑起来  
  Make `SatPC32 -> sat-bridge -> DigiManager -> CEC/K5` work as an FT4 control path
- 确认 `WSJT-X ↔ DigiManager` 之间的实际本机 `UDP` 交互  
  Determine the actual local `UDP` interaction between `WSJT-X` and `DigiManager`

## 硬性约束 / Hard Constraints

- 不允许退回模拟音频 `SSB` 发射  
  No fallback to analog `SSB` audio injection
- 发射过程中也要连续平滑控频  
  Retuning must continue smoothly during TX
- 如果现有 DigiManager 洁净链承载不了 FT4，本项目只停在控制层打通，不做模拟音频替代  
  If the existing DigiManager clean chain cannot carry FT4, the project stops at the control layer instead of adding an analog audio workaround

## 工具 / Tools

- `python scripts/observe_udp_ports.py`  
  读取 `WSJT-X.ini` 并观察 `2237 / 4532 / 5957` 的现场占用情况  
  Read `WSJT-X.ini` and observe the live bindings for `2237 / 4532 / 5957`
- `python scripts/list_serial_topology.py`  
  保留为第二阶段设备侧串口排查工具  
  Kept as a second-stage tool for device-side serial investigation
- `python scripts/serial_capture_proxy.py ...`  
  保留为第二阶段串口透明代理  
  Kept as the second-stage transparent serial proxy

## 配置 / Configuration

配置示例见 [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)。  
See [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml) for the configuration example.

## 验证 / Validation

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```

## 当前限制 / Current Limitations

- 当前首选抓包路线依赖 Windows loopback capture 工具  
  The preferred capture path currently depends on Windows loopback capture tools
- 当前仓库不自带 `pcapng` 解析器  
  The repository does not yet include a built-in `pcapng` parser
- 设备侧串口控制面仍保留，但降级为第二阶段路线  
  The device-side serial control path still exists, but it is now a phase-two path
