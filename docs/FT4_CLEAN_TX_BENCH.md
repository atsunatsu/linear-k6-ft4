# FT4 Clean TX Bench / FT4 洁净发射台架说明

## 这是什么 / What This Is

这是第一版 `FT4` 洁净发射原型。  
This is the first prototype of the `FT4` clean transmitter.

它做的事情是：
- 不再依赖 `DigiManager` 的 `FT4` 通路
- 直接使用我们自己的 `FT4` 发射器
- 仍然保留 `sat-bridge` 的实时控频思路

It does this:
- It no longer depends on the `FT4` path inside `DigiManager`
- It uses our own `FT4` transmitter
- It still follows the real-time retune model used by `sat-bridge`

## 当前原型怎么工作 / How The Current Prototype Works

第一版不是从零生成完整 `FT4` 底层波形，而是：
- 读取一个已知 `FT4` 抓包样本模板
- 自动裁掉“第二次发射”那一半，避免重复发射
- 把模板里的可见文本区替换成你给的新消息
- 只重放一个 `FT4` 发射窗口

The first version does not synthesize a full `FT4` waveform from scratch yet. Instead it:
- Loads a known `FT4` capture template
- Automatically trims it down to a single transmit window
- Replaces the visible text field inside the FT4 marker packets
- Replays only one FT4 transmit window

## 配置位置 / Configuration

配置在：

[sat_bridge.example.toml](/F:/Codex/CEC固件改装FT4/sat_bridge.example.toml)

重点是这个段落：
- `[ft4_clean_tx]`
- `[ft4_clean_tx.commands]`

The important sections are:
- `[ft4_clean_tx]`
- `[ft4_clean_tx.commands]`

## 最短运行方式 / Shortest Way To Run It

先在项目目录打开 `PowerShell`，然后运行：

```powershell
python scripts\run_ft4_clean_tx.py --config sat_bridge.example.toml --payload "CQ TEST OO00" --tx-frequency-hz 145950000
```

Open `PowerShell` in the project folder, then run:

```powershell
python scripts\run_ft4_clean_tx.py --config sat_bridge.example.toml --payload "CQ TEST OO00" --tx-frequency-hz 145950000
```

正常时你会看到：
- `starting_ft4_clean_tx ...`
- `ft4_clean_tx_complete`

On success you should see:
- `starting_ft4_clean_tx ...`
- `ft4_clean_tx_complete`

## 默认行为 / Default Behavior

当前默认是：
- 用 `samples/replay/ft4-replay.json`
- 只取第一个 `FT4` 发射窗口
- 默认 `fast_replay`

Current defaults are:
- Use `samples/replay/ft4-replay.json`
- Keep only the first `FT4` transmit window
- Default to `fast_replay`

这样做的目的，是避免你之前看到的“FT8 会发两次”那种现象。  
This is meant to avoid the earlier “FT8 transmits twice” behavior.

## 如何做实时改频试验 / How To Test Retunes During TX

可以附带 `--retune` 参数。格式是：

```text
频率@延迟毫秒
```

You can add `--retune`. The format is:

```text
frequency@delay_ms
```

例如：

```powershell
python scripts\run_ft4_clean_tx.py --config sat_bridge.example.toml --payload "CQ TEST OO00" --tx-frequency-hz 145950000 --retune 145950050@300 --retune 145950120@600
```

Example:

```powershell
python scripts\run_ft4_clean_tx.py --config sat_bridge.example.toml --payload "CQ TEST OO00" --tx-frequency-hz 145950000 --retune 145950050@300 --retune 145950120@600
```

只要你加了 `--retune`，脚本默认会自动改用 `original_timing`，避免 `fast_replay` 太快导致改频来不及生效。  
As soon as you add `--retune`, the script automatically switches to `original_timing`, so retune events do not get lost inside a too-fast replay.

## 如果失败了怎么看 / How To Judge Failure

如果下面任何一个出现，就算失败：
- 没看到 `starting_ft4_clean_tx`
- 没看到 `ft4_clean_tx_complete`
- 终端直接报 `failed to set start frequency`
- 终端直接报 `failed to enable PTT`
- 终端直接报 `packet send failed`

Any of these means failure:
- You do not see `starting_ft4_clean_tx`
- You do not see `ft4_clean_tx_complete`
- The terminal reports `failed to set start frequency`
- The terminal reports `failed to enable PTT`
- The terminal reports `packet send failed`

## 当前边界 / Current Limits

当前原型还不是最终替代器。它目前：
- 先只做 `FT4 TX`
- 先只支持模板驱动的 `FT4` 发送
- 还没有自动接到 `WSJT-X` 的发送按钮
- 还没有重建更底层的 `CEC` 原生发射协议

This prototype is not the final replacement yet. Right now it:
- Only handles `FT4 TX`
- Uses template-driven FT4 transmission
- Is not yet auto-wired to the `WSJT-X` send button
- Does not yet rebuild a lower-level native `CEC` transmit protocol
