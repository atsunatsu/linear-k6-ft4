# Real 0.3q Reverse Quick Start

## 中文
这份说明是给维护者看的。

它只做一件事：

- 读取真实 `0.3q` 固件和 `UVK5DigManager` 二进制
- 生成当前的逆向地图

## 你要准备什么
把下面文件放进仓库根目录，或者放到 `reverse/input` 对应目录：

- `cec_0.3QB.packed.bin`
- `UVK5DigManager.exe`

## 怎么跑
在项目目录打开 `PowerShell`，运行：

```powershell
python scripts\analyze_real_03q_reverse.py
```

## 输出在哪
- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

最重要的字段是：

- `digital_mode_entry`
- `frequency_set_call_chain`
- `lock_frequency_owner`
- `external_retune_capability`
- `recommended_next_step`

## English
This guide is for maintainers.

It does one thing:

- read the real `0.3q` firmware and `UVK5DigManager` binary
- generate the current reverse map

Run:

```powershell
python scripts\analyze_real_03q_reverse.py
```

Outputs:

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`
