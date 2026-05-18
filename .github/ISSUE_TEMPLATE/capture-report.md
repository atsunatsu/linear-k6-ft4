---
name: Capture Report / 抓包结果提交
about: Submit COM info, capture logs, and observations after you already completed a capture.
title: "[capture] "
labels: ["capture"]
assignees: []
---

## Before You Start / 提交前先确认

- [ ] I already know the WSJT-X COM / 我已经确认 WSJT-X 的 COM
- [ ] I already know the DigiManager COM / 我已经确认 DigiManager 的 COM
- [ ] I already completed at least one capture run / 我已经完成至少一轮抓包

## COM Information / COM 信息

```text
WSJT-X = COM?
DigiManager = COM?
```

- Virtual COM tool / 虚拟串口工具:
- Baud rate / 波特率:
- Other serial settings / 其他串口参数:

## Proxy Topology / 代理插入后的链路

```text
WSJT-X -> COM_A -> capture-proxy -> COM_B -> DigiManager
```

- COM_A =
- COM_B =
- Capture command used / 实际使用的抓包命令:

## Scenarios Captured / 已抓场景

- [ ] `startup`
- [ ] `idle_read`
- [ ] `set_freq`
- [ ] `mode_change`
- [ ] `ptt_on`
- [ ] `ptt_off`
- [ ] `tx_retune`

## Files Attached / 已附文件

- [ ] `serial-topology-template.csv`
- [ ] `serial-capture.jsonl`
- [ ] analyzer output / 分析脚本输出

## Observations / 观察结果

- Was the original fixed-frequency chain working before capture? / 抓包前原始固定频点链路是否正常？
- Which step failed most easily? / 哪一步最容易失败？
- Did retuning during TX clearly happen? / 发射中的改频是否明显发生？
- Did the traffic look more like text or binary? / 抓包看起来更像文本还是二进制？

## One-Sentence Conclusion / 一句话总结

-  
