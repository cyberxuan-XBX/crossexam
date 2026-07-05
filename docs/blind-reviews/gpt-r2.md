> **Provenance** — review of this repository, commissioned by the author.
> Date: 2026-07-05 · Round: 2 (post-0.6.0) · Reviewer: GPT
> Access / evidence class: **citation — fetched repo files over the web; did not execute**
> Prompt framing: “review the new version objectively”
> Redaction policy: passages tying the review to the author's personal environment or identity are removed and marked inline; all technical content is verbatim. Reviewers address the author as “you” — these were commissioned reviews, not spontaneous ones.
> Downstream: seat reliability profiles + non-verifiable task labeling → v0.6.1 roadmap

---

結論先講：**這個專案有想法，而且切中 AI 工程化的真問題；但目前更像「早期高潛力工具／研究型 workflow」，不是成熟企業級產品。**
它最有價值的地方不是「多 AI 投票」，而是把 AI 的判斷過程轉成一套可追責的程序：**盲審 → 交叉質詢 → 用證據驗證 → 錯的人正式讓步 → 剩餘爭議交回人類。** 這點比一般「問三個模型取平均」高明很多。

## 1. 專案本質

CrossExam 是一個 **multi-LLM cross-examination protocol + CLI 工具**。它讓 Claude Code、Codex CLI、Gemini CLI、aider、API 模型、甚至網頁聊天模型，都可以各自成為一個「席位」，針對同一個問題先獨立回答，再互相挑戰。官方 README 明確主張它不是 server、不是 framework，也沒有中央 orchestrator；核心通訊機制是一個 `_Msg/` 目錄，包含 `bus.jsonl`、`analysis/`、`exhibits/`、`task.md` 等純檔案結構。([GitHub][1])

它想解的問題非常實際：**單一 AI 的答案常常很自信，但外部很難知道它是不是對的。** CrossExam 的答案是不要信任單一模型，而是讓多個模型先盲答，之後用可檢查的證據彼此攻防。README 用「三個 AI 查同一份車輛出入紀錄，分別得到 56、61、63 台」作為核心故事，最後靠交叉驗證逼出較可靠結論。([GitHub][1])

## 2. 技術架構判斷

架構是聰明的，因為它沒有一開始就做重型平台，而是選擇「file-based protocol」。這讓它有幾個工程優勢：低部署成本、容易 `git diff`、可被任何能讀寫檔案的 AI CLI 接入，也比較不綁特定模型供應商。README 說明它支援 agentic seat、API seat、clipboard seat；agentic seat 可以實際執行 command，API/clipboard seat 則以 citation-based verification 為主。([GitHub][1])

包裝層面看起來也偏務實。`pyproject.toml` 顯示目前版本是 `0.5.2`，Python 要求為 `>=3.9`，套件名稱是 `crossexam`，CLI 指令包含 `cxam` 與 `crossexam`，授權為 MIT，分類狀態是 Beta。([GitHub][2])

但這個架構不是沒有代價。**file bus 很透明，但不是安全邊界。** SECURITY 文件明講：bus integrity 只靠 filesystem permissions；任何本機 process 都可能 append 或 rewrite bus。prompt injection 也只是 prompt layer mitigation，不是強制性 sandbox。agentic seats 會繼承各自 CLI 的權限，CrossExam 本身不提供額外沙箱。([GitHub][3])

## 3. 強項

第一個強項是它抓到 AI 協作的本質問題：**不是讓 AI 更多，而是讓 AI 彼此不容易集體犯同一種錯。** 盲審階段避免 anchoring；debate 階段要求 challenge 要有 evidence ref；concede 被記錄在 transcript 裡。這比一般「多代理人聊天」更有審計價值。([GitHub][1])

第二個強項是它把「可驗證性」放在產品核心。很多 LLM council 類工具其實只是文字評論、排名、投票；CrossExam 的主張是讓 agentic seat 跑 command，用實際 reproduction 去壓過口才。這個方向是對的，尤其適合 code review、log audit、資料稽核、規格文件審查。([GitHub][1])

第三個強項是 dogfooding 做得漂亮。CHANGELOG 說 0.5.1 是 dogfood release，作者用 CrossExam 審自己的 source，找出 48-test suite 沒抓到的 6 個 bug，包含 seat-name path traversal、blind bypass、phase flip、race condition 等問題，並補 regression test。這是很好的技術敘事，也讓專案可信度比單純 README 行銷高。([GitHub][4])

## 4. 主要風險

最大風險是：**它現在還太早期。** GitHub 頁面顯示目前只有 21 commits、2 stars、0 forks，最新 release 是 `0.5.2`，日期為 2026-07-04。這代表它還沒有社群驗證、企業驗證、長期維護紀錄，也還沒有足夠多真實場景壓測。([GitHub][1])

第二個風險是安全邊界很薄。專案自己也承認：`analysis/*.md` 還是 plain files，惡意或失控 agent 可以偷看；cross-seat prompt injection 只能靠提示詞規範；bus 完整性不防本機偽造；API seat 會把 task、exhibits、其他 seat 分析送到 endpoint。這些在個人工具或開源 repo audit 可以接受，但在客戶資料、專利文件、商業機密、資安事件調查上，不能直接無腦導入。([GitHub][3])

第三個風險是它可能放大成本與雜訊。多模型交叉詰問不會免費提高真實性；它只是提高「錯誤被揭露的機率」。如果題目不可驗證、資料品質差、沒有 command 可跑、或 seat 都來自同一 vendor／同一訓練盲點，它仍可能產生漂亮但錯誤的共識。README 也提到 same-vendor seats 共享 training blind spots，且專案尚未有 confidence weighting synthesis。([GitHub][1])

## 5. 商業與產品定位

這不是一般消費者工具。它的合理定位是：

**AI-assisted audit workflow for engineers。**

最適合的場景是：

| 場景        |  適配度 | 原因                             |
| --------- | ---: | ------------------------------ |
| 程式碼審查     |    高 | 可跑測試、可 grep、可重現 bug            |
| log audit |    高 | 可寫 query、可驗證數字                 |
| 資安初步分析    |   中高 | 多角度有價值，但權限與資料外洩要控管             |
| 專利／合約文件審查 |    中 | 可做多模型盲審，但很多結論不可 command-verify |
| 一般聊天問答    |    低 | 成本高、流程重                        |
| 企業正式決策系統  | 目前偏低 | 缺少權限控管、審計簽章、部署治理               |

它真正有商業價值的方向不是「我可以讓三個 AI 開會」，而是：「**我可以降低單一 AI 自信錯判造成的工程風險，並留下可審計的判斷軌跡。**」

## 6. 跟一般 multi-agent 工具差在哪

一般 multi-agent framework 常見問題是：看起來很多代理人在討論，但實際上可能只是同一個 orchestrator 控制流程，最後還是由 lead model 評分。CrossExam 的差異是它強調 independent peers，而且 evidence class 裡「executed command」比文字辯論更高權重。README 的 related work 也把競品分成 nobody verifies、lead model grades、independent peers，以及 rhetoric/ranking vs executed commands 兩軸，並把 CrossExam 放在 independent peers + executed commands 位置。([GitHub][1])

這個定位有新意，但也要小心：README 說「executed-commands × independent-peers cell was empty」屬於作者自己的比較結論，不等於市場已完全驗證。作為行銷語句可以，但若要拿去募資、商業合作或技術白皮書，最好補更嚴謹的競品 benchmark。

## 7. 我對這專案的評分

以「工程師是否值得研究」來看：**8/10**。
以「現在能否導入正式工作流程」來看：**5.5/10**。
以「產品化潛力」來看：**7/10**。
以「安全成熟度」來看：**4.5/10**。

它的概念強，MVP 也很乾淨；但目前還是單作者、早期版本、低 adoption、低治理成熟度。專案自己 README 也很坦白地說，這是 days-old、single-author project，已有 working protocol 和 real self-audit，但沒有作者自己之外的 production deployments。([GitHub][1])

## 8. 最值得補強的地方

我會優先補這幾個：

1. **真實 benchmark**：拿 20 個 code review / log audit / config audit 案例，比較單模型、普通 multi-agent、CrossExam 的 bug recall、false positive、成本、時間。

2. **安全模式**：提供 `--local-only`、`--no-network`、`--redact-secrets`、Docker sandbox、只讀 repo mount。否則企業資料不敢進去。

3. **證據權重系統**：目前 roadmap 有 confidence-weighted synthesis，這是必要功能。executed repro、unit test、grep evidence、citation、純推論，應該有不同權重。

4. **CI integration**：讓它可以在 PR 裡跑，輸出 GitHub comment 或 markdown report。這會比純 CLI 更容易被工程團隊採用。

5. **seat reliability profile**：記錄不同 seat 歷史上被 challenge / concede 的比例，逐步形成模型可信度紀錄。

6. **不可驗證任務降級策略**：如果題目無法 command-verify，系統應該明確標示「這是文字審查，不是實證驗證」。

## 9. 最終判斷

這個專案的核心方向是對的。它不是在做「AI 群聊」，而是在做 **AI 判斷的治理流程**。這個方向未來會很重要，因為 AI 真正進入工程流程後，問題不是「模型會不會回答」，而是「回答錯了誰負責、怎麼被發現、怎麼留下證據」。

但照實講，現在還不能把它當成熟產品。它比較像一把很有想法的新工具，適合拿來做內部實驗、repo audit、log 分析、AI code review 補強。若要處理客戶機密、正式法務文件、專利核心資料，現階段必須先把資料外流、權限、prompt injection、bus integrity 這些問題管住。

我的建議：**值得 clone 下來試，但不要直接進 production。先拿一個低風險 repo 或歷史 bug 案例跑，看它是否真的能找出單模型漏掉的問題。**

[1]: https://github.com/cyberxuan-XBX/crossexam "GitHub - cyberxuan-XBX/crossexam: Cross-examination protocol for multi-LLM CLI sessions — blind claims, command-verified debate, git-diffable bus. Zero-dep single-file Python. · GitHub"
[2]: https://github.com/cyberxuan-XBX/crossexam/blob/main/pyproject.toml "crossexam/pyproject.toml at main · cyberxuan-XBX/crossexam · GitHub"
[3]: https://github.com/cyberxuan-XBX/crossexam/blob/main/SECURITY.md "crossexam/SECURITY.md at main · cyberxuan-XBX/crossexam · GitHub"
[4]: https://github.com/cyberxuan-XBX/crossexam/blob/main/CHANGELOG.md "crossexam/CHANGELOG.md at main · cyberxuan-XBX/crossexam · GitHub"
