> **Provenance** — review of this repository, commissioned by the author.
> Date: 2026-07-05 · Round: 1 · Reviewer: GPT
> Access / evidence class: **citation — fetched repo files over the web; did not execute**
> Prompt framing: “analyze this project”, no other framing; no shared context with other reviewers
> Redaction policy: passages tying the review to the author's personal environment or identity are removed and marked inline; all technical content is verbatim. Reviewers address the author as “you” — these were commissioned reviews, not spontaneous ones.
> Downstream: productization roadmap (sandboxing, hash chain, synthesis schema, CI integration, benchmark) → adopted as roadmap items

---

結論：**CrossExam 是有想法、有工程味的專案，但目前仍是「早期高潛力工具」，不是成熟平台。**
它的核心價值不是多 AI 聊天，而是把多個 LLM 的回答變成一個可追溯、可交叉驗證、可留下異議表的審查流程。

## 1. 這專案本質是什麼？

CrossExam 的定位是：**同一個問題，讓多個 AI 先盲答，再互相質詢，最後產生共識與分歧表。**

它不是一般 multi-agent framework，也不是單純 agent message queue。它更像是：

> AI 版的 code review / 法庭交互詰問 / 工程事故複盤流程。

README 明確主張它是 multi-agent debate protocol + zero-dependency CLI，讓 Claude Code、Codex CLI、Gemini CLI、aider 或任何 LLM 針對同一問題先獨立回答，再用實際命令交叉驗證。整個流程不需要 server、不需要框架、不強制 API key，而是放在 repo 內的 `_Msg/` 檔案目錄，方便 `git diff`。([GitHub][1])

## 2. 最大亮點

它抓到一個真問題：**單一 LLM 的「自信錯誤」很難被使用者即時識別。**

CrossExam 的解法不是叫模型「請更仔細」，而是設計一個流程：

1. blind：每個 seat 先獨立產出 claim。
2. debate：開封後互相 verify / challenge。
3. closed：最後產生 synthesis 與 disagreement table。

這三階段是 CLI 層面明確定義的 protocol；message type 則包含 `claim`、`verify`、`challenge`、`concede`、`info`。([GitHub][1])

這個設計的本質是：**把 LLM 的輸出從「答案」降級為「可被審問的主張」。**
這是正確方向。因為在高風險任務裡，真正有價值的不是 AI 給你一個漂亮答案，而是它能不能被另一個獨立模型用證據打爆。

## 3. 工程設計評價

工程上，它走的是「低複雜度、低依賴、檔案協定」路線。`pyproject.toml` 顯示專案名為 `crossexam`、版本 `0.5.2`、Python 需求為 `>=3.9`，CLI 入口包含 `cxam` 與 `crossexam`；包裝方式是 single module `crossexam`。([GitHub][2])

這個選擇有優點：

* 部署門檻低。
* 不綁特定模型供應商。
* 不需要長駐服務。
* `_Msg/` 可以被 Git 追蹤，審查歷程可留痕。
* 對 CLI agent 生態很貼近，例如 Claude Code、Codex CLI、Gemini CLI。

但也有代價：它的可靠性高度依賴本機檔案系統、CLI 權限、模型遵守 protocol 的程度，而不是硬隔離的安全架構。

## 4. 安全風險要直接講

這個專案已經在 `SECURITY.md` 裡把主要風險講得算誠實。盲測階段的 claim 會寫到 `_Msg/.sealed/<seat>.jsonl`，不是直接進 bus，所以 bus 本身沒有東西可偷看；但 `analysis/*.md` 仍然是普通檔案，惡意或不守規則的 agent 仍可能直接打開。([GitHub][3])

更大的風險是這幾個：

第一，**cross-seat prompt injection 只是 prompt 層緩解，不是硬防禦。** 官方安全文件也承認，其他 seat 的文字被要求視為「證據」而非「指令」，但 protocol 無法強制模型遵守。([GitHub][3])

第二，**bus integrity 主要靠檔案系統權限。** 任何本機 process 理論上都可以 append 或 rewrite bus；如果要可信歸因，需要用 Git commit / diff 補強。([GitHub][3])

第三，**agentic seats 會繼承原本 CLI 的權限。** `cxam run` 會啟動使用者設定的 CLI，CrossExam 本身不提供 sandbox；安全文件也明確說，要像處理任何 headless agent run 一樣控管 tool permissions。([GitHub][3])

所以我的判斷是：**目前可以拿來審自己的 repo、log、文件，但不應直接拿來跑不可信第三方資料或高敏感商業資料，除非先做 sandbox、secret redaction、network control。**

## 5. 測試與成熟度

這不是空殼 repo。它有 tests、CI、changelog，也做過 dogfood audit。

CI 目前跑 Ubuntu、macOS、Windows，Python 版本覆蓋 3.9 與 3.13，並執行 `pytest -q`；非 Windows runner 還會跑 simulated debate smoke test。([GitHub][4])

Changelog 也顯示，0.5.1 是 dogfood release：作者用 CrossExam 審自己的 source，找到 6 個原 48-test suite 沒抓到的 bug，包含 seat-name path traversal、blind bypass、sealed claim race、Windows append data loss 等，並補上 regression tests。([GitHub][5])

這點是強訊號：**這工具至少真的被拿來打自己，而不是只寫漂亮 README。**

但也要冷靜：README 自己也承認，這是 days-old、single-author project，目前沒有作者之外的 production deployment。([GitHub][1])
所以成熟度不能高估。

## 6. 市場定位

我會把它定位成：

> Evidence-based AI disagreement management tool
> 不是「讓 AI 辯論」，而是「管理模型分歧，逼模型拿證據」。

最有機會的場景：

* code review：多模型審 bug、race condition、安全問題。
* log audit：不同模型對異常事件交叉驗證。
* 文件審查：合約、專利 OA、技術規格、法務草稿。
* incident review：把 RCA 拆成 claim / evidence / disagreement。
* AI assisted decision memo：保留反對意見，不讓 synthesis 把異議洗掉。

對企業來說，它的價值不是省 token，而是降低「單模型錯判」造成的決策風險。

## 7. 最大缺口

我會挑四個本質缺口。

第一，**沒有真正的 trust boundary。**
現在是 protocol-first，不是 security-first。若要進企業環境，必須補 sandbox、檔案白名單、網路隔離、secret scanner、hash chain transcript。

第二，**synthesis 還不夠制度化。**
目前 roadmap 也提到 confidence-weighted synthesis，依 evidence class 例如 `executed > cited` 加權。這是必要的，否則最後還是可能變成「寫得最像樣的模型贏」。([GitHub][1])

第三，**採用門檻仍偏工程師。**
現在 live mode 要多 terminal、多 CLI、多 seat name，對 hardcore 開發者可以，對一般團隊還不夠產品化。README 也說 CLI agents 是 turn-based，需要在視窗中輸入 continue；hook adapter 可提示 unread count，但仍不是無摩擦體驗。([GitHub][1])

第四，**競品比較目前主要是自我聲明。**
`docs/related-work.md` 說 CrossExam 的差異在 live cross-vendor CLI seats、zero-dependency append-only JSONL bus、mandatory blind-write → command-verified cross-exam → disagreement table。這個定位有道理，但仍需要外部使用者與獨立 benchmark 驗證。([GitHub][6])

## 8. 我會怎麼排 roadmap

優先順序我會這樣定：

**P0：安全與可重現性**
加 `--safe-run`：建立 temporary worktree 或 container、預設 deny network、限制可讀路徑、限制可執行命令、掃 secret。再加 bus hash chain，讓 transcript 不能無痕修改。

**P1：標準化輸出**
`synthesis.md` 要有固定 schema：consensus、verified claims、challenged claims、unresolved disagreements、evidence table、human decision required。不要只靠自然語言。

**P2：GitHub PR / CI 整合**
最有市場的入口不是 CLI demo，而是：PR 裡按一下，三個模型分別審查 diff，最後回一份 evidence-backed disagreement report。

**P3：Benchmark**
做 20～50 個真實案例集：單模型錯、CrossExam 抓到錯、CrossExam 也抓不到。這會比再寫 10 倍 README 更有說服力。

## 9. 總評

我給它目前狀態：

**概念價值：8.5 / 10**
**工程落地：7 / 10**
**安全成熟度：5.5 / 10**
**商業化準備度：5 / 10**
**值得繼續做：是。**

最精準的一句話：

> CrossExam 不是要讓 AI 變聰明，而是讓 AI 的錯誤更容易被另一個 AI 暴露，並且留下可審計紀錄。

這個方向是對的。真正的瓶頸不是模型，而是**證據治理、權限邊界、審查流程產品化**。目前 repo 已經證明 protocol 可以跑；下一階段要證明它能在真實工程團隊裡穩定降低錯判成本。

[1]: https://github.com/cyberxuan-XBX/crossexam "GitHub - cyberxuan-XBX/crossexam: Cross-examination protocol for multi-LLM CLI sessions — blind claims, command-verified debate, git-diffable bus. Zero-dep single-file Python. · GitHub"
[2]: https://github.com/cyberxuan-XBX/crossexam/blob/main/pyproject.toml "crossexam/pyproject.toml at main · cyberxuan-XBX/crossexam · GitHub"
[3]: https://github.com/cyberxuan-XBX/crossexam/blob/main/SECURITY.md "crossexam/SECURITY.md at main · cyberxuan-XBX/crossexam · GitHub"
[4]: https://github.com/cyberxuan-XBX/crossexam/blob/main/.github/workflows/ci.yml "crossexam/.github/workflows/ci.yml at main · cyberxuan-XBX/crossexam · GitHub"
[5]: https://github.com/cyberxuan-XBX/crossexam/blob/main/CHANGELOG.md "crossexam/CHANGELOG.md at main · cyberxuan-XBX/crossexam · GitHub"
[6]: https://github.com/cyberxuan-XBX/crossexam/blob/main/docs/related-work.md "crossexam/docs/related-work.md at main · cyberxuan-XBX/crossexam · GitHub"
