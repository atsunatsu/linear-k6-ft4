#!/usr/bin/env python3
"""
DFACS 文献库增强脚本：
1. 添加两篇综述论文本身到笔记库
2. 创建主题分类页
3. 修复/补充之前丢的文献
"""
import os, re

VAULT = "/mnt/c/Users/3301/Documents/Obsidian Vault"
LIB_DIR = os.path.join(VAULT, "DFACS 文献库")

# ─── 1. Add the two review papers ───
reviews = [
    {
        "fname": "Jiao2024_A review on DFACS (I) System design and dynamics modeling.md",
        "content": """---
tags: [DFACS/drag-free, English, review, survey]
source: Original
year: 2024
first_author: Jiao B
---

# A review on DFACS (I): System design and dynamics modeling

**作者：** Jiao B, Liu Q, Dang Z, Yue X, Zhang Y, Xia Y, Duan L, Hu Q, Yue C, Wang P, Guo M, Duan Z, Cui B, Zhang C, Shao X

**期刊：** Chinese Journal of Aeronautics
**年份：** 2024
**卷期：** 37(1)
**页码：** 92-119
**DOI：** [10.1016/j.cja.2024.01.031](https://doi.org/10.1016/j.cja.2024.01.031)

**语言：** 英文

## 摘要

This paper provides a comprehensive review of Drag-Free and Attitude Control System (DFACS) design and dynamics modeling for space-based gravitational wave detection missions, covering LISA, TianQin, Taiji, and related technology demonstration missions. The review covers:

- **System design architectures** for drag-free control
- **Dynamics modeling** approaches for DFACS
- **Key missions** (LISA Pathfinder, GRACE-FO, MICROSCOPE, TianQin, Taiji)
- **Control methods** for drag-free operations

## 关键词
Drag-free, DFACS, System Design, Dynamics Modeling, Control design

## 参考文献数
193

---
*手动录入*
"""
    },
    {
        "fname": "Yue2024_A review on DFACS (II) Modeling and analysis of disturbances and noises.md",
        "content": """---
tags: [DFACS/drag-free, English, review, survey]
source: Original
year: 2024
first_author: Yue C
---

# A review on DFACS (II): Modeling and analysis of disturbances and noises

**作者：** Yue C, Jiao B, Dang Z, Yue X, Zhang Y, Xia Y, Duan L, Hu Q, Liu Q, Wang P, Guo M, Duan Z, Cui B, Zhang C, Shao X

**期刊：** Chinese Journal of Aeronautics
**年份：** 2024
**卷期：** 37(2)
**页码：** 120-147
**DOI：** [10.1016/j.cja.2024.02.013](https://doi.org/10.1016/j.cja.2024.02.013)

**语言：** 英文

## 摘要

This paper provides a comprehensive review of disturbances and noise modeling for Drag-Free and Attitude Control System (DFACS) in space-based gravitational wave detection missions. The review covers:

- **Gravitational disturbances** and their effects
- **Non-gravitational disturbances** (solar radiation pressure, atmospheric drag, etc.)
- **Sensor noise** modeling
- **Actuator noise** and thruster disturbances
- **Environmental disturbances** at Lagrange points
- **Noise budget analysis** for LISA, TianQin, Taiji

## 关键词
DFACS, drag-free, disturbances, noise modeling, gravitational wave detection

## 参考文献数
154

---
*手动录入*
"""
    }
]

for review in reviews:
    path = os.path.join(LIB_DIR, review["fname"])
    with open(path, 'w', encoding='utf-8') as f:
        f.write(review["content"].strip())
    print(f"Created: {review['fname']}")

# ─── 2. Create topic pages ───
topics = {
    "DFACS 系统设计": """---
tags: [DFACS/drag-free, topic-page]
---

# DFACS 系统设计

Drag-Free and Attitude Control System 的系统架构与设计方法。

## 核心文献

### 综述
- [[Jiao2024_A review on DFACS (I) System design and dynamics modeling]]
- [[Yue2024_A review on DFACS (II) Modeling and analysis of disturbances and noises]]

### 经典奠基
- [[B1964_The drag-free satellite]] — Lange (1964)，无拖曳卫星概念奠基
- [[L2010_Survey of drag-free satellite]] — Shi L et al. (2010)，无拖曳卫星综述

### 航天任务
- [[J2007_On-orbit performance of Gravity Probe B drag-free translatio]]
- [[M2019_LISA Pathfinder platform stability and drag-free performance]]
- [[P2017_MICROSCOPE mission On-orbit assessment of the drag-free and]]
- [[S2018_MICROSCOPE mission drag-free and attitude control system exp]]
- [[Z2021_The drag-free control design and in- orbit experimental resu]]
- [[A2018_In-orbit performance of the LISA Pathfinder drag-free and att]]

---
*自动整理*
""",
    "天琴计划": """---
tags: [DFACS/drag-free, topic-page, TianQin]
---

# 天琴计划 (TianQin)

天琴计划是中国提出的空间引力波探测计划，采用地心轨道三颗卫星构成等边三角形干涉仪。

## 核心文献

### 任务总体
- [[Luo2016_TianQin A space-borne gravitational wave detector]]
- [[Jiao2024_A review on DFACS (I) System design and dynamics modeling]]
- [[Yue2024_A review on DFACS (II) Modeling and analysis of disturbances and noises]]

### DFACS 相关
- [[H2021_Key issues in the research on drag-free control for TianQin]]
- [[X2021_Frequency separation control for drag-free satellite with fr]]
- [[X2022_Test mass capture for drag-free satellite based on RBF neura]]
- [[Y2019_Research on control algorithm for the drag-free satellite [d]]
- [[H2019_A new design of drag-free and attitude control based on non-]]

### 噪声与扰动
- [[SH2019_Finding the suitable drag-free acceler- ation noise level fo]]
- [[L2020_Adaptive drag-free control of gravity field satellites via a]]
- [[K2020_Effects of thrust noise and measurement noise on drag-free a]]

---
*自动整理*
""",
    "太极计划": """---
tags: [DFACS/drag-free, topic-page, Taiji]
---

# 太极计划 (Taiji)

太极计划是中国提出的空间引力波探测计划，采用日心轨道三颗卫星构成等边三角形干涉仪。

## 核心文献

### 任务总体
- [[Luo2021_The Taiji program: A concise overview]]
- [[Luo2020_Taiji-1 satellite mission]]
- [[Z2021_The drag-free control design and in- orbit experimental resu]]
- [[Jiao2024_A review on DFACS (I) System design and dynamics modeling]]

### Taiji-1 在轨验证
- [[Hu2021_The drag-free control design and in-orbit experimental results of Taiji-1]]
- [[H2021_H1 robust controller design for deep space drag-free satelli]]

---
*自动整理*
""",
    "LISA 任务": """---
tags: [DFACS/drag-free, topic-page, LISA]
---

# LISA (Laser Interferometer Space Antenna)

LISA 是 ESA/NASA 提出的空间引力波探测计划，采用日心轨道三颗卫星构成等边三角形干涉仪。

## 核心文献

### 任务总体
- [[Danzmann2000_LISA mission overview]]
- [[A2001_LISA mission study overview]]
- [[A2000_Study of the laser interferometer space antenna]]

### LISA Pathfinder 在轨验证
- [[A2018_In-orbit performance of the LISA Pathfinder drag-free and att]]
- [[M2019_LISA Pathfinder platform stability and drag-free performance]]
- [[WJ2003_Position sensors for flight testing of LISA drag-free control]]
- [[N2004_End-to-end modeling for drag-free missions with application]]

### DFACS 相关
- [[B2011_LISA Pathfinder drag-free control and system implications]]
- [[F2009_LISA Pathfinder drag-free control and system implications]]
- [[G2012_LISA Pathfinder drag-free control and system design]]

---
*自动整理*
""",
    "扰动与噪声": """---
tags: [DFACS/drag-free, topic-page, disturbances, noise]
---

# 扰动与噪声建模

DFACS 中的各种扰动源和噪声建模方法。

## 核心文献

### 综述
- [[Yue2024_A review on DFACS (II) Modeling and analysis of disturbances and noises]]

### 引力扰动
- [[AP2009_Gravitational distur- bances in drag-free spacecraft]]
- [[D2014_Invited article Advanced drag-free concepts for future space]]

### 推力器噪声
- [[K2020_Effects of thrust noise and measurement noise on drag-free a]]
- [[N2004_End-to-end modeling for drag-free missions with application]]

### 传感器噪声
- [[A2001_Progress in the development of a position sensor for LISA dr]]
- [[P2006_A charge control method for inertial mass for space gravitational wave detection]]

---
*自动整理*
""",
    "无拖曳控制方法": """---
tags: [DFACS/drag-free, topic-page, control]
---

# 无拖曳控制方法

Drag-Free 控制算法与方法论。

## 核心文献

### 经典方法
- [[S2008_Spacecraft drag-free attitude control system design with qua]]
- [[Y2015_Finite-time rlative position control for drag-free dual-sate]]
- [[W2015_Disturbance estimation and compensation for drag-free satell]]

### 自适应/鲁棒控制
- [[H2016_Adaptive failure compensation control for LEO drag-free sate]]
- [[H2021_H1 robust controller design for deep space drag-free satelli]]
- [[L2020_Adaptive drag-free control of gravity field satellites via a]]

### 频率分离
- [[X2021_Frequency separation control for drag-free satellite with fr]]
- [[E2010_Local orbital frame predictor for LEO drag-free satellite]]
- [[E2014_Angular drag-free control and fine satellite-to-satellite poi]]

### 捕获控制
- [[X2022_Test mass capture for drag-free satellite based on RBF neura]]
- [[Z2019_Research on the drag-free control spacecraft with two test m]]

---
*自动整理*
"""
}

for topic_name, content in topics.items():
    fname = topic_name + ".md"
    path = os.path.join(LIB_DIR, fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"Created topic: {fname}")

print(f"\nDone! Reviews: {len(reviews)}, Topics: {len(topics)}")
