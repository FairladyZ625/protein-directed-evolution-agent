# Review rev_t2a

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_f50ce371b24c0c4396c76f8a4a
- Execution: exe_bb872d2f8353788765c6f695fd
- Verdict: changes_requested
- Commit: 4f456890ca43dfe007e4b17c63c06c3fa26f147f
- Iteration: 0
- Content digest: sha256:8883cefdc09d8bd30f4a270ff451a6890a81aae98e4bfa3c4d03c518702e08a1
- Submission digest: sha256:912b2ed8497b866d030938dd59576a6d414b4f9b227dccf34f59289a28fd9279
- Reviewed at: 2026-09-11T13:52:59.260Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

三池、突变模块、149361x80 one-hot 缓存及已提交的 5000x1280 train ESM 缓存接口均可复核，但 closeout/Execution 的验证陈述未真实成立：指定 tests/test_data_pipeline.py 本次仅 6 passed（非 43 项）；ESM-2 use_cache=False 实测尝试下载权重并因 TLS CERTIFICATE_VERIFY_FAILED 退出，故当前 runtime 无法验证‘650M 权重已本地缓存’及真实实时提取。请将验证数字改为可复现的 6/6，或提供并点名产生 43 passed 的确切命令；同时修正权重缓存表述，并提供可在干净评审环境执行的真实 ESM 冒烟证据，或明确只承诺已提交批次缓存与 one-hot CPU 兜底。

## Evidence checked

- ha task show: task in_review; submitted execution exe_bb872d2f8353788765c6f695fd; commit 4f456890ca43dfe007e4b17c63c06c3fa26f147f
- git ls-tree at submitted commit: evolution/datasets.py, evolution/mutations.py, features/, data/pools/, tests/test_data_pipeline.py all present; submitted commit is an ancestor of HEAD and these paths have no diff to HEAD
- closeout.md contains the exact four sections Summary, Verification, Residual Risk, Same Mechanism Elsewhere
- pytest -q tests/test_data_pipeline.py: 6 passed in 1.38s
- pool CSV inspection: sizes 5000/50000/94361, pairwise intersections 0/0/0, union 149361, WT VDGV in train
- features/cache/gb1-all-one-hot.npz: variants (149361,), embeddings (149361,80), uint8
- committed train ESM cache hit with a forbidden backend: returned (5000,1280) without invoking backend
- positive control: malformed 7-dimensional backend raised ValueError expected (1,1280), proving the dimensionality detector fires
- real ESM negative check: ESM2Embedder(...).transform(['VDGV'], use_cache=False) attempted model download and failed with urllib.error.URLError caused by SSL CERTIFICATE_VERIFY_FAILED
- ha fact show F-997BBF50: standing fact states reproducible 5000/50000/94361 split, full committed 149361x80 one-hot cache, and a 1280-dimensional cached ESM interface; this narrower statement matches the verified artifacts and does not claim a full 149361-row ESM cache
