# patched 固件与 patched DigiManager 测试结果模板

## 1. 基本信息
- 测试日期：
- 测试人：
- 使用的 patched 固件文件名：
- 使用的 DigiManager 文件名：
- 原版固件文件名：
- 原版 DigiManager 文件名：
- 是否全程假负载或断天线：`yes / no`

## 2. 基础状态
- 能否正常开机：`yes / no`
- 开机版本显示：
- 菜单是否仍像真实 `0.3q`：`yes / no`
- 数字模式入口是否仍存在：`yes / no`
- DigiManager 是否能正常启动：`yes / no`

## 3. 第一阶段：固定频点合规 FT4
这一阶段使用：

- `patched DigiManager + 原版真实 0.3q 固件`

请填写：

- FT8 是否仍能正常发射：`yes / no`
- FT4 是否进入 TX：`yes / no`
- DigiManager 是否对 FT4 有反应：`yes / no`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`yes / no`
- 固定频点 FT4 是否可判定为合格：`yes / no`
- 备注：

## 4. 第二阶段：加入 patched 固件后的改频测试
只有当“第一阶段固定频点 FT4 合格”后才填写这一部分。  
这一阶段使用：

- `patched DigiManager + patched 固件`

请填写：

- FT8 是否仍正常：`yes / no`
- FT4 是否仍进入 TX：`yes / no`
- 第二接收机 / 第二套 WSJT-X 是否仍正常解码 FT4：`yes / no`
- 空闲态改频是否生效：`yes / no / temporary`
- 发射态改频是否生效：`yes / no / temporary`
- 加入 patched 固件后，FT4 是否明显变慢或失真：`yes / no`
- 备注：

## 5. 如果 FT4 失败，请继续补充两组对照

### 对照组 A：patched 固件 + 原版 DigiManager
请填写：

- FT8 是否正常：`yes / no`
- FT4 是否进入 TX：`yes / no`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`yes / no`
- 空闲态改频是否生效：`yes / no / temporary`
- 发射态改频是否生效：`yes / no / temporary`
- 备注：

### 对照组 B：原版固件 + patched DigiManager
请填写：

- FT8 是否正常：`yes / no`
- FT4 是否进入 TX：`yes / no`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`yes / no`
- 空闲态改频是否生效：`yes / no / temporary`
- 发射态改频是否生效：`yes / no / temporary`
- 备注：

## 6. 如果用了诊断版 DigiManager
- 是否使用了 `patched-UVK5DigManager-diagnostic.exe`：`yes / no`
- 使用诊断版后，FT4 行为是否与正式版不同：`yes / no`
- 如果不同，请简要描述：

## 7. 一句话总结
- 本轮最关键现象：

## 8. 附件
- 开机界面截图：
- 菜单截图：
- DigiManager 主界面截图：
- 第二接收机 / 第二套 WSJT-X 解码截图：
- 其他补充材料：
