#!/usr/bin/env bash
# v0.8 的 2x2 因子实验:采集档位 x 残差反思。
#
# 第一轮冒烟(scripts/run_v08_arms.sh)发现:在 v0.6 纯利用默认下,LLM 对采集比例
# 没有任何裁量(每轮都是 requested 1.0 -> effective 1.0),反思注入改变了它的动作
# (basin hop 提前 3 轮)却没改变任何一个提名——六轮实测批次逐位相同。
# 所以那一轮测到的不是「反思没用」,是「反思无处着力」。
#
# 本脚本加上 v0.5 的质量感知采集档(LLM 的 exploit_ratio 真能影响批次),
# 构成一个干净的 2x2。四格**全部**固定 --backtrack semi,所以 stall 强制注入与
# redirect_batch 工具在四格里恒定;唯二变动的就是采集段落和反思开关。
#
# 用法:
#   scripts/run_v08_factorial.sh [输出根目录] [seed ...]
#   scripts/run_v08_factorial.sh tmp/v08-factorial 42 11 23
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_root="${1:-$repo_root/tmp/v08-factorial}"
shift || true
seeds=("$@")
[ ${#seeds[@]} -eq 0 ] && seeds=(42)
model="${V08_MODEL:-gpt-5.6-sol}"
mkdir -p "$out_root"

cd "$repo_root"
for seed in "${seeds[@]}"; do
  for acq in v06 v05; do
    for reflexion in off on; do
      arm="acq-${acq}_reflexion-${reflexion}_seed-${seed}"
      [ -f "$out_root/$arm/agentic.metrics.json" ] && { echo "skip $arm (已存在)"; continue; }
      flags=(--dataset aav --feature one_hot --guardrail --surrogate epistasis
             --budget 48 --n-rounds 6 --seed "$seed" --model "$model"
             --backtrack semi --acquisition "$acq" --skip-experiment-log)
      [ "$reflexion" = "on" ] && flags+=(--reflexion)
      start=$SECONDS
      LLM_TIMEOUT=240 PYTHONPATH=. .venv/bin/python -m agent.auto_researcher \
        "${flags[@]}" --out-dir "$out_root/$arm" 2>&1 | tee "$out_root/$arm.stdout.log"
      printf '%s\n' "$((SECONDS - start))" > "$out_root/$arm.wall-seconds.txt"
      echo "=== done $arm ($((SECONDS - start))s) ==="
    done
  done
done
echo "ALL ARMS COMPLETE"
