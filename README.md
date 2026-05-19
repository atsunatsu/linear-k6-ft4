# linear-k6-ft4

中文和 English 并排提供。后续文档默认继续保持双语。  
Chinese and English are provided side by side. Future documentation should stay bilingual by default.

## 现在测试什么 / What We Are Testing Now

当前 GitHub 仓库只保留**当前阶段**：`UVK5DigManager` 的本机 UDP 台架重放测试。  
This repository now keeps only the **current phase**: local UDP bench replay testing for `UVK5DigManager`.

当前要回答的问题只有一个：  
There is only one current question:

- `FT8` 的已知正常样本能不能通过重放触发 `DigiManager` 和电台反应？  
  Can a known-good `FT8` sample trigger `DigiManager` and radio response when replayed?
- `FT4` 的真实抓包样本重放后，反应和 `FT8` 有什么不同？  
  After replaying a real `FT4` capture, what response differs from `FT8`?

已经完成的旧阶段，例如 COM 拓扑梳理、串口抓包、UDP 现场抓包说明，已从公开测试入口移除。  
Completed older phases such as COM topology work, serial capture, and UDP live-capture onboarding have been removed from the public tester entry points.

## 如果你是测试者，从这里开始 / If You Are A Tester, Start Here

你现在**不需要先抓包**，也不需要先研究协议。  
Right now you do **not** need to capture packets first, and you do not need to study the protocol first.

你只需要做这 4 步：  
You only need these 4 steps:

1. 准备台架环境：`假负载 / 无天线`  
   Prepare a safe bench: `dummy load / no antenna`
2. 打开 `UVK5DigManager`，确认电台已连接  
   Open `UVK5DigManager` and confirm the radio is connected
3. 用仓库自带的 `FT8` 和 `FT4` 样本做 UDP 重放  
   Replay the included `FT8` and `FT4` UDP samples
4. 记录 `DigiManager UI / PTT / 电台反应`，然后提交结果  
   Record `DigiManager UI / PTT / radio response`, then submit the result

## 测试者先看这里 / Tester Entry Points

- 当前测试步骤 / Current test steps: [docs/UDP_REPLAY_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_QUICKSTART.md)
- 结果填写模板 / Result template: [docs/UDP_REPLAY_BENCH_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_BENCH_TEMPLATE.md)
- 现成 FT4 样本 / Included FT4 sample: [samples/replay/ft4-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft4-replay.json)
- 现成 FT8 样本 / Included FT8 sample: [samples/replay/ft8-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft8-replay.json)

## 最短可执行流程 / Shortest Working Procedure

### 1. 安全边界 / Safety Boundary

只在下面条件下继续：  
Only continue under these conditions:

- `假负载 / Dummy load`
- `无天线 / No antenna`
- `有人值守 / Attended bench test`

### 2. 打开软件 / Open The Software

- 打开 `UVK5DigManager`
- 确认电台连接正常
- 这一步**不要求打开 `WSJT-X`**

- Open `UVK5DigManager`
- Confirm the radio is connected
- You do **not** need `WSJT-X` for this phase

### 3. 先做不发包检查 / Dry Run First

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --dry-run
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --dry-run
```

这一步只打印顺序，不真正发 UDP。  
This only prints packet order and does not send UDP yet.

### 4. 先重放 FT8，再重放 FT4 / Replay FT8 First, Then FT4

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --fast-replay
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --fast-replay
```

观察这几件事：  
Observe these items:

- `DigiManager` 界面有没有变化  
  Does the `DigiManager` UI change?
- `PTT` 有没有动作  
  Is there any `PTT` action?
- 电台有没有发射相关反应  
  Does the radio show any transmit-related behavior?

### 5. 再做单包模式标记对比 / Compare Single Marker Packets

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --single-packet-tag ft4_mode_marker
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --single-packet-tag ft8_mode_marker
```

这一轮主要看：  
This round mainly checks:

- `04 00` 和 `08 00` 是否触发不同反应  
  Whether `04 00` and `08 00` trigger different responses

## 你要回报什么 / What You Should Report Back

至少告诉我们这些：  
At minimum, report these:

- `FT8` 重放有没有反应  
  Whether `FT8` replay produced a response
- `FT4` 重放有没有反应  
  Whether `FT4` replay produced a response
- `ft8_mode_marker` 单发有没有反应  
  Whether single `ft8_mode_marker` produced a response
- `ft4_mode_marker` 单发有没有反应  
  Whether single `ft4_mode_marker` produced a response
- 你的测试环境是不是 `假负载 / 无天线`  
  Whether your bench used `dummy load / no antenna`

请优先按这个模板提交：  
Please submit using this template if possible:

[docs/UDP_REPLAY_BENCH_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_BENCH_TEMPLATE.md)

## 当前仓库保留的工具 / Tools Kept For The Current Phase

- `python scripts/analyze_udp_capture.py <pcapng> [<pcapng> ...]`  
  解析抓包并输出 `FT4 vs FT8` 差异  
  Parse captures and print `FT4 vs FT8` differences
- `python scripts/export_udp_replay.py --input <pcapng> --mode FT4|FT8 --output <json>`  
  从真实抓包导出可重放样本  
  Export replayable samples from real captures
- `python scripts/replay_udp_sequence.py --input <json> [--dry-run] [--fast-replay]`  
  向 `127.0.0.1:5957` 重放样本  
  Replay samples toward `127.0.0.1:5957`

## 这一步不再要求什么 / What This Phase No Longer Requires

当前公开测试流程**不再要求**：  
The public test flow **no longer requires**:

- 重新做 COM 拓扑梳理  
  Repeating COM topology work
- 重新做串口抓包  
  Repeating serial capture
- 重新做现场 UDP 抓包  
  Repeating live UDP capture

如果后续需要回到这些旧阶段，会在仓库里重新引入。  
If we need to return to those older phases later, they will be reintroduced deliberately.

## 验证 / Validation

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```
