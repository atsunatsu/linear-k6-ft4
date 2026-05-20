# linear-k6-ft4

## 当前阶段 / Current Stage
当前主线已经切到**真实 0.3q 二进制逆向 + 最小动态验证**。

这轮主要做两件事：

- 找到真实 `0.3q` 在数字模式里**是谁把频率锁死**
- 判断 DigiManager 在数字模式里是否持续发改频

同时尽量回答：

- 数字模式入口在哪里
- 设频调用链大概怎么走
- 外部控频入口是否还存在

The project is now focused on **reverse-engineering the real 0.3q binaries plus minimal dynamic validation**.

This phase now has two main goals:

- find who locks frequency inside digital mode on the real `0.3q`
- determine whether DigiManager keeps sending retune commands in digital mode

And, if possible, also answer:

- where digital mode starts
- how the frequency-setting path is structured
- whether an external retune/control path still exists

## 这阶段不做什么 / What This Phase Is Not
现在**不**继续把公开源码树当成真实 `0.3q`。
现在**不**让测试者刷 bench 固件。
现在**不**继续走 DigiManager replay 公开测试流程。

We are **not** treating the public source tree as the real `0.3q`.
We are **not** asking testers to flash the old bench firmware in this phase.
We are **not** using the DigiManager replay flow as the main public path.

## 你现在要准备什么 / What You Need Right Now
请把真实输入材料放到仓库里。最推荐的是放到 `reverse/input` 下面；如果你只是临时分析，也可以直接放在仓库根目录：

1. 真实 `0.3q` 固件 `bin`
   放到 [reverse/input/firmware/README.md](/F:/Codex/CEC固件改装FT4/reverse/input/firmware/README.md) 说明的位置，或者临时直接放仓库根目录
2. `UVK5DigManager.exe` 或 `UVK5DigManager_v1.0.zip`
   放到 [reverse/input/digimanager/README.md](/F:/Codex/CEC固件改装FT4/reverse/input/digimanager/README.md) 说明的位置，或者临时直接放仓库根目录
3. 现有 `FT4 / FT8` UDP replay JSON
   这部分仓库里已经有了，会自动作为辅助证据使用

Please place the real inputs into the repo. The preferred location is `reverse/input`, but temporary root-level placement is also supported:

1. the real `0.3q` firmware `bin`
2. `UVK5DigManager.exe` or `UVK5DigManager_v1.0.zip`
3. existing `FT4 / FT8` UDP replay JSON

The replay JSON files are already present in this repo and will be used automatically as supporting evidence.

## 最短运行方法 / Shortest Way To Run
在项目目录打开 `PowerShell`，然后运行：

```powershell
python scripts\analyze_real_03q_reverse.py
```

脚本会自动：

- 查找真实固件 `bin`
- 查找 DigiManager 二进制
- 结合现有 replay JSON
- 生成逆向地图

Open `PowerShell` in the project folder and run:

```powershell
python scripts\analyze_real_03q_reverse.py
```

The script will automatically:

- look for the real firmware `bin`
- look for the DigiManager binary
- use the existing replay JSON files
- produce a reverse-engineering map

## 输出在哪里 / Where The Output Goes
输出会写到：

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

These files are the current working outputs:

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

## 我该先看哪份文档 / Which Document To Read First
- 逆向快速上手 / reverse quick start:
  [docs/REAL_03Q_REVERSE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_REVERSE_QUICKSTART.md)
- 动态改频验证 / dynamic retune check:
  [docs/REAL_03Q_DYNAMIC_RETUNE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_DYNAMIC_RETUNE.md)
- 逆向结果模板 / reverse result template:
  [docs/REAL_03Q_REVERSE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_REVERSE_RESULT_TEMPLATE.md)
- 动态结果模板 / dynamic result template:
  [docs/REAL_03Q_DYNAMIC_RETUNE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_DYNAMIC_RETUNE_RESULT_TEMPLATE.md)
- 输入资产说明 / asset intake notes:
  [reverse/README.md](/F:/Codex/CEC固件改装FT4/reverse/README.md)

## 当前输出目标格式 / Current Output Targets
这轮希望最终收敛成下面 5 个结论字段：

- `digital_mode_entry`
- `frequency_set_call_chain`
- `lock_frequency_owner`
- `external_retune_capability`
- `recommended_next_step`

动态验证阶段新增 3 个结论字段：

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`

This phase aims to reduce everything to these 5 fields:

- `digital_mode_entry`
- `frequency_set_call_chain`
- `lock_frequency_owner`
- `external_retune_capability`
- `recommended_next_step`

The dynamic validation step also adds:

- `digimanager_continuous_retune`
- `firmware_applies_retune_in_digital_mode`
- `lock_owner`
