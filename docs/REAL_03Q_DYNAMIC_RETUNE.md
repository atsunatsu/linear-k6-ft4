# Real 0.3q Dynamic Retune Check

## 中文
这一步的目标不是恢复 FT4 发射，而是只回答 3 个问题：

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`

如果你手里**没有额外的改频软件**，现在可以直接用仓库自带的最小改频注入器：

- [scripts/inject_retune_sequence.py](/F:/Codex/CEC固件改装FT4/scripts/inject_retune_sequence.py)

它会把现有 `FT8` replay 样本改成“带改频事件的测试流量”，直接发到 `127.0.0.1:5957`，不需要再找第三方控频软件。
默认还会把原始 replay 的长时间轴压缩成较短的固定间隔，避免一次测试要等几十秒。

## 你需要准备什么
放到 [reverse/input/dynamic](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic)：

1. `idle-retune.pcapng`
   说明：数字模式空闲态时，用注入器发一次或多次改频
2. `tx-retune.pcapng`
   说明：数字模式 TX 期间，用注入器发一次或多次改频
3. `actions.json`
   可以直接让注入器帮你生成或更新

## 第一步：先做空闲态改频演练
在项目目录打开 `PowerShell`，先运行：

```powershell
python scripts\inject_retune_sequence.py --profile idle --retune-events "1000:145950000,4000:145950500" --dry-run
```

这一步只打印计划，不真正发 UDP。

如果输出正常，再开始抓包，并运行：

```powershell
python scripts\inject_retune_sequence.py --profile idle --retune-events "1000:145950000,4000:145950500" --actions-output reverse\input\dynamic\actions.json --capture-kind idle --capture-path reverse/input/dynamic/idle-retune.pcapng
```

建议同时用 Wireshark 抓本机 loopback：

```text
udp and port 5957
```

抓完后把文件保存为：

- `reverse/input/dynamic/idle-retune.pcapng`

## 第二步：再做 TX 期间改频演练
同样先演练：

```powershell
python scripts\inject_retune_sequence.py --profile tx --retune-events "3000:145950000,6500:145950500" --dry-run
```

然后开始抓包，并运行：

```powershell
python scripts\inject_retune_sequence.py --profile tx --retune-events "3000:145950000,6500:145950500" --actions-output reverse\input\dynamic\actions.json --capture-kind tx --capture-path reverse/input/dynamic/tx-retune.pcapng
```

抓完后把文件保存为：

- `reverse/input/dynamic/tx-retune.pcapng`

## 第三步：补现场观察
打开 `reverse/input/dynamic/actions.json`，把这两项改成真实观察结果：

- `idle_frequency_change`
- `tx_frequency_change`

只能填这 4 个值之一：

- `yes`
- `no`
- `temporary`
- `unknown`

如果电台只是短暂跳到新频率，然后又回去，请写：

- `temporary`

## 第四步：跑最终分析
在项目目录打开 `PowerShell`，运行：

```powershell
python scripts\analyze_dynamic_lock.py
```

## 输出在哪
- `logs/reverse/dynamic-lock-report.json`
- `logs/reverse/dynamic-lock-report.md`

同样的结论也会并入总报告：

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

## English
This step is only meant to answer 3 questions:

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`

If you do **not** have separate retune software, use the built-in injector:

- [scripts/inject_retune_sequence.py](/F:/Codex/CEC固件改装FT4/scripts/inject_retune_sequence.py)

It converts the existing replay samples into retune test traffic and sends it to `127.0.0.1:5957`.
By default it also compresses the long original replay timing into short fixed gaps, so one test run does not take tens of seconds.

## What you need
Place these in [reverse/input/dynamic](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic):

1. `idle-retune.pcapng`
2. `tx-retune.pcapng`
3. `actions.json`

## Idle retune run
Dry run first:

```powershell
python scripts\inject_retune_sequence.py --profile idle --retune-events "1000:145950000,4000:145950500" --dry-run
```

Then capture loopback traffic and run:

```powershell
python scripts\inject_retune_sequence.py --profile idle --retune-events "1000:145950000,4000:145950500" --actions-output reverse\input\dynamic\actions.json --capture-kind idle --capture-path reverse/input/dynamic/idle-retune.pcapng
```

## TX retune run
Dry run first:

```powershell
python scripts\inject_retune_sequence.py --profile tx --retune-events "3000:145950000,6500:145950500" --dry-run
```

Then capture and run:

```powershell
python scripts\inject_retune_sequence.py --profile tx --retune-events "3000:145950000,6500:145950500" --actions-output reverse\input\dynamic\actions.json --capture-kind tx --capture-path reverse/input/dynamic/tx-retune.pcapng
```

## Final analysis
After both captures are present and `actions.json` has the real radio observations, run:

```powershell
python scripts\analyze_dynamic_lock.py
```
