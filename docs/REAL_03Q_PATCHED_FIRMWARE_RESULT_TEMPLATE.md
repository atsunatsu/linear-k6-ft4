# Patched Real 0.3q Firmware Result Template

## 中文
请尽量按下面格式回报：

### 1. 基础信息
- 测试日期：
- 电台型号：
- 固件文件名：
- 是否全程假负载或断开天线：`yes / no`

### 2. 开机与菜单
- 开机显示：
- 菜单是否正常：`yes / no`
- 数字模式入口是否还在：`yes / no`

### 3. FT8 回归
- FT8 是否还能正常发射：`yes / no`
- 如果不能，请写现象：

### 4. 数字模式改频
- 空闲态改频：`yes / no / temporary`
- TX 态改频：`yes / no / temporary`
- 如有额外现象，请写：

### 5. FT4 发射
- FT4 是否开始真正发射：`yes / no`
- DigiManager 是否有反应：`yes / no`
- 电台是否有发射迹象：`yes / no`
- 发射时频率是否变化：`yes / no / temporary`

### 6. 截图或照片
建议附上：
- 开机版本界面
- 菜单里的数字模式入口
- DigiManager 状态
- 如果方便，再附测试现场照片

### 7. 结论
请选一个最接近的结论：
- `菜单坏了，先别继续`
- `FT8 也坏了，补丁过深`
- `FT8 正常，但改频无效`
- `FT8 正常，改频有效，但 FT4 还是不发`
- `FT8 正常，FT4 开始能发，但改频仍有问题`
- `FT8 正常，FT4 能发，改频也生效`

## English
Please report in roughly this format:

### 1. Basic info
- test date:
- radio model:
- firmware filename:
- dummy load or disconnected antenna: `yes / no`

### 2. Boot and menu
- boot version shown:
- menu looks normal: `yes / no`
- digital-mode entry still present: `yes / no`

### 3. FT8 regression
- FT8 still transmits: `yes / no`
- if not, describe what happened:

### 4. Digital-mode retune
- idle retune: `yes / no / temporary`
- TX retune: `yes / no / temporary`
- extra notes:

### 5. FT4 transmit
- FT4 now really transmits: `yes / no`
- DigiManager reacts: `yes / no`
- radio shows any TX behavior: `yes / no`
- frequency changes during TX: `yes / no / temporary`

### 6. Screenshots or photos
Recommended:
- boot version screen
- digital-mode menu entry
- DigiManager status
- test bench photo if possible

### 7. Overall result
Pick the closest one:
- `menu broken, stop here`
- `FT8 also broken, patch too deep`
- `FT8 works, retune still blocked`
- `FT8 works, retune works, FT4 still blocked`
- `FT8 works, FT4 now transmits, retune still problematic`
- `FT8 works, FT4 transmits, retune works`
