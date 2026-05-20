---
name: Reverse Problem / 逆向流程问题反馈
about: Report a blocker while following the real 0.3q reverse-engineering or dynamic retune validation flow.
title: "[reverse-problem] "
labels: ["reverse-problem"]
assignees: []
---

## Which Step Failed / 哪一步出问题了

- [ ] I do not know where to place the real firmware file / 我不知道真实固件文件该放哪里
- [ ] I do not know where to place DigiManager / 我不知道 DigiManager 文件该放哪里
- [ ] I could not run `python scripts\analyze_real_03q_reverse.py` / 我无法运行真实 0.3q 静态分析
- [ ] I could not prepare `idle-retune.pcapng` / 我无法准备空闲态抓包
- [ ] I could not prepare `tx-retune.pcapng` / 我无法准备发射态抓包
- [ ] I do not know how to fill `actions.json` / 我不知道怎么填写 `actions.json`
- [ ] I could not run `python scripts\analyze_dynamic_lock.py` / 我无法运行动态改频分析
- [ ] I do not know how to interpret the result / 我不知道怎么理解输出结果
- [ ] Other / 其他

## What I Ran / 我运行了什么

```text
python scripts\analyze_real_03q_reverse.py
python scripts\analyze_dynamic_lock.py
```

## What Happened / 实际发生了什么

- 

## Optional Attachments / 可选附件

- [ ] Terminal output / 终端输出
- [ ] `actions.json`
- [ ] `idle-retune.pcapng`
- [ ] `tx-retune.pcapng`
- [ ] `logs/reverse/reverse-map.md`
- [ ] `logs/reverse/dynamic-lock-report.md`
