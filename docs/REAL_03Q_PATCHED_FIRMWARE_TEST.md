# Patched Real 0.3q Combined Test Guide

## Chinese / 中文
这份说明是给测试者看的。

你现在只测试这一条路线：

- 刷入 `patched-0.3q-bench.packed.bin`
- 替换成 `patched-UVK5DigManager.exe`

不要混用：

- 原版 DigiManager
- 旧 replay 路线
- 公开源码树自己编出来的固件
- 只换其中一边的半路线

## 0. 安全要求
只允许：

- 接假负载，或
- 断开天线

不要上空口，不要上星。

## 1. 先拿到这两个文件
请向维护者确认你拿到的是：

- `patched-0.3q-bench.packed.bin`
- `patched-UVK5DigManager.exe`

如果文件名不对，先停下，不要继续刷机。

## 2. 刷入 patched 固件
用你平时给 UV-K5 刷固件的网页或工具，刷入：

- `patched-0.3q-bench.packed.bin`

刷完以后，先不要发射，先检查这 3 件事：

1. 能正常开机
2. 菜单风格仍然像真实 `0.3q`
3. 数字模式入口仍然存在

如果这三件事有一件不对，就不要继续后面的测试。

## 3. 替换 DigiManager
把你原来使用的 `UVK5DigManager.exe` 先备份一份，然后用：

- `patched-UVK5DigManager.exe`

替换原来的 EXE。

替换后先只看两件事：

1. DigiManager 能否正常启动
2. 界面是否仍然基本正常

如果 EXE 启动失败，先不要继续测试。

## 4. 先做 FT8 回归
先确认补丁没有把原来能工作的路径弄坏：

1. 打开 patched DigiManager
2. 进入数字模式
3. 做一次 FT8 发射测试

你只要回答：

- FT8 还能不能发：`yes / no`

如果 FT8 已经坏了，后面的 FT4 和改频测试先不要继续。

## 5. 再做 FT4 发射测试
在确认 FT8 仍然正常后，再测试：

1. 进入 FT4
2. 做一次 FT4 发射尝试

你要观察的是：

- DigiManager 有没有反应
- 电台有没有进入 TX
- FT4 是不是终于像 FT8 一样真的开始发射

## 6. 再做数字模式改频测试
改频测试分两步：

### A. 空闲态改频
- 进入数字模式
- 不发射
- 修改频率
- 看电台频率有没有变化

### B. TX 态改频
- 在数字模式发射期间修改频率
- 看频率是：
  - 立刻稳定变化
  - 完全不变
  - 短暂变化后又被拉回

回报时请只用这三个词：

- `yes`
- `no`
- `temporary`

## 7. 按模板回报
回报时请用这个模板：

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

最少要回报这些内容：

- 开机版本
- 菜单截图
- DigiManager 主界面截图
- FT8 是否仍然正常
- FT4 是否开始能发射
- 空闲态改频是否生效
- TX 态改频是否生效
- 是否全程假负载或断天线

## English
This guide is for testers.

You now test only this combined route:

- flash `patched-0.3q-bench.packed.bin`
- replace the original EXE with `patched-UVK5DigManager.exe`

Do not mix it with:

- stock DigiManager
- old replay route
- public-source firmware builds
- one-sided half routes

### Safety
Test only with:

- a dummy load, or
- the antenna disconnected

Do not use this on-air.

### Test order
1. Flash `patched-0.3q-bench.packed.bin`
2. Confirm normal boot, normal menu, and digital-mode entry
3. Replace the EXE with `patched-UVK5DigManager.exe`
4. Confirm DigiManager still launches
5. Verify FT8 still works
6. Verify whether FT4 now starts transmitting
7. Verify retune in digital-mode idle and TX states
8. Report the result with:

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

