# 测试者快速上手 / Tester Quick Start

## 你现在要做什么 / What You Need To Do Right Now

如果你是第一次帮这个项目测试，请把任务理解成一句话：  
If this is your first time helping this project, think of the task as one sentence:

**先找出 `WSJT-X` 和 `DigiManager` 分别用了哪个 `COM`，再决定要不要继续抓包。**  
**First find which `COM` port `WSJT-X` uses and which `COM` port `DigiManager` uses, then decide whether to continue to capture.**

你现在不需要先理解协议，也不需要先改代码。  
You do not need to understand the protocol first, and you do not need to change code first.

## 第一步只做这件事 / The First Step Is Only This

请回我下面两行中的实际 `COM` 号：  
Please send back the real `COM` numbers for these two lines:

```text
WSJT-X = COM?
DigiManager = COM?
```

如果你现在还填不出来，也没关系，直接发截图。  
If you cannot fill them in yet, that is fine. Just send screenshots.

## 你要打开哪 3 个地方 / Open These 3 Places

请按这个顺序看：  
Please check these in this order:

1. `WSJT-X`
2. `DigiManager`
3. Windows `设备管理器`

## 1. 在 WSJT-X 里找 COM / Find The COM In WSJT-X

请做这些动作：  
Do these actions:

1. 打开 `WSJT-X`
2. 打开设置页  
   Open the settings window
3. 找 `Rig`、`CAT`、`Serial Port`、`Radio` 相关区域  
   Look for the `Rig`, `CAT`, `Serial Port`, or `Radio` area
4. 记下看到的 `COMxx`  
   Write down the `COMxx` you see

你现在只需要知道：  
Right now you only need to know:

- `WSJT-X` 正在使用哪个 `COM`  
  Which `COM` `WSJT-X` is using

## 2. 在 DigiManager 里找 COM / Find The COM In DigiManager

请做这些动作：  
Do these actions:

1. 打开 `DigiManager`
2. 打开设置页  
   Open the settings window
3. 找 `COM Port`、`CAT`、`Serial`、`Port` 相关区域  
   Look for the `COM Port`, `CAT`, `Serial`, or `Port` area
4. 记下看到的 `COMxx`  
   Write down the `COMxx` you see

你现在只需要知道：  
Right now you only need to know:

- `DigiManager` 正在使用哪个 `COM`  
  Which `COM` `DigiManager` is using

## 3. 在设备管理器里核对 / Cross-Check In Device Manager

请做这些动作：  
Do these actions:

1. 打开 Windows `设备管理器`  
   Open Windows `Device Manager`
2. 展开 `Ports (COM & LPT)`  
   Expand `Ports (COM & LPT)`
3. 看看有哪些 `COM` 口  
   See which `COM` ports exist
4. 如果你在前两步看到的 `COM` 号也出现在这里，记下来  
   If the same `COM` numbers from the first two steps also appear here, note that

## 现在最小回传格式 / Minimum Reply Format Right Now

如果你已经找到了，就直接回：  
If you found them, just reply with:

```text
WSJT-X = COM7
DigiManager = COM8
```

如果还不能确定，就不要硬猜。请直接发这 3 张截图：  
If you still cannot confirm them, do not guess. Send these 3 screenshots instead:

1. `WSJT-X` 设置页  
   `WSJT-X` settings page
2. `DigiManager` 设置页  
   `DigiManager` settings page
3. `设备管理器 -> Ports (COM & LPT)`  
   `Device Manager -> Ports (COM & LPT)`

也可以按这个模板回传：  
You can also report with this template:

[docs/COM_TOPOLOGY_HELP_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/COM_TOPOLOGY_HELP_TEMPLATE.md)

## 什么时候继续下一步 / When To Continue

只有在你已经大致确认下面两件事后，才继续抓包：  
Only continue to capture after you have roughly confirmed these two things:

- `WSJT-X = COM?`
- `DigiManager = COM?`

如果这两件事还不清楚，先停在这里就可以。  
If those two things are still unclear, it is okay to stop here for now.

## 确认 COM 后看这里 / After COM Is Confirmed, Read This

确认了两个 `COM` 之后，再继续看：  
After you confirm the two `COM` ports, continue with:

[docs/SERIAL_CAPTURE_GUIDE.md](/F:/Codex/CEC固件改装FT4/docs/SERIAL_CAPTURE_GUIDE.md)

## 一句话记住 / One Sentence To Remember

**先找两个 COM，再抓包。**  
**Find the two COM ports first, then capture.**
