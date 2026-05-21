# linear-k6-ft4

## 当前公开路线 / Current Public Route
当前仓库只保留这一条主线：

- 真实 `0.3q` 固件二进制逆向
- 基于真实 `0.3q` 的补丁工作流
- patched 固件的实机台架测试

不要再走这些旧路线：

- 旧 replay 测试
- 公开源码树直接编译固件
- 旧 bench 固件刷写流程

The repository now only tracks this route:

- reversing the real `0.3q` firmware binary
- building patch manifests against the real binary
- bench testing patched firmware on a real radio

Do not use the old replay route, the public-source build route, or the old bench firmware route anymore.

## 现在仓库里有什么 / What Exists Right Now
当前已经完成：

- 真实 `cec_0.3QB.packed.bin` 的解包、字符串锚点和补丁工作区生成
- `UVK5DigManager.exe` 的静态分析
- patch manifest 变体生成
- 4 个**结构正确、可刷写的候选固件文件**

当前输出位置：

- 逆向地图：
  - [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
  - [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)
- 补丁工作区：
  - [logs/reverse/patch-workspace.json](/F:/Codex/CEC固件改装FT4/logs/reverse/patch-workspace.json)
  - [logs/reverse/patch-workspace.md](/F:/Codex/CEC固件改装FT4/logs/reverse/patch-workspace.md)
- manifest：
  - [reverse/patches/patch-manifest.retune-only.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.retune-only.json)
  - [reverse/patches/patch-manifest.ft4-only.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.ft4-only.json)
  - [reverse/patches/patch-manifest.combined.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.combined.json)
- 固件候选件文件名：
  - `patched-0.3q-retune-only.packed.bin`
  - `patched-0.3q-ft4-only.packed.bin`
  - `patched-0.3q-combined.packed.bin`
  - `patched-0.3q-bench.packed.bin`

说明：

- 这些候选件默认不直接进 Git 仓库
- 测试者应从维护者那里拿到指定的固件文件
- 维护者本地可在 `outputs/patch-build-summary.json` 查看 SHA256 与文件映射

## 重要状态说明 / Important Status
这一步必须说清楚：

- 这些 `patched-0.3q-*.packed.bin` 文件现在已经**结构正确、可刷写**
- 但它们当前仍然是**补丁候选件**
- 其中已经确认的一条新结论是：
  - DigiManager 的改频路径仍然存在
  - `FT4` 的第一道门控很可能发生在 **PC 侧**，不是纯固件侧

所以当前这些固件候选件的用途是：

- 验证补丁链是否稳定
- 验证刷写、开机、菜单、数字模式入口是否保持真实 `0.3q` 风格
- 为下一步真正的功能性补丁做台架准备

They are flashable candidate builds, but they are not yet a proven “FT4 fixed” firmware.

## 如果你是测试者 / If You Are A Tester
如果维护者已经明确让你刷某一个 patched 固件，请只看这两份文档：

- [docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

你的工作只有：

1. 刷入维护者指定的 patched 固件
2. 断开天线或接假负载
3. 确认开机、菜单和数字模式入口是否正常
4. 做 FT8 / FT4 / 改频最小测试
5. 按模板回报

## 如果你是维护者 / If You Are Maintaining The Patch
维护者主入口：

- [docs/REAL_03Q_PATCH_WORKFLOW.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)
- [docs/REAL_03Q_REVERSE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_REVERSE_QUICKSTART.md)

当前最重要的结论是：

- `retune` 仍应继续追真实固件里的数字模式锁频点
- `FT4 TX gate` 现在更像 DigiManager 侧的前置门控

## 安全边界 / Safety Boundary
所有 patched 固件测试都只允许：

- 假负载
- 或断开天线

不要把这些固件当成量产固件，也不要直接上空口或上星。
