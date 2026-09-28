# handset_iface — RJ9 電話話筒 ↔ PC Line In / Line Out 轉接板

把類比電話話筒（RJ9 / 4P4C）接到電腦的 line out 與 line in，並用中介電路處理阻抗與電平，讓音量不掉。

## 電路概要

| 區塊 | 內容 |
|---|---|
| 路徑 A：PC line out → 聽筒 | J1 → R1/R2（L+R 混成單聲道）→ C1 → RV1 音量 → U1 LM386（Av = 20）→ C5 / R3 → J2 聽筒；R4 + C6 為 Zobel |
| 路徑 B：麥克風 → PC line in | J2 electret 麥克風，R5 提供偏壓 → C8 → U2A MCP6022 前級（Av = 5.5 ~ 51，RV2 調整）→ C11 / R10 → J3 |
| VREF | R11 / R12 分壓 + U2B 緩衝，提供 2.5 V 虛擬地 |
| 電源 | J4 USB-B 取 5 V → FB1 / C14；R6 / C7 濾波後給前級（+5V_FILT） |

## PCB

- 80 × 60 mm，兩層板，四角 M3 安裝孔
- 下緣由左到右：J1 LINE OUT、J3 LINE IN、RV1 VOL（Alps RK097，軸伸出板外）、J4 USB-B
- 上緣：J2 RJ9
- 被動元件、IC 為 SMT（0805 / 1206 / SOIC-8）；J1–J4 與 RV1 為 THT
- 設計規則：clearance 0.2 mm，訊號線 0.3 mm，電源線 0.5 mm，via 0.6 / 0.3 mm；底層為完整 GND 平面

## 檔案

| 檔案 | 說明 |
|---|---|
| `handset_iface.kicad_pro / .kicad_sch / .kicad_pcb` | KiCad 專案 |
| `handset_iface_sch.pdf` | 原理圖 PDF |
| `pcb_top.png`, `pcb_bottom.png` | PCB 正反面預覽 |
| `handset_iface_gerber.zip` | Gerber + Excellon 鑽孔檔（送板廠） |
| `handset_iface_pos_top.csv` | SMT 座標檔（原點：板子左下角） |
| `handset_iface_BOM.csv` | BOM |
| `scripts/` | 產生原理圖、擺放、自動佈線、預覽所用的 Python 腳本（KiCad 7 pcbnew API；路徑為產生時的環境，需自行調整） |

## 注意

RJ9 話筒的腳位沒有統一標準。本版預設 J2 pin 1/4 = 聽筒、pin 2/3 = 麥克風（pin 2 為 MIC+）。使用前請先用三用電表確認話筒腳位。
