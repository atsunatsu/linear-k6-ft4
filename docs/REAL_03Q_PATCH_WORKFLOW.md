# Real 0.3q Patch Workflow

## 中文
这份文档是给维护者看的，不是给普通测试者看的。

目标只有一个：

- 从真实 `cec_0.3QB.packed.bin` 出发，做出一个 **patched 真实 0.3q bench 固件**

这个 patched 固件要用于台架验证两件事：

1. 数字模式下外部改频是否终于能生效
2. FT4 是否终于能沿现有数字发射链真正进入发射

## 第一步：准备真实输入
把下面两个文件放进工作区根目录，或者放到 `reverse/input` 对应目录：

- `cec_0.3QB.packed.bin`
- `UVK5DigManager.exe`

## 第二步：先生成补丁工作区
在项目目录打开 `PowerShell`，运行：

```powershell
python scripts\build_real_03q_patch_workspace.py
```

这一步会生成：

- `logs/reverse/patch-workspace.json`
- `logs/reverse/patch-workspace.md`
- `reverse/patches/real-03q-bench.template.json`

重点看：

- `DIG.M`
- `DIG+`
- `LOCK`
- `FREQ:%u.%05u`

以及它们周围的：

- `window_hex`
- `raw_offset_references`

## 第三步：填写补丁清单
打开：

- `reverse/patches/real-03q-bench.template.json`

这里已经预留了 3 类补丁位：

1. `digital_mode_retune_gate_candidate`
2. `ft4_tx_gate_candidate`
3. `patched_version_banner`

规则固定为：

- 只有真正定位清楚的补丁才把 `enabled` 改成 `true`
- `replace_bytes` 必须填写：
  - `offset`
  - `expect_hex`
  - `replace_hex`
- `replace_ascii` 只能做同长度替换

## 第四步：生成 patched 固件
当补丁清单填好后，在项目目录运行：

```powershell
python scripts\apply_real_03q_patch.py reverse\patches\real-03q-bench.template.json
```

输出文件会写到：

- `outputs/patched-0.3q-bench.packed.bin`

这一步会做这些检查：

- 原始固件 SHA256 是否和 manifest 一致
- 原始字节是否和 `expect_hex` 一致
- 至少有一个补丁是启用状态

## 第五步：把 patched 固件交给测试者
测试者不要自己编译，不要自己改 manifest。

测试者只需要拿到：

- `patched-0.3q-bench.packed.bin`

然后按：

- [REAL_03Q_PATCHED_FIRMWARE_TEST.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)

去刷机和测试。

## 当前工作边界
这条路线当前不承诺：

- 恢复完整源码
- 自动化 patch 发现
- 一步到位找到锁频点
- 一步到位恢复 FT4 全功能

当前目标是：

- 建立稳定的真实 `0.3q` 补丁链
- 快速做出可反复台架验证的 patched bench 固件

## English
This document is for maintainers, not for general testers.

The goal is simple:

- start from the real `cec_0.3QB.packed.bin`
- build a **patched real-0.3q bench firmware**

Use this patched firmware to validate:

1. whether digital-mode retune is finally honored
2. whether FT4 can finally enter the existing digital TX path

### Steps
1. Place the real firmware and DigiManager binary in the workspace.
2. Run:

```powershell
python scripts\build_real_03q_patch_workspace.py
```

3. Review:

- `logs/reverse/patch-workspace.json`
- `logs/reverse/patch-workspace.md`
- `reverse/patches/real-03q-bench.template.json`

4. Fill in the patch manifest with real offsets and byte replacements.
5. Run:

```powershell
python scripts\apply_real_03q_patch.py reverse\patches\real-03q-bench.template.json
```

6. The patched firmware will be written to:

- `outputs/patched-0.3q-bench.packed.bin`
