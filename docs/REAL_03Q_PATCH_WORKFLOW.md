# 真实 0.3q 组合补丁工作流

## 这份文档给谁看
这份文档是给维护者看的，不是给普通测试者看的。

如果你想先了解这个项目为什么会走到当前这条路线，先看：
- [研发方法与过程](/F:/Codex/CEC固件改装FT4/docs/研发方法与过程.md)
- [CEC 0.3q 的 FT8 发射方案与 FT4 可行性分析](/F:/Codex/CEC固件改装FT4/docs/CEC_FT8发射方案与FT4可行性分析.md)

## 当前主线
当前成功率优先的路线是：

1. 给真实 `cec_0.3QB.packed.bin` 打补丁，尽量放开数字模式改频
2. 给 `UVK5DigManager.exe` 打补丁，让 `FT4` 能进入现有数字发射下发路径
3. 先用 **patched DigiManager + 原版固件** 验证固定频点下的合格 `FT4`
4. 再用 **patched DigiManager + patched 固件** 回接改频

## 需要放进工作区的真实文件
把这些真实文件放到仓库根目录，或对应的 `reverse/input` 目录：

- `cec_0.3QB.packed.bin`
- `UVK5DigManager.exe`

## 生成组合补丁候选件
在项目目录打开 PowerShell，运行：

```powershell
python scripts\build_real_03q_patch_variants.py
```

当前会生成这些产物：

- `outputs/patched-0.3q-retune-only.packed.bin`
- `outputs/patched-0.3q-combined.packed.bin`
- `outputs/patched-0.3q-bench.packed.bin`
- `outputs/patched-UVK5DigManager.exe`
- `outputs/patched-UVK5DigManager-diagnostic.exe`
- `outputs/patched-UVK5DigManager-diagnostic-profile.json`
- `outputs/patched-UVK5DigManager-diagnostic-profile.txt`
- `outputs/patch-build-summary.json`

## 生成 DigiManager 单独补丁件
如果只想单独重建 DigiManager 补丁件，可以运行：

```powershell
python scripts\build_patched_digimanager.py
```

它会输出：

- `patched-UVK5DigManager.exe`
- `patched-UVK5DigManager-diagnostic.exe`
- `patched-UVK5DigManager-diagnostic-profile.json`
- `patched-digimanager-summary.json`

## 节拍对照分析
如果要比较当前 `FT4` 与 `FT8` 的发送节拍差异，运行：

```powershell
python scripts\analyze_ft4_timing.py
```

默认会读取：

- `samples/replay/ft4-replay.json`
- `samples/replay/ft8-replay.json`

输出：

- `logs/reverse/ft4-ft8-timing-report.json`
- `logs/reverse/ft4-ft8-timing-report.txt`

## 当前补丁分工
### 固件侧
当前固件补丁重点只剩：

- 尽量让数字模式下的外部改频不被立即写回

### DigiManager 侧
当前 DigiManager 补丁重点是：

- 让 `RecvProtocol == 4` 的 `FT4` 进入与 `RecvProtocol == 8` 尽可能相同的下发链

## 当前最重要的判断顺序
1. 先证明固定频点下的 `FT4` 是合格信号
2. 再讨论改频是否生效
3. 如果固定频点下的 `FT4` 仍然不合格，优先修 DigiManager 发送时序
4. 只有固定频点下已经合格后，才继续怀疑 retune 补丁影响时序

## 关键文件
- 逆向总报告：
  - [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
  - [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)
- 节拍分析：
  - [logs/reverse/ft4-ft8-timing-report.json](/F:/Codex/CEC固件改装FT4/logs/reverse/ft4-ft8-timing-report.json)
  - [logs/reverse/ft4-ft8-timing-report.txt](/F:/Codex/CEC固件改装FT4/logs/reverse/ft4-ft8-timing-report.txt)
- 固件 manifest：
  - [reverse/patches/patch-manifest.retune-only.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.retune-only.json)
  - [reverse/patches/patch-manifest.combined.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.combined.json)
- DigiManager manifest：
  - [reverse/patches/patch-manifest.digimanager-ft4-forward.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.digimanager-ft4-forward.json)

## 当前已经确认的事
- 真实 `0.3q` 固件可以稳定解包、补丁、重打包
- DigiManager 补丁可以稳定生成
- 新的 patched DigiManager 已经能让 `FT4` 起发射

## 当前还没确认的事
- `FT4` 是否已经是合格、可被正常解码的标准信号
- 加入 patched 固件后，改频是否会破坏已合格的 `FT4`

所以当前候选件的定位仍然是：

- 可重复生成
- 可控测试
- 还需要实机验证
