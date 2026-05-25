# linear-k6-ft4

## 测试者先看这里
当前仓库现在只测试一条主路线：

- `patched-UVK5DigManager.exe`
- `patched-0.3q-bench.packed.bin`

但**当前第一优先级不是改频**，而是先确认：

- `FT4` 在固定频点下能不能发出**合格、可被第二接收机 / 第二套 WSJT-X 正常解码**的信号

只有固定频点下的 `FT4` 已经合格，才继续测加入 patched 固件后的数字模式改频。

## 当前测试分两阶段
### 第一阶段：固定频点合规 FT4
请优先使用：

- `patched-UVK5DigManager.exe`
- **原版可工作的真实 0.3q 固件**

第一阶段只看一件事：

- 第二接收机 / 第二套 `WSJT-X` 能不能正常解码你发出的 `FT4`

如果第二接收机还不能正常解码，就**不要继续判断改频是否成功**。

### 第二阶段：回接 patched 固件验证改频
只有当第一阶段已经确认：

- `FT4` 可被第二接收机正常解码
- `FT8` 没被破坏

才切到：

- `patched-UVK5DigManager.exe`
- `patched-0.3q-bench.packed.bin`

然后再测：

- 数字模式空闲态改频
- 数字模式发射态改频
- 同时确认第二接收机仍能正常解码 `FT4`

## 你现在需要哪些文件
测试者**不需要自己编译**。  
测试前请先准备好这些文件：

- `patched-UVK5DigManager.exe`
- `patched-UVK5DigManager-diagnostic.exe`
- `patched-0.3q-bench.packed.bin`
- 原版可工作的 `UVK5DigManager.exe`
- 原版可工作的真实 `0.3q` 固件

其中：

- `patched-UVK5DigManager.exe`：正式测试用
- `patched-UVK5DigManager-diagnostic.exe`：节拍定位用

## 安全边界
现在所有测试都只允许：

- 接假负载，或
- 断开天线

不要把它当成量产固件。  
不要直接上空口发射。

## 测试者应该看哪两份文档
- [patched 固件与 patched DigiManager 实机测试说明](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [patched 固件与 patched DigiManager 测试结果模板](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

## 如果 FT4 测试失败
如果 `FT4` 失败，**不要直接结束测试**。  
请继续按教程里的失败预案，做两组单端对照：

- `patched 固件 + 原版 DigiManager`
- `原版固件 + patched DigiManager`

这样才能最快判断问题主要还在：

- DigiManager 的 `FT4` 发送节拍
- 固件侧 retune 补丁
- 还是两边组合后的交互

## 维护者入口
如果你是维护者，当前主要入口是：

- [真实 0.3q 补丁工作流](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)
- [研发方法与过程](/F:/Codex/CEC固件改装FT4/docs/研发方法与过程.md)
- [CEC 0.3q 的 FT8 发射方案与 FT4 可行性分析](/F:/Codex/CEC固件改装FT4/docs/CEC_FT8发射方案与FT4可行性分析.md)
- [WSJT-X 到 DigiManager 的 FT4 数据流分析](/F:/Codex/CEC固件改装FT4/docs/WSJTX_DIGIMANAGER_FT4数据流分析.md)
- [真实 0.3q 中 command 0x35 处理路径分析](/F:/Codex/CEC固件改装FT4/docs/真实0.3q中command35处理路径分析.md)

当前关键输出位置：

- [outputs/patch-build-summary.json](/F:/Codex/CEC固件改装FT4/outputs/patch-build-summary.json)
- [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
- [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)
- [logs/reverse/ft4-ft8-timing-report.json](/F:/Codex/CEC固件改装FT4/logs/reverse/ft4-ft8-timing-report.json)

## 当前已经确认的事
- 真实 `0.3q` 固件可以稳定解包、补丁、重打包
- `patched DigiManager` 可以稳定生成
- 组合候选件可以重复生成
- 新的 `patched DigiManager` 已经能让 `FT4` 起发射

## 当前还没有确认的事
- 发出来的 `FT4` 是否已经符合规范
- 数字模式改频是否会破坏合规 `FT4` 的时序
- 最终组合路线是否已经能同时满足：
  - 合格 `FT4`
  - 数字模式改频

所以当前这些产物的定位是：

- 结构正确
- 来源可追踪
- 可以进入受控台架测试
- 还不是已经验证完成的最终成品
