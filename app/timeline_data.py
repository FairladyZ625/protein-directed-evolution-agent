"""Pure, read-only adapters and structured research knowledge.

No Streamlit, model fitting or campaign execution.
Provides immutable metrics, event parsing, epistasis calculations,
and curated research insights across v0.1 -> v0.7.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

EVIDENCE = Path(__file__).parent / 'timeline_evidence'

# ---------------------------------------------------------------------------
# 版本元信息与科学问题 (学术化实证演进)
# ---------------------------------------------------------------------------
VERSIONS = {
    'v0.1': (
        '无约束探索',
        'v0.1 无约束大模型探索 · 缺乏理化先验导致结构灭活',
        '在脱离生物物理与化学先验约束的条件下评估大语言模型自主探索能力。由于缺乏序列结构可行性约束，高方差探索盲目累积高阶多点突变，导致候选序列陷入结构破坏与功能丧失的活性荒漠（新测最高适应度仅 5.9610，有效强变体仅 15/288）。',
        '必须为离散序列候选搜索空间引入基于空间几何与进化保守性的严谨物理化学可行性门禁。',
    ),
    'v0.2': (
        '理化双门禁',
        'v0.2 理化双门禁约束 · 遏制非功能突变但受制于加性假设',
        '引入突变步长（汉明距离 HD≤4）与氨基酸进化保守度（BLOSUM62≥0）双门禁机制。该约束有效阻断非功能突变并遏制失活，收敛表现成功追平经典加性贪心基线（7.5301，强变体达 93/288），但受制于一阶加性特征假设，后续参数调优均无法突破 7.5301 理论天花板。',
        '收敛瓶颈究竟源于序列采样策略缺陷，抑或底层代理模型对高阶非线性真实能量面缺乏表征能力？',
    ),
    'v0.3': (
        '代理模型诊断',
        'v0.3 代理模型体系化诊断 · 加性特征对高阶真峰的表征失真',
        '暂停高成本湿实验测试，开展全空间表征编码与代理模型的系统级扫描。实验表明，6 组经典加性基线模型将全局真峰预测排序抑制在第 2,776 位之后——在 288 次有限实验预算约束下，高阶真峰在统计学上完全不可观测。',
        '必须跨越一阶加性独立假设，构建能够显式捕获残基成对非线性协同效应的上位感知代理模型。',
    ),
    'v0.4': (
        '上位感知代理',
        'v0.4 残基成对上位感知 · 突破加性天花板并首次定量测定探索税',
        '成对上位感知代理模型将未测候选池全局真峰预测排名由第 2,776 位跃升至第 429 位。确定性交替调度在第 4 批次直接捕获 8.4162 全局真峰，实证击穿加性理论天花板；而纯大模型自主决策停滞于 7.8290 局部鞍点，首次严密量化探索税（Exploration Tax Δ = 0.5872）。',
        '在高置信度代理模型驱动下，需定量度量大语言模型在微观连续空间低效探索对受限实验预算造成的置换损耗。',
    ),
    'v0.5': (
        '探索退火机制',
        'v0.5 批次衰减探索退火 · 动态平衡探索与利用的实证探索',
        '设计小批量采样与动态方差退火机制，旨在通过动态收缩探索权重抑制探索税。然而过早的方差退火在初期过早剪枝了潜在高适应度进化分支，最终实测最高分降至 6.5309。本研究完整归档该关键阴性结果以指导自适应机制设计。',
        '由静态预设探索权重机制转向基于收敛状态动态监测的停滞判定与回溯逃逸机制。',
    ),
    'v0.6': (
        '停滞回溯逃逸',
        'v0.6 元层停滞判定与回溯 · 自主逃逸机制首次落地',
        '针对 v0.5 过早退火剪枝高适应度分支的阴性结果，引入元层停滞判定：累计 top-10 最大值连续 2 轮不提升即判定停滞，智能体可自主调用 redirect_batch 跳出当前簇（basin hop）。semi 构型下由固定规则给出 STALLED 标志、是否行动交由智能体判断。本代实测峰值 7.8290、强变体 166/288，逃逸机制跑通但未突破 8.4162。',
        '智能体确实在调用逃逸工具，但工具动作的变化是否真的改变了送去测量的那一批候选？需要一个不看叙述、只看实测批次的判据。',
    ),
    'v0.7': (
        '确定性机制固化',
        'v0.7 确定性机制固化 · 验证 UCB 参数置信界收敛性',
        '确定性交替采样策略在第 4 批次精确命中 8.4162 未测候选池全局真峰。进一步系统参数网格扫描证实，重探索 UCB 采集函数（β=3）在 30 个独立随机种子下实现 30/30（100%）稳健达峰，正式确立了微观确定性数学优化与宏观智能体战略调度的双环系统架构。',
        '构建具备全周期状态审计能力的外环元控制器，实现对微观连续收敛停滞的自主诊断与参数回溯调度。',
    ),
    'v0.8': (
        '反思注入·零效应',
        'v0.8 残差反思强制注入 · 读了证据却一字未改的阴性结果',
        '事件流首次记录逐变体的提名时刻预测与实测残差，并把上一轮的高估致死案例强制注入下一轮 prompt。四臂 2×2（采集档位 × 反思开关）实测：反思开与反思关的六轮送测集合逐位相同（48/48 × 6），两个采集档下皆然。智能体读了证据、在总结里讨论了那些致死 motif，甚至声称“已排除两个强致死背景”，而实测批次与对照臂逐字节一致。同一判据看得见采集档位造成的差异，所以这不是判据不灵敏。',
        '既然处理确实施加、模型也确实读了，为什么提名一点没变？是模型不会用证据，还是它手上根本没有能表达这条证据的工具？',
    ),
    'v0.9': (
        '工具契约改造',
        'v0.9 工具契约与证据同构 · 同一模型的提名立刻分叉',
        '查代码定位到根因在契约形状而非模型：exploit_ratio 是标量，没有任何取值能表达“别选带 N21D 的候选”；提示词还写着 Prefer that default 劝退显式设定，利用比地板又恰好只禁止残差所指向的“调低利用”方向。加入残基级 exclude_motifs 入口、中性化提示词、释放地板之后——同一模型、同一 seed、同一份注入内容——送测集合立刻分叉并逐轮发散（r1 46/48 → r6 8/48），agent_requested 由 0/20 变为 11/11，被排除的 20 个 motif 全部可追溯到此前注入的证据、零凭空。',
        '契约既要与证据同构，也要在实际批量下有足够分辨率：n=12 时标量杠杆的整个可用区间塌成同一个分配。下一步该测的是“门禁照常执行、同时让智能体也推理知识”。',
    ),
}

# ---------------------------------------------------------------------------
# 核心科研发现与系统结论 (Executive Summary)
# ---------------------------------------------------------------------------
EXECUTIVE_SUMMARY = [
    {
        'num': '01',
        'dimension': '微观连续收敛空间',
        'dimension_en': 'Micro-scale Convergence',
        'badge': '微观收敛 · 诚实边界',
        'badge_color': '#e11d48',
        'badge_bg': '#fff1f2',
        'badge_border': '#fecdd3',
        'proposition': '大模型微观连续参数优化的诚实边界',
        'tag': '对齐 2026 国际计算生物学干净负结果',
        'title': '大模型微观连续参数优化的诚实边界',
        'highlight': '纯 LLM 停滞于 7.8290 vs UCB (β=3) 稳健达峰 8.4162 (30/30)',
        'data_contrast': (
            '• 纯大模型自主决策：深陷 <b>7.8290</b> 局部鞍点停滞<br>'
            '• 重探索 UCB (β=3)：<b>30/30 种子 100% 达峰 8.4162</b><br>'
            '• 探索税定量测定：<b>Δ = 0.5872</b>（8.4162 − 7.8290）'
        ),
        'text': (
            '在 288 次受限微观采样中，纯大语言模型无法精准估算高维非凸能量面的连续梯度与认知方差，极易陷入局部鞍点停滞；'
            '而引入置信上界的贝叶斯优化算子（UCB β=3）在 30 个独立随机种子下达成 100% 稳健收敛。'
            '这一具有高度可信度的干净负结果，定量确认了连续参数空间并非大语言模型的优势空间，对齐 2026 年最新国际计算生物学前沿。'
        ),
        'conclusions': (
            '高维非凸蛋白质适应度能量面具有极高崎岖度与剧烈负上位性深谷。自回归大模型基于离散 token 建模，'
            '缺乏微积分尺度的认知不确定性方差精细度量与连续能量面梯度解析能力，极易陷入局部极值吸引盆。<br>'
            '<b>定量确认微观连续参数优化并非 LLM 优势空间</b>，确定性贝叶斯高斯过程/置信上限算子具备不可替代的数学收敛优势。'
            '这一具有高度可信度的干净负结果（Clean Negative Result）完全对齐 2026 年最新国际前沿文献认知。'
        ),
    },
    {
        'num': '02',
        'dimension': '系统层级与认知架构',
        'dimension_en': 'System Hierarchy',
        'badge': '系统分工 · 外环元控制',
        'badge_color': '#2563eb',
        'badge_bg': '#eff6ff',
        'badge_border': '#bfdbfe',
        'proposition': '大模型系统级分工与外环司令官重塑',
        'tag': 'Dual-Loop Meta-Controller 终局架构',
        'title': '大模型系统级分工与外环司令官重塑',
        'highlight': '外环人机协同推导关键超参 β=3；终局为调度确定性算法的 Meta-Controller',
        'data_contrast': (
            '• 外环人机协同推导：4 轮实证反思推导出致胜参数 <b>β = 3</b><br>'
            '• 内环确定性算法保障：微观采样实现 <b>100%</b> 稳健收敛<br>'
            '• 认知自证伪纠偏：主动纠正“纯贪心达峰”误判归因'
        ),
        'text': (
            '解耦微观打分与宏观推理：大模型不介入微观候选打分，而在外环承担假设生成、反思自证伪与因果归因司令官角色。'
            '本研究正是通过人机外环协同推导出致胜参数 β=3 并打破早期加性认知局限。'
            '系统终局定位为感知收敛状态、自主诊断停滞并调度确定性算法算子的 Outer-Loop Meta-Controller。'
        ),
        'conclusions': (
            '彻底解耦“高频微观数值打分”与“低频宏观假设演进”。<b>大模型不介入微观候选打分，而在系统外环承担假设生成、反思自证伪与因果归因司令官角色</b>（正如本研究人机外环协同推导出 β=3 并打破早期加性认知局限）。<br>'
            '智能体的核心价值在于高维语义空间的科学假设演绎与实验逻辑纠偏。系统终局定位为感知实验收敛状态、自主诊断鞍点停滞并调度确定性算法算子与回溯机制的 <b>Outer-Loop Meta-Controller</b>。'
        ),
    },
    {
        'num': '03',
        'dimension': '工程优化目标设定',
        'dimension_en': 'Engineering Objectives',
        'badge': '工程目标 · 目标契约收工',
        'badge_color': '#059669',
        'badge_bg': '#ecfdf5',
        'badge_border': '#a7f3d0',
        'proposition': '摆脱全知单峰假设与目标契约即收工准则',
        'tag': 'Target-Driven Stopping & 帕累托优化',
        'title': '摆脱全知单峰假设与目标契约即收工准则',
        'highlight': 'Target-Driven Stopping 准则 + 6~7 突变位点 3~4 目标帕累托前沿寻优',
        'data_contrast': (
            '• 序列空间规模：2.7 万候选池 vs 20^7 理论组合空间<br>'
            '• 真实突变维度：直面 <b>6 ~ 7 个残基位点</b>联合突变<br>'
            '• 多维目标协同：<b>3 ~ 4 项核心理化指标</b>前沿权衡'
        ),
        'text': (
            '实际实验中缺乏全量标签信息，盲目追求单一极致极值将耗尽受限实验预算。'
            '确立“工程目标契约即收工（Target-Driven Stopping）”准则，以达标临床或产业转化阈值作为终止条件。'
            '面向工业级工程落地，核心在于跨越低阶突变玩具模型，针对 6~7 个残基位点实施活性、稳定性、表达量与免疫逃逸多目标帕累托寻优。'
        ),
        'conclusions': (
            '真实未知蛋白质工程探索不存在全知先验全局最高峰，盲目追求单一极致极值在湿实验成本上并不合理。<br>'
            '确立<b>“工程目标契约即收工（Target-Driven Stopping）”</b>准则，以有限实验预算换取符合临床或产业转化阈值的有效工程体。<br>'
            '面向真实产业级落地，核心挑战在于跳出单突变/双突变玩具模型，针对 <b>6~7 个突变位点</b>上的 <b>3~4 项核心指标</b>（催化活性、热稳定性、宿主表达量、免疫逃逸）实施高阶非凸帕累托前沿寻优。'
        ),
    },
]

# ---------------------------------------------------------------------------
# 核心科研发现与未来方向 (Research Insights & Future Blueprint)
# ---------------------------------------------------------------------------
RESEARCH_INSIGHTS = [
    {
        'id': 'insight-1',
        'title': '【核心结论 1：大模型微观连续收敛的诚实边界】高维非凸参数寻优劣于确定性置信界算法',
        'tag': '干净负结果 (Clean Negative Result) · 对齐 2026 计算生物学国际共识',
        'color': '#e11d48',
        'bg': '#fff1f2',
        'border': '#fecdd3',
        'summary': '在 288 步受限微观采样预算下，纯大语言模型在连续能量面寻优中陷入 7.8290 局部鞍点停滞；而确定性 UCB 采集函数（β=3）在 30 个独立随机种子下实现 30/30（100%）收敛至 8.4162 全局真峰。该实证构成高度可信的干净负结果，定量确认了连续参数空间并非自回归大语言模型的优势场域。',
        'core_data': [
            {'label': '纯 LLM 自主决策最高分', 'val': '7.8290', 'desc': '深陷高维局部鞍点吸引盆，邻域突变呈现活性悬崖，后续轮次边际收益归零'},
            {'label': '确定性交替参考达峰', 'val': '8.4162', 'desc': '于第 4 批次命中未测候选池唯一全局真峰，击穿加性理论天花板'},
            {'label': '重探索 UCB (β=3) 稳健达峰率', 'val': '30 / 30 (100%)', 'desc': '30 个独立随机种子全部于第 3 轮达峰；纯均值贪心 (β=0) 达峰率严格为 0/30'},
            {'label': '探索税 (Exploration Tax)', 'val': 'Δ = 0.5872', 'desc': '8.4162 − 7.8290，定量表征微观低效试错付出的置换机会成本'},
        ],
        'sections': [
            {
                'title': '🔬 机理深层归因：高维非凸能量面中大模型与贝叶斯优化的数学本质差异',
                'content': (
                    '在从数万离散序列空间中按批次筛选高潜变体的微观任务中，本质属于<b>极度稀疏、高维非凸黑盒函数的数值优化问题</b>。<br><br>'
                    '1. <b>离散语义自回归与连续不确定性测度的本征失配：</b>大语言模型优势在于高维语义模式关联与定性假设演绎，但对连续空间中认知不确定性方差（Uncertainty Variance）缺乏微积分尺度的严格解析与梯度感知。<br>'
                    '2. <b>局部鞍点（Saddle Point）与负上位活性悬崖阻隔：</b>在第 2 轮攀升至 7.8290 时，变体邻域一阶单步突变均出现严重的活性骤降（适应度降至 3~4）。大语言模型因语义概率衰减误判为“演化死胡同”而过早收敛；而基于置信上限的贝叶斯算子利用方差项 $\\mu(x) + \\beta\\sigma(x)$ 赋予高不确定性区域充足探索权重，成功跨越负上位深谷并精准收敛至 8.4162。<br>'
                    '3. <b>科研价值：</b>敢于通过严谨对照实验界定“大模型微观数值优化的局限性”，是极具学术信誉的科学诚实，与 2026 年国际顶级 AI4Science 领域关于大模型分工边界的前沿认知完全契合。'
                )
            }
        ]
    },
    {
        'id': 'insight-2',
        'title': '【核心结论 2：大模型系统级分工与定位重塑】外环元认知控制器与跨尺度假设演进',
        'tag': '双环协同架构 (Dual-Loop Architecture) · 外环元控制器 · 终局形态',
        'color': '#2563eb',
        'bg': '#eff6ff',
        'border': '#bfdbfe',
        'summary': '大语言模型应解耦于微观变体数值打分，而在系统外环承担假设生成、因果归因、自证伪纠偏与算法策略编排的元控制器（Meta-Controller）角色。本研究人机外环协同经 4 轮严谨对撞推导出致胜参数 β=3，确立了外环战略推演与内环数值确定性计算的分工模式。',
        'core_data': [
            {'label': '内环实验循环 (Inner Loop)', 'val': '288 预算 DBTL', 'desc': '高频数值计算层：负责代理拟合、高通量排序、确定性采集与密码学存证'},
            {'label': '外环认知循环 (Outer Loop)', 'val': 'v0.1 → v0.9 演进', 'desc': '低频元认知层：负责实证观测归因、认知自证伪、科学假设推演与策略编排'},
            {'label': '关键突破机制', 'val': '因果认知自证伪', 'desc': '严密推翻“纯贪心达峰”误判，因果溯源确立多样性交替采样的关键贡献'},
            {'label': '自主化终局演进', 'val': 'Self-Driving Lab', 'desc': '赋予智能体自主收敛停滞诊断（Stalled Detection）能力，动态调度内环数学算子与回溯'},
        ],
        'sections': [
            {
                'title': '🔬 系统架构演进：人机外环协同如何推导关键机制并确立双环分工',
                'content': (
                    '在 v0.1 至 v0.7 的真实研发演进中，决定系统突破的关键并非微观单点序列的偶然命中，而是<b>人类专家与智能体在外环元认知层的高阶协同演进</b>：<br><br>'
                    '• <b>v0.1 无约束偏差归因：</b>无物理先验导致突变发散至非功能区，外环归因揭示“预测不确定性方差与功能致死率显著正相关”，确立空间几何与进化先验双门禁需求；<br>'
                    '• <b>v0.3 代理体系化表征诊断：</b>针对 6 组经典加性模型无法表征真峰的实证结果，外环决策果断暂停湿实验测试，调度研究智能体全面转向成对上位互作建模；<br>'
                    '• <b>v0.4 关键认知自证伪：</b>团队严密自查代码因果链，公开发表自我否定声明，推翻“纯贪心达峰”假设，确认多样性探索的不可替代性；<br>'
                    '• <b>终局系统设计：</b>未来 AI 驱动的自主科学实验室（Self-Driving Lab），核心在于“外环因果反思与超参数自适应寻优”——当内环确定性算法在复杂高维鞍点陷入停滞时，外环元控制器自主诊断瓶颈、重置采集函数置信界或触发空间回溯算子。'
                )
            }
        ]
    },
    {
        'id': 'insight-3',
        'title': '【核心结论 3：工程决策与停止准则】目标驱动终止准则与高维多目标帕累托前沿寻优',
        'tag': '工程决策契约 · 目标驱动终止 (Target-Driven Stopping) · 多目标帕累托',
        'color': '#059669',
        'bg': '#ecfdf5',
        'border': '#a7f3d0',
        'summary': '实际蛋白质工程面临无先验全知标签的高维非凸序列空间，盲目追求单一全局极值在经济学与湿实验成本上不可持续。确立“目标驱动终止（Target-Driven Stopping）”准则；指出工业级工程落地的核心在于突破低阶单突变玩具模型，实现在 6~7 个关键突变位点上协同优化 3~4 项理化指标的高阶帕累托前沿寻优。',
        'core_data': [
            {'label': '单一基准局限', 'val': '全知单峰极限假设', 'desc': '依赖完备标签先验假设，穷尽高成本实验预算以追求边际收敛极值'},
            {'label': '工业级工程准则', 'val': 'Target-Driven Stopping', 'desc': '当工程体达到预设目标契约（如特异性提升 5 倍、抗原漂移抑制）即刻终止'},
            {'label': '高阶突变组合维度', 'val': '6 ~ 7 个残基联合突变', 'desc': '跨越单/双点突变玩具模型，直面 20^7 组合爆炸下的高阶上位能量荒漠'},
            {'label': '多目标协同权衡', 'val': '3 ~ 4 目标帕累托前沿', 'desc': '多维物理化学性质联合约束：催化活性 × 热稳定性 × 宿主表达量 × 免疫逃逸'},
        ],
        'sections': [
            {
                'title': '🔬 实际工程优化机制：从理想化单点基准走向高维真实生物系统',
                'content': (
                    '1. <b>摒弃全知单峰假设：</b>在未知蛋白质新功能工程化改造中，客观上不存在全局能量面全知视图。若将目标设定为无限逼近理论极限，受限的工业级高通量实验预算将在边际收益递减的盲目试错中耗竭；<br><br>'
                    '2. <b>目标驱动终止准则（Target-Driven Stopping）：</b>工业级转化追求满足工程契约的有效候选体——例如针对 AAV 病毒衣壳靶向改造，只要对靶向细胞转导效率提升达标且中和抗体逃逸率满足临床前阈值，即刻收工转入下游产线验证，实现研发资源配置帕累托最优；<br><br>'
                    '3. <b>高阶多目标非凸帕累托优化：</b>单目标优化仅是算法基准测试的初级阶段。工业界核心卡点在于多性状之间的物理化学权衡（Trade-off，例如提升催化活性往往破坏蛋白质三维结构热稳定性）。这要求算法在 6~7 个突变位点构成的组合空间中，精确描摹多目标帕累托前沿解集（Pareto Optimal Front）。'
                )
            }
        ]
    },
    {
        'id': 'insight-4',
        'title': '【核心结论 4：先验知识库机制演进】冷启动 71.88% 缺测盲区审计与 3D 结构空间软权重导向',
        'tag': '数据完整性审计 · 3D 结构空间先验 · 缺测导向采集 (Coverage-Aware)',
        'color': '#7c3aed',
        'bg': '#f5f3ff',
        'border': '#ddd6fe',
        'summary': '数据审计揭示初始冷启动文库中 71.88% 的具体残基对存在未测缺损盲区。先验知识库应由被动式硬过滤门禁重构为主动式“缺测雷达”，结合 AAV2 衣壳三维空间接触距离构建连续软权重，引导不确定性探索进入高潜未知区域。',
        'core_data': [
            {'label': '冷启动文库样本规模', 'val': '10,433 条实测样本', 'desc': '名义上覆盖 AAV 突变窗口内全部 378 个位点对位置 (i, j)'},
            {'label': '具体残基对未测缺损率', 'val': '71.88% 认知盲区 (7,937 / 11,130)', 'desc': '门禁内候选包含的 11,130 种具体组合 (i, a, j, b) 中近 3/4 缺乏历史测定'},
            {'label': '硬过滤门禁系统性局限', 'val': '误阻断远端高活性非线性真峰', 'desc': '以天然进化保守性为绝对硬过滤条件，阻断了远离野生型的高阶协同增效突变'},
            {'label': '三维空间先验软权重', 'val': '3D 结构接触加权 $w_{ij}$', 'desc': '基于 AAV2 衣壳空间欧氏距离，对 <8Å 接触位点对动态赋权：$1+\\exp(-(d_{ij}/8\\text{Å})^2)$'},
        ],
        'sections': [
            {
                'title': '🔬 结构生物学与数据审计：从天然保守性硬过滤到三维拓扑空间引导',
                'content': (
                    '在 v0.2 阶段，引入基于 BLOSUM62 的进化保守性门禁实现了功能止损，但随后的全空间数据审计揭示了先验硬过滤的深层缺陷：<br><br>'
                    '• <b>名义位点覆盖与残基微观组合空白：</b>虽然 10,433 条冷启动数据覆盖了突变区段所有位点对几何位置，但特定氨基酸组合（例如位点 17 谷氨酸与位点 20 谷氨酸共现）在候选空间中有 <b>71.88% 处于无实测数据的认知暗区</b>；<br>'
                    '• <b>天然演化保守性与人工定向进化的目标差异：</b>自然演化以宿主生存为选择压，倾向于保守突变；而人工定向进化常需开发非天然极端催化环境或靶向功能。死板的天然序列硬门禁会系统性误杀具有显著协同上位效应的非天然高活性突变体；<br>'
                    '• <b>基于 3D 拓扑结构的主动引导机制：</b>先验知识库应由被动的“空间硬门禁”演进为<b>“缺测引导雷达（Coverage-Aware Radar）”</b>——主动量化并标记残基对的认知缺损度，引导探索预算优先勘探高方差盲区；同时融入 AAV2 衣壳三维空间欧氏距离，对空间临近（<8Å）相互作用位点赋予更高权重的非线性上位表征。'
                )
            }
        ]
    }
]

# ---------------------------------------------------------------------------
# 基础只读读取器
# ---------------------------------------------------------------------------
def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def parse_events(path: Path) -> list[dict]:
    """Reject malformed or tampered streams, including an invalid final record."""
    events, previous = [], ''
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            body = {k: event[k] for k in ('seq', 'ts', 'event_type', 'round_id', 'strategy', 'actor', 'payload')}
            digest = hashlib.sha256((previous + json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True)).encode()).hexdigest()
            if event['seq'] != len(events) + 1 or event['prev_hash'] != previous or event['hash'] != digest:
                raise ValueError('hash chain mismatch')
            if not isinstance(event['payload'], dict):
                raise ValueError('payload must be an object')
            previous = digest
            events.append(event)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'{path.name}: line {number}: {exc}') from exc
    if not events:
        raise ValueError(f'{path.name}: empty event stream')
    return events


def load_version(version: str, root: Path = EVIDENCE) -> dict:
    if version not in VERSIONS:
        raise ValueError(f'Unknown version: {version}')
    if version == 'v0.3':
        return {'metrics': None, 'events': [], 'scan': read_json(root / version / 'surrogate_scan.json')}
    return {
        'metrics': read_json(root / version / 'agentic.metrics.json'),
        'events': parse_events(root / version / 'agentic.events.jsonl'),
    }


def indicators(metrics: dict, baseline: float) -> dict:
    summary = metrics['summary']
    best = summary['final_cum_top10_max']
    strong = summary['final_cum_n_strong']
    spent = metrics['budget_spent']
    return {
        'best': best,
        'strong': strong,
        'spent': spent,
        'rate': strong / spent if spent else None,
        'peak_round': next(r['round'] for r in metrics['rounds'] if r['cum_top10_max'] == best),
        'gap': baseline - best,
        'gain': best - 7.5301,
    }


def variants(metrics: dict) -> dict[str, dict]:
    result = {}
    for row in metrics['rounds']:
        for seq, fitness in row.get('top10', []):
            result.setdefault(seq, {'fitness': fitness, 'round': row['round']})
    return dict(sorted(result.items(), key=lambda pair: -pair[1]['fitness']))


def mutations(sequence: str, wt: str) -> list[dict]:
    if len(sequence) != len(wt):
        raise ValueError('长度与 WT 不同；不进行未经比对的位点或成对互作推断。')
    return [
        {'position': i, 'WT': a, 'variant': b, 'mutation': f'{a}{i}{b}'}
        for i, (a, b) in enumerate(zip(wt, sequence))
        if a != b
    ]


def pairwise_effects(sequence: str, wt: str, measured: dict) -> list[dict]:
    """Observed fitness epistasis on the WT background; never physical energy."""
    muts = mutations(sequence, wt)
    rows = []
    for a, b in itertools.combinations(muts, 2):
        def seq_for(items):
            s = list(wt)
            for item in items:
                s[item['position']] = item['variant']
            return ''.join(s)

        keys = [wt, seq_for([a]), seq_for([b]), seq_for([a, b])]
        vals = [measured.get(k) for k in keys]
        epsilon = vals[3] - vals[1] - vals[2] + vals[0] if all(v is not None for v in vals) else None
        rows.append({
            'pair': f"{a['mutation']} × {b['mutation']}",
            'f(WT)': vals[0],
            'f(i)': vals[1],
            'f(j)': vals[2],
            'f(ij)': vals[3],
            'epsilon': epsilon,
        })
    return rows


# ---------------------------------------------------------------------------
# 实验决策逻辑与状态审计解释器 (Experiment Decision & Audit Interpreter)
# ---------------------------------------------------------------------------
def interpret_event(event: dict) -> dict:
    """Transform raw technical execution logs into rigorous computational biology experiment audit narratives."""
    etype = event.get('event_type', '')
    p = event.get('payload', {})
    rid = event.get('round_id')
    round_str = f'第 {rid} 轮' if rid is not None else '系统初始化'

    if etype == 'agent.tool.test':
        batch_max = p.get('batch_max', 'N/A')
        measured = p.get('measured', p.get('spent', 48))
        spent = p.get('spent', 48)
        return {
            'icon': '🧪',
            'title': f'{round_str} · 批次湿实验测定交付',
            'badge': f'测定 {measured} 条 · 批次最高 {batch_max}',
            'badge_color': '#059669',
            'summary': f'【批次湿实验测定交付】执行器完成真实湿实验（无标签高通量仿真环境）测定：本轮完成 {measured} 条候选变体测定，消耗实验预算 {spent} 点。批次最高实测适应度达 {batch_max}。',
        }
    elif etype == 'agent.tool.analyze_measured':
        best_measured = p.get('best_measured', 'N/A')
        best_score = best_measured[0][1] if isinstance(best_measured, list) and best_measured else best_measured
        stalled = p.get('stalled', False)
        rounds_since = p.get('rounds_since_improvement', 0)
        n_meas = p.get('n_measured', 0)
        rem = p.get('budget_remaining', 0)
        status_text = '处于局部鞍点停滞状态，触发探索模式加权' if stalled else '适应度收敛推进正常'
        return {
            'icon': '📊',
            'title': f'{round_str} · 全局收敛状态巡检与能量面审计',
            'badge': f'最高 {best_score} · {"停滞预警" if stalled else "收敛正常"}',
            'badge_color': '#d97706' if stalled else '#2563eb',
            'summary': f'【全局收敛状态巡检】系统遍历已测文库（已测 {n_meas} 条，候选池剩余未测 {p.get("n_pool_unmeasured", 0)} 条）：当前全局最高实测适应度为 {best_score}。连续 {rounds_since} 轮未突破局部鞍点（{status_text}）；实验剩余预算配额 {rem} 点。',
        }
    elif etype == 'agent.acquisition':
        action = p.get('action', {})
        mode = action.get('mode', 'predicted_mean')
        mode_desc = '多样性方差加权探索模式跳出局部鞍点，针对高认知不确定性残基区域采样' if mode == 'diverse' else '后验均值利用模式，聚焦高置信预测区域冲刺目标适应度'
        n_cand = len(p.get('candidates', []))
        return {
            'icon': '🎯',
            'title': f'{round_str} · 候选变体采集策略决策',
            'badge': f'策略: {mode} · 提名 {n_cand} 条',
            'badge_color': '#7c3aed' if mode == 'diverse' else '#2563eb',
            'summary': f'【候选变体采集决策】采集函数根据当前能量面收敛状态生成候选批次：采用{mode_desc}，向批次湿实验提名 {n_cand} 条候选变体序列。',
        }
    elif etype == 'agent.tool.list_pool':
        n = p.get('n', 0)
        gated = p.get('gated', False)
        by = p.get('by', 'default')
        return {
            'icon': '🔍',
            'title': f'{round_str} · 离散候选搜索空间检索',
            'badge': f'提取 {n} 条 · 门禁: {"严格约束" if gated else "无约束"}',
            'badge_color': '#047857' if gated else '#64748b',
            'summary': f'【候选搜索空间检索】从未测候选文库中检索备选序列：依据 {by} 维度初筛提取 {n} 条变体序列，空间约束状态为 {"执行理化双门禁严格过滤高危失活突变" if gated else "无约束全空间探索"}。',
        }
    elif etype in ['agent.tool.check_knowledge', 'agent.tool.knowledge_gate']:
        return {
            'icon': '🛡️',
            'title': f'{round_str} · 生物物理与先验门禁审查',
            'badge': 'BLOSUM62 & 理化门禁',
            'badge_color': '#047857',
            'summary': '【生物物理约束审查】调用先验知识库模块：对候选变体执行突变步长（HD≤4）与进化保守度（BLOSUM62≥0）空间约束检验，阻断结构破坏性非功能变体。',
        }
    elif etype == 'agent.tool.predict':
        return {
            'icon': '🔮',
            'title': f'{round_str} · 代理模型前向推断与方差评估',
            'badge': '后验均值 μ & 认知方差 σ',
            'badge_color': '#2563eb',
            'summary': '【能量面代理前向推断】调用训练好的代理模型，批量推断候选序列的预测适应度后验均值 μ 与认知不确定性方差 σ。',
        }
    elif etype == 'agent.llm.model':
        model = p.get('model', 'LLM Agent')
        return {
            'icon': '🤖',
            'title': f'{round_str} · 智能体控制器元规划与状态反思',
            'badge': f'调度内核: {model}',
            'badge_color': '#2563eb',
            'summary': f'【智能体元认知规划】大语言模型控制器挂载上下文（调度内核: {model}），综合历史实测反馈与当前收敛状态，推演下一步采集与实验行动策略。',
        }
    elif etype == 'agent.measurements':
        return {
            'icon': '📈',
            'title': f'{round_str} · 实验测定数据链写入与归档',
            'badge': '只读证据哈希存证',
            'badge_color': '#059669',
            'summary': '【不可篡改证据归档】湿实验测定数据写入只读实验证据账本，经 SHA-256 签名存证，并同步更新全局累积 Top 10 适应度分布及强变体统计。',
        }
    elif etype in ['agent.tool.compose_batch', 'agent.tool.test_composed_batch']:
        return {
            'icon': '📦',
            'title': f'{round_str} · 批次衰减退火微调组装',
            'badge': '退火分批调度',
            'badge_color': '#d97706',
            'summary': '【动态退火分批执行】执行批次退火拆解流程：将 48 实验预算划分为子批次，依据先验衰减曲线分配方差探索权重。',
        }
    elif etype == 'agent.llm.no_test':
        return {
            'icon': '⏸️',
            'title': f'{round_str} · 控制器前置评估 (未发起测定)',
            'badge': '无测定调度',
            'badge_color': '#e11d48',
            'summary': '【实验调度等待】大语言模型控制器在此步未发起实测测定，判定等待前置数据分析完成或处于收敛停滞状态。',
        }
    else:
        return {
            'icon': '⚙️',
            'title': f'{round_str} · {etype}',
            'badge': event.get('actor', 'system'),
            'badge_color': '#64748b',
            'summary': f'【系统底层事件】执行系统底层操作 {etype}，存证时间戳 {event.get("ts", "")}。',
        }


# ---------------------------------------------------------------------------
# 外环决策流与全景记录
# ---------------------------------------------------------------------------
OUTER_KINDS = {
    'signal': {'icon': '⚡', 'label': '实测反差 / 触发信号', 'color': '#d97706'},
    'human': {'icon': '👤', 'label': '人在环 · Human-in-the-Loop', 'color': '#2563eb'},
    'harness': {'icon': '📋', 'label': 'Harness 决策与任务', 'color': '#059669'},
    'insight': {'icon': '💡', 'label': '认知进化与纠错', 'color': '#7c3aed'},
}

OUTER_LOOP = {
    'v0.1': [
        {
            'kind': 'human',
            'title': '无约束探索基线确立：检验盲目探索的失活风险',
            'detail': '评估大模型在脱离生物物理与化学先验约束下的自主决策表现，探究高维突变空间无导向探索对蛋白质折叠与功能稳定性的破坏性。',
            'ref': 'harness/reports/final-report-v0.1',
        },
        {
            'kind': 'signal',
            'title': '无先验探索陷入高阶突变失活深谷',
            'detail': '无约束探索盲目涌向多位点高阶突变与功能破坏区域：新测变体最高适应度仅 5.9610，强变体仅 15/288，显著劣于加性基线（7.5301）。',
            'ref': 'v0.1/agentic.metrics.json',
        },
        {
            'kind': 'insight',
            'title': '认知不确定性与功能失活概率显著正相关',
            'detail': '实测统计表明方差与功能致死率呈正相关（r ≈ +0.47）：在 288 次有限预算下，纯不确定性驱动探索代价高昂。确立为搜索空间引入物理化学可行性门禁的工程决策。',
            'ref': 'reports/explainer_for_humans.html #sec4',
        },
    ],
    'v0.2': [
        {
            'kind': 'human',
            'title': '人在环干预：引入生物物理先验双门禁',
            'detail': '研发团队对候选生成流实施协议级干预：将汉明距离（HD≤4）与氨基酸保守度（BLOSUM62≥0）双门禁植入候选空间生成逻辑，阻断高危非功能突变。',
            'ref': 'git 67bc067',
        },
        {
            'kind': 'signal',
            'title': '事后硬过滤机制导致实验预算被动损耗',
            'detail': '初版事后硬过滤机制导致大量候选被拦截抛弃、实验预算被动消耗；优化方案由「事后硬过滤」重构为「先验塑形搜索空间」（list_pool 仅输出门禁内可行候选）。',
            'ref': 'git d1140a2',
        },
        {
            'kind': 'harness',
            'title': 'v0.2 阶段性实证报告归档',
            'detail': '门禁约束流成功追平贪心基线（7.5301），强变体提升至 93/288，探索惩罚有效消除；报告客观记录「功能止损达成但未突破加性峰值」。',
            'ref': 'git 6c7b31a · harness/reports/agentic-v0.2',
        },
        {
            'kind': 'insight',
            'title': '收敛瓶颈归因：加性表征天花板',
            'detail': '系统收敛于 7.5301 且无法进一步突破：核心科学问题由「采样探索策略优化」深化为「底层一阶加性表征无法表达高阶能量面」。',
            'ref': 'git 6c7b31a',
        },
    ],
    'v0.3': [
        {
            'kind': 'human',
            'title': '暂停湿实验并启动代理模型全空间表征诊断',
            'detail': '团队果断叫停盲目湿实验测试，将整代研发周期置换为全空间表征与代理模型系统级扫描，定位真实真峰不可见性的理论根源。',
            'ref': 'harness/reports/agentic-v0.3',
        },
        {
            'kind': 'signal',
            'title': '六组基线模型扫描均未打破 7.5301 瓶颈',
            'detail': '表征编码 × 代理模型 6 组经典组合及 ESM-2 zero-shot 推断均未将真峰纳入 288 预算射程；最优组合下全局真峰仅列第 2,776 位。',
            'ref': 'git f884314 · 3cfdd5e',
        },
        {
            'kind': 'harness',
            'title': '构建 de-research 自动化调研智能体',
            'detail': '将前沿学术文献调研与机理破局论证封装为标准化研究工序，正式纳入 Harness 自动化研发调度体系。',
            'ref': 'git f134e02',
        },
        {
            'kind': 'insight',
            'title': '理论上限界定：一阶加性假设表征失真',
            'detail': '理论归因锁定：击穿加性天花板必须构建能够显式捕获残基成对非线性互作的上位感知模型，该结论直接指引 v0.4 架构演进。',
            'ref': 'git 0132829',
        },
    ],
    'v0.4': [
        {
            'kind': 'signal',
            'title': '上位感知模型将全局真峰纳入算法可探测范围',
            'detail': '成对上位互作代理模型将候选池全局真峰预测排名由第 2,776 位大幅提升至第 429 位，真峰进入算法可触达窗口。',
            'ref': 'git 54bc249',
        },
        {
            'kind': 'signal',
            'title': '实证击穿 7.5301 加性理论天花板',
            'detail': '在上位感知模型驱动下，确定性交替策略直接收敛至全局真峰 8.4162，实证推翻了一阶加性表征的上限假说。',
            'ref': 'git 8a2d6d0 · c807b70',
        },
        {
            'kind': 'human',
            'title': '认知自证伪：反思纠正「纯贪心达峰」早期误判',
            'detail': '早期曾草率归因为「纯均值贪心可直达 8.4162」；深入底层代码审计与机理反思后发现该基线实际依赖多样性交替采样。团队主动公开纠偏，确认达峰必须依赖探索机制。',
            'ref': 'reports/explainer_for_humans.html #sec8',
        },
        {
            'kind': 'harness',
            'title': '增加采样轮次无法弥补微观优化缺陷',
            'detail': '消融实验表明：大模型的根本短板在于高维微观连续空间的梯度利用效率而非单纯迭代轮次，盲目增加轮次无法对冲探索税损耗。',
            'ref': 'git 3280724 · harness/reports/agentic-v0.4',
        },
        {
            'kind': 'insight',
            'title': '探索税（Exploration Tax）的形式化测定',
            'detail': 'LLM 自主决策停滞于 7.8290，确定性参考达 8.4162：在高置信度模型下，探索配额置换代价首次被严密量化（描述性差值 Δ = 0.5872）。',
            'ref': 'harness/reports/agentic-v0.4',
        },
    ],
    'v0.5': [
        {
            'kind': 'human',
            'title': '设计批次退火实验验证探索税假说',
            'detail': '实施小批量采样结合自适应方差分配机制，实证检验「在高质量代理模型下抑制过度探索即可逼近最优」的理论假设。',
            'ref': 'git a6a2819',
        },
        {
            'kind': 'signal',
            'title': '阴性实验结果归档：6.5309',
            'detail': '小批次固定方差配额在初期过早剪枝了高潜力远端突变，导致最高适应度大幅衰减；系统严格依据原始 JSON 证据修正指标。',
            'ref': 'v0.5/agentic.metrics.json',
        },
        {
            'kind': 'harness',
            'title': '决策优化与方差调度调研报告归档',
            'detail': '将高质量代理模型下的探索权重退火规律形式化为研究任务，沉淀关键机理报告。',
            'ref': 'git a6a2819',
        },
        {
            'kind': 'insight',
            'title': '不可篡改的阴性结果入账与机制转向',
            'detail': '从静态固定探索分配转向基于收敛状态动态监测与回溯机制，该失败直接催化了 v0.7 稳健确定性参考策略的设计。',
            'ref': 'harness/reports/agentic-v0.4',
        },
    ],
    'v0.6': [
        {
            'kind': 'human',
            'title': '人在环干预：把停滞判定与逃逸权交给智能体',
            'detail': 'v0.5 的过早退火剪掉了潜在高适应度分支。研发团队据此加入元层：固定规则监测累计 top-10 最大值，连续 2 轮不提升即在轮次提示中给出 STALLED 标志；是否行动、跳多远交由智能体判断。逃逸工具是 redirect_batch——按与最优簇的突变组成重叠度跳到另一个高预测盆地。',
            'ref': 'harness/reports/agentic-v0.6',
        },
        {
            'kind': 'signal',
            'title': '逃逸机制跑通，但未突破加性天花板之上的孤峰',
            'detail': 'semi 构型实测峰值 7.8290、强变体 166/288、预算 288 全部花满。智能体确实在停滞判定后调用了逃逸工具，工具动作层面机制成立；但本代未达到候选池真峰 8.4162。',
            'ref': 'v0.6/agentic.metrics.json',
        },
        {
            'kind': 'insight',
            'title': '判据危机：工具动作变了，不等于送去测量的批次变了',
            'detail': '本代暴露出一个此前没有的方法学问题——衡量“智能体做了什么”一直靠工具调用次数与自然语言总结，而这两者都可能在实测批次完全不变的情况下发生变化。必须建立只看实测批次、不看叙述的判据。这个缺口直接催生了 v0.8 的逐变体残差事件流。',
            'ref': 'harness/reports/REPORT-HANDOFF.md',
        },
    ],
    'v0.7': [
        {
            'kind': 'signal',
            'title': '确定性交替策略精准收敛至候选池真峰 8.4162',
            'detail': '确定性交替参考在 192 预算节点处捕获候选池内唯一孤峰，严格验证了非凸能量面最优路径的可达性。',
            'ref': 'v0.7/agentic.metrics.json',
        },
        {
            'kind': 'signal',
            'title': '纯贪心鞍点停滞对照验证',
            'detail': '纯均值贪心在 3 个独立随机种子下均于第 2 轮停滞于 7.8290 局部鞍点；而 30-seed 网格扫描确证 UCB (β=3) 在 30/30 种子下 100% 收敛达峰。',
            'ref': 'reports/explainer_for_humans.html #sec4·#sec8',
        },
        {
            'kind': 'human',
            'title': '诚实科学边界确立：冷启动已知样本 vs 未测池内真峰',
            'detail': '明确统计学定义边界：9.5360 为冷启动已知样本历史极值，8.4162 为未测候选池唯一真峰——「未知空间勘探登顶」不可偷换为「超越已知全局最高」。',
            'ref': 'reports/explainer_for_humans.html #sec8',
        },
        {
            'kind': 'harness',
            'title': '理论形式化推导与架构定稿',
            'detail': '完成有限时域探索税形式化推导与信息价值（VoI）采集算子设计；受控自演进智能体（RSI）五机架构定稿。',
            'ref': 'app/timeline_evidence/whitepapers/02·03',
        },
        {
            'kind': 'insight',
            'title': '因果归因边界审慎声明',
            'detail': '确定性参考证实路径可达性，但「自主停滞识别 → 回溯跳出」的因果归因机制仍需独立消融，审慎区分确定性算法贡献与自主智能体贡献。',
            'ref': 'reports/scientific_report_v1.0.md',
        },
    ],
    'v0.8': [
        {
            'kind': 'harness',
            'title': '补上一个结构性数据缺失：失败推荐此前一条都没被记录过',
            'detail': '在此之前，逐变体真值只存在于每轮 top-10 里，而“预测很高、实测致死”的失败提名按定义进不了 top-10——失败案例是结构性地缺失的。新增 campaign.oracle.residuals 与 agent.tool.test.residuals 两类事件，记录提名时刻的预测均值/方差、实测值与残差。残差取提名时刻而非重训后：拿重训后的模型算残差是在跟一个已经看过这批标签的预测器比，那是穿越。',
            'ref': 'events/reflexion.py',
        },
        {
            'kind': 'signal',
            'title': '强制注入残差，四臂送测集合逐位相同',
            'detail': '2×2 因子实验（采集档位 × 反思开关，AAV，seed 42，48×6=288 预算，四格固定 backtrack semi）：反思开与反思关的六轮实测批次逐位相同，48/48 × 6，两个采集档下皆然。处理确实施加——反思臂有 5 次注入、6007 字符真实残差内容，且比对照臂慢 20–25%。四臂 LLM 均 6/6 成功、零超时。',
            'ref': 'v0.8/agentic.events.jsonl',
        },
        {
            'kind': 'insight',
            'title': '自述与行为的分离：它声称排除了致死背景，批次却一字未改',
            'detail': '反思臂的总结写着 “Residual reflexion excluded the two strongly lethal round-5 contexts”，而该轮实测送测集合与对照臂逐字节相同。这确立了本项目的核心判据：只认 agent.tool.test.residuals 里 records[].seq 的集合哈希——那是唯一真正花掉预算的东西。同一判据看得见采集档位造成的差异，所以“未分叉”是关于处理的结论，不是判据不灵敏。',
            'ref': 'harness/reports/REPORT-HANDOFF.md',
        },
        {
            'kind': 'harness',
            'title': '方法学纠错：只修一层比两层都不修更危险',
            'detail': '第一次 2×2 是无效的。采集策略挂在 backtrack 上的地方有两处——系统提示词段落与 compose_batch 的工具级默认——第一次只解耦了提示词层，结果四个臂命令行看起来是 2×2、实际 allocation_source 全是同一档、批次逐位相同。实验看起来是受控的，其实不是。已加双层守护测试并反向验证，比对脚本改为取事件流里的实测档位而非命令行意图。',
            'ref': 'tests/test_auto_researcher_backtrack.py',
        },
    ],
    'v0.9': [
        {
            'kind': 'insight',
            'title': '根因不在模型，在契约的形状',
            'detail': '逐行核对工具契约后确认四层原因，其中三层是本仓自己设的：①两个采集段落都写着 Prefer that default，每轮提示模板把 compose_batch(n=48) 写死、参数位上没有 exploit_ratio；②利用比地板（CV≥0.80→0.80，末两轮→0.90）恰好只禁止残差所指向的“调低利用”方向，实测第 4 轮起可行区间为空集；③根因——exploit_ratio 是标量，没有任何取值能表达“别选带 N21D 的候选”；④test_composed_batch 无参数，连手工剔除都做不到。',
            'ref': 'agent/auto_researcher.py',
        },
        {
            'kind': 'human',
            'title': '契约改造：给证据一个同构的落点',
            'detail': 'compose_batch 增加残基级 exclude_motifs（按 W<零基位置>M 剔除候选，剔完不足 n 时返回 exclusion_too_strict 而非静默缩批）；采集段落删去 Prefer that default 并点名新入口；释放利用比地板使因变量不再被压成常数。两个契约的差异落在工具 schema 上而不只在提示词——v0.8 臂根本看不到那个参数，否则对照臂就不是对照。',
            'ref': 'harness/tasks/task_feb731c779788be5bfff65e979-v0-9',
        },
        {
            'kind': 'signal',
            'title': '同一模型、同一 seed、同一注入内容，提名立刻分叉',
            'detail': '重跑同一 2×2：v0.8 契约下批次仍逐位相同；v0.9 契约下批次分叉并逐轮发散（r1 46/48 → r6 8/48）。agent_requested 由 0/20 变为 11/11，排除入口 6 轮用了 5 轮，被排除的 20 个 motif 全部可追溯到此前注入的残差证据、零凭空，且证据池标记 34 个它只排 20 个——是有选择而非一刀切。对照臂六轮哈希与 v0.8 逐位相同，证明改动对默认路径惰性。',
            'ref': 'v0.9/agentic.events.jsonl',
        },
        {
            'kind': 'insight',
            'title': '同构还不够，还要有分辨率；且契约不是越宽越好',
            'detail': '把每轮预算压到 12 重跑发现：n=12 时 [0.875, 0.958] 整个区间映射到同一个 11/1 分配——智能体调了 ratio，分配没变，事件流里却记着 agent_requested。标量杠杆的分辨率随批量线性缩水，离散的排除入口不受影响，这也是唯一跨协议复现的杠杆。另一面：check_knowledge 在八个臂中零调用，而那是理性的——门禁已在环境里无条件执行、compose_batch 只返回过门候选。结论是约束的执行归环境，证据驱动的选择归智能体。',
            'ref': 'reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md',
        },
        {
            'kind': 'harness',
            'title': '指标饱和的自我揭发',
            'detail': '八个臂全部在第 2 轮达到候选池真实最优 8.416205，即 67% 的预算花在答案已经找到之后——峰值与样本效率两个主指标同时失去区分力。压到 12×6 后达峰推到 r4、浪费降到 33%，但四臂仍同轮达峰。改用致死 motif 复现率（此前算好却全仓无人消费的死指标）后，后段四臂为 13.9% / 13.9% / 20.1% / 6.2%。另更正一处口径：候选池 27,832 条里超过冷启动 incumbent 9.536457 的是 0 条，全表最优本身落在 HD=2——“未超越 incumbent”是数据集构造，不是智能体的失败。',
            'ref': 'harness/reports/v09-contract-b12',
        },
    ],
}

COGNITION_ARC = [
    {
        'tag': '第 1 阶段 · 初始假设',
        'color': '#e11d48',
        'title': '初始假设：“纯均值利用直达 8.4162，探索机制引入无效损耗”',
        'detail': 'v0.4 早期单次确定性基线命中 8.4162，团队曾初步推断：高置信度代理模型下无需探索算子，贪心利用即可解决非凸景观优化。',
        'ref': 'git c807b70',
    },
    {
        'tag': '第 2 阶段 · 认知自证伪',
        'color': '#d97706',
        'title': '因果反思与证伪：高适应度达成实质依赖多样性交替探索',
        'detail': '经底层代码审计与因果链复盘：早期基线实为多样性交替采样。纯均值利用下真峰排序仅在第 426 位，贪心算法在 3 个独立随机种子下均停滞于 7.8290 局部鞍点。实证确证跨越负上位深谷必须依赖不确定性探索，团队主动推翻原先判断。',
        'ref': 'reports/explainer_for_humans.html #sec8',
    },
    {
        'tag': '第 3 阶段 · 跨文献假设对撞',
        'color': '#7c3aed',
        'title': '文献认知对撞：优化目标差异决定采集函数偏好（Greenman et al., 2021）',
        'detail': '经典文献侧重于文库整体平均适应度产出（Bulk Yield，纯贪心均值占优），而本系统致力于离散候选空间全局极值命中（Peak Hit，需高置信度不确定性探索）。二者数学目标函数的差异直接决定了采集策略的反向选择。',
        'ref': 'reports/explainer_for_humans.html #sec8',
    },
    {
        'tag': '第 4 阶段 · 机制形式化确立',
        'color': '#059669',
        'title': '贝叶斯置信界固化：重探索 UCB (β=3) 达成 30/30 (100%) 稳健收敛',
        'detail': '通过 30 独立随机种子网格扫描，排除单次随机偶发性：重探索 UCB 采集函数在第 3 轮实现 100% 达峰率，而纯贪心对照达峰率为 0/30，完成探索机制必要性的数学定理级实证。',
        'ref': 'reports/explainer_for_humans.html #sec8',
    },
]

HONEST_BOUNDARIES = [
    {
        'title': '极值定义边界（未测离散候选池极值 vs 历史全库全局记录）',
        'detail': '8.4162 为未测候选池（27,000 条未表征序列）的最优真值；冷启动历史样本库包含已知最高记录 9.5360。「在未知离散文库中勘探登顶」不可等同或偷换为「超越历史全景总记录」。',
    },
    {
        'title': '超参数后验性说明（网格扫描最优解不可替代先验未知适应）',
        'detail': 'UCB 探索置信界 β=3 是外环通过事后网格扫描发现的收敛最优参数；在迁移至全新未知蛋白质能量面时，先验无法预设该参数，必须依赖外环元控制器的动态自适应调节。',
    },
    {
        'title': '人在环认知迭代界定（内环确定性物理隔离 vs 外环专家监督介入）',
        'detail': '内环单次闭环严格执行无标签盲测与 SHA-256 密码学防篡改链物理隔离；但跨版本宏观方法论演进由人在环（Human-in-the-Loop）专家协同驱动，客观拒绝非理性的“全零先验全自动”宣传。',
    },
    {
        'title': '工程基准任务定位（闭环定向进化环境 vs 静态基准回归）',
        'detail': 'FLIP-AAV 原始学术基准主要用于评估静态回归排序指标（Spearman 相关系数）；本系统严格按照现代合成生物学与生物医药工业真实需求，构建为具有受限实验预算的闭环批次定向进化仿真系统。',
    },
]

DUAL_LOOP = {
    'inner': {
        'icon': '🧬',
        'color': '#2563eb',
        'title': '内环 · 蛋白质工程微观闭环实验流 (Microscopic DBTL Loop)',
        'text': '高频自动化循环：执行器单轮提名 48 条候选变体，结合湿实验仿真测定与只读密码学校验，在 288 步预算内快速迭代。「实验事件回放」与「变体上位互作检视器」展示该内环过程，所有状态变迁受 SHA-256 不可篡改哈希链保护。',
    },
    'outer': {
        'icon': '🛰️',
        'color': '#059669',
        'title': '外环 · Harness 科学决策与元演进流 (Macroscopic Meta-Cognitive Loop)',
        'text': '低频元认知演进：科研专家与 Harness 智能体协同记录 Fact / Decision / Task 知识流——由实验观测偏差触发假设修正、人在环干预与审慎边界裁定、阴性结果系统性归档及理论形式化推导，最终收敛出 UCB β=3 的关键机制。',
    },
}
