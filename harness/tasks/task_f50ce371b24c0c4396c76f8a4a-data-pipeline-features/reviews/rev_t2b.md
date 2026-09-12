# Review rev_t2b

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_f50ce371b24c0c4396c76f8a4a
- Execution: exe_8fd900a059b9d1baad11c65420
- Verdict: approved
- Commit: 91d9a17154617c0b068a44bcb99f1e44c1ee7fd1
- Iteration: 1
- Content digest: sha256:4b55d6f7817a575fa6481d4d72a7aea5eaf76272e075799395d65a68ddbef053
- Submission digest: sha256:86ecba17ba50d445d4e6ad321fa61eb6d11ff405d5fab5b00b4050e9336bd3b4
- Reviewed at: 2026-09-11T14:01:23.833Z
- Consent: cons_feea010556c6
- Consent actor: person-ai4s
- Consent source: "local"

## Reason

修正后的 Execution 与 closeout 陈述在本轮独立复核中成立：定向测试真实为 6 passed；三池规模、互斥性与 149361 并集成立；one-hot 全空间缓存为 149361x80；完整 train 顺序按内容键命中已提交 ESM 缓存并返回 5000x1280。closeout 已明确 650M 权重仅为机器本地资源，仓库交付边界是已提交的 train 批次缓存与 one-hot 兜底，没有把全量实时提取冒充为仓库内可复现证据。F-997BBF50 的较窄陈述与产物一致。

## Evidence checked

- ha task show/task execution file: current submitted execution is exe_8fd900a059b9d1baad11c65420 at commit 91d9a17154617c0b068a44bcb99f1e44c1ee7fd1; verificationNotes names tests/test_data_pipeline.py = 6 passed as directed evidence
- clean directed run: env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider --basetemp /tmp/ai4s-t2-review-rev_t2b tests/test_data_pipeline.py -q -> 6 passed in 1.33s
- disk CSV inspection: train/query/holdout rows and unique variants are 5000/50000/94361; all pairwise intersections are 0; union is 149361; VDGV occurs only in train
- features/cache/gb1-all-one-hot.npz with allow_pickle=False: variants (149361,) unique and embeddings (149361,80) uint8; every row has four active bits
- content-keyed train cache: expected key dbfd1ecc45bd4b72148d exists; ESM2Embedder.transform on ordered train variants returns finite float32 (5000,1280) with injected failing backend called 0 times
- cache-hit positive control: changing the first train variant causes the injected backend to run and raise LIVE_BACKEND_CALLED, confirming the exact-order cache-hit detector is active
- git cat-file at submitted commit confirms all three pool CSVs, gb1-all-one-hot.npz, and esm2_t33_650M_UR50D-dbfd1ecc45bd4b72148d.npz are present
- ha fact show --id F-997BBF50: standing high-confidence fact states reproducible 5000/50000/94361 pools, full 149361x80 one-hot coverage, and a 1280-dimensional cached ESM interface; this matches the verified delivery boundary
- closeout.md and execution known gaps explicitly identify ESM-2 650M weights as machine-local/not in repository and limit self-contained evidence to committed batch cache plus one-hot fallback
