# UDP 重放台架快速上手 / UDP Replay Bench Quick Start

## 这份说明适合谁 / Who This Is For

这份说明适合已经完成 `FT4-only` 和 `FT8-only` 抓包、准备推进到台架发射验证的人。  
This guide is for people who already completed `FT4-only` and `FT8-only` captures and want to move to bench replay validation.

## 安全边界 / Safety Boundary

请只在下面条件下继续：

- 假负载  
  Dummy load
- 无天线  
  No antenna
- 明确可控的台架环境  
  A controlled bench environment

## 第一步：先分析两份抓包 / Step 1: Analyze The Two Captures

```powershell
python scripts/analyze_udp_capture.py ft4-only.pcapng ft8-only.pcapng
```

你应该重点确认：

- `FT4` 是否到达 `5957`
- `FT8` 是否到达 `5957`
- `59 57 04 00` 是否只出现在 `FT4`
- `59 57 08 00` 是否只出现在 `FT8`

## 第二步：导出重放样本集 / Step 2: Export Replay Sequences

```powershell
python scripts/export_udp_replay.py --input ft4-only.pcapng --mode FT4 --output ft4-replay.json
python scripts/export_udp_replay.py --input ft8-only.pcapng --mode FT8 --output ft8-replay.json
```

## 第三步：先做 dry-run / Step 3: Dry Run First

```powershell
python scripts/replay_udp_sequence.py --input ft8-replay.json --dry-run
python scripts/replay_udp_sequence.py --input ft4-replay.json --dry-run
```

这一步只打印包顺序，不真的发包。  
This step only prints the packet order and does not actually send anything.

## 第四步：先重放 FT8，再重放 FT4 / Step 4: Replay FT8 First, Then FT4

```powershell
python scripts/replay_udp_sequence.py --input ft8-replay.json --fast-replay
python scripts/replay_udp_sequence.py --input ft4-replay.json --fast-replay
```

优先观察：

- `DigiManager` 界面变化  
  `DigiManager` UI changes
- `PTT` 是否响应  
  Whether `PTT` responds
- 电台是否表现出与真实 `FT8` 相近的发射行为  
  Whether the radio behaves similarly to real `FT8`

## 第五步：单包验证模式差异 / Step 5: Replay Single Marker Packets

```powershell
python scripts/replay_udp_sequence.py --input ft4-replay.json --single-packet-tag ft4_mode_marker
python scripts/replay_udp_sequence.py --input ft8-replay.json --single-packet-tag ft8_mode_marker
```

这一步用来观察 `04 00` 和 `08 00` 是否触发不同响应。  
This step checks whether `04 00` and `08 00` trigger different responses.

## 结果记录 / What To Record

请至少记录：

- `FT8` 重放是否有响应
- `FT4` 重放是否有响应
- 单发 `ft4_mode_marker` 是否有响应
- 单发 `ft8_mode_marker` 是否有响应

建议按这个模板整理：  
Use this template if possible:

[docs/UDP_REPLAY_BENCH_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_BENCH_TEMPLATE.md)
