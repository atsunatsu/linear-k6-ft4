# Real 0.3q Reverse Quick Start

## 中文
这份说明只做一件事：

- 让你把真实 `0.3q` 固件和 `UVK5DigManager` 二进制放进仓库
- 然后一条命令生成逆向地图

### 第 1 步：放真实固件
把真实 `0.3q` 固件 `bin` 放到：

- [reverse/input/firmware](/F:/Codex/CEC固件改装FT4/reverse/input/firmware)

推荐文件名：

- `real-0.3q.bin`

如果你只是临时分析，也可以直接放在仓库根目录。

### 第 2 步：放 DigiManager
把下面任意一种放到：

- [reverse/input/digimanager](/F:/Codex/CEC固件改装FT4/reverse/input/digimanager)

可以是：

- `UVK5DigManager.exe`
- `UVK5DigManager_v1.0.zip`

如果你只是临时分析，也可以直接放在仓库根目录。

### 第 3 步：打开 PowerShell
在项目目录空白处按住 `Shift`，点击右键，打开 `PowerShell` 或终端。

### 第 4 步：运行分析
直接运行：

```powershell
python scripts\analyze_real_03q_reverse.py
```

### 第 5 步：看结果
脚本结束后，看这两个文件：

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

最重要的是看里面这几项：

- `digital_mode_entry`
- `frequency_set_call_chain`
- `lock_frequency_owner`
- `external_retune_capability`
- `recommended_next_step`

## English
This guide does only one thing:

- get the real `0.3q` firmware and `UVK5DigManager` binary into the repo
- then generate a reverse-engineering map with one command

### Step 1: Place the real firmware
Put the real `0.3q` firmware `bin` in:

- [reverse/input/firmware](/F:/Codex/CEC固件改装FT4/reverse/input/firmware)

Suggested filename:

- `real-0.3q.bin`

For a temporary one-off analysis, putting it in the repo root also works.

### Step 2: Place DigiManager
Put one of these in:

- [reverse/input/digimanager](/F:/Codex/CEC固件改装FT4/reverse/input/digimanager)

Accepted files:

- `UVK5DigManager.exe`
- `UVK5DigManager_v1.0.zip`

For a temporary one-off analysis, putting it in the repo root also works.

### Step 3: Open PowerShell
Open `PowerShell` or a terminal in the project folder.

### Step 4: Run the analysis
Run:

```powershell
python scripts\analyze_real_03q_reverse.py
```

### Step 5: Read the result
After the script finishes, read:

- `logs/reverse/reverse-map.json`
- `logs/reverse/reverse-map.md`

The most important fields are:

- `digital_mode_entry`
- `frequency_set_call_chain`
- `lock_frequency_owner`
- `external_retune_capability`
- `recommended_next_step`
