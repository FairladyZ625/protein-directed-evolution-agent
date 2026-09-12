# 独立执行评审：T8 Streamlit 看板

## Verdict

**通过（approved）**。

冻结提交 `4f456890ca43dfe007e4b17c63c06c3fa26f147f` 中的 `app/demo.py` 满足任务契约：单文件提供四策略曲线、五角色事件回放、变体打分与一轮自动推荐；消费版本化结果树，磁盘事件流保持只读，缺真值变体明确提示不在 149,361 可测空间。提交摘要在登记前仍为 `sha256:59240f7656411f67802022acc85c12ce22b1fa53b4959ca082175b2784134a03`。

## 工具证据依据

- 冻结内容：使用 `git archive 4f456890...` 建立隔离快照，并从该快照读取、运行 `app/demo.py`，未用当前工作树文件替代交付物。
- 定向测试：在快照中挂载仓库本地的两份数据输入后运行 `python -m pytest -q tests/test_demo_app.py`，结果 `8 passed in 5.54s`。覆盖三主 tab、四策略展示、五角色回放、WT 打分、149,361 空间外提示、一轮内存推荐和只读源码红线。
- 服务冒烟：`python -m streamlit run app/demo.py --server.headless true --server.port 18731` 成功启动；请求 `/_stcore/health` 返回 `ok`，进程日志无应用异常。
- 事件校验阳性对照：对 `campaign_easy.events.jsonl` 的 50 个事件复算哈希链，输出 `哈希链校验 ✅ 通过（50 事件）`；聚合得到 6 条完整链，全部具备 data analyst、hypothesis generator、mutation designer、fitness evaluator、scientific critic 五角色。
- 事件校验阴性对照：篡改第 26 个事件 payload 后，同一检测器输出 `哈希链校验 ❌ chain broken at seq=26`，证明页面的完整性提示并非静默失效。
- 只读审计：对冻结 `app/demo.py` 搜索磁盘写入/API/子进程入口，无 `write_text`、`write_bytes`、`to_json`、`to_csv`、`.open(`、`EventStore(`、`requests`、`httpx`、`subprocess`、`unlink` 或 `remove` 命中；唯一 `append` 位于 `_MemoryRecorder` 的内存列表。
- 依赖：冻结提交的 `requirements.txt` 声明 `streamlit==1.63.0`；`app/demo.py` 顶部文档给出 `streamlit run app/demo.py`。
- Harness gate：`ha task show` 显示本 execution 的 CI witness 为 `pass`，code-doc witness 固定 `app/demo.py` 与同一提交。

## 具体缺陷清单

无阻断或需返工缺陷。

## 可操作修复方向

无需修复即可进入 owner consent。运行环境仍须预先生成 metrics/events，并提供 gitignored 的 GB1 landscape 与 train pool；这是提交已声明的依赖，不是本次回归。真实商业 LLM 路径本轮未调用，保持 **unverified**；默认确定性路径和无密钥冷启动已由 AppTest 覆盖。

## Harness 登记状态

执行指定的 `ha task review-execution ... --review-id review-dispatch_8f5b528b3b17be67e3ddc360 --from-file ...json` 返回 `executor_binding_invalid`：daemon 认为当前 actor `agent:runtime-session:runtime_78d803fcf40b85130388ce13` 不是绑定到 execution `exe_67de23cb4595dfd5723b458460` 的 reviewer RuntimeSession。因此本报告已落盘，但 review 尚未写入 canonical lifecycle；未尝试绕过 gate，亦未执行 consent 或 complete。修复方向是由调度方以 reviewer role 将本 runtime 正确绑定到该被审 task 后，原命令重试。
