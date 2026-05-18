# UDP 回环抓包手册 / UDP Loopback Capture Guide

## 这份手册适合谁 / Who This Guide Is For

这份手册适合这样的测试者：

- `WSJT-X` 用 `VOX`
- `DigiManager` 用 `UDP`
- 当前链路本来就能工作

This guide is for testers whose setup already works and uses:

- `VOX` in `WSJT-X`
- `UDP` in `DigiManager`

## 最小成功标准 / Minimum Success Standard

第一次不要求你立刻抓出完整协议。  
The first run does not need to fully decode the protocol.

只要你能做到下面任意一项，就已经有价值：  
Any of these is already valuable:

- 回传 `logs/udp-port-observation.json`
- 确认 `2237 / 4532 / 5957` 哪些端口在现场真的被使用
- 抓到一份包含 `startup / idle / tx_symbols` 的 `pcapng`

## 阶段 A：先确认现场端口 / Phase A: Confirm The Live Ports First

先运行：

```powershell
python scripts/observe_udp_ports.py
```

请先记录这些事实：  
Record these facts first:

- `WSJT-X.ini` 中的 `PTTMethod`
- `WSJT-X.ini` 中的 `UDPServerPort`
- `WSJT-X.ini` 中的 `SendSymPort`
- `wsjtx.exe` 当前实际占用了哪些 UDP 口
- `DigiManager` 设置页里显示的 UDP 端口

如果这里已经出现明显不一致，比如：

- 配置写的是 `2237`
- 运行现场却主要是 `4532`

那也没关系，正是这种差异最值得记录。  
If you already see a mismatch here, such as `2237` in config but `4532` live, that mismatch is exactly worth recording.

## 阶段 B：开启 Windows loopback 抓包 / Phase B: Start Windows Loopback Capture

请先安装：

- `Npcap`
- `Wireshark` 或 `tshark`

然后在抓包工具里选择 **loopback** 接口。  
Then choose the **loopback** interface in the capture tool.

推荐过滤规则：  
Recommended display or capture filter:

```text
udp and (port 2237 or port 4532 or port 5957)
```

## 阶段 C：按场景抓最小样本 / Phase C: Capture The Minimum Scenario Set

请按这个顺序抓：

1. `startup`
   - 先启动 `WSJT-X`
   - 再启动 `DigiManager`
2. `idle`
   - 两边都开着但不发射
3. `decode`
   - 观察接收解码时 UDP 是否有明显流量
4. `tx_prepare`
   - 点击准备发射但先不正式发射
5. `vox_tx_start`
   - 进入 VOX 触发发射
6. `tx_symbols`
   - FT4 发射过程中持续观察，重点盯 `5957`
7. `tx_end`
   - 发射结束
8. `error_case`
   - 故意断开一个软件或改错一个关键设置，再观察端口行为

## 每个场景后要确认什么 / What To Confirm After Each Scenario

- 抓包仍在正常记录  
  Capture is still recording
- 当前场景名记下来了  
  The scenario label is recorded in your notes
- 你知道刚才做的是哪一个动作  
  You know which action you just triggered

## 要回传什么 / What To Send Back

请至少回传：

- `pcapng` 原始抓包文件
- `logs/udp-port-observation.json`
- 你抓到的场景列表
- 软件版本
- 一句话说明每个场景做了什么

建议按这个模板整理：  
Use this template if possible:

[docs/UDP_CAPTURE_REPORT_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_REPORT_TEMPLATE.md)

## 什么时候才去看串口 / When To Fall Back To Serial

只有在这些情况发生时，才回到串口路线：

- UDP 流量不足以解释 DigiManager 如何驱动洁净发射
- FT4 发射关键行为没有体现在 UDP 面
- 必须进一步观察 `DigiManager ↔ CEC/K5` 的设备控制流

这时再看：  
Only then use:

[docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)

## 一句话总结 / One-Sentence Summary

**先做端口观察，再抓 `2237 / 4532 / 5957` 的 loopback UDP。**  
**Do port observation first, then capture loopback UDP for `2237 / 4532 / 5957`.**
