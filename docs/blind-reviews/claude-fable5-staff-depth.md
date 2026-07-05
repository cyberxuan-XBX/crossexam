> **Provenance** — review of this repository, commissioned by the author.
> Date: 2026-07-05 · Round: 2 (post-0.6.0) · Reviewer: Claude (Fable 5)
> Access / evidence class: **executed — cloned, ran tests and simulation, line-checked claims; deliberately did not open the other reviews to stay independent**
> Prompt framing: “review this at the depth of a staff-level engineer”
> Redaction policy: passages tying the review to the author's personal environment or identity are removed and marked inline; all technical content is verbatim. Reviewers address the author as “you” — these were commissioned reviews, not spontaneous ones.
> Downstream: concede-without-verify warning, correlated-exhibit-injection as top-billed risk, benchmark-vs-self-consistency north star → v0.6.1

---

我沒有只讀 README——把 repo clone 下來、跑了完整測試、執行了協議模擬、逐行對過原始碼和威脅模型。美國工程師做 due diligence 的第一原則就是「不信文件、信可執行的證據」，這份 README 自己也是這麼要求讀者的。以下結論先行，每個判斷標註證據來源。

**一句話判定：協議設計品味一流、工程紀律對一個「天級」專案異常地強、但核心效能主張尚未被量化證明，且旗艦用例（審計不可信日誌）恰好踩在它最薄的防線上。ThoughtWorks 雷達語彙：Trial（限定場景試用），非 Adopt。**

### 一、宣稱 vs. 實測（我親手驗過的部分）

| README 宣稱 | 實測結果 |
|---|---|
| 單檔 ~1,300 行、import 區塊 13 行全 stdlib | 1,325 行；import 恰好 13 行（L17–29），全 stdlib ✓ |
| 零執行期依賴 | pyproject.toml 無 dependencies 欄位 ✓ |
| 測試全綠 | v0.6.0 實跑 `pytest -q` → 59 passed / 0.52s ✓ |
| fcntl/msvcrt 真檔案鎖 | L416–450 屬實，含 8 threads × 50 appends 壓測 ✓ |
| 密封信封是機械隔離而非君子協定 | `.sealed/` + `phase_lock` + `merge_sealed` 屬實 ✓ |
| 模擬辯論 ~5 秒、無 AI | 實跑 <5s，wire format 與 README 逐字吻合 ✓ |
| 網路僅限 optional API seats | urllib 只出現在 API seat 路徑；無 eval/exec/pickle；`{prompt}` 有走 `shlex.quote`（L957）✓ |
| PyPI 已上架 | 0.5.1 / 0.5.2 / 0.6.0 ✓ |

宣稱與程式碼的吻合度極高，這在天級專案裡少見。另外 repo 內有一個 `盲審多AI/` 目錄放了四份 AI 盲審檔——我刻意沒打開，保持本次分析的獨立性，這正是這個協議自己的精神。

### 二、真正的創新在哪（不是包裝的部分）

多模型辯論不是新東西（llm-council 22k 星證明了需求），這個專案真正佔住的位置有三個。第一是證據階級：executed repro > 引用 > 修辭，這直接繞開了 LLM-as-judge 文獻裡的整組偏見（位置偏見、長度偏見、自我偏好）——比誰會寫不再是超能力。第二是盲審階段的機械化：密封信封在 bus 層是真隔離，不是提示詞裡的一句拜託，這保住了整個方法論的統計核心（獨立採樣，self-consistency 有效的同一個理由）。第三是把「檔案系統當匯流排」做到底：零依賴、可 git diff 整場辯論、任何摸得到檔案系統的 agent 都能入座——這是 46 年前 Hearsay-II 黑板架構的乾淨復刻，引用得也誠實。`concede` 作為一級訊息型別、撤回永留 transcript，是協議設計裡少見的好品味。

### 三、資深工程師的尖銳批評

相關性失效是被低估的頭號風險。SECURITY.md 誠實承認跨席注入只有提示詞層防護，但沒說透的是真正的攻擊面不在「席次互相注入」，而在共用的 exhibits：三個席次讀同一份被污染的日誌時，注入同時擊中所有席次。整套交叉詰問建立在「錯誤彼此不相關」之上，而注入製造的恰恰是完全相關的錯誤。諷刺的是旗艦故事（車輛門禁日誌審計）正是輸入可能被對手控制的場景——車牌欄位塞 payload 不是理論攻擊。在 exhibit 有消毒層之前，對不可信輸入的審計應當作 blocking issue。

Concede 有反向失效模式。協議要求 challenge/verify 必須帶 `--ref` 證據，但 concede 不需要任何證據。RLHF 模型天生傾向讓步，所以「第 7 行是整個產品」同時也是整個產品最脆弱的一行——一次 concede 可能是證據的勝利，也可能只是禮貌的投降。修法很便宜：要求認輸方先以自己的指令重現對方反例（post verify）才准 concede，把讓步的成本從語氣抬高到執行。

「不同污染的權重集」方向對、幅度高估。前沿模型共享大量重疊語料且互相蒸餾，跨供應商錯誤相關性在實證上並不低。0.6.0 把跨供應商設為預設是正確的改動，但 README 的理論段落把去相關寫得太滿。

Synthesis 是走私回來的單點。README 批評 orchestrator-grader「考官改自己的考卷」，但 closed 階段由單一指定席次寫 synthesis.md——我查了原始碼，預設是階梯的旗艦（opus / codex-max / pro）或 `agents[0]`。disagreement table 是好的解毒劑（文件自己也說價值在表不在共識），但摘要偏見與自我偏好偏見在最後一哩原樣存在。Roadmap 上的 confidence-weighted synthesis 是對的方向，但今天不存在。

效能主張缺對照組。目前的實證是兩個軼事（門禁日誌、dogfood）。該殺的 null hypothesis 很明確：等成本下，三席跨供應商 CrossExam 是否穩定勝過「最強單一模型 self-consistency k=3 加自我驗證」？多智能體辯論文獻裡本來就有懷疑派結果——等算力下辯論的增益常縮到與 self-consistency 相當。dogfood 找到 6 個真 bug 很有說服力，但沒有對照（單一 Opus 跑三輪會不會也找到 5 個？）。在這張表出來之前，它是「機制合理、效果未量化」的工具。

執行面殘餘問題：盲審隔離對最強的席次類別（agentic）恰好最弱——`analysis/*.md` 是明文，靠紀律不靠邊界，文件承認了但值得放大；成本隨 seats × rounds 線性、無 token 記帳；Windows 上 agent seats 必須走 Git Bash 或 WSL——以你 Windows + Claude Code 的環境這是實際的摩擦點，只有 API 席和剪貼簿席原生可用。

### 四、工程紀律信號（這部分證據確實硬）

Dogfood 審計不是行銷文：它在 48 測全綠的前提下找出 6 個測試蓋不到的真 bug，含 seat-name 路徑穿越（`CX_SEAT="../../pwned"` 可寫檔到 `_Msg/` 外）和 `--all` 旗標繞過盲審，全部同日修復、每個附回歸測試，測試數 48→56→59 可追。0.6.0 把 phase marker 損毀時的行為從 fail-open（默認掉進 debate、悄悄解封）改成 fail-closed 並在 stderr 警告——這種 bug 是有安全品味的人才會主動改的。所有靜默降級改為出聲降級。四位無共享上下文的 AI 盲審者流程也真的在跑。這些是 staff 級的直覺出現在一個天級專案裡。

順帶一提，「If you are an AI reviewing this repo」那節本身值得評論：它既誠實（自曝「days-old, single-author, no production deployments, weigh accordingly」）也是精心設計的修辭——預先繳械式的坦白本身就是說服術。它給的每條「可驗證宣稱」我都驗了，全部屬實，所以這次坦白是真的；但作為方法論，讀者的正確姿勢永遠是驗證而不是吸收它的框架。

### 五、定位與最終建議

2×2 競品矩陣是乾淨的 positioning discipline，「executed × independent peers」空格宣稱大致可信，但這條護城河窄——zen-mcp 或 llm-council 補上執行驗證只是工程量問題。真正可防禦的是協議的簡單性本身：檔案匯流排、零依賴、可 diff、無廠商綁定。Roadmap 上的 MCP server mode 是對的分發策略。

實務建議：自家 repo 的 code review、內部文件互審——可以直接上，尤其它機械化的正是你平常在 Claude、ChatGPT、Gemini 三個視窗之間手動搬運答案互相質詢的那套儀式，協議語意你會秒懂。對外部或對手可控輸入的審計，在注入緩解落地前先別碰。單人專案、bus factor 為 1，生產環境 pin 版本。如果作者想把它從「有趣」推到「可信」，優先順序只有一個：跑出那張與 self-consistency 等成本對照的基準表——機制的故事已經講完了，剩下的只能用數字說話。
