# linear-k6-ft4

## 当前测试入口 / Current Public Test Route
当前公开主线已经切到：

- **真实 `0.3q` 固件二进制逆向补丁**
- **patched 真实 `0.3q` bench 固件实机测试**

现在不要再走下面这些旧路线：

- 旧的 replay 发布测试
- 公开源码树直接编译固件
- 旧的 bench 固件刷写流程

The current public route is now:

- **reverse patching the real `0.3q` binary**
- **real-device testing of a patched real-0.3q bench firmware**

Do not use the old replay route, the public-source build route, or the old bench firmware route anymore.

## 如果你是测试者 / If You Are A Tester
你现在只需要做这一条路：

1. 从维护者给你的位置下载 **patched 真实 0.3q bench 固件**
2. 按实机测试教程刷机
3. 做 3 个最小测试：
   - FT8 是否仍能正常发射
   - FT4 是否开始能真正发射
   - 数字模式里改频是否生效
4. 按模板回报结果

先看这里：

- [docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

If you are a tester, start here:

- [docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

## 如果你是维护者 / If You Are Maintaining The Patch
这条线现在的目标不是恢复完整源码，而是尽快做出一个可台架验证的 **patched 真实 0.3q bench 固件**：

- 放开数字模式下的锁频
- 让 FT4 沿现有数字发射链进入发射

维护者先看：

- [docs/REAL_03Q_PATCH_WORKFLOW.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)
- [docs/REAL_03Q_REVERSE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_REVERSE_QUICKSTART.md)

Maintainers should start here:

- [docs/REAL_03Q_PATCH_WORKFLOW.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)
- [docs/REAL_03Q_REVERSE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_REVERSE_QUICKSTART.md)

## 现在仓库里有哪些关键产物 / Key Repo Outputs
- 逆向地图：
  - `logs/reverse/reverse-map.json`
  - `logs/reverse/reverse-map.md`
- 补丁工作区生成脚本：
  - `scripts/build_real_03q_patch_workspace.py`
- 补丁应用脚本：
  - `scripts/apply_real_03q_patch.py`
- 实机测试教程：
  - `docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md`

## 安全边界 / Safety Boundary
当前 patched 固件只允许：

- 假负载
- 或断开天线的台架验证

不要把它当成量产固件，也不要直接上星。

The patched firmware is for bench validation only:

- use a dummy load
- or disconnect the antenna

Do not treat it as a production firmware and do not use it on-air yet.
