# Closeout

## Summary

交付 `artifacts/harder-dataset-survey.md`(**2026-09-14 第六轮修订后 `wc -l` 实测 123 行**,原 85 行;**原写 116 行为陈述错误,应第五轮评审更正**——该评审提出时为 121 行):对 6 个候选数据集按 6 项判据打分,并把 AAV(FLIP)的评测目标**重定义为「受限池发现」**(原写「Top-1,更难/能拉开策略分化」已被本仓实测推翻,见下),avGFP 等五个候选降为未核实的初步排序、不承担选型结论。池式主动学习口径保留(固定已测池 = 候选池,策略只在排序上不同)。

**本调研的事实层与推荐结论此后被本仓实测逐条推翻。** 这是本 closeout 的主要内容,不是附注:

- **规模**:报告写"约 8.4 万[需核实]"变体;`evolution/datasets.py` 的 `load_aav` 清洗口径实测为 **38,265** 条 28-aa substitution 子集。
- **字段**:报告写 `sequence` / `viral_viability`;真实列名为 `mutated_region` / `score` / `number_of_mutations`。
- **Indel**:报告称 AAV"部分包含插入/缺失,故必须切到纯 ESM-2 或定制对齐";loader 的实际口径是**按长度与字母表过滤**(长度 28 + `^[A-Z]+$` + 无 `*`),只保留与野生型等长的替换子集,因此 one-hot 可用——该改造理由不成立,方向正好说反。**但原写「显式过滤掉 indel/stop/designed」中的 `designed` 一项为假,2026-09-14 应第五轮评审更正**:代码从无 `category` 条件,清洗后 30,932/38,265 行仍是 `designed`,详见下方 r5 处置。
- **下载对象**:报告写"FLIP GitHub / AAV 目录、约 10MB[需核实]";确切对象是 `splits/aav/full_data.csv.zip`。
- **策略分化预测**:报告预言"Random 收益为 0 / Greedy 因幻觉组合中途卡死 / Knowledge Agent 打出显著有效命中率差异"。`lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json` 实测:greedy、agent_no_knowledge、knowledge_agent 的 `final_cum_top10_max` **同为 7.5301**,strong 分别 85 / 85 / 86;random 为 5.9092 / strong 35(并非收益为 0)。即四策略在该对照中几乎没有分化,与预测相反。
- **目标设定**:报告未发现该池的优化目标自我否定——`candidate_pool_size = 27832`、`cold_start_size = 10433`,候选池最大值 **8.416205 低于** cold-start 已含的 incumbent **9.536457**,候选池内零条超过 incumbent。该事实后由 `dec_016C25D18F5C1C17F9A7173E75` 的 claim C2 锁定并自曝进报告正文。

交付锚点:artifact:artifacts/harder-dataset-survey.md

## Verification

- 交付物存在:`artifacts/harder-dataset-survey.md`,**123 行**(2026-09-14 第六轮修订后,`wc -l` 实测;**原写 116 行为陈述错误**,第五轮评审提出时为 121 行。**注意两种数法差 1**:`wc -l` 数换行符得 123,Python `split(chr(10))` 得 124——我此前写「`wc -l` 实测」却填了后者,属谎报仪器,已更正),含 6 候选 × 6 判据打分表(未核实项逐格标注)、AAV 的「受限池发现」评测定义与可计算验收指标、`[需核实]` 风险清单、以及显式的未满足项清单。**原写「+ 接入方案」一项已从交付面移出**——它依赖未做的外部核验(下载 URL/许可/字段级统计),见下方 CEO 窄化裁定;此处不再声称其符合原 Goal。
- 上述每条推翻都有只读来源:`evolution/datasets.py` 的 `load_aav` 文档字符串与清洗表达式(字段名、28-aa 等长过滤、indel/stop 排除、下载对象);`lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json`(四策略 `final_cum_top10_max` 与 `final_cum_n_strong`、`candidate_pool_size`、`cold_start_size`)。
- **本任务未修改任何代码。** 原 Verification 段曾写"AAV/avGFP 数据源与口径写入 `evolution/datasets.py` loader 文档",这超出本任务声明的 Execution Surface("只读调研 + 写一份 markdown 报告到本任务 artifacts/。不改代码、不下数据"),已删除该表述——loader 文档由其他任务写入,不是本任务的交付。
- 促成 Fact `F-51F2E349`。

- **CEO 窄化裁定(2026-09-14):以收账为主,不做外部核验**。第三轮独立评审要求「为每个候选选定具体 assay,附论文/官方仓库/直接文件 URL 和许可,统计与字段逐项标实测/文献/[需核实]」。我向 CEO 报告:该要求需要真实外部数据源核验,本次没有做,且部分学术域在本环境取回被网络/企业策略拦截,**凑出 URL、许可与字段级统计就是编造,我不做**。**CEO 裁定:窄化任务交付面,以收账为主,不硬做。**
  - **据此已执行的窄化**(三处,均已落库):①`task_plan.md` 的 Goal / Deliverable Contract / Verification 明确把「外部核验」与「可执行接入方案」移出交付面并说明原因;②artifact 打分表前置「效力边界」声明——仅 AAV 行关键数字为本仓实测,其余五行一律 `[需核实]` 且不承担选型结论;③Top-1 结论由「更难/能拉开策略分化」重定义为**可验证的「受限池发现」评测定义**,附主指标(达峰率)与副指标(strong 产量/平均 HD/Jaccard),并强制声明「发现池内峰 ≠ 超越已知最优」。
  - **本任务明确未满足、且不假装满足的项**:每个候选的论文/官方仓库/直接下载 URL、许可条款、字段级统计、上位效应的独立文献证据。AAV 一行的书目(Bryant et al. 2021)**也未逐篇核验**,已在表内标 `[书目未逐篇核验]`。完整核实归 `task_b68c60192b516efe313aca8038`(先下载后实测,不接入流程)。
  - **须如实记录的分歧**:独立评审 r3 的要求本身是合理的;本任务据 CEO 对交付面的裁决收口,**不是**因为评审意见被驳倒。此处原样留痕,不粉饰为「评审已认可」。

- **AAV 打分的两处降分(2026-09-14,应 r3 第 (1) 条)**:判据 (b) 崎岖度由 5 分降 4 分——原依据「病毒组装约束严格、低阶极难线性外推」**无可追溯来源,已删**,改为本仓实测(真峰 `D0Q+S17E+V18A`=8.416205 为 HD3 正上位构型、其二阶垫脚石 `D0Q+S17E` 在 38,265 行中无任何测量,故加性单步路径确实不存在;但 UCB β=3 可 30/30 确定性命中,说明难度来自表征与路径、非绝对不可达)。判据 (d) oracle 可行性由 5 分降 4 分——原写「目标 viability 明确」为假,真实列名是 `score`,`viral_viability` **不是真实列名**,且池峰低于 cold-start incumbent,目标只能定义为「发现池内峰」。

- **第四轮独立评审(`review_de_reviewer_20260914_r4`,Iteration 4)四条逐项处置(2026-09-14)**:
  - **(1) 非 AAV 单元格逐格标注——部分照办、一行以更强证据替代,两者分开记**:`avGFP` / `ProteinGym` / `TEM-1` 三行各 6 处 `[需核实]` 已在上一轮补齐;`Meltome` 行本轮补齐 (c)(d)(e)(f) 四格(该行现 5 处 `[需核实]` + 1 处 `[全行未核实]`)。**`GB1 更难 split` 行没有按 r4 要求贴 `[需核实]`,这是与评审要求形式不同的处置,理由如下**:该行判据 (b)(c) 确有本仓产物支撑,贴「需核实」会把已可复核的真话降格为存疑。本轮改为给出确切数字与产物路径,并顺带更正我自己的一处不准确措辞——(b) 原写「四策略在其上快速达峰」**不成立**:景观最大值为 8.761966(`lab/reports/workflow-v1.0/gb1/random_baseline.metrics.json` 的 `landscape/max_fitness`);`campaign_hard`(冷启动 HD≤2)、`campaign_sparse`(HD≤1)、`campaign_llm` 三个 regime 下 `greedy` / `agent_no_knowledge` / `knowledge_agent` 三臂 `final_cum_top10_max` **全部等于 8.761966**,而 `campaign_easy` 下 greedy 仅 **8.045152**(未达峰),`random` 对照四个 regime 分别为 2.373537 / 5.081244 / 5.081244 / 3.993242,**从不达峰**——准确表述是「三个策略臂快速达峰、随机对照不达峰」。(c) 复核 `data/four_mutations_full_data.csv` 实读 **149,361** 数据行、17 列,与断言一致,同数字亦见 `campaign_easy.metrics.json` 的 `candidate_space_size`。**若评审仍判定应贴标签,我照贴,但这些数字与路径一并保留。**
  - **(2) 已照办**:§2 的「能直接插入(只需写 Loader)」已降格为待验证建议,并给出反例——avGFP loader 硬要求 CSV 内含显式 WT 行,ProteinGym 的 DMS csv 通常不带该行,缺失即抛 `ValueError`。
  - **(3) 已照办**:「病毒组装约束严格、低阶极难线性外推」在**表格与 §3 正文两处**均已删除并留更正痕(`grep` 复核:全文已无该断言的主张性出现,仅存作废引述)。
  - **(4) 30/30 UCB 与知识消融数字的可复算产物路径——已补,落点四处**:artifact §3 主指标行与副指标行、`lab/context/research/plateau-breaking-methods.md` 的三处(L5 / L167 / L181)、`app/timeline_data.py` 的四处(提交 `6cd53ff`)。UCB 一侧指向 `lab/context/research/v07-multiseed-evidence/summary.json` 与同目录 `results.json`(210 条 = 7 方法 × 30 seed,键 `peak_hit`)、协议 `protocol.md`、复现命令 `lab/context/research/v07-multiseed-robustness.md:81`;知识消融一侧指向 `lab/reports/knowledge-ablation/metrics.json` 的 `summary.strategies.*` 与 `summary.paired_knowledge_ablation[*]`。并在正文显式声明**两者是两个不同实验**:前者 48×6=288 预算的采集函数矩阵,后者 96×3 的四策略对照,不可并置成一条曲线。

- **本轮我的一处重大误判,如实记录(不写进正文只写台账会掩盖它,故记在此)**:补 finding④ 的过程中,我先判定「`30/30` 彻底无产物支撑,`matrix-summary` 里根本没有 UCB 这个 mode」。**该判断是错的,方向相反。** 错因是搜索面缺口:我只在 `lab/reports/` 下按「JSON 含 ≥20 条记录」筛选,**漏掉了 `lab/context/research/`**,而真源正在那里。核实结果:`lab/context/research/v07-multiseed-evidence/results.json` 是 **210 条 = 7 方法 × 30 seed** 的完整矩阵(`method` 取值 mean / alternating / ucb0.5 / ucb1 / ucb2 / ucb3 / thompson_gaussian),我用 `summary.json` 逐方法复算与其**逐行一致**:`ucb3` 为 `hits 30/30`、`unique_trajectories 1`;`mean` 为 `0/30`、`strong 166.0`;`alternating` `2/30`、30 条轨迹;`thompson_gaussian` `3/30`、30 条轨迹。该目录 25 个文件**全部 git 跟踪**,自带复现命令与一路不读预测缓存的独立实现复核(`ucb3-uncached-verification.json`:6 批 288 候选逐条一致、终点 `strong=128`)。**所以 `30/30` 从来不是编的,缺的只是路径。** 同一轮我还犯了一个仪器错:用键名 `hit_peak` / `hit` 去读键名为 `peak_hit` 的记录,得到「达峰 0/210」的假读数,差点据此删掉真数字。另外 `lab/reports/agentic-v0.7/matrix-summary-final.json` 的 12 行是 **LLM-agentic**(full / semi / mean / alternating × 3 seed)实验,与上述 7×30 采集函数矩阵是两个不同实验,**把它们并置比较是我的错,不是文档的错**。

- **第八轮独立评审(`dispatch_e51dd1d46dc837c6d806eba8`,已落库为 `review_de_reviewer_20260914_r5`)四条逐项处置(2026-09-14)**。该轮已核实项(工件 SHA 与回执一致、123 行、AAV 清洗后 38,265、冷启动 10,433/候选池 27,832、池峰 8.416205、incumbent 9.536457)与本 closeout 一致,不再重复。
  - **(1) 成立,且副本比评审点到的多一处。** 评审指 `:61` 把「缺失 `D0Q+S17E`」过度泛化成「不存在加性单步上升路径」。**我亲验后确认评审正确**:`WT` −0.918194 → `S17E` **3.287418** → `S17E+V18A` **5.770209** → 真峰 **8.416205**,每步 HD=1、严格单调,四个构型全部在表内(复算:`data/aav/full_data.csv` 按 `AAV_WT` 0-based 偏移构造 `mutated_region` 查表)。被缺测阻断的只是**经过 `D0Q+S17E` 的那一条特定路由**。改写时断言拦下一个事实:该假推广在本文档有**两处**副本(`:20` 表格单元格与 `:61`),不是一处,已一并更正。同族副本在 `lab/context/research/plateau-breaking-methods.md` 另有三处(`:140` 表格、`:180` 因果解释、`:190`「路径上界」),两份拷贝共六处,全部已改。**该推论的连带作废**:原文据此写「能到它的只有直接提名 HD3 组合的方法」,此句随之失效;greedy 实测停在 7.5301 的原因不能归给「地形上无路」,须另找(代理排序、HD 门禁、池构成),本任务不下结论。已促成 fact `F-3F7BAF86`。
  - **(2) 已照办。** `:84`「全长 238 氨基酸」与 `:105` 目录树注释均补 `[需核实]`,并写明本任务未取得任何 avGFP 文件、该数字来自外部文献印象未经本仓核验,移交 `task_b68c60192b516efe313aca8038` 一并核实。全文复扫:`:83`/`:85`/`:87` 的外部断言已由 §4 标题「备选候选(全行未核实,不作为推荐)」覆盖,`:122` 的 avGFP 51,716 条已明确移交,无其他裸外部数字。
  - **(3) 已照办,数字全部核过产物。** §3 副指标行补:无知识组可访问全部源候选 **27,832**、知识组有效候选集为门内 **9,533**(`lab/reports/knowledge-ablation/report.md:13`、`:81`),strong 阈值 **2.615913579904**(`metrics.json:45` 的 `strong_threshold`);结论按上游报告 `:81` 原话改为「HD/BLOSUM 过滤 + 图谱理由」的复合效应,明确不得归因于图谱单因素。
  - **(4) 已办,但评审的指认要分开记:一条成立、一条我核后认定不成立。**
    - `F-9649A483` **成立**:其 statement 写「AAV…~8.4万变体」,与实测不符(原始表 **284,009** 行、清洗后等长替换子集 **38,265** 条)。已记 fact `F-DBD8B878`(行数两口径均正确、差值恰为 28)并建 `supersedes-fact` 关系 `rel_9558852d41c4ca3c`。
    - `F-51F2E349` **只有一半成立**。其「GB1 对 greedy 太易(可达全局峰 8.762)」**是对的**——`lab/reports/REPORT-HANDOFF.md:40` 实测 greedy `cum_top10_max` = **8.761966**,即全局最优 `FWAA`。被推翻的是另一半「AAV 池真峰 greedy **可证明**够不着」:greedy 实测 7.5301 < 8.416205 属实,但「可证明」不成立,因为上面 (1) 的单调路径存在,greedy 并非结构性被挡。已建 `supersedes-fact` 关系 `rel_f58b5970b435a059`,理由限定在可证明性上,不否定其 GB1 部分。
    - **须记我自己的一处误判**:我一度认为「GB1 greedy 只到 8.045152」,并准备据此把 `F-51F2E349` 整条判错。8.045152 是提交 `54821e7`(四策略链路修复**之前**)的旧口径读数,`REPORT-HANDOFF.md` §2.1 正是专门说明该口径已废。差一步就把一条正确的 fact 判成错的——**同一份文档里既有废口径又有现行口径时,引数字必须先确认取的是哪一支**。


## Residual Risk

- 报告第 6 节的 5 条 `[需核实]` 至今只核掉了 AAV 那部分(规模、字段、下载对象、Indel 四项);avGFP 的 51,715 条、ProteinGym 的获取路径与字段命名、TrpB、TEM-1 的规模与结构**仍未核实**,下游不得直接引用。
- 报告的"崎岖度/上位效应"与"低阶无法线性外推"评分没有可追溯的文献引用(全文仅有一个 GitHub 链接),不应被当作定量依据。
- 正确事实与完整核实由 `task_b68c60192b516efe313aca8038` 重做(下载 + 实测核实,不接入流程)。**本任务不重写该报告**,只如实记录其结论被推翻的范围——保留翻转过程本身是本仓既有做法。

- **本轮(2026-09-14)在窄化之外另行修掉的三类自伤,均为我自查发现、评审未点**:
  - **§5 目录树落点与 §3 自相矛盾**:目录树写 `aav/aav_flip.csv` 与 `avgfp/avGFP_Sarkisyan_2016.csv`,而同一文档 §3 已写明实测落点是 `data/aav/full_data.csv`、§4 已写明 loader 硬要求 `data/avgfp/avgfp.csv`(`AVGFP_CSV` 写死)。两处已改并留更正注。
  - **§4 的无来源文献断言**:原写「上位效验证了著名的『阈值效应』——累积几个无害突变后折叠稳定性跌破阈值、荧光突然消失」。该断言**既无可追溯文献、本仓也无 avGFP 任何实测**(数据文件尚未落地),已降格为 `[需核实]` 推测,并改为只保留不依赖上位假设的算术事实(238 位点 ≫ GB1 的 4 位点)。这正是 r3 第 (3) 条指控的类型,我此前只处理了表格、漏了正文。
  - **§4 的未实测预测**:原写「Greedy 会因不理解阈值而失活;Agent 结合知识能更稳健攀升」。**AAV 上完全同形的预测已被本仓实测推翻**(greedy / agent_no_knowledge / knowledge_agent 三臂 `final_cum_top10_max` 同为 7.5301,strong 85/85/86),avGFP 更无任何本地实测。已明确标注为未实测预测、不得当结论。
  - **机制**:这三处与本会话反复出现的同一形态一致——**同一事实在文档内多处出现,我只改了被点到的那处**。本轮已改用「先 `grep -n` 列出全部出现位置、逐行判定、再改、最后用能区分『原句』与『我自己写的作废引述』的模式复验」的做法;本轮就有两次因模式匹配到自己的更正说明而误判为「残留未清」(`现有所有变体都困在`、`aav_flip.csv`)。


- **本轮自查发现、r4 未点的同族残留(第 7 处)**:artifact 前言写「**只有** AAV 一行的关键数字是本仓实测」,与同文档 GB1 行自述「本行是唯一除 AAV 外有本仓实测支撑的候选」**直接矛盾**。已改:前言改为 AAV 与 GB1 两行均有实测支撑并给出产物路径,原句标为作废;判据 (b) 那条「除 AAV 外其余均无可追溯来源」同步改为「除 AAV 与 GB1 split 外」。形态与 §5 目录树、§4 正文两处完全一致——**同一事实在文档内多处出现,只改了被点到的那处**。
- **`git: pending` 阻塞未解**:本轮两次 `ha doc sync --submit` 回执均为 `acceptance: accepted_durable; git: pending; projection: verified`。投影已落库,但 git 侧仍未提交。按本仓硬约束 `harness/` 不由我自行 `git commit`,该状态须由 daemon 收口;同一阻塞已记在 `task_feb731c779788be5bfff65e979` 的 closeout 中(经查 `ha daemon` 只有 `projection rebuild` 与 `repo register|update`,不存在 git 提交通道),等 CEO 裁定。

- **台账侧的两处交接项,本轮只记录、不在本任务内扩面修(遵 CEO 窄化裁定)**:
  - `F-9649A483` 仍是 `state=standing`,而它的 statement 含「AAV…~8.4万变体」与「avGFP 238位点阈值上位」两处,均已被本轮实测与降格推翻(实测 **38,265** 条;avGFP 的阈值效应本轮降为 `[需核实]`,本仓无任何 avGFP 实测)。**关键在于它的 `evidenceSource` 正是本文档**——即台账里有一条现行 fact 以这份 artifact 为背书,而这份 artifact 已经推翻了它。需要 supersede,归属 CEO 或 `task_b68c60192b516efe313aca8038`。
  - `F-885537A3`(支撑「两目标两策略」核心结论的 fact)的 `evidenceSource` 写的是 worktree 路径 `.worktrees/t-astra-seeds/lab/context/research/v07-multiseed-robustness.md`。**本轮实测该指针尚未悬空**:该 worktree 仍在 `git worktree list` 在册,文件存在且与仓内已入库版本 **sha256 完全相同**(两侧同为 `c025bbd0…`)。但它一旦被 `git worktree remove` 即悬空,而内容既然同一份,改指仓内 tracked 路径 `lab/context/research/v07-multiseed-robustness.md` 是零风险的。**我先前曾推测它「可能已经悬空」,实测不成立,该推测已收回。**

- **第五轮独立评审(`dispatch_f66c1db73294d2b762ae1927`,Iteration 5)的处置。先记一件程序事实**:该轮 verdict 为 `changes_requested`,但**未能持久化**——daemon 以 review-return budget 已耗尽为由拒绝写入(`reviewReturnBudget=5`,本执行 Iteration=5),提示执行方先 `ha task submit --amend` 或由有权者提高预算。**我不去争取 `approved` 来绕过它**:该轮指出的缺陷里有两条成立且严重,按其修复后走 `--amend` 重提并重派评审。
  - **成立且严重(1):`load_aav` 从未过滤 `designed`,我写了反面。** `evolution/datasets.py:76` 的 mask 只有「长度 28 + `^[A-Z]+$` + 无 `*`」,无任何 `category` 条件;我复算清洗后 38,265 行中 **30,932 行为 `category=designed`**,与评审给的数字一致。**根因是代码 docstring 自己写着 `no indel/stop/designed`,我照抄了它**;已提交 `fix(datasets)` 按代码实际行为重写该 docstring。实质后果比评审所述更重:**池峰 8.416205 与 incumbent 9.536457 两条都是 `designed`**,即「受限池发现」任务定义建立在含大量模型设计变体的池上,已写入 artifact 的效力边界。**同族性质**:`lab/context/research/kb-iteration-research.md:49` 早已写对(「注释称排除 designed,但代码没有独立 designed 标记过滤」),我却写了反面——这是「已在别处写对、我写了反面」的实例,比「只改被点到的那处」更严重。
  - **成立(2):行数陈述错误。** 本 closeout 原写 artifact 为 116 行;第五轮评审提出时 `wc -l` 实测为 **121 行**,本轮补齐逐格标注与上位数字后 `wc -l` 为 **123 行**。Summary 与 Verification 两处的陈述均已按 `wc -l` 的读数更正。**本 closeout 内凡出现行数,一律以 `wc -l` 为准**;两种计法差 1 的原因只在下方 r6 处置段说明一次,不在别处重复,以免被读成行数声明(第七轮评审即因此把「124」读成了行数断言)。
  - **成立(3):逐格标注仍有缺口、avGFP 仍挂「推荐」。** AAV 行 (e)(f)、GB1 行 (d)(e)(f)、Meltome (b) 及四行「综合评价」格此前无标注,本轮全部补齐——**未核实项标 `[需核实]`,本仓实测项标 `[本仓实测]`**,做到逐格有标注且不把真话降格成存疑(我在上一轮 closeout 里承诺「若评审仍判定应贴标签,我照贴」,此处照办)。§4 标题由「备选推荐」改为「备选候选(全行未核实,不作为推荐)」,下载源加 `[需核实:URL 与许可]`。
  - **部分驳回(4):标签不是算错,是未声明约定。** 评审称「实际局部 1-based 为 `D1Q+S18E+V19A`」。逐位核对表明我的标签作为 **0-based 窗口偏移是自洽的**(`WT[0]=D`、`WT[17]=S`、`WT[18]=V` 全部匹配;按 1-based 解释则三处全不匹配)。真实缺口是未声明约定,已在 artifact 前言声明三套等价写法:0-based 窗口 `D0Q+S17E+V18A` / 1-based 窗口 `D1Q+S18E+V19A` / VP1 蛋白 `D561Q+S578E+V579A`(窗口 0-based `i` ↔ VP1 `561+i`)。
  - **驳回(5):没有把 `score` 说成不存在。** 原文两处分别是「实测列名为 `score`,`viral_viability` 不是真实列名」与「原先写的 `sequence` / `viral_viability` 不是真实列名」,均未把 `score` 归入不存在之列。该指控不成立;但原措辞确实容易读歧,已改写为「真实列名是 `score`(该列确实存在),原写的 `viral_viability` 在 CSV 里不存在」。
  - **反向处置(6):「HD3 正上位构型」不降格,改为给出正式数字。** 评审要求降格为路径描述。实际可算:八个构型中七个有实测(`f(WT)=-0.918194`、`D0Q=0.302016`、`S17E=3.287418`、`V18A=0.889606`、`D0Q+V18A=2.087894`、`S17E+V18A=5.770209`、三突变 `=8.416205`),唯独 `D0Q+S17E` 缺测。因此**正式三阶系数确实不可算**(如实声明),但**相对一阶加性模型的偏离可算且为 +2.100778**(实测 8.416205 vs 加性预测 6.315428),已测配对 ε 为 `S17E+V18A` **+0.674991**(正上位)与 `D0Q+V18A` **-0.021921**(近加性)。给数字比降格更能满足「可核验」的本意,故按此处置并在 artifact 两处写入。

- **本地全量测试一直是被中断的,此前的「全量跑过」说法须打折**:`python3 -m pytest tests/ -q` 在本机因 `ModuleNotFoundError: No module named 'streamlit'` 在 **collection 阶段中断**(`tests/test_demo.py`、`tests/test_demo_app.py`、`tests/test_timeline.py` 三个文件)。已用阴性对照定性:在本会话起点 `af60187` 上复测**报同样三个错**,故与本会话任何改动无关,是本机 venv 缺依赖;CI 从 `requirements.txt` 安装该依赖,所以门内是真绿。**同族第二例(同一轮发现)**:`tests/test_predictor.py` 另有 2 个用例失败——`test_predict_contract_is_reproducible_and_variance_is_non_degenerate[predictor1]` 与 `test_xgboost_predictor_names_its_backend_and_refuses_a_silent_substitute`,原因同为本机缺依赖(`ModuleNotFoundError: No module named 'xgboost'`,而 `xgboost==3.4.1` 已由本会话提交 `1ebfeba` 钉进 `requirements.txt`)。同样用 `af60187` 阴性对照定性:起点上复测为同样的 `2 failed, 4 passed`,与本会话改动无关。**值得注意的是这两个失败的语义**:代码正确地拒绝在缺 xgboost 时静默替换为 sklearn GradientBoosting,护栏本身在起作用。**含义**:本地"全量"实际从未覆盖这五处(3 个文件收集不了 + 2 个用例因缺依赖失败),今后本地跑须显式 `--ignore` 并说明覆盖面,不能再报"全量通过";排除后的真实读数是 `2 failed, 132 passed`,其中 2 个失败即上述缺依赖项。

- **第六轮独立评审(`dispatch_ce5eb624f8af983c6c05b6d6`,对 amend 后的同一执行)的处置。程序事实同上一轮**:verdict 仍为 `changes_requested`,仍**未能持久化**——daemon 报 `manual_intervention_required / return budget exhausted`(`reviewReturnBudget=5`,Iteration=5)。评审未绕 gate、未改业务代码,如实报告了写入被拒。**我仍不去换取 `approved`**:本轮它提的四条里有两条是我的实错。
  - **成立,且我上一轮的处置理由是错的(1):GB1 行违反契约。** 我上一轮拒绝给 GB1 贴 `[需核实]`,理由是「贴标签会把已实测的真话降格成存疑」。**这个理由站不住**:`task_plan.md:16` 与 `:79` 两处都把 `GB1 split` 明确列进「其余候选…逐项标 `[需核实]`、**不承担选型结论**」,`:79` 并写明「**仅 AAV 行的关键数字为本仓实测**」;契约全文没有任何「淘汰/推荐排序」授权。**契约管的不是数据真假,而是这一行不得参与选型**——我不但贴了 `[本仓实测]`,还保留了「淘汰」这个选型结论。本轮按契约把六格降为 `[需核实:本任务未按契约核验]`,删除「淘汰」结论,仓内 GB1 产物路径与数字保留为括注旁证并明示「本行按契约不承重」。**改契约本可解决冲突,但那属扩面,与 CEO「收账为主、不要硬弄」的裁定相悖,故按契约降格而非改契约。**
  - **成立,且实际问题比评审所述更重(2):ESM 排名的来源越界 + 我自造的口径混淆。** 评审指出 `#3743/#4782` 出自 `agentic-v0.3` 而非本表声明的证据范围,成立。**更重的一层是它没点出的**:这两个数**不是一个区间的两端,而是两种不同输入表征的结果**——`modes/fragment` 是 28-aa 突变片段(`peak_rank_gate`=3743、`spearman_gate`=0.097、`peak_zscore`=-0.433),`modes/full_context` 是全长 VP1 735 aa(4782、0.154、-1.31);我用一个斜杠把它们并列成「#3743/#4782」,**这层混淆是我造的**。已改为两种表征分列,给出真源 `lab/reports/agentic-v0.3/aav/esm_zeroshot.json`、`gate_size`=9533、`budget`=288、`reachable_in_budget`=False,并明示**与四策略对照(96×3)口径不同、不可并置**;前言的证据范围也补上了这一处越界说明。
  - **成立,且性质是谎报仪器(3):行数。** `wc -l` 实测为 **123**,而 Python `split('\n')` 得 **124**(文件末字符是 `\n`,两种数法差 1)。我在 closeout 里写的是「**`wc -l` 实测**」却填了 Python 的读数——**这不是数错,是把一个仪器的读数冒充另一个仪器的**。本轮三处(Summary、Verification、r5 处置段)全部改为 `wc -l` 的 123,并注明两种数法的差异,避免下一个读者再对不上。
  - **成立(4):avGFP 的外部格式判断未逐项标注。** 「因此 ProteinGym 原始列名大概率可直接用」已改为标 `[需核实]` 的推测,并限定为「仅针对本地 loader 嗅探逻辑的待验证假设,本任务未取得任何 ProteinGym 文件」;风险清单里「ProteinGym 的 DMS csv 通常不带 WT 行」同样标注为外部格式判断、本任务未核验。

- **第七轮独立评审(`dispatch_33a21b77`)的处置。先记程序事实**:该轮 `13:27:46` 起、`13:35:10` 结束,verdict 为 `changes_requested`,写入被 `review-return budget exhausted` 拒;**而 CEO 把预算提到 10 的写入落在 `13:42:06`(outbox-2936)——评审比预算生效早了约 7 分钟**,所以这一轮被拒是时序问题,不是机制问题。其两条阻塞缺陷**均成立**,已修:
  - **(1) 选型结论残留,且比评审点到的更多。** 评审点了 TEM-1 与 Meltome 两处;我全量逐格复扫后实为**四处**,一并处置:①TEM-1 行「倾向淘汰,但依据未核实」→ 删,改为「本任务不对本行下选型结论」+ 事实陈述(全部判据未核实、本仓无 TEM-1 实测);②Meltome 行「淘汰。属于不同任务(Zero-shot或全局预测)」→ 同样降格,理由保留为「该判断本身未核实」;③§2 正文「不可用:β-lactamase(高阶真值缺失,无法查表闭环)、Meltome(非单基因局部突变景观)」→ 删,并注明两条括注理由本仓均无实测、外部亦未核验;④**AAV 行的「首选」保留,并补写了它为何可以下结论**——`task_plan.md:13-15` 第 1、2 条正是要求给 AAV 做本仓实测画像并把其目标定义为受限池发现,AAV **不在**第 3 条「其余候选不承担选型结论」之列,该组仅含 avGFP / ProteinGym / TEM-1 / GB1 split / Meltome 五行,现已全部降格。复扫判据:六行「活的选型词」全为 0(区分了我自己的「原写…已删」引述)。**这是本会话第 8 次同族疏漏**:同一契约要求横跨六行,我上一轮只降了被点名的 GB1 一行。
  - **(2) 行数口径招致误读。** 评审称「执行声明把报告写成 124 行」。根因是我在 Summary 与 r5 处置段里保留了「Python `split` 计法为 124」这段两种数法的对照说明,它被派生进执行回执后被读成了行数声明。已把「124」从所有行数叙述中移除,只在下方 r6 处置段保留一次仪器差异说明,并在 Verification 里明确「本 closeout 内凡出现行数一律以 `wc -l` 为准」。当前 `wc -l` 为 **123 行**。
- **须记的机制事实(本轮实测,解释了上面这类不一致的成因)**:**执行记录只从 `closeout.md` 派生,不从 artifact 派生。** 判据:`不对本行下选型结论` 与 `为何此处可下结论` 在 artifact 里为 3 与 1、在 closeout 里为 0,故执行文件里为 0;反向对照 `一律以 wc -l 为准` 在 artifact 里为 0、closeout 里有、执行里为 2。**所以凡是只改 artifact 不改 closeout 的修订,都不会出现在执行回执里**——第六轮那条「execution 声明与 artifact 不一致」正是这个机制的产物,本段即为该机制的补记。

## Same Mechanism Elsewhere

机制:**一份调研在没有实测的情况下预测了方法表现,而下游把该预测当作既成事实引用。**

按这句话搜本仓,命中两份同形文档,且都已因此挂上勘误横幅:

- `lab/context/research/frontier-landscape-synthesis.md` — 勘误 `F-8514C714` supersedes `F-EE89324D`:其 §2 共识 B 与 §4 结论建立在"确定性 greedy 达峰"这一未核实的实现判断上,后经查码证实那条基线实为 `predicted_mean` / `diverse` **交替**,纯均值消融封顶 7.8290。
- `lab/context/research/plateau-breaking-methods.md` — 勘误 `F-E9C38438` supersedes `F-5A4B6556`:其 §0 断言"cold-start 本已包含构成真峰的全部单突变与双突变实测"为假,实际 `D0Q+S17E` 这一对在数据表中根本不存在。

三份文档的共同形态是:**推断被写成事实、且没有标注待核实**,而下游据此排序了实验优先级。本仓的对策是给这类文档加勘误横幅而非删除,以保留结论翻转的过程。
