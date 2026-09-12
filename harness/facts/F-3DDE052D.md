# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-3DDE052D

- Statement: 和解记录矛盾:507fa9早期execution写'no local weights exist',系当时未找到;后确认ESM-2 650M权重已本地缓存(~/.cache/torch/hub/checkpoints/esm2_t33_650M_UR50D.pt 2.6GB),并据此构建了AAV ESM嵌入缓存(harness/reports/cache/esm_aav.npz 173MB/38265条,full clean subset)。GB1 ESM缓存为~51k分片(按需子集,非全149361,设计如此)。closeout的'已本地缓存'针对AAV成立;avGFP完整跑分仍诚实延到优化阶段。
- Evidence source: codex de-reviewer dispatch_f9c98a87报告 + reports/cache/esm_aav.npz + features/cache/
- Observed at: 2026-09-11T13:39:38.577Z
- Confidence: high
- State: standing

