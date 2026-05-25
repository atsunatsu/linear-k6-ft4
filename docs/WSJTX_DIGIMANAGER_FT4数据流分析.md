# WSJT-X 到 DigiManager 的 FT4 数据流分析

## 这份文档解决什么问题
这份文档只回答一个很具体的问题：

- `WSJT-X` 输出给 `DigiManager` 的 `FT4` 数据，到底是不是真实 `FT4` 语义的数据？
- 如果是，问题又是在哪一层被“压平”或“送错”了？

这份文档不是空口合规证明。  
它讨论的是：

- `WSJT-X -> DigiManager` 的上游数据流
- `DigiManager` 在进入固件前的重组方式

它不能单独证明：

- 电台空口已经发出合格 `FT4`

## 当前结论
当前最合理的判断是：

- `WSJT-X` 给 `DigiManager` 的上游 `FT4` 数据**不是假的**
- `FT4` 和 `FT8` 在 `5957` 端口上的模式包、长度字节、局部字段都明显不同
- 问题更像出在 `DigiManager` 下发给固件前，把这些差异**压进了同一条 sender 路径**

换句话说：

- 问题不是 `WSJT-X` 没有给出真实 `FT4`
- 而是 `DigiManager -> 固件` 这一步，没有把 `FT4` 按合适的节拍和身份信息送进去

## 我们是怎么分析的
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

## DigiManager 原始 sender 为什么可疑
当前逆向已经确认 DigiManager 的核心 sender 入口是：

- `UDPDataCheck`
- `SetDigitalData2`
- `SetCECMessage2(command 0x35)`

其中 `SetDigitalData2` 原始头字段组织方式非常关键：

- `byte[0..1]`：副频
- `byte[2]`：固定写 `0`
- `byte[3]`：固定写 `0`
- `byte[4]`：长度

这意味着原始路径下：

- `FT4` 最终头字段大概是：`05 dc 00 00 67`
- `FT8` 最终头字段大概是：`05 dc 00 00 4f`

也就是说：

- 上游 `FT4/FT8` 的大量差异，在 sender 头字段这里被压到只剩“长度不同”

## 目前 patched DigiManager 修到了哪一步
当前补丁已经做了两类事情：

1. 让 `protocol 4` 能复用现有 digital 下发门
2. 让 sender 头字段至少保留更多差异

现在的头字段不再是：

- `05 dc 00 00 67`

而是更接近：

- `05 dc 67 00 67`

这仍然不是“已经证明合格 FT4”，但它至少说明：

- 我们不再把 `FT4` 完全压成“和 `FT8` 只有长度不同”的同一类包

## 这份分析能证明什么，不能证明什么
### 能证明的
- `WSJT-X -> DigiManager` 这段上游流量已经具有真实 `FT4` 语义差异
- `DigiManager` 原始 sender 确实会把这些差异压扁
- 当前补丁已经开始保留更多 `FT4` 身份信息

### 不能证明的
- patched DigiManager 已经发出合格 `FT4`
- 空口信号已经符合规范
- 固件完全没有责任

## 这对后续研发意味着什么
当前最合理的主线是：

1. 继续优先修 DigiManager 的发送组织方式
2. 不再先怀疑 `WSJT-X` 输出本身
3. 只有当固定频点下的 `FT4` 仍然不能被第二接收机 / 第二套 `WSJT-X` 正常解码时，才继续细拆 sender 节拍链

一句话总结：

- 上游 `FT4` 已经是真的
- 现在更像是 `DigiManager` 没把它正确送成标准 `FT4`
