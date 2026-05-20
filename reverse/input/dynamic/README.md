# Dynamic Validation Input

## 中文
这里放“最小动态验证”需要的输入。

当前固定输入文件是：

- `actions.json`
- `idle-retune.pcapng`
- `tx-retune.pcapng`

`actions.json` 用来告诉脚本：

- 哪个文件是空闲态抓包
- 哪个文件是 TX 态抓包
- 在抓包里的哪几个时间点做了改频动作
- 电台现场是否真的变频

分析命令：

```powershell
python scripts\analyze_dynamic_lock.py
```

## English
This folder holds the inputs for the **minimal dynamic validation** step.

Required files:

- `actions.json`
- `idle-retune.pcapng`
- `tx-retune.pcapng`

`actions.json` tells the script:

- which file is the idle-mode capture
- which file is the TX capture
- when the retune actions happened
- whether the radio actually changed frequency on the bench

Analysis command:

```powershell
python scripts\analyze_dynamic_lock.py
```
