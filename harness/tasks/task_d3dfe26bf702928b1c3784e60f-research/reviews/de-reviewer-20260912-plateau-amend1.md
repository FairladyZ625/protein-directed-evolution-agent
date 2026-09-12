# Review de-reviewer-20260912-plateau-amend1

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_d3dfe26bf702928b1c3784e60f
- Execution: exe_c594c973ea9a44cae30dfd063d
- Verdict: changes_requested
- Commit: 01328291e5b2ac789337acb55ee1b3c737048490
- Iteration: 1
- Content digest: sha256:8d8c5d0de54aec60e8ffbe303e6e531c32f7c9f45adde1b15571a371bf612581
- Submission digest: sha256:e99db79253889c03fc7e98e37c87834f7f62cbb4df688ed1e3ba188482b7ba56
- Reviewed at: 2026-09-12T13:10:18.090Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：amend 后的 submitted content pin（commit 01328291e5b2ac789337acb55ee1b3c737048490）仍包含已被 oracle 否定的承重论断：声称 cold-start 已含构成真峰的全部 doubles，并据此排除数据覆盖、把瓶颈唯一归因于 surrogate 表达力。当前工作区虽在文首加了勘误，但该勘误未进入提交 commit，且正文 §0、族2判断、排序 #2、提名 B 和总纲仍沿用旧论证，内部自相矛盾，不能靠页首免责声明替代正文修订。交付也未满足每条方法的五要素契约：现有内容按方法族合并叙述，未逐条明确方法原理、代表文献/工具、突破隐藏峰机制、现有工具笼合法性及需新增工具、answer-agnostic 判定；多数引用正文又明确承认未逐篇核验，缺标题/可定位标识，达不到‘真实可核引用’通过判据。修复方向：把双因素机制（关键 D0Q+S17E 二阶缺测 + 模型表达力/头部外推失真）真正改入全文并重排 shortlist/实验提名；避免用真峰成分做实验设计，只可用于事后机制审计；为每个候选方法补齐五字段和可核书目（标题、作者、年份、出处及 DOI/稳定链接），删除或标为不采信的未核条目；将修订文档提交为新的 commit 并 amend execution，使 content pin 与磁盘正文一致后再审。

## Evidence checked

- 按顺序读取 ai4s-worker-handbook.md、task_plan.md、AI4S-assignment.md，并读取 AI4S-domain-research.md、agentic-v0.2/report.md、agentic-v0.3/aav/surrogate_scan.json
- git show 01328291e5b2ac789337acb55ee1b3c737048490：提交仅新增 plateau-breaking-methods.md 96 行；提交版 SHA256=428095b1e3045e2f197acadcdf74eb56b56916f76088f14af8750946048ee255
- 当前磁盘文档 SHA256=e36c0cc22d38c87cc6d2f3bf4cf791e6cdadb30946bc7039529610257c3e14d8，与 submitted commit 不同；页首勘误不在 content pin 中
- evolution.datasets.load_aav() ground-truth：clean_rows=38265；WT=-0.9181937107；D0Q=0.3020158736；S17E=3.2874179974；V18A=0.8896062183；D0Q+V18A=2.08789430573；S17E+V18A=5.77020873916；peak=8.41620513056；D0Q+S17E present=False
- 阴性对照：同一 lookup 成功检出 WT、singles、其余 doubles 和 peak，仅 D0Q+S17E 缺失，排除检测器静默
- rg/结构检查：7 个方法族、10 项排序、3 个实验提名存在；但正文仍在 §0、族2、排序 #2、提名 B 使用已证伪的全 doubles 覆盖/表达力唯一归因
- 结构字段检查：文档未按逐条五要素提供明确字段；附录承认除少数条目外其余引用来自扫描、正式引用前需逐条核对
- ha fact search --task：纠正事实 F-E9C38438 已存在，但 standing 的 F-851790B5 仍复述错误单因素结论；旧 F-5A4B6556 虽 superseded，正文和 submission 尚未同步纠正
