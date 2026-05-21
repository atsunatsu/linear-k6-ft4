# Patched Real 0.3q Firmware Test

## 中文
这份说明是给测试者看的。

你的任务不是逆向，不是编译，也不是判断补丁逻辑。你只需要：

1. 刷入维护者指定的 patched 固件
2. 在假负载或断天线条件下做最小测试
3. 按模板回报结果

## 先确认安全边界
这次测试只允许：

- 接假负载
- 或断开天线

不要直接上空口。

## 先确认你拿到的是哪个文件
维护者可能会发给你下面 4 个文件里的一个：

- `patched-0.3q-retune-only.packed.bin`
- `patched-0.3q-ft4-only.packed.bin`
- `patched-0.3q-combined.packed.bin`
- `patched-0.3q-bench.packed.bin`

其中：

- `patched-0.3q-bench.packed.bin` 目前等于 `combined`
- 它们现在都属于 **patched 候选件**
- 不是量产固件

## 第一步：刷机
用你平时给 UV-K5 刷固件的通用网页或工具，刷入维护者指定的那一个 `.packed.bin` 文件。

刷完后先不要急着发射，只看这 3 件事：

1. 能不能正常开机
2. 菜单是不是仍然像真实 `0.3q`
3. 数字模式入口还在不在

如果这 3 件事里有任意一件不对，就先停，不要继续发射测试。

## 第二步：做 FT8 回归
先确认：

- DigiManager 仍然能和电台正常配合
- FT8 是否还像以前一样能走原有数字发射链

如果 FT8 都坏了，后面的 FT4 和改频测试没有意义。

## 第三步：做数字模式改频测试
在数字模式里做两种观察：

1. 空闲态改频
   - 不发射
   - 修改频率
   - 看电台频率有没有变化

2. TX 态改频
   - 发射时修改频率
   - 看频率是持续生效、短暂生效，还是完全无效

回报时只需要用这 3 个词：

- `yes`
- `no`
- `temporary`

含义：

- `yes`：改了就真的生效
- `no`：完全不生效
- `temporary`：会短暂变化，但又被拉回

## 第四步：做 FT4 发射测试
在确认 FT8 没坏以后，再测：

- FT4 是否开始真正进入发射

如果 FT4 仍然不发，请记录：

- DigiManager 是否有反应
- 电台是否有任何发射迹象
- 频率是否变化

## 第五步：按模板回报
请按这个模板回报：

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

至少要回报这些：

- 刷的是哪个固件文件
- 开机版本显示
- 菜单是否正常
- 数字模式是否存在
- FT8 是否还能发
- FT4 是否开始能发
- 空闲态改频是否生效
- TX 态改频是否生效
- 是否全程假负载或断开天线

## English
This guide is for testers.

Your job is simple:

1. flash the patched firmware file chosen by the maintainer
2. test only on a dummy load or with the antenna disconnected
3. report the result with the template

Test order:

1. confirm normal boot, normal menu, and digital-mode entry
2. verify FT8 still works
3. verify retune behavior in idle and TX
4. verify whether FT4 starts to transmit
5. report the result using:

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)
