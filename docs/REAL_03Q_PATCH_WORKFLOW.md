# Real 0.3q Patch Workflow

## Purpose / 目的
This document is for maintainers.

The current success-first route is:

- patch the real `cec_0.3QB.packed.bin` so digital-mode retune is no longer blocked
- patch `UVK5DigManager.exe` so FT4 is forwarded like FT8
- test only the combined pair on a real bench setup

## Inputs / 输入
Place these real files in the workspace root or the matching `reverse/input` folders:

- `cec_0.3QB.packed.bin`
- `UVK5DigManager.exe`

## Build The Combined Candidates / 生成组合补丁候选件
Open PowerShell in the project directory and run:

```powershell
python scripts\build_real_03q_patch_variants.py
```

This currently generates:

- `outputs/patched-0.3q-retune-only.packed.bin`
- `outputs/patched-0.3q-combined.packed.bin`
- `outputs/patched-0.3q-bench.packed.bin`
- `outputs/patched-UVK5DigManager.exe`
- `outputs/patch-build-summary.json`

## Current Patch Split / 当前补丁分工
### Firmware side / 固件侧
Current firmware patch goal:

- keep the real `0.3q` menu and digital-mode entry
- allow digital-mode retune updates to survive instead of snapping back

Current firmware variants:

- `retune-only`
- `combined`

### DigiManager side / 上位机侧
Current DigiManager patch goal:

- let `RecvProtocol == 4` reuse the same digital forward path already used by `RecvProtocol == 8`

Current EXE patch uses:

- `UDPDataCheck` gate rewrite
- repurposed helper method for `protocol == 4 || protocol == 8`

## Important Files / 关键文件
- Reverse report:
  - [logs/reverse/reverse-map.json](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.json)
  - [logs/reverse/reverse-map.md](/F:/Codex/CEC固件改装FT4/logs/reverse/reverse-map.md)
- Firmware manifests:
  - [reverse/patches/patch-manifest.retune-only.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.retune-only.json)
  - [reverse/patches/patch-manifest.combined.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.combined.json)
- DigiManager manifest:
  - [reverse/patches/patch-manifest.digimanager-ft4-forward.json](/F:/Codex/CEC固件改装FT4/reverse/patches/patch-manifest.digimanager-ft4-forward.json)

## What Is Proven And What Is Not / 已确认与未确认
Already proven:

- the real firmware can be unpacked, patched, and repacked
- the DigiManager EXE can be patched reproducibly
- the combined candidate files can be generated reproducibly

Not yet proven on a real radio:

- that FT4 now always starts transmitting
- that digital-mode retune is fully unlocked

So the current outputs are:

- structurally valid patch candidates
- traceable to the real source binaries
- ready for controlled bench testing

