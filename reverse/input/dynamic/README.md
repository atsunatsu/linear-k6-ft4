# Dynamic Reverse Input

## 中文
这个目录专门放“最小动态验证”需要的输入。

请把下面这些文件放在这里：

- `idle-retune.pcapng`
- `tx-retune.pcapng`
- `actions.json`

如果你没有额外的改频软件，可以直接用：

- [scripts/inject_retune_sequence.py](/F:/Codex/CEC固件改装FT4/scripts/inject_retune_sequence.py)

它会把现有 replay 样本改造成“带改频事件的测试流量”。

## English
This folder is for the minimal dynamic validation inputs:

- `idle-retune.pcapng`
- `tx-retune.pcapng`
- `actions.json`

If you do not have separate retune software, use:

- [scripts/inject_retune_sequence.py](/F:/Codex/CEC固件改装FT4/scripts/inject_retune_sequence.py)

It turns the existing replay samples into retune test traffic.
