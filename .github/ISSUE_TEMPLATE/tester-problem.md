---
name: Tester Problem / 测试问题反馈
about: Report a blocker while running the current FT4 firmware UART bench test.
title: "[tester-problem] "
labels: ["tester-problem"]
assignees: []
---

## Which Step Failed / 哪一步出了问题
- [ ] I could not download the current bench firmware / 我无法下载当前 bench 固件
- [ ] I could not flash the radio / 我无法给电台刷机
- [ ] I could not identify the radio COM port / 我找不到电台串口
- [ ] `pyserial` would not install / `pyserial` 无法安装
- [ ] I could not run `send-ft4` / 我无法运行 `send-ft4`
- [ ] I could not run `retune` / 我无法运行 `retune`
- [ ] I could not run `stop-tx` / 我无法运行 `stop-tx`
- [ ] I do not know how to judge the result / 我不知道怎么判断结果
- [ ] Other / 其他

## What I Ran / 我运行了什么
```text
python scripts\uvk5cec_ft4_cli.py send-ft4 --port COM5 ...
python scripts\uvk5cec_ft4_cli.py retune --freq ...
python scripts\uvk5cec_ft4_cli.py stop-tx
```

## What Happened / 实际发生了什么
- 

## Screenshots Or Photos / 截图或照片
- [ ] Flashing tool screenshot / 刷机工具截图
- [ ] Radio front panel photo / 电台前面板照片
- [ ] PowerShell output / PowerShell 输出

## One-Sentence Conclusion / 一句话总结

- 
