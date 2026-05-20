# Real 0.3q Dynamic Retune Check

## 中文
这一步只验证 3 个结论：

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`

## 你要准备什么
放到 [reverse/input/dynamic](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic)：

1. `idle-retune.pcapng`
   说明：数字模式空闲态时改一次频
2. `tx-retune.pcapng`
   说明：数字模式 TX 期间改一次频
3. `actions.json`
   可以从 [actions.template.json](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic/actions.template.json) 复制后改

## `actions.json` 里要写什么
- 哪个文件是空闲态抓包
- 哪个文件是 TX 态抓包
- 在第几毫秒做了改频动作
- 电台有没有真的变频：
  - `yes`
  - `no`
  - `temporary`
  - `unknown`

## 怎么跑
在项目目录打开 `PowerShell`，运行：

```powershell
python scripts\analyze_dynamic_lock.py
```

## 输出在哪里
- `logs/reverse/dynamic-lock-report.json`
- `logs/reverse/dynamic-lock-report.md`

脚本也会把同样的结论并入主逆向报告：
- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

## English
This step validates only 3 conclusions:

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`

## What you need
Place these in [reverse/input/dynamic](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic):

1. `idle-retune.pcapng`
2. `tx-retune.pcapng`
3. `actions.json`
   You can start from [actions.template.json](/F:/Codex/CEC固件改装FT4/reverse/input/dynamic/actions.template.json)

## What goes into `actions.json`
- which file is the idle capture
- which file is the TX capture
- at which millisecond offsets the retune actions happened
- whether the radio actually changed frequency:
  - `yes`
  - `no`
  - `temporary`
  - `unknown`

## How to run it
Open `PowerShell` in the project folder and run:

```powershell
python scripts\analyze_dynamic_lock.py
```

## Outputs
- `logs/reverse/dynamic-lock-report.json`
- `logs/reverse/dynamic-lock-report.md`

The same conclusions are also folded into:
- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`
