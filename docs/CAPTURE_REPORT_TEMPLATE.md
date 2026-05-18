# 抓包回报模板 / Capture Report Template

把下面模板复制一份，按实际情况填写后发回。  
Copy this template, fill it in with real data, and send it back.

## 1. 测试人 / Tester

- 姓名或昵称 / Name or nickname:
- 测试日期 / Test date:
- 操作系统 / Operating system:

## 2. 当前工作链路 / Current Working Chain

- `WSJT-X` 版本 / `WSJT-X` version:
- `DigiManager` 版本 / `DigiManager` version:
- `CEC/K5` 固件版本 / `CEC/K5` firmware version:
- 当前这套链路是否原本可用 / Was the original chain working before capture:

## 3. COM 拓扑 / COM Topology

请附上填写后的 CSV，并在这里简述关键链路：  
Attach the completed CSV and summarize the important chain here:

- `WSJT-X` 使用的 COM / COM used by `WSJT-X`:
- `DigiManager` 使用的 COM / COM used by `DigiManager`:
- 虚拟串口工具 / Virtual COM tool:
- 波特率 / Baud rate:
- 其他串口参数 / Other serial parameters:

## 4. 代理插入后的链路 / Topology After Proxy Insertion

- `COM_A`:
- `COM_B`:
- 抓包代理命令 / Capture proxy command:

## 5. 实际抓到的场景 / Scenarios Captured

请逐项勾选并补充说明：  
Check each scenario and add notes:

- [ ] `startup`
- [ ] `idle_read`
- [ ] `set_freq`
- [ ] `mode_change`
- [ ] `ptt_on`
- [ ] `ptt_off`
- [ ] `tx_retune`
- [ ] `shutdown`
- [ ] `error_case`

补充说明 / Notes:

## 6. 输出文件 / Output Files

- COM 拓扑清单 / COM topology worksheet:
- 抓包日志 / Capture log:
- 分析脚本输出 / Analyzer output:

## 7. 你的观察 / Your Observations

请尽量用自然语言描述你看到的现象：  
Describe what you observed in plain language:

- 哪一步最容易失败 / Which step failed most easily:
- 发射中改频是否明显发生 / Whether in-TX retuning clearly happened:
- 有没有看到错误弹窗、超时或掉线 / Any error dialogs, timeouts, or disconnects:
- 如果你看了抓包文本，它更像文本协议还是二进制协议 / If you inspected the capture, did it look text-like or binary:

## 8. 总结 / Summary

一句话总结这次抓包：  
One-sentence summary of this capture:

-  
