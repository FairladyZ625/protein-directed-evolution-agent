# Research Atlas · 前端展示交付

独立入口 `app/timeline.py` 提供 v0.1、v0.2、v0.3、v0.4、v0.5、v0.7 和六篇理论白皮书导航。原 `app/demo.py` GB1 演示保持可用。

## 运行

```sh
python -m streamlit run app/timeline.py
```

需安装仓库 `requirements.txt` 中的 Streamlit、Pandas 及 Streamlit 依赖 Altair。本次验证使用规范仓库 `.venv/bin/python`（Python 3.13，Streamlit 1.63.0）。默认系统 Python 未安装 Streamlit。

本机已启动：<http://localhost:8511>。

## 组件与数据

- `app/timeline_data.py`：纯只读适配器，解析及验证 JSONL 哈希链、指标计算、突变定位、WT 背景成对上位效应计算，不依赖 Streamlit 或模型训练。
- `app/timeline.py`：浅色响应式界面，版本叙事、四指标卡、预算曲线、按日志轮次过滤及逐步回放、原始 JSONL 下载、变体序列对比、实测互作表与图。
- `app/timeline_evidence/`：652 KB 可携带证据包。五组 campaign 的 metrics / JSONL 为逐字节副本，共 179 个事件。`provenance.json` 记录原路径和 SHA-256。UI 不依赖本机绝对路径，也不访问网络、LLM 或原始大数据表。
- `app/build_timeline_snapshot.py`：显式运行的离线打包工具；UI 不调用它。背景测定子集来自 FLIP CSV，按 `evolution.datasets.load_aav` 的首个同序列记录规则选取，附原 CSV 校验和。

```sh
python app/build_timeline_snapshot.py --root /path/to/canonical-repo \
  --v05 /path/to/canonical-repo/.worktrees/t-v05 \
  --v07 /path/to/canonical-repo/.worktrees/t-v07 \
  --out app/timeline_evidence
```

## 实测口径与证据校正

| 版本 | 新增测定最高分 | 强变体 / 实际测定数 | 事件数 |
|---|---:|---:|---:|
| v0.1 | 5.9610 | 15 / 288 | 25 |
| v0.2 | 7.5301 | 93 / 284 | 43 |
| v0.3 | 无 campaign | 诊断扫描 | 0 |
| v0.4 | 7.8290 | 108 / 288 | 50 |
| v0.5 | 6.5309 | 163 / 288 | 25 |
| v0.7 | 8.4162 | 151 / 288 | 36 |

v0.3 原报告明确未运行 LLM campaign；本页展示六组真实扫描，回放与新增变体不伪造。v0.5 原始 metrics 为 163 强变体，与总报告 82 不一致。v0.2 实际花费 284，不能用名义 288 计算命中率。

v0.7 数据来自 `alternating-seed42`，`llm_used=false`、`reference=alternating`、`backtrack=null`。它是确定性交替参考实验，不足以证明 LLM 自主停滞回溯。8.4162 是未测候选池峰，冷启动中存在更高 incumbent，不能称为整个数据集的全局峰。原始研究白皮书作为来源文稿保留，结论须结合其条件审阅。

探索税卡定义为 v0.4 确定性参考峰 8.4162 减本次新增最高分；它是描述性差值，非跨协议因果估计。基线增益为相对加性基线 7.5301 的绝对差。日志 round_id 与 metrics 测定批次可能不一一对应，界面分别标注。

互作使用 ε = f(ij) − f(i) − f(j) + f(WT)，仅为 WT 背景的实测适应度上位效应。缺背景时留空；不同长度变体拒绝直接位置比对。未提供 Potts 拟合系数、物理 ΔG 或三维结构，界面不伪造能量或结构。

## 验证

```sh
python -m pytest app/tests/test_timeline.py -q
# 4 passed
python -m streamlit run app/timeline.py --server.headless true --server.port 8511
python app/tests/browser_timeline.py --channel chrome \
  --output reports/timeline-showcase/screenshots
# All six versions, whitepaper and mobile viewport passed.
```

浏览器测试需要 Playwright 和本机 Chrome；也可安装 Playwright Chromium 后省略 `--channel chrome`。覆盖每个版本真实点击切换、各实验版本下一步回放、白皮书页面、390px 手机无横向溢出。AppTest 另外覆盖轮次过滤、变体切换。证据测试覆盖哈希快照、指标汇总、坏链和破损末行拒绝、互作缺失值与不等长序列。

截图：`screenshots/v0.1.png` 至 `v0.7.png`（无 v0.6）和 `screenshots/mobile.png`。

## 残余边界

该前端展示离线研究证据，不产生新实验；不触碰核心算法或 CI。独立 review-execution、review-consent 与 complete 由其他审查者/GUI 执行。原 GB1 测试依赖外部大数据与模型，本次未重跑；其源码未修改。
