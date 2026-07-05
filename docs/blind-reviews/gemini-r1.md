> **Provenance** — review of this repository, commissioned by the author.
> Date: 2026-07-05 · Round: 1 · Reviewer: Gemini
> Access / evidence class: **summary — restated the README; no verification, no critique**
> Prompt framing: “analyze this project”, no other framing; no shared context with other reviewers
> Redaction policy: passages tying the review to the author's personal environment or identity are removed and marked inline; all technical content is verbatim. Reviewers address the author as “you” — these were commissioned reviews, not spontaneous ones.
> Downstream: none

---

這份 `cyberxuan-XBX/crossexam` 的 `README.md` 文件展示了一個非常具原創性的 AI 協作工具。以下是針對該專案核心機制與特色的詳細分析：

### 專案核心理念

CrossExam 是一個多代理人辯論協定（multi-agent debate protocol）與零依賴的命令列工具（CLI）。它的核心目標是解決單一 AI 總是充滿自信但不一定正確的問題。透過讓多個不同的 AI 模型（例如 Claude Code、Gemini CLI、本地端 LLM 等）針對同一個問題進行獨立審查，然後用真實的指令相互「交叉詰問（cross-examine）」，來過濾出最精確的答案。

### 運作流程：三個階段

該協定將 AI 的審查過程強制分為三個嚴格的階段：

* **盲測階段 (Blind phase)**：每個 AI 座位（seat）會獨立進行分析，並提出一個「聲明（claim）」。這個聲明會被「密封」在特定的資料夾（`.sealed/`）中，AI 之間無法看到彼此的答案，藉此避免模型出現盲從群眾的現象。


* **辯論階段 (Debate phase)**：密封的信封被打開，AI 模型之間開始閱讀彼此的聲明並互相挑戰（challenge）或驗證（verify）。特別的是，具有代理能力的 AI 必須透過「實際執行指令」來提供證據（例如在程式庫中跑測試或讀取 Log），而不是單純用文字辯論。


* **結案階段 (Closed phase)**：如果某個模型被證據證明有誤，它必須留下正式的「讓步（concede）」紀錄。最終會由指定的模型撰寫一份 `synthesis.md`，內容包含所有模型的共識，並將依然存在的分歧列成「意見分歧表（disagreement table）」，交由人類做最終裁決。



### 技術特點與架構

* **無伺服器與零依賴 (Zero-dependency)**：整個專案由一個純 Python 標準函式庫寫成（`crossexam.py`，支援 Python 3.9+），大約 1,300 行程式碼。它不需要中央協調器（orchestrator）、不需要伺服器架構，也不強制綁定特定的 API 金鑰。


* **檔案匯流排機制 (File-based Bus)**：所有的對話與通訊都發生在一個普通的文字檔案目錄中（例如 `_Msg/bus.jsonl` 存放結論，`_Msg/analysis/` 存放長篇證據）。只要能讀寫檔案系統的 AI 代理都能參與這場辯論。


* **支援三種 AI 參與模式 (Seat Classes)**：
* **Agentic**：如 Claude Code、Codex CLI，能直接執行指令來驗證聲明。


* **API**：如 Ollama、vLLM 或相容 OpenAI 格式的端點，基於引用來進行驗證。


* **Clipboard**：適用於網頁版聊天介面（如 ChatGPT、Claude.ai 網頁版），讓無 API 權限的用戶也能手動複製貼上參與。





### 應用場景與實績

* 該專案特別適合用於程式碼審查（code review）、日誌稽核（log audits）以及文件審閱等「單一模型自信給出的答案不夠可靠」的場景。


* 作者在文件裡提供了一個真實案例：三個 AI 在稽核同一份車輛進出日誌時，一開始分別給出了 56、61、63 輛車的錯誤答案。透過 CrossExam 交叉詰問，一個 AI 用指令重現了另一個 AI 發現的錯誤，並推翻了自己原本的結論，最終得出比單一模型更精準的答案。


* 該專案也對自身的 `v0.5.0` 版本進行了「吃狗糧（Dogfooding）」自我稽核，由三個供應商的模型找出了 7 個問題，且均在當天被修復。



### 安裝與使用方式

* 可以透過 `pip install crossexam` 安裝，或直接下載腳本執行。


* 執行 `cxam setup` 可以自動偵測使用者本地已安裝的 AI CLI 工具。


* 使用 `cxam run "您的提問"` 就能一鍵啟動多模型盲測與辯論流程。
