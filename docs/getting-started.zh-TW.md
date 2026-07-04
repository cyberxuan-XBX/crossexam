# CrossExam 入門說明（給第一次用的人）

## 這是什麼

同一個問題丟給不同的 AI，常常得到不同答案。CrossExam 讓多個 AI 對同一個題目
先各自獨立分析、再互相驗證對方的說法、最後產出一份「共識 + 分歧表」。
你不用在視窗之間複製貼上，也不用自己判斷該信誰 — 分歧表會告訴你
哪些結論被多方驗證過、哪些還需要人做決定。

一切都是資料夾裡的純文字檔，沒有伺服器、不用架任何東西。

## 安裝

```bash
pip install crossexam
```

裝不了 pip 也行：把 `crossexam.py` 單檔複製到任何機器，
`alias cxam='python3 /路徑/crossexam.py'`。

## 你需要至少一種「腦」

任選，可混用，越多種越好：

| 你有什麼 | 就能開哪種席位 |
|---|---|
| AI 編程 CLI（Claude Code、Codex CLI、Gemini CLI…）且已登入 | Agentic 席 — 最強，會實際跑指令驗證 |
| 任何 OpenAI 相容 API（OpenAI、OpenRouter、公司自架模型、本機 Ollama…） | API 席 — 自動化，讀材料出意見 |
| 只有網頁版聊天帳號（ChatGPT、Claude.ai、Gemini…） | 剪貼簿席 — 複製貼上就能參加 |

## 第一局（3 分鐘）

```bash
cxam setup        # 一次性：自動偵測你裝的 AI CLI 和本地模型，寫好預設
mkdir review && cd review
cp ~/Downloads/report.csv .
cxam run "驗算 report.csv 的月度加總是否正確，找出任何異常列" --exhibit report.csv
```

預設面板 = 你那家廠商的三層模型（例：haiku/sonnet/opus）互相詰問，
最高層寫判決書。想跨廠商混桌才需要下面的進階寫法。

## 進階：自組面板（10 分鐘）

以「審一份報表數字對不對」為例，換成你自己的題目即可。

```bash
# 1. 開一個資料夾當考場，把要審的材料放進去
mkdir review && cd review
cp ~/Downloads/report.csv .

# 2. 一條指令開局（席位挑你有的填，一席起跑，兩席以上才有互驗價值）
cxam run --task "驗算 report.csv 的月度加總是否正確，找出任何異常列" \
  --exhibit report.csv \
  --agent 'claude=claude -p {prompt}' \
  --agent 'codex=codex exec --skip-git-repo-check {prompt}' \
  --api   'local=http://localhost:11434/v1|qwen2.5:14b'
```

程式會自動走完三個階段：

1. **盲寫** — 每個席位獨立分析，看不到彼此（防止跟風）
2. **互驗** — 互相檢查對方的具體說法；CLI 席會真的執行指令重算
3. **收斂** — 產出 `_Msg/synthesis.md`：共識 + 分歧表

**跑完先看分歧表。** 空的 = 各方獨立得到同一結論，可信度高；
有內容 = 這幾點需要你自己判斷，其他都不用你操心。

## 沒有任何 CLI？純網頁帳號也能開局

```bash
cxam init --task "你的題目"
cp 材料 _Msg/exhibits/

cxam brief --name gpt        # 印出一段提示詞 → 全選複製，貼到網頁聊天
# 把模型的回覆整段複製，貼回來：
cxam ingest --name gpt <<'EOF'
（貼上回覆）
EOF
```

換第二個腦（另一家的網頁帳號）重複一次，然後 `cxam phase debate`
再各跑一輪 brief/ingest，模型就會開始互相檢查。

## 常用指令

| 指令 | 用途 |
|---|---|
| `cxam status` | 看目前階段、各席位發言數 |
| `cxam log --all` | 看全程對話紀錄 |
| `cxam watch` | 即時直播（另開一個終端） |
| `cxam post info "補充說明" --as 你的名字` | 你隨時插話，所有席位都會看到 |
| `cxam phase blind\|debate\|closed` | 手動切換階段（run 模式會自動切） |

## 常見問題

| 狀況 | 處理 |
|---|---|
| `no claim from: X` 警告 | 該席位沒完成。CLI 席最常見原因是權限：Claude 加 `--allowedTools "Bash,Read,Write"`；Codex 記得加 `--skip-git-repo-check` |
| `unparseable reply` | 該模型太弱、吐不出要求的格式 — 換強一點的模型；原始回覆存在 `_Msg/analysis/<席位>.raw.txt` |
| `TIMEOUT` | 題目太大，加 `--seat-timeout 1800` |
| `already has traffic` | 這個資料夾開過局 — 加 `--force` 續跑，或換新資料夾 |

## `_Msg/` 資料夾是什麼？可以刪嗎？

CrossExam 的全部狀態就是這個資料夾：`bus.jsonl`（發言流水帳）、
`analysis/`（各席位的長篇分析）、`synthesis.md`（最終報告）、
`exhibits/`（你放的材料）。全是純文字，可以 git 版控、可以整包寄給別人、
局結束不要了就整個資料夾刪掉，乾乾淨淨。

## 一句話心法

**共識是賺到的，分歧是重點。** 這個工具的產出不是「AI 的答案」，
而是「哪些答案經得起別的 AI 用證據打，哪些地方輪到人類出手」。
