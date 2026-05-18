# UDP 端口观察模板 / UDP Port Observation Template

这个模板适合“还没正式抓包，但已经开始确认本机 UDP 端口”的测试者。  
This template is for testers who have not started a formal packet capture yet but have begun confirming the local UDP ports.

## 1. 先回这些值 / Send These Values First

```text
WSJT-X PTT = ?
WSJT-X UDPServerPort = ?
WSJT-X SendSymPort = ?
DigiManager UDP port = ?
wsjtx.exe live UDP port = ?
```

## 2. 请附上这些信息 / Please Attach These Items

- `WSJT-X` 设置页截图  
  `WSJT-X` settings screenshot
- `DigiManager` UDP 设置页截图  
  `DigiManager` UDP settings screenshot
- `logs/udp-port-observation.json`

## 3. 说明现在的链路 / Describe The Current Link

- 当前固定频点链路是否正常工作？  
  Does the current fixed-frequency chain work normally?
- `WSJT-X` 是否明确使用 `VOX`？  
  Is `WSJT-X` clearly using `VOX`?
- `DigiManager` 是否明确使用 `UDP`？  
  Is `DigiManager` clearly using `UDP`?

## 4. 一句话目标 / One-Sentence Goal

**先确认 `2237 / 4532 / 5957` 的现场关系，再决定正式抓包。**  
**Confirm the live relationship between `2237 / 4532 / 5957` before the formal capture.**
