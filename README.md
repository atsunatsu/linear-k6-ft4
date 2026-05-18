# sat-bridge

中文与 English 文档并排提供。后续项目文档默认保持中英双语。  
Chinese and English documentation are provided side by side. Future project documentation should stay bilingual by default.

## 目标 / Goal

`sat-bridge` 的首要目标是把线性卫星上的 **FT4** 实机测试通路打通，同时保留 `CEC + DigiManager` 的洁净数字发射链。  
The primary goal of `sat-bridge` is to make a **real-radio FT4** test path work on linear satellites while preserving the clean `CEC + DigiManager` digital transmit chain.

硬性约束 / Hard constraints:

- 不允许退回模拟音频 SSB 发射  
  No fallback to analog SSB audio injection.
- 发射过程中也要连续平滑控频  
  Doppler control must continue smoothly during TX.
- 如果现有 DigiManager 洁净链承载不了 FT4，本项目止步于控制层打通，不会伪造音频发射兜底  
  If the current DigiManager clean chain cannot carry FT4, this project stops at the control layer instead of faking an audio workaround.

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
  `SatPC32` is the uplink/downlink frequency authority.
- `WSJT-X` 只负责 FT4 业务、PTT、模式和状态查询  
  `WSJT-X` is limited to FT4 workflow, PTT, mode, and status reads.
- `sat-bridge` 是唯一向 DigiManager 输入口发控制命令的进程  
  `sat-bridge` is the only process allowed to drive DigiManager's input COM port.

## TX 连续跟频策略 / TX Continuous Retune Policy

发射中不再冻结频率，而是持续跟随上行目标值。  
Frequency is no longer frozen during TX. The bridge continuously tracks the latest uplink target.

默认策略 / Default policy:

- 小于 `10 Hz` 的变化先合并  
  Changes smaller than `10 Hz` are merged.
- 正常模式即时跟随  
  Normal mode follows updates immediately.
- 如果串口超时、后端无响应或更新过快造成积压，自动降级到 `5 Hz` 限速模式  
  If the backend times out, stalls, or gets overwhelmed, the bridge degrades to a `5 Hz` rate-limited mode.
- 限速模式下只发送最新目标值，不补发历史点  
  Rate-limited mode always sends only the newest target value.

## 配置 / Configuration

主配置文件示例见 [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)。  
The main configuration example lives at [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml).

关键配置段 / Important sections:

- `bridge`: FT4 默认频率与 TX 平滑参数  
  FT4 default frequencies and TX smoothing parameters.
- `satellite_server`: 给 `SatPC32` 的 TCP rig 控制口  
  TCP rig control for `SatPC32`.
- `wsjtx_server`: 给 `WSJT-X` 的 TCP rig 控制口，可选  
  Optional TCP rig control for `WSJT-X`.
- `wsjtx_serial_frontend`: 给 `WSJT-X` 的虚拟串口前端  
  Virtual COM frontend for `WSJT-X`.
- `digimanager_serial_backend`: 指向 DigiManager 输入 COM 的后端串口  
  Backend COM connected to DigiManager input.
- `adapter`: 当前选择 `serial` 或 `hooks`  
  Chooses either `serial` or `hooks`.

## 上机准备 / Hardware Prep

你需要 / You need:

- 一条 `DigiManager -> CEC/K5` 已经成功的洁净数字发射链  
  An already-working clean `DigiManager -> CEC/K5` digital transmit chain.
- 一个虚拟串口对工具，例如 `com0com`  
  A virtual COM pair tool such as `com0com`.
- 一对新的虚拟串口用于 `WSJT-X <-> sat-bridge`  
  One new COM pair for `WSJT-X <-> sat-bridge`.
- DigiManager 当前监听的输入 COM 号  
  The current DigiManager input COM port number.

推荐角色分配 / Suggested port roles:

- `COM11` 给 `sat-bridge` 前端  
  `COM11` for the `sat-bridge` frontend.
- `COM12` 给 `WSJT-X`  
  `COM12` for `WSJT-X`.
- DigiManager 现有输入 COM 保持不变  
  Keep DigiManager's current input COM unchanged.

## 启动步骤 / Startup Steps

1. 调整 [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)。  
   Edit [sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml).
2. 如果只是离线调试，把 `adapter.kind` 留在 `hooks`。  
   Keep `adapter.kind = "hooks"` for offline debugging only.
3. 如果上实机，把 `adapter.kind` 改为 `serial`，并填好 `wsjtx_serial_frontend` 与 `digimanager_serial_backend`。  
   Switch to `adapter.kind = "serial"` for real hardware, then fill in `wsjtx_serial_frontend` and `digimanager_serial_backend`.
4. 启动桥接服务 / Start the bridge:

```powershell
python -m src.sat_bridge --config sat_bridge.example.toml --log-level DEBUG
```

5. 启动 DigiManager，并保持它和 CEC/K5 的连接方式不变。  
   Start DigiManager and leave its CEC/K5 connection path unchanged.
6. 启动 `WSJT-X`，把 CAT 指向 `sat-bridge` 的前端虚拟串口或 TCP 端口。  
   Start `WSJT-X` and point CAT at the `sat-bridge` frontend COM port or TCP port.
7. 启动 `SatPC32`，把 rig control 指向 `127.0.0.1:4533`。  
   Start `SatPC32` and point rig control to `127.0.0.1:4533`.

## 测试顺序 / Test Sequence

建议按这个顺序做：  
Run tests in this order:

1. 先看 RX 态下行是否连续跟频  
   Verify continuous RX downlink retuning.
2. 再看 TX 拉起后上行是否连续跟频  
   Verify continuous TX uplink retuning after PTT goes high.
3. 再做 FT4 的“收-发-回收”完整周期  
   Run a full FT4 receive-transmit-return cycle.
4. 最后观察频谱是否仍保持洁净数字发射特征  
   Confirm the transmit spectrum still looks like the clean digital DigiManager path.

## 当前限制 / Current Limitations

- 当前串口前端实现的是最小 `rigctl` 文本语义，不模拟复杂 CAT 设备方言  
  The serial frontend currently implements a minimal text `rigctl` dialect rather than a full CAT radio personality.
- 当前后端默认命令格式也是 `rigctl` 风格文本，可在配置里覆盖模板  
  The backend defaults to text `rigctl`-style commands, with configurable templates.
- 如果你现有修改版 `WSJT-X` 或 DigiManager 使用不同串口方言，需要在协议层再补一层兼容  
  If your modified `WSJT-X` or DigiManager uses a different serial dialect, an additional compatibility layer will still be needed.

## 开发调试 / Development

运行测试 / Run the tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```
