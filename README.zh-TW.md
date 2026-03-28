# EvalBot — 教學評估表單自動填寫工具

> *「評估的目的是改進，而非證明。」* — Daniel Stufflebeam

## 為什麼要做這個工具

### 形式主義的代價

醫學教育評估制度的初衷是好的：透過結構化的回饋機制，確保每位受訓醫師得到充分的臨床指導與評量。DOPS 評估操作技能、Mini-CEX 評估臨床能力、360 度評量蒐集多元回饋、EPA 追蹤信賴等級 —— 每一種表單背後都有扎實的教育理論支撐。

然而，當一位主治醫師同時帶領多位受訓醫師，每人每月需要完成數份甚至十數份評估表單時，制度的良善初衷便逐漸被行政負擔所吞噬。教師花在填寫表單的時間，遠超過表單本身所能承載的教育價值。

這就是**形式主義的表演**（performative formalism）—— 一種著重外在程序而忽略實質內容的行為模式。社會學家高夫曼（Erving Goffman）的「擬劇理論」精確地描述了這個現象：當評估成為例行的「舞台演出」，教師在前台（front stage）扮演符合制度期待的角色，填寫「正確」的分數與「適當」的評語，而真正有教育意義的互動，早已在病房、在手術台旁、在晨會討論中完成了。

形式主義表演的特徵在醫學教育評估中無處不在：

- **唯指標行為**：填寫評估表的目的是讓護照完成度達到 100%，而非真正反映學員的學習歷程
- **偽裝完美**：所有學員都得到 7-9 分的量尺評分、幾乎相同的正向評語，個體差異被抹平
- **無用功的堆疊**：同一位學員的同一項技能，需要填寫格式幾乎相同但系統編號不同的五份表單

當制度的形式壓過了實質，當指標取代了目標，臨床教師面臨一個選擇：花兩小時填表，還是花兩小時帶學員看一個困難的病例？

### 我們的立場

**這個工具不是在偷懶，而是在奪回被形式主義偷走的時間。**

EvalBot 自動化的是機械性的部分 —— 選擇能力等級、評分量尺、產生符合語境的正向評語。它讓臨床教師把有限的時間，重新投入到真正重要的事情上：在病床旁教學、討論困難病例、指導下一代醫師的成長。

真正的教學評估，從來不在表單上。

## 架構

```
evalbot CLI (Python)          Claude Code Agent
  ├── list    → JSON    ←──  讀取待評估清單
  ├── parse   → JSON    ←──  解析表單結構
  ├── profile → JSON    ←──  讀取評核者身分
  ├── radio   ← submit  ──→  選擇最佳選項
  ├── text    ← submit  ──→  產生正向評語
  ├── textarea← submit  ──→  產生正向評語
  ├── checkbox← submit  ──→  勾選選項
  ├── combo   ← submit  ──→  選擇下拉選項
  ├── date    ← submit  ──→  填入日期
  ├── ruler   ← submit  ──→  填入分數
  └── finalize← submit  ──→  完成評估
```

Python 處理 HTTP/HTML 解析與提交，Claude Code 負責理解表單語意、產生評語。不需要額外的 API key —— 執行這個工具的 agent 本身就是語言模型。

## 前置需求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.com/claude-code)

## 安裝

```bash
make setup
```

## Cookie 與 Profile 設定

支援多使用者 profile：

```
profiles/
├── default/
│   ├── cookies.json      ← 瀏覽器匯出的 cookie
│   └── profile.json      ← 身分資訊（姓名、職稱、科別）
├── user2/
│   ├── cookies.json
│   └── profile.json
└── ...
```

### 設定步驟

1. `mkdir -p profiles/yourname`
2. 瀏覽器登入系統 → Cookie 匯出擴充套件匯出 JSON → 存為 `profiles/yourname/cookies.json`
3. 建立 `profiles/yourname/profile.json`：

```json
{
  "name": "你的姓名",
  "role": "主治醫師",
  "department": "你的科別"
}
```

> `role` 用來自動選擇「評核者身分」（主治醫師/住院醫師/護理師/同儕等）

## 使用方式

### 在 Claude Code 中使用 skill（推薦）

```
/eval-form
/eval-form --user user2
```

Agent 會自動：讀取 profile → 列出待評估表單 → 逐一解析 → 產生評語 → 填寫送出

### 手動 CLI

```bash
# 列出待評估表單
make list
make list USER=user2

# 查看 profile
uv run python -m evalbot -u user2 profile

# 解析單一表單
make parse SFID=88492

# 個別提交
uv run python -m evalbot radio --sfid=88492 110443 113734
uv run python -m evalbot textarea --sfid=88492 110446 "表現優異，操作流暢"
uv run python -m evalbot ruler --sfid=88492 106503 8
uv run python -m evalbot finalize --sfid=88492
```

## 注意事項

- Session cookie 過期 → 重新匯出 cookies.json
- 每次 AJAX 間隔 0.5 秒，避免伺服器負擔
- 所有送出的評語會記錄在 `log/submissions.jsonl`
- 建議先用 `make parse SFID=XXX` 確認表單結構

---

## 如何為你的醫院建立自己的評估填寫系統

這個專案是針對特定醫院的 e-portfolio 系統開發的，但**模式是通用的**。如果你的醫院使用類似的網頁式評估系統，你可以 clone 這個 repo，幾小時內改造成自己的版本。

### 核心模式

```
瀏覽器（手動操作）    →  .har 檔案  →  Claude Code 分析  →  Python CLI 工具  →  Claude Code skill
     ↓                     ↓               ↓                    ↓                  ↓
登入 + 手動填一份表單   擷取網路流量    逆向工程 API         建立解析器+提交器      編排自動化流程
```

### 步驟一：擷取 HAR 檔案

1. 用 Chrome/Edge 開啟你醫院的評估系統
2. 開啟開發者工具（`F12`）→ **Network** 分頁 → 勾選 **Preserve log**
3. 登入系統，進入一份評估表單，**手動完整填寫一份**（每種欄位類型都要碰到 —— 單選、文字、下拉、量尺等）
4. 在 Network 面板右鍵 → **Save all as HAR with content**
5. 儲存為專案根目錄下的 `your-system.har`

> 這一個 HAR 檔案包含了所有的 API 端點、請求格式、回應結構、認證機制。它是你的羅塞塔石碑。

### 步驟二：讓 Claude Code 分析 HAR

在專案目錄啟動 Claude Code session，貼上這段 prompt：

```
分析 ./your-system.har 這個 HAR 檔案，找出：

1. 認證機制：session 怎麼運作？（cookie、token、header）
2. 表單列表：哪個 URL 列出待評估表單？HTML 結構是什麼？
3. 表單載入：哪個 URL 載入單一評估表單？欄位怎麼組織？
4. 欄位提交：哪些 AJAX 端點處理各種欄位類型？送什麼參數？
5. 表單完成：怎麼標記評估為已完成？

對每個 AJAX 端點，記錄：
- HTTP 方法與 URL
- 請求參數（附 HAR 中的實際範例）
- 回應格式
- JavaScript 怎麼觸發它（函式名稱、事件處理器）

輸出一份結構化的參考文件，我可以用來建立 CLI 工具。
```

Claude Code 會讀取 HAR、解析 JavaScript、追蹤 AJAX 呼叫，產出完整的 API 參考文件。

### 步驟三：建立 Python CLI

```bash
uv init --name evalbot
uv add requests beautifulsoup4
mkdir -p src/evalbot
```

CLI 子指令遵循同一模式：`list`、`parse`、`radio`、`text`、`textarea`、`ruler`、`checkbox`、`combo`、`date`、`finalize`、`profile`。

設計原則：
- **所有輸出都是 JSON** —— CLI 是給 Claude Code 驅動的工具，不是給人看的
- **每個指令都重新解析表單** —— 取得最新的 token/session 值
- **POST 加上 `Referer` header** —— 很多系統會驗證這個
- **每次提交記錄到 `log/submissions.jsonl`** —— 留下稽核軌跡

### 步驟四：建立 Claude Code Skill

建立 `.claude/skills/eval-form/SKILL.md`，教 Claude Code：

1. `evalbot profile` → 知道評核者的身分
2. `evalbot list` → 取得待評估表單
3. `evalbot parse --sfid=X` → 讀取表單結構
4. 根據欄位類型與標籤語意決定填什麼
5. **直接產生評語** —— 不需要 API 呼叫，Claude Code 本身就是語言模型
6. 透過 `evalbot radio/text/textarea/ruler/...` 提交
7. `evalbot finalize` 完成評估

Skill 檔案是關鍵 —— 它編碼了領域知識：選什麼分數、怎麼寫評語、哪些欄位要跳過。

### 步驟五：測試

```bash
uv run python -m evalbot list              # 確認連線
uv run python -m evalbot parse --sfid=123  # 檢查表單結構
# 然後在 Claude Code 中輸入：/eval-form
```

### 小提示

- **從一種表單開始**（例如 DOPS），做到完整可用，再擴展到其他類型
- **HAR 檔案是你的羅塞塔石碑** —— 端點、參數、JS 原始碼、HTML 結構全在裡面
- **注意 CSRF token** —— 有些系統會在隱藏欄位或 meta 標籤中嵌入
- **保留 `log/submissions.jsonl`** —— 你的稽核軌跡與除錯紀錄

### 給新系統的起手 Prompt

如果你有一個完全不同系統的 HAR 檔案：

```
我有一個來自我們醫院教學評估系統的 HAR 檔案。
我想建立一個 CLI 工具，可以：
1. 列出待評估表單
2. 解析表單結構
3. 填寫欄位（單選、文字、量尺等）
4. 送出完成的評估

請分析這個 HAR 檔案，逆向工程 API，
幫我建立一個 Python CLI，遵循這個 repo 的 evalbot 模式。
先從讀取 HAR 檔案開始。
```

Claude Code 會接手完成。

---

[English README](README.md)
