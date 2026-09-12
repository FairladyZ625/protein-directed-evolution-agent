# T8 完成：Streamlit 看板三模块本地跑通并已本地 commit

**TLDR**:`app/demo.py`(单文件 836 行新增)三模块全部可交互、真实浏览器验证通过、8 个 AppTest 全绿，已记 fact(F-A41D3899)并停在本地 commit `6bed9ba`(分支 `t8-demo`,作者 ZeyuLi,未 push)。

## 交付物

- **`app/demo.py`** — 单文件看板，`streamlit run app/demo.py`(或 `make demo`)
- **`app/README.md`** — 运行说明、数据前置表、缺失时的降级行为
- **`tests/test_demo_app.py`** — 8 个 AppTest 冒烟用例(含只读红线断言)
- **`requirements.txt`** — 确认保留 `streamlit==1.63.0`(CEO 预置的待确认项)

## 三模块实测证据(Chrome headless 驱动真实页面，截图在 `/tmp/t8_shots/`)

| 模块 | 验证结果 |
|---|---|
| ① 四策略对比 | 读 `campaign_metrics.json` 画累计 top10_max 曲线，末端标注去重(两条 agent 曲线并列 8.76 只标一次)；可选 6-seed 随机误差带(T1 `simulate()` 只读重模拟，约 12s 后走缓存) |
| ② 五角色回放 | 读 `campaign_events*.jsonl`,页面内联复算 SHA-256 哈希链校验(50 事件 ✅);策略+轮次选择器回放五角色推理链，位点柱状图标签 `V39/D40/G41/V54` 正常渲染 |
| ③a 实时打分 | 输入 `FWAA` → 预测 mean 0.685 / 真值 **8.762** / 分位 **100%** / 排名 **#1/149,361**,秒级；输入真值表缺失变体(实测 `VVVD`)→ 明确警告「无真值」并给出预测 |
| ③b 自动推荐 | 一键跑 `run_campaign(n_rounds=1)` 确定性 **2.7s** 出 Top-10(预测 vs 真值对照)+ `llm_source=deterministic` 标注 + 严格知识校验预演 + 与模块②同源的五角色链 |

**纪律守住**：全程零磁盘写——事件收集走内存 recorder(接口对齐 `EventStore.append`);哈希校验为纯读复算(不镜像落盘)；源码级断言 demo 无 `write_text/to_json/EventStore(` 等写操作。

## 需 CEO 知悉的三点

1. **主事件流无 Critic 拒稿可回放**：campaign 里五角色以 `no_knowledge=True` 运行(evolution/campaign.py:190),知识差异由 acquisition 层承载，所以事件流全部 `accepted: true`。页面如实说明，并提供了「严格知识校验预演」(只读跑 `knowledge/validators`)展示知识规则与 agent 提名的「打架」。
2. **origin/main 已被重写**：与本 worktree 分支无共同祖先(24 ahead / 2 behind),rebase/合并策略属发布层，未动。
3. **worktree 数据 symlink**:46MB 真值表不在版本库，worktree 里建了 gitignored symlink 指向 canonical 副本供本地跑；另为取证在 canonical `.venv` 装了 playwright(不影响 requirements.txt)。

## 验证与收口

- `pytest tests/test_demo_app.py` → **8 passed**(0 字形警告，图内文字全英文防评测机缺中文字体)
- 回归:`tests/test_events.py + test_campaign.py + test_agent.py` → **17 passed**
- fact `F-A41D3899` 已记(含全部运行证据)
- 下一步建议：CEO 亲验使用满意度门(`streamlit run app/demo.py`);LLM 模式 checkbox 可用(canonical `.env` 会被 `agent/llm.py` 沿父目录找到)但本次未实测真实 LLM 调用，标 **unverified**。