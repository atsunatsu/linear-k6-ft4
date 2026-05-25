# WSJT-X 到 DigiManager 的 FT4 数据流分析

## 这份文档回答什么问题
这份文档只回答一个很具体的问题：

- `WSJT-X` 输出给 `DigiManager` 的 `FT4` 数据，到底是不是真实 `FT4` 语义的数据？
- 如果是，问题又是在什么地方被“压平”或“送错”了？

它讨论的是：

- `WSJT-X -> DigiManager` 的上游数据流
- `DigiManager` 在把数据交给固件前，怎么重新组织这些数据

它**不能单独证明**：

- 电台空口已经发出合格 `FT4`

## 当前结论
当前最合理的判断是：

- `WSJT-X` 给 `DigiManager` 的上游 `FT4` 数据**不是假的**
- `FT4` 和 `FT8` 在 `5957` 端口上的模式包、长度字节、局部字段都明显不同
- 但 `DigiManager` 原始 sender 会把这些差异大量压进同一条发送路径
- 当前 replay 里的业务包平均只有 `8` 到 `9` 个非零字节，更像**稀疏控制帧**，不像“完整音调序列”

换句话说：

- 问题不是 `WSJT-X` 没给出真实 `FT4`
- 而是 `DigiManager -> 固件` 这一步，没有把 `FT4` 以正确的发送组织方式交给固件

## 我们怎么分析
分析入口脚本：

- [scripts/analyze_wsjtx_digimanager_flow.py](/F:/Codex/CEC固件改装FT4/scripts/analyze_wsjtx_digimanager_flow.py)

核心分析模块：

- [src/sat_bridge/wsjtx_digimanager_flow_tools.py](/F:/Codex/CEC固件改装FT4/src/sat_bridge/wsjtx_digimanager_flow_tools.py)

默认输入样本：

- [samples/replay/ft4-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft4-replay.json)
- [samples/replay/ft8-replay.json](/F:/Codex/CEC固件改装FT4/samples/replay/ft8-replay.json)

默认输出报告：

- [logs/reverse/wsjtx-digimanager-flow.json](/F:/Codex/CEC固件改装FT4/logs/reverse/wsjtx-digimanager-flow.json)
- [logs/reverse/wsjtx-digimanager-flow.md](/F:/Codex/CEC固件改装FT4/logs/reverse/wsjtx-digimanager-flow.md)

## 当前抓包里能直接看到什么
在 `5957` 的 replay 样本中，至少已经能稳定看到：

- `59 57 04 00`：`FT4` 模式包
- `59 57 08 00`：`FT8` 模式包
- `59 57 f4 00`：业务包

其中最关键的差异是：

- `FT4` 的长度字节是 `0x67`，也就是 `103`
- `FT8` 的长度字节是 `0x4f`，也就是 `79`

这说明在 DigiManager 收到数据之前：

- `FT4` 和 `FT8` 已经不是同一种东西
- `FT4` 至少在长度和模式标记层面是独立存在的

## 业务包为什么说明“这更像控制帧”
当前样本里，`business_packet` 的统计结果非常稳定：

- `FT4` 业务包平均非零字节数约 `8.70`
- `FT8` 业务包平均非零字节数约 `8.70`

热点位置主要集中在：

- `0..2`
- `244..247`
- `254..255`

这很不像“完整音调序列”或“完整调制流”，更像：

- 固定头
- 少量尾部参数
- 少量模式/控制字段

这条证据很重要，因为它说明：

- DigiManager 更像是在把 `WSJT-X` 的数字业务整理成一类**控制/参数帧**
- 而不是直接把一长串已经完成调制的 `FT4` 音调流原封不动推给固件

## DigiManager 原始 sender 为什么可疑
当前逆向已经确认 DigiManager 的核心 sender 路径是：

- `UDPDataCheck`
- `SetDigitalData2`
- `SetCECMessage2(command 0x35)`

其中 `SetDigitalData2` 原始头字段组织方式很关键：

- `byte[0..1]`：副频
- `byte[2]`：固定写 `0`
- `byte[3]`：固定写 `0`
- `byte[4]`：长度

这意味着原始路径下：

- `FT4` 头字段大概是：`05 dc 00 00 67`
- `FT8` 头字段大概是：`05 dc 00 00 4f`

也就是说：

- 上游 `FT4/FT8` 的大量差异，在 sender 头字段这里几乎被压到只剩“长度不同”

## 一个很关键的新判断：DigiManager 这里不像真正的“发送节拍器”
进一步拆 `UDPDataCheck -> SetDigitalData2 -> SetCECMessage2` 后，可以看到：

- `UDPDataCheck` 只是识别协议、提取字段、组一个 256 字节缓冲区
- `SetDigitalData2` 只是组 5 字节 sender 头
- `SetCECMessage2` 只是把整包重新排好后立即写串口

也就是说，当前可见的 DigiManager sender 链更像：

- **组包器**
- **串口写出器**

而不像一个内部自己带复杂符号级定时的“发送节拍器”。

这条结论不能直接证明固件没问题，但它很重要，因为它说明：

- 我们需要继续检查 DigiManager 的发送组织方式
- 但也不能再简单假设“所有慢节拍都一定是 DigiManager 本机定时器造成的”

## 当前 patched DigiManager 修到了哪一步
当前补丁已经做了两类事情：

1. 让 `protocol 4` 能复用现有 digital 下发门
2. 让 sender 头字段至少保留更多差异

现在的头字段不再是：

- `05 dc 00 00 67`

而是更接近：

- `05 dc 67 00 67`

这仍然不是“已经证明合格 FT4”，但它至少说明：

- 我们不再把 `FT4` 完全压成“和 `FT8` 只有长度不同”的同一路径包

## 这份分析能证明什么，不能证明什么
### 能证明的
- `WSJT-X -> DigiManager` 这段上游流量已经具有真实 `FT4` 语义差异
- `DigiManager` 原始 sender 确实会把这些差异压扁
- 当前补丁已经开始保留更多 `FT4` 身份信息
- DigiManager 当前可见 sender 链更像“组包 + 串口写出”，不像完整调制器

### 不能证明的
- patched DigiManager 已经发出合格 `FT4`
- 空口信号已经符合规范
- 固件完全没有责任

## 这对后续研发意味着什么
当前最合理的主线是：

1. 继续优先修 DigiManager 的发送组织方式
2. 不再怀疑 `WSJT-X` 输出本身
3. 同时保持一个开放判断：
   - 如果 DigiManager sender 只是在发控制帧，那固件如何解释 `command 0x35` 也仍然值得继续深挖

一句话总结：

- 上游 `FT4` 已经是真的
- DigiManager 原始 sender 会把它压平
- 当前更像是 `DigiManager` 没把它正确送成标准 `FT4`
- 但 sender 链本身又不像完整调制器，所以后面仍要留意固件对 `command 0x35` 的解释方式
