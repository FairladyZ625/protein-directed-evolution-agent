# Feature cache

`gb1-all-one-hot.npz` contains the complete 149,361-variant nomination space in
deterministic 80-dimensional (`4 x 20`) form. The archive stores aligned
`variants` and `embeddings` arrays.

ESM-2 archives are named
`esm2_t33_650M_UR50D-<content-key>.npz`. Build the train-pool cache on the MPS
worker after the official model weights are available locally:

```bash
python -m features.build_cache --esm-pool train_pool --device mps
```

The content key covers the ordered variants and model identifier. Cache writes
are atomic, and readers verify the variant order before reuse. The runtime
falls back to CPU if MPS is unavailable; one-hot remains the no-model-weight
fallback.
