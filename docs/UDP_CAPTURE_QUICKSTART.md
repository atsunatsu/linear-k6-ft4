# UDP 抓包快速上手 / UDP Capture Quick Start

## 你现在先做什么 / What To Do First

如果你现在的链路是：

- `WSJT-X` 用 `VOX`
- `DigiManager` 用 `UDP`

那你现在**不要先找 COM**，也不要先插串口代理。  
Then **do not start with COM ports** and do not start with a serial proxy.

你现在先做这两件事：  
Start with these two things:

1. 观察 `2237 / 4532 / 5957`  
   Observe `2237 / 4532 / 5957`
2. 安装并使用 Windows loopback capture  
   Install and use Windows loopback capture

## 第一步：运行端口观察脚本 / Step 1: Run The Port Observation Script

```powershell
python scripts/observe_udp_ports.py
```

它会做两件事：  
It does two things:

- 读取 `WSJT-X.ini`
- 观察本机 `UDP 2237 / 4532 / 5957` 的现场绑定情况

它会生成：

- 终端里的文字摘要  
  A text summary in the terminal
- [logs/udp-port-observation.json](/F:/Codex/CEC固件改装FT4/logs/udp-port-observation.json)  
  [logs/udp-port-observation.json](/F:/Codex/CEC固件改装FT4/logs/udp-port-observation.json)

## 第二步：先回传端口观察结果 / Step 2: Send Back The Port Observation First

如果你还没装 `Wireshark`，现在也没关系。  
If you have not installed `Wireshark` yet, that is okay.

先把下面这些信息回传就已经有价值：  
It is already useful to send back these items:

- `WSJT-X.ini` 里看到的 `UDPServerPort`
- `WSJT-X.ini` 里看到的 `SendSymPort`
- `WSJT-X.ini` 里看到的 `PTTMethod`
- `netstat` 现场里谁占用了 `2237 / 4532 / 5957`
- `logs/udp-port-observation.json`

你也可以按这个模板回传：  
You can also use this template:

[docs/UDP_PORT_OBSERVATION_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_PORT_OBSERVATION_TEMPLATE.md)

## 第三步：安装抓包工具 / Step 3: Install The Capture Tool

请安装：

- `Npcap`
- `Wireshark`

或者至少：

- `Npcap`
- `tshark`

重点是要能抓 **Windows loopback**。  
The important part is that you must be able to capture **Windows loopback** traffic.

## 第四步：开始抓最小场景 / Step 4: Capture The Minimum Scenarios

最小场景先抓这些：

1. `startup`
2. `idle`
3. `decode`
4. `vox_tx_start`
5. `tx_symbols`
6. `tx_end`

具体怎么抓，看这里：  
For the full procedure, see:

[docs/UDP_LOOPBACK_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_LOOPBACK_CAPTURE_GUIDE.md)

## 一句话记住 / One Sentence To Remember

**先看 `2237 / 4532 / 5957`，再抓 loopback UDP。**  
**Observe `2237 / 4532 / 5957` first, then capture loopback UDP.**
