# FT4 Firmware UART Bench Result Template

## 基本信息 / Basic Info
- Tester:
- Date:
- Radio:
- Serial port:
- Dummy load or no antenna confirmed:

## 工具检查结果 / Tool Check Result
- `check_uvk5cec_toolchain.py` output:
- `python` found:
- `arm-none-eabi-gcc` found:
- `make` found:
- `docker` found:

## 固件编译结果 / Firmware Build Result
- `build_uvk5cec_firmware.py --target auto` output:
- Build succeeded:
- Firmware file generated:
- Flashing succeeded:

## 离线协议检查结果 / Offline Protocol Check Result
- `mock_uvk5cec_ft4_responder.py` started:
- `bootstrap version=...` seen:
- `configure version=...` seen:
- `start_ft4_tx status=0(OK)` seen:
- `retune status=0(OK)` seen:
- `stop_tx status=0(OK)` seen:

## 真机 Bench 结果 / Real Bench Result
- `send-ft4` command:
- `retune` command:
- `stop-tx` command:
- Did the radio enter TX:
- Did retune change the frequency:
- Did `stop-tx` return to safe state:
- Spectrum observation:

## 失败点 / Failure Point
- Failed at step:
- Error message:
- Anything unusual on screen:

## 贴完整输出 / Paste Full Output
```text
Paste the important command output here.
```

