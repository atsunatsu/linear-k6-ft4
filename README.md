# linear-k6-ft4

## 测试者先看这里
这个仓库现在只测试一条路线：

- `patched-0.3q-bench.packed.bin`
- `patched-UVK5DigManager.exe`

当前目标是：

- 保留真实 `0.3q` 的数字模式菜单和基本工作流
- 让 FT4 像 FT8 一样进入现有数字发射链
- 让数字模式能够接受外部改频，而不是立刻被拉回固定频率

请不要再走这些旧路线：

- 旧的 replay 路线
- 公开源码树直接编译固件路线
- 原版 DigiManager + patched 固件的半路线
- patched DigiManager + 原版固件的半路线

## 安全边界
现在所有测试都只允许：

- 接假负载，或
- 断开天线

不要把它当成量产固件。  
不要直接上空口发射。

## 测试者需要什么
测试者**不需要**自己编译任何东西。

测试者只需要从维护者那里拿到这两个文件：

- `patched-0.3q-bench.packed.bin`
- `patched-UVK5DigManager.exe`

然后按这两份文档操作：

- [patched 固件实机测试说明](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [patched 固件测试结果模板](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

## 测试者实际只做这些事
1. 刷入 `patched-0.3q-bench.packed.bin`
2. 用 `patched-UVK5DigManager.exe` 替换原来的 DigiManager
3. 确认能正常开机、菜单正常、数字模式入口还在
4. 先做 FT8 回归，确认原有可用路径没坏
5. 再测 FT4 是否开始真正发射
6. 再测数字模式下改频是否生效
7. 如果 FT4 失败，不要直接结束测试，继续按教程里的单端对照组做补充测试
8. 按模板回报结果

## 维护者入口
如果你是维护者，当前主入口是：

- [真实 0.3q 补丁工作流](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)

当前关键输出文件位置：

- [outputs/patch-build-summary.json](/F:/Codex/CEC固件改装FT4/outputs/patch-build-summary.json)
- [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
- [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)

## 当前状态
现在已经可以确认的事情：

- 真实 `0.3q` 固件的解包、补丁、重新打包流程已经跑通
- patched DigiManager 的生成流程已经跑通
- 仓库现在可以稳定生成这些候选件：
  - `patched-0.3q-retune-only.packed.bin`
  - `patched-0.3q-combined.packed.bin`
  - `patched-0.3q-bench.packed.bin`
  - `patched-UVK5DigManager.exe`

现在还**没有**实机证明的事情：

- 当前这对候选件是否已经在真机上完全修好 FT4 发射
- 当前这对候选件是否已经在数字模式下完全放开改频

所以现阶段这些产物的定位是：

- 结构正确
- 来源可追踪
- 可以进入受控的台架测试
