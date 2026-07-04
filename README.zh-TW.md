[English](README.md) | 繁體中文

# CrossExam 交互詰問

[![CI](https://github.com/cyberxuan-XBX/crossexam/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberxuan-XBX/crossexam/actions)
[![PyPI](https://img.shields.io/pypi/v/crossexam)](https://pypi.org/project/crossexam/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/crossexam/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**三個 AI 稽核同一份門禁紀錄，分別回報場內有 56、61、63 台車。
真相是它們互相詰問之後才出現的。**

讓你的 AI 出庭作證。CrossExam 是一個多代理辯論協議 + 零依賴 CLI，讓
**Claude Code、Codex CLI、Gemini CLI、aider，以及任何 LLM**（API 或網頁版）
對同一個問題先盲寫作答，再**用真實指令互相詰問** — 程式碼審查、log 稽核、
文件審閱，任何「單一模型的自信答案不夠好」的場合。沒有伺服器、沒有框架、
不強制 API key：只有一個可以 `git diff` 的純文字資料夾。

面板在線上長這樣（`bash examples/simulated-debate.sh` 的真實輸出 —
不接 AI、純協議、約 5 秒）：

```console
=== 2. blind phase: three seats post independent claims
sealed as sonnet (claim) — envelopes open when the moderator flips to debate
sealed as gpt (claim) — envelopes open when the moderator flips to debate
sealed as gemini (claim) — envelopes open when the moderator flips to debate

=== 3. blind means blind: sonnet 想偷看 — 匯流排上根本沒有東西
(no unread messages; phase: blind)

=== 4. 主持人開辯論：拆封
phase -> debate (3 sealed claim(s) revealed)

=== 8. 全程紀錄（主持人視角）
#1   sonnet     claim     56 台在場；信了儀表板聚合值
#2   gpt        claim     63 台；抓到 7 筆鬼影出場（進場後 5-9 秒假出場）
#3   gemini     claim     61 台；雙向排除 49 筆讀不到的車牌
#4   moderator  info      phase -> debate
#5   sonnet     verify    gpt 的 7 筆鬼影重現成功：7 組進出間隔低於 10 秒，物理上不可能
#6   gemini     challenge gpt 漏了 11 筆：5 位有帳號但車牌未授權者，永遠 Pass=False
#7   sonnet     concede   我的 56 是儀表板聚合假象；採用 gpt 的事件級框架
#8   moderator  info      phase -> closed
```

第 7 行就是整個產品：一個模型**因為證據而認輸**，不是因為客氣。

```
 終端 1                  終端 2                  終端 3
 CX_SEAT=sonnet claude   CX_SEAT=gpt codex       CX_SEAT=gemini gemini
      │                        │                        │
      └────────┬───────────────┴────────────┬───────────┘
               ▼                            ▼
        _Msg/bus.jsonl   ◄── 只進不改的結論匯流排
        _Msg/analysis/   ◄── 各席位的長文證據
        _Msg/exhibits/   ◄── 受審材料（log、diff、文件）
        _Msg/task.md     ◄── 階段：blind → debate → closed
```

## 為什麼

上面那段是真實事件的重演。三個 AI session 稽核同一份車輛門禁紀錄，回報
**56、61、63** 三個數字。如果你只開了一個視窗 — 而多數人只開一個視窗 —
你就會把拿到的那個數字直接交出去，永遠不知道另外兩個存在。

把它們的結論互貼、並要求用真實查詢驗證而不是嘴上辯論之後，出現了比任何
單一模型都好的東西：一個 session 用自己的指令**重現**了另一個的鬼影發現、
承認自己的 56 是儀表板聚合假象，第三個抓到兩者都漏掉的 11 筆。最終答案
不是平均出來的，是**被詰問出來的**：每個活下來的數字，都被另一個模型用
自己跑的指令重現過。

工作流機械化之後這件事持續發生：在後來一次真實面板中，Anthropic 席在
詰問壓力下**用數學推翻了自己稍早的結論**，OpenAI 席獨立重現出一模一樣的
四個數字。模型就是會分叉 — 不同廠商會分叉，同一個模型跑兩次也會分叉
（self-consistency、multi-agent debate、LLM jury 整條研究線都因此而生，
見[參考文獻](#參考文獻)）。CrossExam 把人肉傳話儀式變成協議。

## 安裝

```bash
pip install crossexam
# 或零依賴備案：把 crossexam.py 複製到任何地方，alias cxam='python3 crossexam.py'
```

單一檔案、純標準庫、Python ≥ 3.9。

## 快速開始 — 一句話

```bash
cxam setup                      # 一次性：偵測你裝的 AI CLI + 本地模型
cxam run "稽核 auth.py 的 token 過期 bug"
```

`setup` 偵測你手上已有的東西（claude / codex / gemini CLI，或本地
Ollama/vLLM/LM Studio），寫出可自行編輯的預設檔。預設面板 = 你那家廠商的
**三層模型階梯互相詰問**——每家大廠都出至少三級模型（haiku/sonnet/opus、
codex-mini/codex/codex-max、flash-lite/flash/pro），而層級之間的分歧，正好
標出「便宜模型錯在哪」或「旗艦模型想太多」。最高層負責寫判決書。

`run` 接著跑完整生命週期：各席位盲寫調查（CLI 席真的在你的 repo 跑指令；
API 席自動被簡報 `_Msg/exhibits/` 的材料）→ 切入辯論互相詰問 → 產出
`synthesis.md`：共識 + 明列的分歧表，直接印在終端。

審 log、文件、對話而不是程式碼？加 `--exhibit 檔案`（可重複）。
在 Claude Code 裡面用？有 [`/crossexam` 斜線指令](adapters/claude-code-skill.md)。

### 跨廠商與自訂面板

明確給席位，旗標永遠蓋過預設：

```bash
cxam run "同一個問題" \
  --agent 'sonnet=claude -p {prompt}' \
  --agent 'gpt=codex exec --skip-git-repo-check {prompt}' \
  --api   'qwen=http://localhost:11434/v1|qwen2.5:14b'
```

或把自己的陣容存進 `~/.config/crossexam/config.json`，用 `--preset 名字` 挑。

### Live 模式（進階）

想用真互動 session — 載你的記憶檔、釘精確模型版本、隨時介入引導？

```bash
cxam init --task "..."
# 每席一個終端：
CX_SEAT=sonnet claude      # /model 可釘任何精確版本
CX_SEAT=gpt    codex
```

各 CLI 接上對應 adapter（[adapters/](adapters/)）；每回合席位跑
`cxam read`、動工、寫回：

```bash
cxam post claim   "63 台在場；7 筆鬼影出場" --ref analysis/gpt.md#ghosts
cxam post verify  "sonnet 的配對檢查重現成功 7/7" --ref analysis/gpt.md#recheck
cxam post concede "我的數字是聚合假象；採用 gpt 的框架"
```

你的工作縮減成：在任一視窗打「繼續」、claim 到齊時 `cxam phase debate`。
隨時插話：`cxam post info "先查出口感測器" --as 你的名字`，全席都收到。

## 任何 LLM 都能入席

三種席位，同桌混用：

| 席位 | 誰 | 驗證方式 | 怎麼入席 |
|---|---|---|---|
| **Agentic** | Claude Code、Codex CLI、Gemini CLI、aider… | **執行指令** | hook / 記憶檔 adapter，或 `cxam run` 無頭驅動 |
| **API** | 任何 OpenAI 相容端點：OpenAI、Anthropic/Gemini 相容層、OpenRouter、**自架 vLLM / Ollama / LM Studio / 自有微調模型** | 引用材料 | `cxam seat` 一次跑完一回合：簡報 → 模型 → 分析歸檔 → 結論上匯流排 |
| **Clipboard** | 網頁版用戶：ChatGPT、Claude.ai、任何聊天介面，零 API | 引用材料 | `cxam brief` 印出自包提示詞；回覆貼給 `cxam ingest` |

```bash
# 你自己的地端模型入席（例：Ollama）
cxam seat --name qwen --endpoint http://localhost:11434/v1 --model qwen2.5:14b

# 網頁版模型入席
cxam brief --name grok   # 複製到網頁聊天 → 回覆貼回 cxam ingest --name grok
```

**誠實註記：** API 與剪貼簿席位不能執行指令，驗證靠引用而非執行。
它們的訊息帶 `via` 欄位（`api` / `clipboard`），收斂時可據此加權。

## 協議

三階段，由 CLI 強制執行：

| 階段 | 發生什麼 | 強制什麼 |
|---|---|---|
| **blind 盲寫** | 各席獨立分析、發一條 `claim` | claim 進**彌封信封**（`.sealed/`，不上匯流排），辯論開啟才拆封；`cxam read` 另過濾繞道訊息；拒收 verify/challenge/concede |
| **debate 詰問** | 挑他席「具體可查證」的說法，**跑指令**驗證 | verify/challenge 不附證據 `--ref` 會被警告；輸家明文 `concede` |
| **closed 收斂** | 指定席寫 `synthesis.md`：共識 + **分歧表** | 匯流排只收 info |

五種訊息：`claim` / `verify` / `challenge` / `concede` / `info`。一條一行
JSON。結論上匯流排，長文進 `analysis/`。

詰問後仍一致 = 掙來的信度；仍分歧 = 分歧表精準標出**需要你判斷的位置**。
分叉是訊號，不是雜訊。

## 常見問題

**session 之間即時通訊嗎？**
CLI 代理是回合制的，訊息在回合邊界收取。實務上你在某視窗打「繼續」，那席
就跟上進度；Claude Code 的 hook adapter 每次輸入自動顯示未讀數。
`cxam run` 模式完全不需要人工推進。

**為什麼不直接用 subagent？**
Subagent 是一顆腦扇出 — 同廠商、通常無記憶、釘不了版本，而且出題者自己
改考卷。CrossExam 的席位是互相獨立的完整 session，互改考卷。

**幾席才夠？**
不限。兩席等於多一個審查者；三席以上就是陪審團，有多數決訊號。

**Windows？**
協議、測試、全部核心指令純標準庫原生可跑，檔案鎖優雅降級。一個但書：
`cxam run --agent` 透過 POSIX shell 開席，Windows 上請在 WSL 或 Git Bash
驅動 agent 席（API 席與剪貼簿席無此限制）。

**壞掉的 agent 能在盲寫期偷看嗎？**
偷不到匯流排：盲寫期的 claim 在彌封信封裡，辯論開啟前匯流排上根本沒有。
`analysis/*.md` 仍是普通檔案 — adapter 明令禁讀，但那部分是紀律不是邊界。
完整威脅模型見 [SECURITY.md](SECURITY.md)。

**它會幫我管理 CLI 程序嗎？**
`cxam run` 會開無頭回合；除此之外它不是程序管理器 — tmux / claude-squad
類工具管那個，跟本工具正好互補。協議本身永遠不強制 API key；`cxam seat`
只是給沒有 CLI 的模型的選配橋樑。

## 相關專案

2026-07-04 掃了 40+ 個鄰居 — 含星數的完整表在
[docs/related-work.md](docs/related-work.md)。兩個軸看懂全地圖：
**誰驗證**（沒人／主模型／獨立同儕）×**怎麼驗**（嘴上辯論與排名／執行指令）：

| | 嘴上辯論與排名 | 執行指令 |
|---|---|---|
| **沒人驗證／純傳輸** | [agmsg](https://github.com/fujibee/agmsg)、[hcom](https://github.com/aannoo/hcom)、[claude-squad](https://github.com/smtg-ai/claude-squad)¹ | — |
| **主模型改考卷** | [llm-council](https://github.com/karpathy/llm-council)（22k★）、[PAL/zen-mcp](https://github.com/BeehiveInnovations/pal-mcp-server)（11.6k★）、[ensemble](https://github.com/raiyanyahya/ensemble)、[adversarial-review](https://github.com/alecnielsen/adversarial-review) | — |
| **獨立同儕互驗** | [MassGen](https://github.com/massgen/MassGen)、學術辯論 repo | **CrossExam** |

¹ 程序管理器把多個 session 排排開但彼此不說話，與 CrossExam 互補。

就我們所能查證，「執行指令 × 獨立同儕」這格是空的：議會類辯的是*文字*
（審查者從不對你的 repo 跑任何指令）、傳輸類不帶驗證協議、主從審查類則是
考官自己改考卷。如果我們漏了你的專案，開 issue，我們補引用。

## 參考文獻

協議站在前人肩上：

- Du, Li, Torralba, Tenenbaum & Mordatch (2023). *Improving Factuality and
  Reasoning in Language Models through Multiagent Debate.*
  [arXiv:2305.14325](https://arxiv.org/abs/2305.14325) — 模型互辯提升事實性；
  CrossExam 加上指令級驗證。
- Wang et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning.*
  [arXiv:2203.11171](https://arxiv.org/abs/2203.11171) — 為什麼同一個模型
  也值得多跑幾次獨立推理。
- Erman, Hayes-Roth, Lesser & Reddy (1980). *The Hearsay-II
  Speech-Understanding System.* ACM Computing Surveys 12(2) — 黑板架構的
  原點。`_Msg/` 就是一塊黑板，46 年後。
- Verga et al. (2024). *Replacing Judges with Juries.*
  [arXiv:2404.18796](https://arxiv.org/abs/2404.18796) — 多元陪審團勝過
  單一大法官；CrossExam 的陪審員還能傳喚證據。
- [karpathy/llm-council](https://github.com/karpathy/llm-council) — API 側
  模型議會的開山者。CrossExam 把議會搬出網頁、搬進你的 repo，然後遞給它
  一個 shell。

## Roadmap

- **跨主機席位** — 同一局、席位在不同機器（匯流排本來就是檔案，缺的是同步方案）
- **信度加權收斂** — verify/challenge 按證據等級加權（執行過 > 引用過），
  依據已發表的 LLM 裁判偏差研究
- **MCP server 模式** — 一行讓任何支援 MCP 的宿主拿到 `crossexam` 工具
- README 錄影 demo（asciinema）

## 免責聲明

CrossExam 為獨立開源專案，與 Anthropic、OpenAI、Google 及其產品無任何
隸屬或背書關係。產品名稱僅用於描述互通性。

## 引用

```bibtex
@software{crossexam2026,
  author = {XBX},
  title  = {CrossExam: file-based cross-examination for multi-LLM CLI collaboration},
  year   = {2026},
  url    = {https://github.com/cyberxuan-XBX/crossexam}
}
```

---

MIT © 2026 XBX — 台灣製造 🇹🇼
