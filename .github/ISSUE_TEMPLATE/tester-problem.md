---
name: Tester Problem / 测试问题反馈
about: Report a blocker while running the current FT8/FT4 replay bench test.
title: "[tester-problem] "
labels: ["tester-problem"]
assignees: []
---

## Which Step Failed / 哪一步出了问题

- [ ] I could not prepare a safe dummy-load bench / 我没法准备好假负载台架
- [ ] `UVK5DigManager` did not open normally / `UVK5DigManager` 没有正常打开
- [ ] The radio did not connect to `UVK5DigManager` / 电台没有连上 `UVK5DigManager`
- [ ] I could not run the dry-run step / 我无法运行 dry-run
- [ ] I could not run `FT8` replay / 我无法运行 `FT8` 重放
- [ ] I could not run `FT4` replay / 我无法运行 `FT4` 重放
- [ ] I could not run the single marker test / 我无法运行单包模式标记测试
- [ ] I do not know how to judge the result / 我不知道该怎么判断结果
- [ ] Other / 其他

## What I Ran / 我运行了什么

```text
python scripts\replay_udp_sequence.py --input samples\replay\ft8-replay.json ...
python scripts\replay_udp_sequence.py --input samples\replay\ft4-replay.json ...
```

## What Happened / 实际发生了什么

- 

## Screenshots Or Photos / 截图或照片

- [ ] `UVK5DigManager` screenshot / `UVK5DigManager` 截图
- [ ] Radio front panel photo / 电台前面板照片
- [ ] Console output / 命令行输出

## One-Sentence Conclusion / 一句话总结

- 
