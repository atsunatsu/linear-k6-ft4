# linear-k6-ft4

## Tester Start Here / 测试者从这里开始
This repository now tests only one route:

- `patched-0.3q-bench.packed.bin`
- `patched-UVK5DigManager.exe`

Current goal:

- keep the real `0.3q` digital-mode menu and workflow
- let FT4 enter the same digital transmit path that FT8 already uses
- let digital mode accept external retune updates instead of snapping back to a fixed frequency

Please do **not** use these old routes:

- old replay-only route
- public-source build route
- stock DigiManager + patched firmware half-route
- patched DigiManager + stock firmware half-route

## Safety First / 先看安全边界
Only test with:

- a dummy load, or
- the antenna disconnected

Do not treat this as a production firmware.  
Do not use it on-air yet.

## What A Tester Needs / 测试者需要什么
You do **not** need to compile anything.

You only need these two files from the maintainer:

- `patched-0.3q-bench.packed.bin`
- `patched-UVK5DigManager.exe`

Then follow:

- [Patched Firmware Test Guide](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_TEST.md)
- [Patched Firmware Result Template](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCHED_FIRMWARE_RESULT_TEMPLATE.md)

## What A Tester Actually Does / 测试者实际只做这些
1. Flash `patched-0.3q-bench.packed.bin`
2. Replace the original DigiManager EXE with `patched-UVK5DigManager.exe`
3. Confirm normal boot, normal menu, and digital-mode entry
4. Verify FT8 still works
5. Test whether FT4 now starts transmitting
6. Test whether retune now works in digital mode
7. Report the result with the template

## Maintainer Notes / 维护者说明
Maintainers can rebuild the current patch candidates locally.

Main maintainer entry:

- [Real 0.3q Patch Workflow](/F:/Codex/CEC固件改装FT4/docs/REAL_03Q_PATCH_WORKFLOW.md)

Current generated outputs are tracked in:

- [outputs/patch-build-summary.json](/F:/Codex/CEC固件改装FT4/outputs/patch-build-summary.json)
- [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
- [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)

## Current Status / 当前状态
What is already true:

- the real `0.3q` firmware unpack/patch/repack workflow works
- a patched DigiManager build pipeline works
- the repo can now generate:
  - `patched-0.3q-retune-only.packed.bin`
  - `patched-0.3q-combined.packed.bin`
  - `patched-0.3q-bench.packed.bin`
  - `patched-UVK5DigManager.exe`

What is **not** yet proven:

- that the current candidate pair already fixes FT4 on a real radio
- that retune is already fully unlocked in digital mode on a real radio

So the current artifacts are:

- structurally valid
- traceable to the real source binaries
- ready for controlled bench testing

