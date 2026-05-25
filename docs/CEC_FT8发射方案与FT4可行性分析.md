# CEC 0.3q 的 FT8 发射方案与 FT4 可行性分析

## 这份文档解决什么问题
这份文档不是给普通测试者看的，而是给后续继续参与研发的人看的。

它回答 3 个问题：

1. 作者真实 `CEC 0.3q` 固件里的 `FT8`，更像是走什么发射方案
2. `FT4` 的正式发射制式和 `FT8` 有什么关键差异
3. `K6/BK4819` 的 `FSK` 能力结合 CEC 当前路线，究竟能不能做出**合格 FT4**

## 先说结论
当前最合理的结论是：

- 作者现有的 `FT8` 发射链**大概率不是**直接复用 `BK4819` 的 packet `FSK` 硬件发射器
- 更像是：
  - `DigiManager` / 主机侧准备数字业务节拍和发送数据
  - 固件侧走一条 CEC 私有的“洁净数字发射底座”
  - `BK4819` 主要承担干净的射频/基带输出，而不是自己按 1200/2400 packet `FSK` 协议发完整 `FT8`
- 因此：
  - **“让 BK4819 packet FSK 直接承担 FT4”** 这条路大概率不成立
  - **“保留 CEC 的洁净数字发射思路，但为 FT4 重新做正确的发送节拍/分帧/定时”** 这条路原则上可行

## 我们为什么开始怀疑主线走偏了
最新实机结果已经说明：

- 用新的 `patched DigiManager`
- 无论配 `原版固件` 还是 `patched 固件`
- `FT4` 都已经能起发射

但新的关键问题是：

- 发出来的信号节拍**明显慢于标准 FT4**

这说明当前主矛盾已经不是：

- `FT4` 能不能进发射链

而是：

- 现在这条链发出来的东西**是不是合格 FT4**

这也是为什么主线要从“优先猜固件锁频”转成“先理解作者的 FT8 真实发射方案”。

## 用 capstone 看真实 0.3q，能看到什么
我们现在已经有一套脚本会直接对真实 `cec_0.3QB.packed.bin` 解包后做 `capstone` 反汇编摘要：

- [scripts/analyze_cec_ft8_scheme.py](/F:/Codex/CEC固件改装FT4/scripts/analyze_cec_ft8_scheme.py)
- [src/sat_bridge/cec_ft8_scheme_tools.py](/F:/Codex/CEC固件改装FT4/src/sat_bridge/cec_ft8_scheme_tools.py)

输出位置：

- [logs/reverse/cec-ft8-ft4-feasibility.json](/F:/Codex/CEC固件改装FT4/logs/reverse/cec-ft8-ft4-feasibility.json)
- [logs/reverse/cec-ft8-ft4-feasibility.md](/F:/Codex/CEC固件改装FT4/logs/reverse/cec-ft8-ft4-feasibility.md)

这轮 `capstone` 的价值，不是“完整恢复源码”，而是：

- 确认真实 `0.3q` 里和 `DIG.M / DIG+ / LOCK / FREQ` 相关的执行锚点确实存在
- 确认外部改频命令 `0x32` 在真实固件里确实有候选入口
- 给出“这更像菜单/UI/命令入口，还是像真正的数字发射链”的上下文线索

当前这一步**还不足以单靠固件反汇编就还原完整 FT8 发射器**，但已经足够帮助我们判断：

- 真实系统不是一条“公开源码树重编译就能得到”的简单路线
- 也不能再把问题粗暴地全扔回“只改固件”

## 公开源码里的 BK4819 packet FSK 到底是什么
公开源码虽然不是作者真实数字模式源码，但它仍然能告诉我们 **BK4819 硬件 packet FSK 的能力边界**。

关键参考文件：

- [uvk5cec-0.3q/app/aircopy.c](/F:/Codex/CEC固件改装FT4/uvk5cec-0.3q/app/aircopy.c)
- [uvk5cec-0.3q/driver/bk4819.c](/F:/Codex/CEC固件改装FT4/uvk5cec-0.3q/driver/bk4819.c)
- [uvk5cec-0.3q/driver/bk4819.h](/F:/Codex/CEC固件改装FT4/uvk5cec-0.3q/driver/bk4819.h)
- [uvk5cec-0.3q/radio.c](/F:/Codex/CEC固件改装FT4/uvk5cec-0.3q/radio.c)

从里面可以直接看出：

### 1. AIRCOPY 走的是 packet FSK
`AIRCOPY_SendMessage()` 明确做的是：

- 准备固定大小缓冲区
- 算 CRC
- 调 `RADIO_SetTxParameters()`
- 调 `BK4819_SendFSKData(g_FSK_Buffer)`

而 `g_FSK_Buffer` 是：

- `uint16_t g_FSK_Buffer[36]`

也就是：

- 固定 36 个 16-bit word
- 即固定 72 字节 packet

### 2. BK4819 的公开 FSK 配置是固定 packet 模式
公开 `BK4819_SetupAircopy()` 里写死了这些关键信息：

- `REG_72 = 0x3065`
  - 注释里直接写的是 `Tone2 baudrate 1200`
- `REG_58 = 0x00C1`
  - 注释里直接写的是 `FSK Enable`
- `REG_5D = 0x4700`
  - 注释里直接写的是 `FSK Data Length 72 Bytes`

这说明公开 `BK4819` 的这条 `FSK` 链，本质上是：

- 固定速率
- 固定包长
- 带 FIFO / preamble / CRC 语义

它更像：

- 空口拷贝
- 窄带 packet 数据链

而不像：

- `FT8/FT4` 这种要求特定符号节拍、多音调、严格时序控制的标准弱信号模式

## FT4 的正式制式，为什么不能只“放通一下”
根据 WSJT-X 作者的协议说明，`FT4` 的关键点不是“只是消息内容和 FT8 不一样”，而是：

- `FT4` 属于更快的 4-tone / 4-GFSK 家族
- 它的 T/R 周期比 `FT8` 更短
- 它的发送时间更短
- 它的符号节拍和发送组织方式与 `FT8` 不同

参考：

- [FT4 and FT8 Communication Protocols](https://wsjt.sourceforge.io/FT4_FT8_QEX.pdf)

这就意味着：

- 让 `protocol 4` 仅仅复用 `protocol 8` 的门控
- 只解决“能不能起发射”

并**不能自动得到合格 FT4**。

当前实机已经正好验证了这一点：

- `FT4` 起发射了
- 但节拍明显比标准 FT4 慢

## 为什么现在更怀疑 DigiManager 的发送时序，而不是先怪固件
这是本轮路线校正里最关键的一步。

我们已经看到：

1. `patched DigiManager + 原版固件`
   - `FT4` 能起发射
   - 但节拍慢
2. `patched DigiManager + patched 固件`
   - `FT4` 也能起发射
   - 节拍同样慢

也就是说：

- 慢节拍现象同时出现在**原版固件**和 **patched 固件**

这对判断非常重要。

因为它说明：

- 至少当前第一嫌疑对象，不该再是 patched 固件 retune 补丁
- 而更像是 `patched DigiManager` 把 `FT4` 塞进了一个本来给 `FT8` 用的发送时序器

换句话说：

- **现在最值得优先修的是 DigiManager 的 FT4 发送时序**
- 不是先继续扩大固件 retune 补丁

## 所以：K6 的 FSK + CEC 方案到底能不能做 FT4
这个问题要拆成两个版本回答。

### 版本 A：如果“FSK”指的是 BK4819 的 packet FSK 硬件链
那我的判断是：

- **大概率不能直接实现合格 FT4**

原因不是它“完全发不出去”，而是：

- 公开可见的 `BK4819_SendFSKData` 方案是 packet FSK
- 它的速率、包结构、节拍方式都更像 1200/2400 baud 的数据包链
- 这和 FT4 所需的发送时序不是同一类问题

所以这条思路如果硬推，最可能得到的是：

- 能发出某种数字样子的东西
- 但不是标准可解码 FT4

### 版本 B：如果“结合 CEC 方案”指的是保留洁净数字注入思路
那我的判断是：

- **原则上可以**

但前提是：

- 不能只依赖 BK4819 packet FSK 硬件链
- 必须为 FT4 单独做正确的发送时序 / 分帧 / 节拍控制
- 然后仍然沿用 CEC 当前“避免 K5 模拟音频缺陷”的洁净发送底座

也就是说，真正可行的路线不是：

- “让 BK4819 的 packet FSK 自己发 FT4”

而是：

- “让 DigiManager / CEC 的数字发送链会发**标准 FT4**，BK4819 只负责干净地把这条数字发射链送上空口”

## 这对后续研发意味着什么
这轮分析后的主线应该改成：

1. **先把 fixed-frequency FT4 做成可被第二接收机 / 第二套 WSJT-X 正常解码**
   - 优先使用：
     - `patched DigiManager + 原版固件`
2. **如果 fixed-frequency FT4 仍然不合格**
   - 主攻 DigiManager 的发送时序
   - 不是先继续深挖固件 retune
3. **只有 fixed-frequency FT4 已合格**
   - 才把 `patched 固件` 接回来
   - 再测数字模式改频是否会破坏合格 FT4

## 一句话总结
当前最合理的总判断是：

- **作者真实 CEC 0.3q 的 FT8 发射方案，大概率不是“直接用 BK4819 packet FSK 发 FT8”**
- **BK4819 的 packet FSK 能力本身不太像合格 FT4 的正确承载方式**
- **但保留 CEC 的洁净数字注入思路，重新做 FT4 专用发送节拍，这条路线是有希望成立的**

