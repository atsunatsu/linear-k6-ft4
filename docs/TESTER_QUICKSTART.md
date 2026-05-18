# 测试者快速上手 / Tester Quick Start

## 你现在要做什么 / What You Need To Do Right Now

如果你的现场是：

- `WSJT-X` 用 `VOX`
- `DigiManager` 用 `UDP`

那你现在的第一步不是找 `COM`，而是确认 **本机 UDP 端口**。  
Then your first step is not to find a `COM` port. Your first step is to confirm the **local UDP ports**.

## 第一步只做这件事 / The First Step Is Only This

请先回我这些值：  
Please send back these values first:

```text
WSJT-X PTT = ?
WSJT-X UDPServerPort = ?
WSJT-X SendSymPort = ?
DigiManager UDP port = ?
wsjtx.exe live UDP port = ?
```

## 最快的方法 / Fastest Way

直接运行：

```powershell
python scripts/observe_udp_ports.py
```

然后回传：

- 终端摘要  
  The terminal summary
- [logs/udp-port-observation.json](/F:/Codex/CEC固件改装FT4/logs/udp-port-observation.json)

## 如果你还没装抓包工具 / If You Have Not Installed The Capture Tool Yet

也没关系。  
That is okay.

你现在还不需要正式抓包。  
You do not need to do the formal capture yet.

先确认端口观察结果就已经有价值。  
The port observation result is already useful.

## 确认端口后看这里 / After Port Confirmation, Read This

- UDP 快速上手 / UDP quick start: [docs/UDP_CAPTURE_QUICKSTART.md](/F:/Codex/CEC固件改装FT4/docs/UDP_CAPTURE_QUICKSTART.md)
- UDP 抓包手册 / UDP capture guide: [docs/UDP_LOOPBACK_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_LOOPBACK_CAPTURE_GUIDE.md)

## 串口路线什么时候才看 / When To Look At The Serial Path

只有当你已经确认：

- 当前链路不是 `UDP`
- 或者 `UDP` 不足以解释问题

才回到串口路线。  
Only return to the serial path when the live chain is not `UDP`, or when `UDP` is not enough to explain the problem.

## 一句话记住 / One Sentence To Remember

**先看 `2237 / 4532 / 5957`，再抓 loopback UDP。**  
**Observe `2237 / 4532 / 5957` first, then capture loopback UDP.**
