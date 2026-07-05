> **Provenance** — review of this repository, commissioned by the author.
> Date: 2026-07-05 · Round: 2 (post-0.6.0) · Reviewer: Claude (Fable 5)
> Access / evidence class: **executed — diffed 0.6.0, re-ran tests, checked PyPI and the zh-TW mirror; opens by declaring its conflict of interest (round-1 reviewer, no longer blind)**
> Prompt framing: “review the new version objectively”
> Redaction policy: passages tying the review to the author's personal environment or identity are removed and marked inline; all technical content is verbatim. Reviewers address the author as “you” — these were commissioned reviews, not spontaneous ones.
> Downstream: own-medicine wording fixes (voting-rights-as-norm, contamination odds) + Breaking marker → v0.6.1; proposed publishing this very directory with provenance headers

---

照例，先聲明這一輪的利益衝突，因為你特別說了「要客觀」：我已經不是盲的。我知道作者是誰，而且 SECURITY.md 新段落裡那句「independently flagged by an external AI code review, 2026-07-05」，指的就是我上一輪的審查。所以這輪的「客觀」只能靠方法補：全部對著 `git diff 06f35ca..23aa4e1` 和另外三席的逐字稿打分，不對著我自己的偏好打分。以下每一條都是我拉了 diff、跑了測試、查了 PyPI 之後的結果。

## 事實層：改了什麼

兩個 commit，版本跳 0.6.0。三個程式碼修正，各附回歸測試（我跑了：**59 passed**，原本 56）；`read_phase` 從「沒有 phase 標記時靜默預設 debate」改成 **fail-closed 到 blind 並在 stderr 警告**；`_DirLock` 的兩種降級（建不了鎖檔、Windows 等鎖逾時）從靜默改成大聲警告；`cxam setup` 偵測到兩家以上廠商時，**預設面板改為跨廠商**（每家一個中階席＋第一個本地模型，同廠商階梯降為 fallback）。SECURITY.md 新增「Known degradations — loud, not silent」一節。0.6.0 已經上了 PyPI——從審查意見到修正、測試、發佈，還是當天完成，這個節奏維持住了。zh-TW README 我抽查過，決策權那段有完整鏡像。README 宣稱的每一件事，程式碼裡都對得上——這次沒有抓到「文件先行、實作沒跟上」的地方，除了下面要講的兩處措辭。

## README 本身：三處變強，兩處過頭

變強的：開頭那段「你大概早就手動跑過這個協議——把 A 的答案貼給 B 問對不對，再把反駁貼回去」是整份文件裡最好的入門文字，因為它描述的是讀者已經在做的儀式，然後把人從裡面抽掉。Irving, Christiano & Amodei 2018 補進 References 是還債——AI Safety via Debate 本來就是這條線的祖譜，之前缺著是個洞，arXiv 編號我核對過沒錯。跨廠商預設的段落把「為什麼」講清楚了，而且程式碼真的改了、測試真的蓋了。

過頭的兩處，而且剛好都在寫得最漂亮的新理論段落裡。第一，「Evidence class allocates *voting* rights——一個跑得動的重現勝過任何漂亮散文」——這句話目前是**規範，不是機制**。同一份 README 的 limitations 自己還寫著 synthesis 沒有信心加權。四種權利裡三種是機械的（發言權＝密封信封＋訊息類型閘門；權力移轉＝concede 是 append-only 的一級類型；殘餘管轄權＝分歧表這個產出物），唯獨「投票權」現在靠的是 iron rules 的文字和 moderator 的自律。這個專案的招牌就是「機制與紀律分開誠實標註」，那這一節就該用同一把尺標註自己。第二，「訓練污染騙得過自家階梯，**騙不過**另一組不同污染的權重」——「cannot」太滿。各家的語料重疊得很兇（Common Crawl、GitHub、Wikipedia、arXiv，再加上合成資料和蒸餾），跨廠商的相關盲點是真實存在的；準確的講法是「大幅降低共享盲點的機率」，不是「不可能」。而且「被迫用跑得動的反例攻擊它」那半句，默默假設了對面是 agentic 席——API 和 clipboard 席只有引用級證據。兩處都是一行就能改的措辭，但這種措辭正是這個專案專門抓別人的東西。

## 盲審多AI/：最有意思的新增，也欠自己一份標註

這個目錄回答了我兩輪前要的分歧表。四席對照，用它自己的協議語言記帳：

| 席次 | 證據等級 | 獨有貢獻 | 下場 |
|---|---|---|---|
| Fable 5 | executed（跑了測試、模擬、PyPI） | 靜默降級 ×2、Windows 摩擦 | 兩條當天變成修正＋回歸測試 |
| Opus 4.8 | 讀碼（約千行，未執行） | **預設面板與招牌 demo 自相矛盾**；不假設所有權、直接問 | 變成 0.6.0 最大的一條修正 |
| GPT | citation（全靠引用 URL） | 最完整的產品化路線圖：safe-run 沙箱、hash chain、synthesis schema、PR 整合、benchmark | 零條落地，全部還在 roadmap |
| Gemini | summary（複述 README，零驗證零批評） | 無 | 無 |

這張表本身就是這次更新裡最客觀的一個發現：**修了什麼，跟證據等級完全相關**。執行級的發現和具體到能指出行號的矛盾，當天修掉；引用級的戰略建議，繼續躺 roadmap；純複述，什麼都沒產生。工具的核心命題（executed > cited > prose）在它自己的審查面板上重演了一次，而且這是記錄，不是修辭。另外要公道地說：跨廠商那條的功勞主要在 Opus——我提的是「同廠商共享盲點」，它提的是「你最能展示價值的配置不是你的預設值」，後者才是產品級的一刀，CHANGELOG 把這條記給「a reviewer」是準確的。

但這個目錄用專案自己的標準打，有欠缺。四份逐字稿沒有任何 provenance 標頭——日期、模型版本、給的 prompt、有沒有工具權限——也就是**沒有標註它們自己的證據等級**。讀者光看檔案分不出 FABLE5 那份是跑過指令的、GEMINI 那份是純複述的；對一個把 `via` 欄位當賣點的 repo，這是自家展品沒掛標籤。衛生層面：`GTP.txt` 是 GPT 的錯字；`CLAUDE-OPUS4。8.txt` 檔名裡是全形句號 U+3002（我驗過位元組），在 shell quoting、跨平台工具鏈裡是顆小地雷，git 輸出裡已經變成跳脫位元組了；中文目錄名混在全英文的樹裡，本地沒事，對國際貢獻者和 CI glob 是摩擦。

## 沒動的部分（免得這輪變成互相搔背）

四席共識的第一大風險——跨席 prompt injection 只有 prompt 層防護、沒有沙箱——**一行都沒動**，GPT 開的 P0（safe-run、網路隔離、hash chain）全數未落地。這使得新理論段落「一桌互不信任的模型」的說法微微超前現實：認識論上互不信任，作業上共用同一個沒有邊界的檔案系統。synthesis 加權沒動（有承認）。benchmark 沒動——盲審逐字稿是「對工具的評論」，不是 GPT 要的那種 20–50 案例的對照集。還有一條該標而沒標的：`read_phase` fail-closed 對「手工建 bus、沒寫 task.md」的既有用法是**行為斷裂**（0.5.x 視為開放，0.6.0 視為密封），方向對、警告夠大聲，但 CHANGELOG 裡值得一個明確的 breaking 標記，而不是埋在敘述裡。

總評：這不是 README 化妝，是一次真的工程回應——我能查證的宣稱全部成立，回應速度依然是這個專案的簽名。代價是文字品質上去之後，第一次出現「散文跑在機制前面」的縫（voting rights、cannot fool），一行可修，但值得修，因為那是它自己執法的罪名。盲審目錄是整個 repo 目前最好的行銷物件——前提是補上 provenance，讓它從「證詞」升級成「證據」。
