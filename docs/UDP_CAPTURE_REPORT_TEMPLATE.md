# UDP 抓包结果模板 / UDP Capture Report Template

这个模板适合已经完成至少一轮 loopback UDP 抓包的人。  
This template is for people who already completed at least one loopback UDP capture run.

## 1. 基本信息 / Basic Information

- 测试日期 / Test date:
- 测试者 / Tester:
- 操作系统 / Operating system:
- WSJT-X 版本 / WSJT-X version:
- DigiManager 版本 / DigiManager version:
- CEC/K5 固件版本 / CEC/K5 firmware version:

## 2. 端口观察结果 / Port Observation Result

```text
WSJT-X PTT = ?
WSJT-X UDPServerPort = ?
WSJT-X SendSymPort = ?
DigiManager UDP port = ?
wsjtx.exe live UDP port = ?
```

- 是否已附 `logs/udp-port-observation.json`？  
  Is `logs/udp-port-observation.json` attached?

## 3. 抓包设置 / Capture Setup

- 是否使用了 `Npcap`？  
  Did you use `Npcap`?
- 是否使用了 `Wireshark` 或 `tshark`？  
  Did you use `Wireshark` or `tshark`?
- 使用的过滤规则 / Filter used:

```text
udp and (port 2237 or port 4532 or port 5957)
```

## 4. 抓了哪些场景 / Which Scenarios Were Captured

- [ ] `startup`
- [ ] `idle`
- [ ] `decode`
- [ ] `tx_prepare`
- [ ] `vox_tx_start`
- [ ] `tx_symbols`
- [ ] `tx_end`
- [ ] `error_case`

## 5. 已附文件 / Files Attached

- [ ] `pcapng`
- [ ] `logs/udp-port-observation.json`
- [ ] 文字说明 / notes

## 6. 你的观察 / Your Observations

- `WSJT-X` 主要发往哪个端口？  
  Which port did `WSJT-X` mainly send to?
- `DigiManager` 看起来主要监听哪个端口？  
  Which port did `DigiManager` appear to mainly listen on?
- `5957` 是否承载了 FT4 发射关键数据？  
  Did `5957` appear to carry the key FT4 transmit data?
- `2237` 和 `4532` 更像什么关系？  
  What relationship did `2237` and `4532` seem to have?
- 哪个场景最容易出现明显 UDP 流量？  
  Which scenario produced the clearest UDP traffic?

## 7. 一句话总结 / One-Sentence Conclusion

-  
