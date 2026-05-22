# Patched Real 0.3q Combined Test Guide

## 这份文档给谁看
这份文档是给测试者看的。

你现在只测试这一条主路线：

- 刷入 `patched-0.3q-bench.packed.bin`
- 替换成 `patched-UVK5DigManager.exe`

如果 `FT4` 失败，不是直接结束，而是继续做文档里写好的两组单端对照测试。

## 0. 安全要求
只允许：

- 接假负载，或
- 断开天线

不要上空口，不要上星。

## 1. 先准备这 4 样东西
开始前，请先确认你手里有下面 4 样东西：

1. `patched-0.3q-bench.packed.bin`
2. `patched-UVK5DigManager.exe`
3. 一个原版可工作的 `UVK5DigManager.exe`
4. 一个原版可工作的真实 `0.3q` 固件

顺序不要乱，后面失败预案要靠这 4 样东西做单端对照。

## 2. 先测组合补丁主路径
### 第一步：刷入 patched 固件
用你平时给 UV-K5 刷固件的网页或工具，刷入：

- `patched-0.3q-bench.packed.bin`

刷完后先检查：

1. 能正常开机
2. 菜单风格仍然像真实 `0.3q`
3. 数字模式入口仍然存在

如果这 3 件事有任何一件不对，就不要继续发射测试，直接回报。

### 第二步：替换 DigiManager
把你原来使用的 `UVK5DigManager.exe` 先备份一份，再用：

- `patched-UVK5DigManager.exe`

替换原来的 EXE。

替换后先检查：

1. DigiManager 能否正常启动
2. 主界面是否基本正常

如果 patched DigiManager 启动失败，也先不要继续发射测试。

### 第三步：FT8 回归
先做一次 FT8 测试，确认原本已知可用的路径没坏。

你只需要记录：

- FT8 是否还能发射：`yes / no`

如果 FT8 已经坏了，不要跳到 FT4，直接按模板回报。

### 第四步：FT4 发射测试
在确认 FT8 仍然正常后，再测试：

1. 进入 FT4
2. 做一次 FT4 发射尝试

你要观察：

- DigiManager 有没有反应
- 电台有没有进入 TX
- FT4 是否终于像 FT8 一样真正开始发射

### 第五步：数字模式改频测试
改频测试分两步：

#### A. 空闲态改频
- 进入数字模式
- 不发射
- 修改频率
- 看电台频率有没有变化

#### B. TX 态改频
- 在数字模式发射期间修改频率
- 看频率是：
  - 稳定变化
  - 完全不变
  - 短暂变化后又被拉回

回报时请只用这三个词：

- `yes`
- `no`
- `temporary`

## 3. 如果 FT4 还是不能发射，请继续做这 3 组补充测试
这里的目标不是让你自己判断原因，而是把问题快速缩到：

- patched 固件
- patched DigiManager
- 或两边组合

### 3.1 先确认 FT8 是否仍然正常
这是第一分流点：

- 如果 FT8 也坏了：优先说明当前组合补丁破坏了原有已知可用路径
- 如果 FT8 正常、FT4 失败：继续做下面两组对照

### 3.2 对照组 A：patched 固件 + 原版 DigiManager
按这个顺序做：

1. 保留当前刷好的 `patched-0.3q-bench.packed.bin`
2. 把 DigiManager 换回原版可工作的 EXE
3. 再做一次：
   - FT8 测试
   - FT4 发射测试
   - 数字模式改频测试

这组的目标是看：

- 固件补丁单独存在时，行为有没有明显变化

### 3.3 对照组 B：原版固件 + patched DigiManager
按这个顺序做：

1. 把电台刷回原版可工作的真实 `0.3q` 固件
2. 再把 DigiManager 换回 `patched-UVK5DigManager.exe`
3. 再做一次：
   - FT8 测试
   - FT4 发射测试
   - 数字模式改频测试

这组的目标是看：

- DigiManager 补丁单独存在时，FT4 是否开始前进了一步

## 4. 最简单的失败判断表
测试者不用自己下技术结论，但可以参考这张表理解为什么还要做补充测试：

| 现象 | 更值得优先怀疑哪边 |
| --- | --- |
| FT8 也坏了 | 当前组合补丁整体破坏了原有已知可用路径 |
| FT8 正常，FT4 失败，原版固件 + patched DigiManager 也失败 | DigiManager 的 FT4 forward 补丁仍然不够 |
| FT8 正常，FT4 失败，但 patched 固件 + 原版 DigiManager 行为变化明显 | 固件侧补丁影响到了数字模式路径 |
| 只有组合补丁失败，两个单端对照都不明显坏 | 更像双端组合交互问题 |

## 5. 最后按模板回报
回报时请使用这个模板：

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

至少要回报这些内容：

- 开机版本
- 菜单截图
- DigiManager 主界面截图
- 组合补丁下：
  - FT8 是否正常
  - FT4 是否开始能发射
  - 空闲态改频是否生效
  - TX 态改频是否生效
- 对照组 A：`patched 固件 + 原版 DigiManager`
  - FT8 是否正常
  - FT4 是否起发射
  - 改频是否生效
- 对照组 B：`原版固件 + patched DigiManager`
  - FT8 是否正常
  - FT4 是否起发射
  - 改频是否生效
- 是否全程假负载或断天线

