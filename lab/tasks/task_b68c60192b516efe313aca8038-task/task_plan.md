# 获取多个更难的定向进化基准数据集:先下载核实,不接入

Task Contract: harness-task v1

## Brief

把几个候选的更难数据集**下载到本地并实测核实**(规模、字段、序列长度、HD 分布、是否含插入删除、是否有显式野生型行),产出每个数据集的 manifest 与一份核实报告。**本任务不接入流程、不改 campaign、不跑任何实验**——它只负责把数据拿到手并把"传闻数字"换成实测数字,让 CEO 据此拍板先上哪一个。

## Goal

`data/` 下就位下列数据集,每个附一份 `manifest.json`(含 sha256 与全部实测数字),外加一份核实报告说明每个数据集"实际是什么样、难在哪、我们的流程能不能直接吃"。

交付物第一个读者是 CEO;他读完要能不查代码就回答:**哪个数据集可以明天就跑,哪个需要改代码,哪个根本不适合。**

## Context

### 为什么要做这件事(两条实测,不是推测)

1. **GB1 的指标饱和了**:三档冷启动(easy 5,000 / hard 2,168 / sparse 77)下,四策略里有三个都达到同一个全局最优 `FWAA` 8.761966,只有 sparse 档的无知识臂停在 5.7720。**指标封顶 ⇒ 策略之间拉不开差距**,对照实验失去鉴别力。
2. **AAV 暴露的不是难度不够,而是优化目标自我否定**:候选池峰值 8.416205 **低于** cold-start 里已经含着的最高值 9.536457(初始集合中高于候选峰的共 3 条,均为 HD2)。也就是说"找到池内峰"这个指标衡量的是"能否找到一个比已知最优更差的点"。这条已在 `dec_016C25D18F5C1C17F9A7173E75` 的 claim C2 里自曝进报告正文。换一个更难的数据集**不会自动修掉这个问题**(它由 `task_cec65c821f05a08d9a86681332` 单独处置)。

### 一条必须先说清的教训:"选更难的地形"不保证方法分化

本仓 2026-09-11 已经做过一次同类调研,产物是 `lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md`,它选的 Top-1 就是 **AAV**,理由正是"能真正把模型与 Agent 推向极限"。它当时押了三条,实测只兑现一条:

| 当时的预测 | 实测结果 |
|---|---|
| 知识增强会显出价值 | ✅ 兑现:无知识 strong 69 / 峰 6.1862 / 平均 HD 8.53;知识 strong 166 / 峰 7.8290 / 平均 HD 3.42 |
| "greedy 会因幻觉组合而中途卡死" | ❌ 反了:纯利用 greedy 就是全场最高分 strong=166 |
| "Agent 靠推理与探索显出优势" | ❌ 反了:真峰要 UCB β=3 才能确定性 30/30 达到(strong=128),LLM 自主决策两个指标都没匹配最优 |

**所以本任务只负责"把数据拿到手并核实",不承诺任何难度结论,也不预测策略会怎么分化。** 谁再写"这个数据集会让 Agent 显出优势",必须先有实测。

### 我们流程对数据集的硬约束(决定一个数据集能不能用)

1. **oracle = 真值查表**:Agent 只能提名并"测量"已在表内的变体。所以数据集必须自带一张够大的「变体 → fitness」表。没有高阶变体真值的数据集(如 β-lactamase TEM-1,以单突变为主)**无法支撑多轮闭环**,只能用于预测器评估。
2. **等长替换假设**:`DatasetSpec` 假设所有序列与野生型**等长、只有替换**(`evolution/pool_campaign.py:45-49` 的契约说明与 `:66-67` 的 `_subs()` 用 `zip(seq, wt)` 逐位比;`evolution/datasets.py:76,108` 按 `len(wt)` 过滤)。**含插入/删除的数据集属于重构,不属于接入**——核实时必须明确报告每个数据集是否含 indel,但不要尝试适配。
3. **avGFP 的 loader 已经写好了**:`evolution/datasets.py:89-115` 的 `load_avgfp` 已实现列名嗅探(`mutated_sequence|sequence|seq` × `DMS_score|fitness|score|target`)、强制要求**显式 WT 行**(`mutant` 列取值 `WT|WILD_TYPE|WILDTYPE`)、自算 hd、自动去重与非法字符过滤;`REGISTRY`(`:118`)已注册 `avgfp`;`evolution/pool_campaign.py:213` 与 `agent/auto_researcher.py:1175` 的 `--dataset` choices 都已含 `avgfp`。**唯一缺的是 `data/avgfp/avgfp.csv` 这个文件**(目录当前不存在),且该 loader 至今只被 `tests/test_pool_campaign.py:26` 用临时 csv 单测过、**从未真跑**。
4. **大文件不入 git**:按 `data/README.md` 的既有约定(GB1 那份 44MB 地形就是故意不提交的),下载下来的原始数据文件一律不进 git,只提交 manifest。

## 候选数据集清单(逐个说清"是什么、为什么它可能更难、要核实什么")

### ① avGFP — Sarkisyan et al. 2016(优先级最高)

- **是什么**:绿色荧光蛋白的全域随机突变文库,238 个氨基酸位点,fitness 是对数荧光强度。
- **为什么可能更难**:它有 GB1 和 AAV 都没有的一个结构——**阈值型致死断崖**。累积若干个各自无害的突变后,折叠稳定性一旦跌破阈值,荧光会**突然消失**而不是平滑下降。纯贪心会一路累积微小正向突变直到掉进深渊。
- **为什么对我们特别值**:报告第 7 章唯一有正面证据的机制是"工具契约能表达排除,agent 行为才改变"。在 GFP 上,"排除某些突变组合"从一个可追溯的装饰动作变成**决定成败的动作**,这个机制在这里才有非平凡的考场。
- **下载源**:ProteinGym 的 DMS 数据集,标识形如 `avGFP_Sarkisyan_2016`。落点 `data/avgfp/avgfp.csv`(loader 写死了这个路径,见 `datasets.py:86`)。
- **必须核实**:①总变体数(传闻 51,715,**未核实**);②HD 分布——尤其 HD≥3 的变体有多少,这决定多轮闭环会不会提前把池子耗尽;③**是否有显式 WT 行**(loader 强制要求,没有会直接抛 `ValueError`);④fitness 列的实际名字与取值范围;⑤是否含 indel。

### ② TrpB 四位点组合文库

- **是什么**:色氨酸合成酶 β 亚基的四残基组合文库,与 GB1 同形——4 个位点、接近完备测量(量级 16 万)。
- **为什么可能更难**:GB1 饱和的原因是地形平滑;TrpB 同样规模但显著更崎岖。**它的科学价值在于能做"唯一变量 = 地形"的受控对比**:同样 4 位点、同样 288 预算、同样代码,只换地形,看四策略是否分化。这能直接回答"GB1 饱和到底是地形平滑,还是我们预算给太宽了"。
- **接入代价要在报告里说清**:它若只走 pool 线,成本与 avGFP 相同;但若要出**四策略对比**(走 workflow 线),会撞上三处核心硬编码——`evolution/mutations.py:10` 的 `MUTABLE_POSITIONS=(39,40,41,54)`、`features/one_hot.py:10` 的 `FEATURE_DIM=80`,以及 `features/esm2.py:65` 那句 `variant_to_sequence(variant) if len(variant) == 4 else variant`(**任何长度恰为 4 的新序列会被静默展开进 56-aa 的 GB1 骨架**,这是最危险的一处)。
- **必须核实**:①真实变体数与完备度;②位点编号与野生型残基;③fitness 的定义与量纲;④数据是否公开可直接下载(还是需要从论文补充材料里扒)。

### ③ ProteinGym 的高难 DMS 子集(挑 2-3 个)

- **是什么**:ProteinGym 是标准化的 DMS 基准集合(两百余个替换型 assay),字段统一。
- **挑选判据**(answer-agnostic,不看我们的方法表现):优先挑**高阶变体占比高**且**零样本预测相关性低**的 assay——前者保证闭环有纵深,后者保证任务不是一眼就能被通用先验解掉。
- **为什么值得多拿几个**:单一数据集上的结论永远可以被质疑成"挑了个对自己有利的地形"。手里有 3-5 个同格式数据集,结论才能从"我们在一个地形上赢了/输了"升级成"跨地形看,知识增强在什么条件下有用"。
- **必须核实**:①每个 assay 的变体数与 HD 分布;②`mutant` 列的格式(是否 `A1B` 风格、多突变如何分隔);③序列长度;④是否含 indel(ProteinGym 有单独的 indel 子集,**不要拿那部分**)。

### ④ SARS-CoV-2 RBD — Starr et al.(战略候选)

- **是什么**:受体结合域的深度突变扫描,同时测了**ACE2 结合力**与**RBD 表达量**两个目标,并且在**多个背景**(Wuhan-Hu-1 / Omicron 各亚系)上各做了一遍。
- **为什么它在清单里是特殊的**:前面三个都只是"更崎岖的单目标地形",而前沿共识(我们自己四版也复现了)是——**在"选下一批"这个利用步上,LLM 自主决策打不过固定采集函数**。地形更崎岖只会让固定采集函数赢得更明显。真正能给 agent 腾出位置的,是固定采集函数**无法表达**的决策面:多目标权衡、跨背景迁移。这个数据集是清单里唯一提供该结构的。
- **必须核实**:①两个目标列是否都齐全、量纲与缺失情况;②有几个背景、同一变体在不同背景间是否可对齐;③变体数与 HD 分布;④许可与引用要求。

### ⑤ β-lactamase TEM-1 — Firnberg et al. 2014(仅作预测器评估,不做闭环)

- **是什么**:试题原文点名的数据集之一,以单突变为主。
- **定位要写清**:已判定**不适合多轮闭环**(高阶真值缺失,oracle 查不到 agent 提名的组合)。拿它只为两件事:①试题点名了它,手里有它便于答"为什么没用它";②可作预测器阶梯的额外评估集。
- **必须核实**:是否真以单突变为主(即 HD≥2 的变体占比),用实测数字支撑"不适合闭环"这个判断。

## Required Reading

按顺序,并标明权威级别:

1. `evolution/datasets.py`(**权威**:接入契约的唯一真源)——`load_aav`(`:61-86`)与 `load_avgfp`(`:89-115`)是两份现成样板,`DatasetSpec` 的字段定义在 `evolution/pool_campaign.py:43-54`。
2. `data/README.md`(**权威**:大文件是否入库的约定)。
3. `lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md`(**参考,且已知部分结论被推翻**)——它第 6 节有一份"[需核实] 风险清单",本任务要把那 5 条逐条核掉。读它时以本 plan 的 Context 为准。
4. `lab/context/research/AI4S-assignment.md`(**权威**:试题点名的可用资源范围)。

## Entry Conditions

- 需要网络访问以下载公开数据集。
- 不需要 GPU;不需要 ESM-2(核实阶段只看表格结构,不抽特征)。
- 磁盘需留出若干 GB(ProteinGym 全量较大,**只下需要的 assay,不要整包拉取**)。

## Dependencies

- 无上游依赖。
- 下游:CEO 据本报告拍板后,接入工作单独立任务。GB1 遗留硬编码的清理是 `task_ff24b0e33edb3412f4dd070e4b`(当前 planned);若核实结论指向"要走 workflow 线",该任务是前置。

## Execution Surface

- 仓库:`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`,独立 worktree 与任务分支。
- 允许写入:`data/<dataset>/`(数据文件与 manifest)、`data/README.md`(补充新数据集说明)、本任务包 `artifacts/`(核实报告)、必要的一次性核实脚本(放 `scripts/`,需可复跑)。
- **禁区**:`evolution/campaign.py`、`evolution/pool_campaign.py`、`agent/auto_researcher.py`、`features/`、`knowledge/`、`models/` 一律不改——本任务不接入。

## Constraints

- **不接入、不跑实验、不改采集或门禁逻辑。** 发现 loader 有 bug 也只记录不修(留给接入任务)。
- **不得改动 AAV 的门内 9533 候选口径**,它被锁为跨版本可比基准。
- **原始数据文件不得 commit 进 git**;只提交 manifest 与脚本。提交前用 `git status --porcelain` 自查有没有大文件混进去。
- **不得把传闻数字当实测**:报告里每个数字要么附上产生它的命令,要么显式标 `unverified` 并注明来源。这条是硬要求——本仓已有多次"记忆里的数字与实测不符"的记录。
- **绝不 `git commit` / `git add` `harness/` 下任何文件**(daemon 单写);任务包内的产出通过 `ha` 命令或 `ha doc sync` 落库。
- 某数据集若需要注册账号、接受额外许可或申请授权才能下载,**停手报回**,不要代替 CEO 接受任何条款。

## Checkpoint

命中即停并上报:
- 某数据集需要登录/申请许可/接受协议才能获取;
- 某数据集实际含 indel(报告它,但不要尝试改 `DatasetSpec` 去适配);
- 下载体积远超预期(单个 assay > 1GB);
- 核实结果与 `harder-dataset-survey.md` 的既有断言冲突(这是好事,要明确写出来,并说清哪一方有实测支撑);
- 发现某数据集根本不满足"真值查表"前提。

计划性回报点:每完成一个数据集的下载 + 核实,就 `ha task progress append` 报一次,不要攒到最后一次性交。

## CI/Gate Authority Stop Condition

本任务不是 CI/gate/governance 任务。若推进需要修改 CI 或门禁权威面,停止实现、记录 blocker、报回 CEO。

## Implementation Plan

对清单里每个数据集,逐个走:

1. **定位**:找到确切的公开下载地址,记录 URL、文件名、体积、许可与引用要求。
2. **下载**:落到 `data/<dataset>/`,记录 sha256。
3. **实测核实**(全部用命令算,不靠记忆):
   - 总行数 / 去重后变体数;
   - 全部列名与前几行样例;
   - 序列长度分布(是否等长);
   - 相对野生型的 HD 分布(尤其 HD≥3 的数量);
   - 是否有显式 WT 行、WT 的 fitness 值;
   - fitness 的取值范围、缺失值数量;
   - 是否含 indel(长度不等即为信号)。
4. **写 manifest**:`data/<dataset>/manifest.json`,含来源 URL、sha256、上述全部实测数字、核实日期。
5. **可加载性判定**:对已有 loader 的(avgfp)直接试 `python -c "from evolution.datasets import load; s=load('avgfp','one_hot'); print(s.name, len(s.df), s.wt[:20])"`;对没有 loader 的,给出"需要新 loader,预计改动 = datasets.py 加一个 load_xxx + REGISTRY 一行 + 两处 choices"的结论,**但本任务不写那个 loader**。
6. **写报告一节**:这个数据集是什么、实测数字、能不能直接吃、难在哪(只说数据结构层面的事实,不预测策略表现)。

最后汇总一张对比表 + 一条明确建议(哪个先上、为什么)。

## Deliverable Contract

- **形态与落点**:
  1. `data/<dataset>/` 下的原始数据(**不入 git**);
  2. `data/<dataset>/manifest.json`(**入 git**);
  3. 核实报告落本任务包 `artifacts/dataset-verification.md`;
  4. 可复跑的核实脚本落 `scripts/verify_dataset.py`(或按数据集分文件)。
- **交给谁**:CEO。他读报告后拍板接入顺序。
- **报告必须包含的一节**:「与既有调研的冲突」——逐条回应 `harder-dataset-survey.md` 第 6 节那 5 条 `[需核实]`,说明核实结果是确认还是推翻。

## Evidence Protocol

- 每个数字附上产生它的命令(或脚本内的函数名 + 调用方式),使其可复算。
- 传闻/记忆里的数字一律标 `unverified` 并注明出处。
- sha256 必须实算并写进 manifest。
- 声称"loader 能吃这个数据集"之前,必须真的把 `load()` 跑一遍并贴出输出;**回执不是证据,跑通才是**。
- 对"是否含 indel"这类二值判断,给出阴性对照:说明你是怎么确认"没有"的(例如序列长度唯一值只有一个)。

## Verification

- 每个下载的数据集都有 manifest,且 manifest 里的 sha256 与磁盘文件实算一致。
- `avgfp` 能被 `evolution.datasets.load('avgfp', 'one_hot')` 成功加载并打印出变体数与 WT 前缀(若失败,报告里写清失败原因与所需修复,**不要改 loader**)。
- `git status --porcelain` 确认没有大数据文件被 stage。
- 报告里每个数字可追溯到一条命令或被标注 `unverified`。
