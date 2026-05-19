# UDP Replay Bench Quick Start / UDP 重放台架快速开始

## 这份说明是给谁的 / Who This Guide Is For

这份说明是给“不会写代码，但愿意帮忙测试”的人。  
This guide is for people who do not write code, but are willing to help test.

你现在不需要先抓包，也不需要先懂协议。  
You do not need to capture packets first, and you do not need to understand the protocol first.

## 你现在要做什么 / What You Need To Do Now

你现在只做一件事：  
You only need to do one thing now:

**把仓库里现成的 `FT8` 和 `FT4` 样本，发给本机的 `UVK5DigManager`，然后看它有没有反应。**  
**Send the included `FT8` and `FT4` sample files to local `UVK5DigManager`, then check whether it reacts.**

## 开始前先确认 / Before You Start

请先确认下面 4 件事：  
Please confirm these 4 things first:

1. 电台接的是 `假负载`
2. 没有接天线
3. `UVK5DigManager` 已经打开
4. 电台已经连上 `UVK5DigManager`

1. The radio is connected to a `dummy load`
2. No antenna is connected
3. `UVK5DigManager` is already open
4. The radio is already connected to `UVK5DigManager`

如果上面有任何一条做不到，请先停下来。  
If any of the above is not true, stop here first.

## 第 1 步：打开项目文件夹 / Step 1: Open The Project Folder

找到这个项目文件夹：  
Find this project folder:

`CEC固件改装FT4`

## 第 2 步：打开 PowerShell / Step 2: Open PowerShell

最简单的方法：  
The easiest method:

1. 在这个文件夹的空白地方点一下
2. 按住键盘上的 `Shift`
3. 在空白处点鼠标右键
4. 选择：
   - `在此处打开 PowerShell 窗口`
   - 或 `在终端中打开`

1. Click on empty space inside the folder
2. Hold the `Shift` key
3. Right-click on empty space
4. Choose:
   - `Open PowerShell window here`
   - or `Open in Terminal`

打开后你会看到一个蓝色或黑色窗口。  
After that, you should see a blue or black terminal window.

## 第 3 步：先做“不会发射”的检查 / Step 3: Do The “No Transmit” Check First

这里的 `dry-run` 意思是：  
Here `dry-run` means:

- 只显示“如果正式测试，会做什么”
- 现在**不会**真的发数据
- 现在**不会**真的触发发射

- It only shows “what would happen in a real test”
- It does **not** really send data yet
- It does **not** really trigger transmit yet

先复制下面这一整行，粘贴到 PowerShell 里，然后按回车：  
Copy this whole line, paste it into PowerShell, and press Enter:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --dry-run
```

如果正常，你会看到很多行文字，里面会出现这些词：  
If it works, you will see many lines of text containing words like:

- `source_capture`
- `mode`
- `packets`
- `index=`
- `tag=`

这就说明：  
That means:

- 命令运行成功了
- 文件找到了
- 这一步没有真的发射

- The command worked
- The file was found
- This step did not really transmit anything

然后再复制下面这一整行，粘贴进去，再按回车：  
Then copy this whole line, paste it, and press Enter:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --dry-run
```

如果这一步也正常，就继续下一步。  
If this also works, continue to the next step.

## 第 4 步：先测 FT8 / Step 4: Test FT8 First

现在才开始真正发送测试数据。  
Only now does the tool start sending real test data.

复制下面这一整行，粘贴到 PowerShell，然后按回车：  
Copy this whole line, paste it into PowerShell, then press Enter:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --fast-replay
```

运行的时候，请盯着看这 3 个地方：  
While it runs, watch these 3 things:

1. `UVK5DigManager` 界面有没有变化
2. `PTT` 有没有动作
3. 电台有没有发射相关反应

1. Whether the `UVK5DigManager` UI changes
2. Whether `PTT` changes state
3. Whether the radio shows any transmit-related response

看完以后，请记住结果。  
After it finishes, remember the result.

## 第 5 步：再测 FT4 / Step 5: Test FT4 Next

复制下面这一整行，粘贴到 PowerShell，然后按回车：  
Copy this whole line, paste it into PowerShell, then press Enter:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --fast-replay
```

还是看同样 3 个地方：  
Again, watch the same 3 things:

1. `UVK5DigManager` 界面有没有变化
2. `PTT` 有没有动作
3. 电台有没有发射相关反应

1. Whether the `UVK5DigManager` UI changes
2. Whether `PTT` changes state
3. Whether the radio shows any transmit-related response

## 第 6 步：做“单独发一个特殊包”的检查 / Step 6: Test One Special Packet At A Time

这一步的意思很简单：  
This step is simple:

- 不是整段重放
- 而是只发一个特殊包
- 看看 `FT8` 和 `FT4` 的特殊包会不会有不同反应

- This is not a full replay
- It sends only one special packet
- We check whether the `FT8` and `FT4` special packets behave differently

先运行这一行：  
Run this line first:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json --single-packet-tag ft8_mode_marker
```

再运行这一行：  
Then run this line:

```powershell
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json --single-packet-tag ft4_mode_marker
```

还是看：  
Again, watch:

- `UVK5DigManager` 界面有没有变化
- `PTT` 有没有动作
- 电台有没有反应

- Whether the `UVK5DigManager` UI changes
- Whether `PTT` changes state
- Whether the radio reacts

## 第 7 步：把结果告诉我们 / Step 7: Report The Result

至少告诉我们这 4 件事：  
At minimum, tell us these 4 things:

1. `FT8` 整段重放有没有反应
2. `FT4` 整段重放有没有反应
3. `ft8_mode_marker` 单发有没有反应
4. `ft4_mode_marker` 单发有没有反应

1. Whether full `FT8` replay produced a response
2. Whether full `FT4` replay produced a response
3. Whether single `ft8_mode_marker` produced a response
4. Whether single `ft4_mode_marker` produced a response

最好按这个模板填写：  
Best option: fill in this template:

[docs/UDP_REPLAY_BENCH_TEMPLATE.md](/F:/Codex/CEC固件改装FT4/docs/UDP_REPLAY_BENCH_TEMPLATE.md)

## 如果哪一步失败了怎么办 / What If Something Fails

如果你看到报错，或者不知道自己做对了没有，请把下面这些发回来：  
If you see an error, or you are not sure whether you did it right, send back these things:

- 你运行的是哪一行命令
- PowerShell 里显示的报错文字
- `UVK5DigManager` 的截图
- 电台前面板照片

- Which command you ran
- The error text shown in PowerShell
- A screenshot of `UVK5DigManager`
- A photo of the radio front panel
