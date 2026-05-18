# 抓包结果提交模板 / Capture Report Template

这个模板适合已经完成抓包的人。  
This template is for people who already completed a capture.

## 1. 基本信息 / Basic Information

- 测试日期 / Test date:
- 测试者 / Tester:
- 操作系统 / Operating system:
- WSJT-X 版本 / WSJT-X version:
- DigiManager 版本 / DigiManager version:
- CEC/K5 固件版本 / CEC/K5 firmware version:

## 2. 原始链路是否正常 / Was The Original Chain Working

- 抓包前，固定频点链路是否正常工作？  
  Was the original fixed-frequency chain working before capture?
- 你的回答 / Your answer:

## 3. COM 信息 / COM Information

```text
WSJT-X = COM?
DigiManager = COM?
```

- 虚拟串口工具 / Virtual COM tool:
- 波特率 / Baud rate:
- 其他串口参数 / Other serial settings:

## 4. 抓包后链路 / Topology After Proxy Insertion

```text
WSJT-X -> COM_A -> capture-proxy -> COM_B -> DigiManager
```

- COM_A =
- COM_B =
- 你实际运行的抓包命令 / The capture command you actually ran:

## 5. 抓了哪些场景 / Which Scenarios Were Captured

- [ ] `startup`
- [ ] `idle_read`
- [ ] `set_freq`
- [ ] `mode_change`
- [ ] `ptt_on`
- [ ] `ptt_off`
- [ ] `tx_retune`

## 6. 附件 / Files Attached

- [ ] `serial-topology-template.csv`
- [ ] `serial-capture.jsonl`
- [ ] analyzer output / 分析脚本输出

如果文件太大，请说明你是怎么分享的。  
If a file is too large, explain how you shared it.

## 7. 你的观察 / Your Observations

- 哪一步最容易失败？  
  Which step failed most easily?
- 发射中的改频是否明显发生了？  
  Did retuning during TX clearly happen?
- 有没有弹窗、超时、断开？  
  Any popups, timeouts, or disconnects?
- 抓包看起来更像文本还是二进制？  
  Did the traffic look more like text or binary?

## 8. 一句话总结 / One-Sentence Conclusion

-  
