---
name: UDP Capture Report / UDP 抓包结果提交
about: Submit loopback UDP capture results for WSJT-X / DigiManager.
title: "[udp-capture] "
labels: ["capture"]
assignees: []
---

## Before You Start / 提交前先确认

- [ ] I already confirmed the live UDP ports / 我已经确认现场 UDP 端口
- [ ] I already completed at least one loopback UDP capture / 我已经完成至少一轮 loopback UDP 抓包

## Port Facts / 端口事实

```text
WSJT-X PTT = ?
WSJT-X UDPServerPort = ?
WSJT-X SendSymPort = ?
DigiManager UDP port = ?
wsjtx.exe live UDP port = ?
```

## Scenarios Captured / 已抓场景

- [ ] `startup`
- [ ] `idle`
- [ ] `decode`
- [ ] `tx_prepare`
- [ ] `vox_tx_start`
- [ ] `tx_symbols`
- [ ] `tx_end`
- [ ] `error_case`

## Files Attached / 已附文件

- [ ] `pcapng`
- [ ] `logs/udp-port-observation.json`
- [ ] notes / 文字说明

## Observations / 观察结果

- Which port did WSJT-X mainly send to? / WSJT-X 主要发往哪个端口？
- Which port did DigiManager appear to listen on? / DigiManager 看起来主要监听哪个端口？
- Did 5957 carry key FT4 transmit data? / 5957 是否承载 FT4 发射关键数据？
- What did 2237 vs 4532 look like? / 2237 和 4532 看起来是什么关系？

## One-Sentence Conclusion / 一句话总结

-  
