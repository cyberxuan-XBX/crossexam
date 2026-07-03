# CrossExam 交互詰問

**同一個問題。三個 AI。三個不同答案。你信哪個？**

CrossExam 是一個檔案級協議 + 極小 CLI，讓多個 AI 編程代理 — **Claude Code、
Codex CLI、Gemini CLI、aider，任何能跑 shell 指令的東西** — 共同處理同一個
問題，並且**用真實指令互相詰問彼此的結論**，而不是留你在終端視窗之間複製貼上。

沒有伺服器。沒有 API key。沒有框架。只有一個可以 `git diff` 的純文字資料夾。

## 起源

同一份分析丟給三個 AI CLI session，你會拿到三個不同答案 — 不同模型本來就會
分叉，同一個模型跑兩次也會分叉。學界早知道（self-consistency、multi-agent
debate、LLM jury 全是為此而生），但 CLI 使用者只能自己當人肉匯流排。

本工具生於真實事件：三個 session 稽核同一份車輛門禁紀錄，分別回報場內有
**56、61、63** 台車。把它們的結論互貼之後發生了奇妙的事 — 一個 session 用
自己的查詢**重現**了另一個的鬼影出場發現、承認自己的數字是儀表板聚合假象，
第三個則抓到兩者都漏掉的 11 筆。最終答案比任何單一 session 都好。
CrossExam 就是把這個工作流機械化。

## 安裝與快速開始

```bash
pip install crossexam

cd your-project
cx init --task "稽核 auth.py 的 token 過期 bug"

# 每個模型開一個終端，想釘什麼版本就釘什麼版本
CX_SEAT=sonnet claude
CX_SEAT=gpt    codex
CX_SEAT=gemini gemini
```

給每個 CLI 接上對應 adapter（一個 hook 或一段記憶檔，見 [adapters/](adapters/)），
然後對每個 session 說「繼續」就行。每回合各席位自己讀未讀、動工、寫結論回去。

不接 AI 先看流程：`bash examples/simulated-debate.sh`（5 秒模擬全生命週期）。

## 協議三階段

| 階段 | 做什麼 | CLI 強制什麼 |
|---|---|---|
| **blind 盲寫** | 各席位獨立分析，發一條 `claim` | `cx read` 扣留他人訊息（防錨定）；拒收 verify/challenge/concede |
| **debate 互驗** | 挑他人「具體可查證」的說法，**跑指令**驗證 | verify/challenge 不附證據 `--ref` 會被警告；輸了明文 `concede` |
| **closed 收斂** | 指定席位寫 `synthesis.md`：共識 + **分歧表** | bus 只收 info |

五種訊息：`claim` / `verify` / `challenge` / `concede` / `info`。
一條一行 JSON。結論上 bus，長文進 `analysis/`。

互驗後仍一致的 = 掙來的信度；仍分歧的 = 分歧表精準標出**需要人類裁決的位置**。
分叉是訊號，不是雜訊。

## 設計原則

- **檔案，不是框架。** bus 就是 repo 裡的 JSONL — 可稽核、可 grep、可 git diff。
- **CLI 是便利，不是依賴。** 會 `tail` 和 `echo >>` 的 agent 就能入席。
- **跨廠商是天生的。** 席位是對等的 session，不是誰的 subagent。互動式
  session 能釘 subagent API 釘不到的精確模型版本（Sonnet 4.6 vs Sonnet 5）。
- **對抗是預設。** 「不空口稱讚，不空口質疑」是協議核心規範。結論靠被重現
  存活，不靠語氣自信。

## 免責聲明

CrossExam 為獨立開源專案，與 Anthropic、OpenAI、Google 及其產品無任何
隸屬或背書關係。產品名稱僅用於描述互通性。

MIT © 2026 XBX
