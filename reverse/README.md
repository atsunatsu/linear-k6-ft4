# Reverse Workspace

## 中文
这里专门放**真实 0.3q 二进制逆向**需要的输入说明。

当前主线不是公开源码 bench，也不是 DigiManager replay。
当前主线是：

- 真实 `0.3q` 固件 `bin`
- `UVK5DigManager` 二进制
- 现有 `2237 / 5957` 抓包结果只作为辅助证据

把输入文件放到这里：

- 固件：`reverse/input/firmware/`
- 上位机：`reverse/input/digimanager/`

建议运行：

```powershell
python scripts\analyze_real_03q_reverse.py
```

输出会写到：

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

## English
This folder is reserved for **real 0.3q binary reverse-engineering** input assets.

The current main path is not the public-source bench build and not DigiManager replay.
The current main path is:

- the real `0.3q` firmware `bin`
- the `UVK5DigManager` binary
- existing `2237 / 5957` capture data only as supporting evidence

Place files here:

- firmware: `reverse/input/firmware/`
- DigiManager: `reverse/input/digimanager/`

Then run:

```powershell
python scripts\analyze_real_03q_reverse.py
```

Outputs go to:

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`
