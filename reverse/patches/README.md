# Real 0.3q Patch Manifests

## 中文
这个目录只放**真实 0.3q 固件**的补丁清单。

当前推荐流程：

1. 先运行：

```powershell
python scripts\build_real_03q_patch_workspace.py
```

2. 再编辑：

- `real-03q-bench.template.json`

3. 最后运行：

```powershell
python scripts\apply_real_03q_patch.py reverse\patches\real-03q-bench.template.json
```

## English
This folder stores patch manifests for the **real 0.3q firmware**.

Recommended flow:

1. Run:

```powershell
python scripts\build_real_03q_patch_workspace.py
```

2. Edit:

- `real-03q-bench.template.json`

3. Then run:

```powershell
python scripts\apply_real_03q_patch.py reverse\patches\real-03q-bench.template.json
```
