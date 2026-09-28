# handset_iface — RJ9 電話話筒 ↔ PC Line In / Line Out 轉接板

把類比電話話筒（RJ9 / 4P4C）接到電腦的 line out 與 line in，並用中介電路處理阻抗與電平，讓音量不掉。

目前版本：**Rev B**（新增 J2 話筒腳位選擇跳線 JP1–JP6）

## 電路概要

| 區塊 | 內容 |
|---|---|
| 路徑 A：PC line out → 聽筒 | J1 → R1/R2（L+R 混成單聲道）→ C1 → RV1 音量 → U1 LM386（Av = 20）→ C5 / R3 → EAR+；R4 + C6 為 Zobel |
| 路徑 B：麥克風 → PC line in | electret 麥克風，R5 提供偏壓 → C8 → U2A MCP6022 前級（Av = 5.5 ~ 51，RV2 調整）→ C11 / R10 → J3 |
| VREF | R11 / R12 分壓 + U2B 緩衝，提供 2.5 V 虛擬地 |
| 電源 | J4 USB-B 取 5 V → FB1 / C14；R6 / C7 濾波後給前級（+5V_FILT） |
| 話筒腳位選擇 | JP1–JP6 焊接跳線，見下節 |

## 話筒腳位選擇跳線（Rev B）

市面上的類比話筒，聽筒與麥克風的腳位組合不只一種，electret 麥克風也有極性。JP1–JP6 都是三墊式焊接跳線，出廠時 1–2 以銅箔預先短接（預設），要改設定時用刀片切斷 1–2 之間的細銅，再用錫把 2–3 接起來。

| 跳線 | 作用 | 1–2（預設） | 2–3 |
|---|---|---|---|
| JP1–JP4（四個一起改） | 聽筒 / 麥克風對調 | J2.1 = 聽筒 EAR+、J2.4 = 聽筒 GND、J2.2 / J2.3 = 麥克風 | J2.2 = 聽筒 EAR+、J2.3 = 聽筒 GND、J2.1 / J2.4 = 麥克風 |
| JP5–JP6（兩個一起改） | 麥克風極性 | 麥克風對的第一腳（MA）= MIC+，第二腳（MB）= GND | MA = GND，MB = MIC+ |

預設設定（全部 1–2）與 Rev A 的接法相同：J2 pin 1/4 = 聽筒，pin 2 = MIC+，pin 3 = MIC GND。

判斷方式：用三用電表量話筒線，聽筒那一對約 30–300 Ω 且正反向讀值相同；electret 麥克風那一對正反向讀值不同。麥克風極性最可靠的判斷是看膠囊本體：與金屬外殼相連的那一腳是 GND，另一腳是 MIC+。無法拆開時，也可以先用預設值試，沒有聲音或聲音極小再改 JP5–JP6。

## PCB

- 80 × 60 mm，兩層板，四角 M3 安裝孔
- 下緣由左到右：J1 LINE OUT、J3 LINE IN、RV1 VOL（Alps RK097，軸伸出板外）、J4 USB-B
- 上緣：J2 RJ9；J2 右側一排為 JP4、JP3、JP2、JP1（PAIR）與 JP5、JP6（MIC POL）
- 被動元件、IC 為 SMT（0805 / 1206 / SOIC-8）；J1–J4 與 RV1 為 THT；JP1–JP6 為 PCB 銅箔，不需零件
- 設計規則：clearance 0.2 mm，訊號線 0.3 mm，電源線 0.5 mm，via 0.6 / 0.3 mm；底層為 GND 平面

## 檔案

| 檔案 | 說明 |
|---|---|
| `handset_iface.kicad_pro / .kicad_sch / .kicad_pcb` | KiCad 專案 |
| `handset_iface_sch.pdf` | 原理圖 PDF |
| `pcb_top.png`, `pcb_bottom.png` | PCB 正反面預覽 |
| `handset_iface_gerber.zip` | Gerber + Excellon 鑽孔檔（送板廠） |
| `handset_iface_pos_top.csv` | SMT 座標檔（原點：板子左下角） |
| `handset_iface_BOM.csv` | BOM（跳線為銅箔，不列入） |
| `scripts/` | 產生原理圖、擺放、自動佈線、預覽所用的 Python 腳本（KiCad 7 pcbnew API；路徑為產生時的環境，需自行調整） |

## 版本紀錄

- **Rev B**：新增 J2 腳位選擇跳線 JP1–JP6（聽筒 / 麥克風對調、麥克風極性）
- **Rev A**：初版原理圖與兩層板 layout
