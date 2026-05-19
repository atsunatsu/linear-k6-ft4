# UDP Replay Bench Quick Start / UDP 重放台架快速开始

## 这份说明给谁看 / Who This Is For

这份说明给现在要做**真实台架重放测试**的人。  
This guide is for people who are doing the **current bench replay test**.

你现在不需要先抓包。仓库里已经附带了现成样本。  
You do not need to capture packets first. The repository already includes ready-made samples.

## 先准备什么 / What To Prepare First

请先确认这 4 件事：  
Please confirm these 4 things first:

1. `假负载 / Dummy load`
2. `无天线 / No antenna`
3. `UVK5DigManager` 已经打开
4. 电台已经连到 `UVK5DigManager`

如果这 4 件事里有任何一件不满足，请先停住。  
If any of these 4 conditions is not true, stop here first.

## 用哪两个样本 / Which Two Samples To Use

直接使用仓库里的这两个文件：  
Use these two files directly from the repository:

- [samples/replay/ft8-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft8-replay.json)
- [samples/replay/ft4-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft4-replay.json)

## 第一步：先做 dry-run / Step 1: Dry Run First

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --dry-run
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --dry-run
```

这一步只是检查顺序，不会真正发包。  
This step only checks the sequence and does not send packets yet.

## 第二步：先重放 FT8 / Step 2: Replay FT8 First

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --fast-replay
```

请观察：  
Please observe:

- `DigiManager` 界面是否有变化  
  Whether the `DigiManager` UI changes
- `PTT` 是否动作  
  Whether `PTT` changes state
- 电台是否出现接近真实 `FT8` 的发射反应  
  Whether the radio shows behavior similar to real `FT8` transmit

## 第三步：再重放 FT4 / Step 3: Replay FT4 Next

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --fast-replay
```

请继续观察同样三件事：  
Observe the same three things again:

- `DigiManager` 界面变化  
  `DigiManager` UI changes
- `PTT` 动作  
  `PTT` action
- 电台发射相关反应  
  Radio transmit-related response

## 第四步：做单包模式对比 / Step 4: Compare Single Marker Packets

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --single-packet-tag ft8_mode_marker
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --single-packet-tag ft4_mode_marker
```

这一步主要看：  
This step mainly checks:

- `ft8_mode_marker` 是否单独就能触发反应  
  Whether `ft8_mode_marker` alone triggers a response
- `ft4_mode_marker` 是否单独就能触发反应  
  Whether `ft4_mode_marker` alone triggers a response

## 你要记录什么 / What To Record

至少记录下面这些：  
At minimum, record these:

- `FT8` 重放有没有反应  
  Whether `FT8` replay produced a response
- `FT4` 重放有没有反应  
  Whether `FT4` replay produced a response
- `ft8_mode_marker` 单发有没有反应  
  Whether single `ft8_mode_marker` produced a response
- `ft4_mode_marker` 单发有没有反应  
  Whether single `ft4_mode_marker` produced a response

建议直接按这个模板填写：  
Use this template if possible:

[docs/UDP_REPLAY_BENCH_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_BENCH_TEMPLATE.md)
