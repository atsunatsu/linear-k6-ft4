# patched 固件与 patched DigiManager 测试结果模板

## 1. 基本信息
- 测试日期：2025-05-24
- 测试人：atsunatsu
- 使用的 patched 固件文件名：patched-0.3q-combined.packed.bin
- 使用的 DigiManager 文件名：patched-UVK5DigManager.exe
- 原版固件文件名：cec_0.3QB.packed.bin
- 原版 DigiManager 文件名：UVK5DigManager.exe
- 是否全程假负载或断天线：`yes`

## 2. 基础状态
- 能否正常开机：`yes`
- 开机版本显示：CEC_3QPC
- 菜单是否仍像真实 `0.3q`：`yes`
- 数字模式入口是否仍存在：`yes`
- DigiManager 是否能正常启动：`yes`

## 3. 第一阶段：固定频点合规 FT4
这一阶段使用：

- `patched DigiManager + 原版真实 0.3q 固件`

请填写：

- FT8 是否仍能正常发射：`yes`
- FT4 是否进入 TX：`yes`
- DigiManager 是否对 FT4 有反应：`yes`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`no`
- 固定频点 FT4 是否可判定为合格：`no`
- 备注：FT4能触发发射，但接收端无法解码

## 4. 第二阶段：加入 patched 固件后的改频测试
只有当"第一阶段固定频点 FT4 合格"后才填写这一部分。

未测试（第一阶段FT4解码失败）

## 5. 如果 FT4 失败，请继续补充两组对照

### 对照组 A：patched 固件 + 原版 DigiManager
请填写：

- FT8 是否正常：`yes`
- FT4 是否进入 TX：`no`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`N/A`
- 空闲态改频是否生效：`N/A`
- 发射态改频是否生效：`N/A`
- 备注：旧版DigiManager不能发射FT4

### 对照组 B：原版固件 + patched DigiManager
请填写：

- FT8 是否正常：`yes`
- FT4 是否进入 TX：`yes`
- 第二接收机 / 第二套 WSJT-X 是否正常解码 FT4：`no`
- 空闲态改频是否生效：未测试
- 发射态改频是否生效：未测试
- 备注：新旧固件无差异，均可触发发射；固件端将FT4当作FT8发射（15秒周期），实际应为7.5秒周期、4.48秒发射时长

## 6. 如果用了诊断版 DigiManager
- 是否使用了 `patched-UVK5DigManager-diagnostic.exe`：`no`

## 7. 一句话总结
新旧固件无差异；旧DigiManager不能发FT4，新版可以；固件端将FT4当作FT8发射（15秒周期），实际应为7.5秒周期、4.48秒发射时长；问题在固件端的模式识别/发射时长控制。

## 8. 附件
- 开机界面截图：
- 菜单截图：
- DigiManager 主界面截图：
- 第二接收机 / 第二套 WSJT-X 解码截图：
- 其他补充材料：
