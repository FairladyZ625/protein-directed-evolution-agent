## Summary

完成 `harness/context/research/assignment-coverage-audit.md`：逐条审计 53 项硬要求与 7 项加分项，给出工具证据、四态判定、五条锁定 decision 复核、三张汇总表和七个按优先级排序的修复包。Verdict 为 changes requested：40 项硬要求已交付、13 项部分交付、0 项完全未做；D2、D4、D5 未通过。


交付锚点:`artifact:tasks/task_d5e9455a1235d1554b1967c708-ai4s-assignment-md-vs/artifacts/assignment-coverage-audit.md@1537`

## Verification

- `.venv/bin/pytest -q tests/test_data_pipeline.py tests/test_agent.py tests/test_campaign.py tests/test_knowledge.py tests/test_events.py tests/test_demo_app.py tests/test_pool_campaign.py`：`38 passed in 6.88s`。
- `.venv/bin/pytest -q tests/test_events.py::test_append_hash_chain_and_verification tests/test_events.py::test_tampering_is_detected_at_changed_event`：`2 passed in 0.02s`，同时覆盖正常链阳性对照与篡改阴性对照。
- `pdfinfo harness/final-report/report.pdf`：A4、4 页；`pdftotext` 确认含八节，但内容是旧 GB1 主叙事。
- 数据实读：149361 行；三池 5000/50000/94361、两两不交、并集 149361；WT `VDGV=1.0`；最大 `FWAA=8.76196565571`。
- `rg build_knowledge_graph`：生产无调用，唯一调用在测试；`rg no_knowledge|guardrail`：GB1 有消融，AAV 无同协议 no-knowledge 对照。
- Fact：`F-083C5DD0`。
- 独立 `review-execution` 与 owner consent 尚未执行，不在本次自审范围。

## Residual Risk

本次未调用外部 LLM、未重跑 ESM-2 650M、未重跑完整 GB1/AAV campaign、未检查远端 GitHub 页面或全 CI。`ha doc sync --submit --path context/research/assignment-coverage-audit.md` 被 `lease_conflict` 拒绝；审计正文已在声明路径落盘，任务进度与 Fact 已由 daemon 持久化，需要后续通过任务绑定的文档通道确认正文已进入 canonical projection。

## Same Mechanism Elsewhere

机制句：**交付入口可能继续指向已被新证据替代的旧工件，使正确的新正文存在但消费者仍读到过期结论。**

搜索方式：核对 `git ls-files`、`find`、README 的报告链接，并对旧 PDF 与 `reports/final-report-v0.3/report.md` 两侧执行 `pdfinfo`、`pdftotext`、标题/关键结论搜索。

发现：README 指向不存在的 `reports/report.pdf`，真实受控 PDF 位于 `harness/final-report/report.pdf` 且仍是旧 GB1 主叙事；当前 v0.3 Markdown 已纠正结论但尚未制成最终受控 PDF。同一机制也出现在 README 的旧主结论与 Makefile 的旧训练入口。
