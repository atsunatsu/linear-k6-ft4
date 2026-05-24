# FT4 Protocol Analysis

## 1. Overview

- Design: High-speed contest mode, 2x faster than FT8
- T/R period: 7.5 seconds
- TX duration: ~4.48 seconds (per user observation)
- Sensitivity: ~3.2 dB worse than FT8

## 2. Encoding Pipeline

### 2.1 Source Encoding
- 77 bits user information per transmission
- 3 bits (i3) message type (0-7)
- 74 bits user data
- Supports: callsigns, grid locators, signal reports, acks

### 2.2 CRC
- 14-bit CRC (polynomial 0x6757)
- 77 + 14 = 91 bits

### 2.3 LDPC FEC
- (174, 91) LDPC code
- 91 bits + 83 parity = 174 bits
- Generator matrix: 83x91 (generator.dat)
- Parity matrix: 83x174 (parity.dat)

### 2.4 Channel Symbol Mapping
- 4-FSK modulation (2 bits/symbol)
- 174 / 2 = 87 data symbols
- Gray code mapping:
  - 00 -> 0
  - 01 -> 1
  - 11 -> 2
  - 10 -> 3

### 2.5 Sync Sequences (Costas Arrays)
Four 4-tone Costas arrays:
- S1 = {0, 1, 3, 2}
- S2 = {1, 0, 2, 3}
- S3 = {2, 3, 1, 0}
- S4 = {3, 2, 0, 1}

### 2.6 Full Symbol Sequence
```
{R, S1, M_A, S2, M_B, S3, M_C, S4, R}
```
- R = Ramp symbol (tone 0, 48ms raised-cosine ramp)
- M_A, M_B, M_C = Data symbols (29 each)
- Total: 105 symbols

### 2.7 GFSK Modulation
- Modulation index h = 1.0
- Gaussian filter BT = 1.0
- Symbol duration T = 48 ms
- Symbol rate = 1/0.048 = ~20.83 baud
- Soft keying: raised-cosine ramp over 48 ms

## 3. Modulation Parameters Table

| Parameter        | FT4       | FT8       |
|-----------------|-----------|-----------|
| Symbol duration T | 0.048 s  | 0.160 s   |
| Symbol rate      | ~20.83   | ~6.25     |
| Mod index h      | 1        | 1         |
| Pulse shape      | Gauss BT=1 | Gauss BT=2 |
| Modulation       | 4-FSK    | 8-FSK     |
| Total symbols    | 105      | 79        |

## 4. TX Duration

### FT8
79 symbols x 0.160s = 12.64s (confirmed)

### FT4
- Per protocol: 105 symbols x 0.048s = 5.04s (theoretical)
- Actual TX duration: ~4.48s (user measured)
- Difference may be due to ramp symbol handling

## 5. Comparison: FT4 vs FT8

| Feature          | FT4       | FT8       |
|-----------------|-----------|-----------|
| T/R period      | 7.5s      | 15s       |
| TX duration     | ~4.48s    | ~12.64s   |
| Symbol rate     | ~20.83    | ~6.25     |
| FSK tones       | 4         | 8         |
| Sensitivity     | worse     | better    |
| Use case        | Contest   | DXing     |

## 6. Firmware Problem

Current firmware treats FT4 like FT8:
- Uses 15s T/R period (should be 7.5s)
- TX duration ~12.64s (should be ~4.48s)
- May use wrong modulation parameters

### Firmware parameters to fix
1. T/R period: 15s -> 7.5s
2. TX duration: 12.64s -> 4.48s
3. Symbol duration: 0.160s -> 0.048s (if configurable)
4. Modulation: 8-FSK -> 4-FSK (if configurable)

## 7. References

- WSJT-X QEX Paper: FT4 and FT8 Communication Protocols
- Authors: K9AN, G4WJS, K1JT
- BK4819 datasheet for FSK register configuration
