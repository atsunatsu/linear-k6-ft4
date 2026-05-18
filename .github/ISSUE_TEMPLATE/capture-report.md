---
name: Capture Report / 抓包结果提交
about: Submit COM topology, serial capture logs, and tester observations.
title: "[capture] "
labels: ["capture"]
assignees: []
---

## Summary / 简述

- What was tested? / 这次测试了什么？
- Was the original WSJT-X + DigiManager + CEC/K5 chain working before capture? / 抓包前原有链路是否可用？

## Tester / 测试人

- Name or nickname / 姓名或昵称:
- Test date / 测试日期:
- Operating system / 操作系统:

## Software Versions / 软件版本

- WSJT-X version / WSJT-X 版本:
- DigiManager version / DigiManager 版本:
- CEC/K5 firmware version / CEC/K5 固件版本:

## COM Topology / COM 拓扑

- WSJT-X COM / WSJT-X 使用的 COM:
- DigiManager COM / DigiManager 使用的 COM:
- Virtual COM tool / 虚拟串口工具:
- Baud rate / 波特率:
- Other serial parameters / 其他串口参数:

Please attach the completed topology worksheet if available.  
如已填写拓扑表，请一并上传。

## Proxy Topology / 代理插入后的链路

- COM_A:
- COM_B:
- Capture proxy command / 抓包代理命令:

## Scenarios Captured / 已抓到的场景

- [ ] `startup`
- [ ] `idle_read`
- [ ] `set_freq`
- [ ] `mode_change`
- [ ] `ptt_on`
- [ ] `ptt_off`
- [ ] `tx_retune`
- [ ] `shutdown`
- [ ] `error_case`

## Files Attached / 附件

- [ ] `serial-topology-template.csv`
- [ ] `serial-capture.jsonl`
- [ ] analyzer output / 分析脚本输出

If a file is too large, describe how you are sharing it.  
如果文件太大，请说明你是如何分享它的。

## Observations / 观察结果

- Which step failed most easily? / 哪一步最容易失败？
- Did in-TX retuning clearly happen? / 发射中改频是否明显发生？
- Any popups, timeouts, or disconnects? / 是否出现错误弹窗、超时或掉线？
- Did the traffic look text-like or binary? / 抓包看起来更像文本协议还是二进制协议？

## One-Sentence Conclusion / 一句话总结

-  
