# Patched Real 0.3q Firmware Test

## 中文
这份教程是给测试者看的。

你的目标不是逆向，也不是编译固件。你只需要做 3 件事：

1. 刷入维护者给你的 **patched 真实 0.3q bench 固件**
2. 做 3 个最小测试
3. 按模板回报结果

## 先确认安全边界
这次测试只能这样做：

- 接假负载
- 或断开天线

不要直接上空口测试。

## 第一步：下载 patched 固件
你应该从维护者那里拿到这个文件：

- `patched-0.3q-bench.packed.bin`

如果你拿到的不是这个类型，而是别的旧 bench 固件、旧 replay 固件、或公开源码编出来的固件，就先不要刷。

## 第二步：刷机
用你平时刷 UV-K5 固件的**通用网页或工具**刷入：

- `patched-0.3q-bench.packed.bin`

刷完后先只看 3 件事：

1. 能不能正常开机
2. 菜单是不是还像真实 `0.3q`
3. 数字模式入口是不是还在

如果这 3 项有任何一项不对，就先停止，不要继续做发射测试。

## 第三步：先做 FT8 回归
先不要急着测 FT4。

先确认：

- 进入数字模式
- FT8 是否还像以前一样能正常发射

如果 FT8 都已经不正常了，后面的 FT4 测试没有意义。

## 第四步：再做数字模式改频测试
在数字模式里做两种观察：

1. **空闲态改频**
   - 不发射
   - 修改频率
   - 看电台频率有没有变化

2. **TX 态改频**
   - 在发射时修改频率
   - 看频率是不是持续生效、短暂生效，还是完全无效

记录结果时只需要用这些词：

- `yes`
- `no`
- `temporary`

含义：

- `yes`：改了就真的生效
- `no`：完全不变
- `temporary`：会短暂变化，但又被拉回

## 第五步：最后做 FT4 发射测试
确认 FT8 没坏以后，再测：

- FT4 是否终于开始真正发射

如果 FT4 仍然不发，请记录：

- DigiManager 是否有反应
- 电台是否有任何发射迹象
- 频率是否变化

## 第六步：按模板回报
请按这份模板回报：

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

至少要回报这些：

- 开机显示
- 菜单是否正常
- 数字模式是否存在
- FT8 是否还能发
- FT4 是否开始能发
- 空闲态改频是否生效
- TX 态改频是否生效
- 是否全程假负载或断开天线

## English
This guide is for testers.

Your job is not to reverse-engineer or compile anything. Only do 3 things:

1. flash the **patched real-0.3q bench firmware**
2. run the 3 minimum tests
3. report the result with the template

## Safety
Use only:

- a dummy load
- or a disconnected antenna

Do not use this firmware on-air.

## Test order
1. Flash `patched-0.3q-bench.packed.bin`
2. Confirm:
   - normal boot
   - menu still looks like real `0.3q`
   - digital-mode entry still exists
3. Verify FT8 still transmits
4. Verify digital-mode retune in idle and TX
5. Verify FT4 finally transmits
6. Report using:

- [REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)
