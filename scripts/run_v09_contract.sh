#!/usr/bin/env bash
# v0.9 的 2x2 因子实验:工具契约 x 残差反思。
#
# v0.8 的 2x2 结论是:强制注入残差对提名零影响,四臂批次逐位相同(48/48 x 6),
# 两个采集档下皆然。查代码后确认这不是模型缺陷,是**契约形状**:
#   1. 两个采集段落都写着「Prefer that default」,round prompt 把 compose_batch(n=48)
#      写死、参数位上根本没有 exploit_ratio —— agent_requested=0 首先是遵从指令;
#   2. 利用比地板(CV>=0.80 -> 0.80,末两轮 -> 0.90)恰好只禁止残差该触发的
#      「调低利用比」方向,实测第 4 轮起可行区间为空集;
#   3. **根因**:exploit_ratio 是标量,没有任何取值能表达「别选带 N21D 的候选」。
#
# --contract v09 一次性动这三样(它们互相封锁,单动一样等于没动),
# 于是「反思是否改变提名」第一次成为一个**可以真的失败也可以真的成功**的问题。
#
# 对照臂是 --contract v08(= 不传),必须复现 v0.8 的「不分叉」,否则本轮无效。
# 四格全部固定 --backtrack semi --acquisition v05,与 v0.8 的 v05 两格严格可比。
#
# 用法:
#   scripts/run_v09_contract.sh [输出根目录] [seed ...]
#   scripts/run_v09_contract.sh harness/reports/v09-contract 42
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_root="${1:-$repo_root/harness/reports/v09-contract}"
shift || true
seeds=("$@")
[ ${#seeds[@]} -eq 0 ] && seeds=(42)
model="${V09_MODEL:-gpt-5.6-sol}"
# 每轮预算可调。48x6 下八个臂全部在第 2 轮(96/288 次 oracle)达到候选池真实最优
# 8.416205,此后四轮峰值不再变化 —— 67% 的预算花在答案已经找到之后,任何 r3-r6 的
# 策略差异按构造都无法体现在峰值上。把每轮预算压到 12,让峰不在前两轮就被够到,
# 峰值指标才重新具备区分力。
budget="${V09_BUDGET:-48}"
mkdir -p "$out_root"

cd "$repo_root"
for seed in "${seeds[@]}"; do
  for contract in v08 v09; do
    for reflexion in off on; do
      arm="contract-${contract}_reflexion-${reflexion}_seed-${seed}"
      [ -f "$out_root/$arm/agentic.metrics.json" ] && { echo "skip $arm (已存在)"; continue; }
      flags=(--dataset aav --feature one_hot --guardrail --surrogate epistasis
             --budget "$budget" --n-rounds 6 --seed "$seed" --model "$model"
             --backtrack semi --acquisition v05 --skip-experiment-log)
      [ "$contract" = "v09" ] && flags+=(--contract v09)
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
