#!/usr/bin/env bash
# Reproduce the delivery spine, preferring a useful offline demonstration on clean clones.
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

if [ ! -x .venv/bin/python ]; then
  printf '%s\n' "Missing .venv/bin/python. Run ./scripts/install.sh first." >&2
  exit 1
fi

venv_python="$(pwd)/.venv/bin/python"
run_make() {
  PYTHON="$venv_python" PATH="$(dirname "$venv_python"):$PATH" make "$@"
}

printf '%s\n' '[run-all] 1/3 smoke: synthetic, offline; outputs go to tmp/smoke/'
run_make smoke

if [ ! -f data/four_mutations_full_data.csv ]; then
  printf '%s\n' '[run-all] GB1 CSV is absent: completed the self-contained smoke path only.'
  printf '%s\n' '[run-all] For predictor and four-strategy GB1 results, place data/four_mutations_full_data.csv as described in data/README.md, then rerun.'
  exit 0
fi

printf '%s\n' '[run-all] 2/3 predictor: measured GB1; outputs go to tmp/run-all/gb1/'
mkdir -p tmp/run-all/gb1
"$venv_python" -m models.train_ladder --feature one_hot \
  --output tmp/run-all/gb1/predictor_metrics.json

# 产物写到 tmp/run-all/,不写版本化产物树。两个理由:
#   ① 版本树里的 metrics/events 是随报告一起提交的证据,让一次本地运行把它们覆盖掉,
#      读者就再也无法把报告里的数字和仓库里的文件对上。
#   ② campaign.py 的默认输出名是 campaign_easy.*,而这里跑的是 low_hd(hard regime);
#      沿用默认名会把 hard 的数据写进 easy 的文件名,给出一份张冠李戴的产物。
#      所以下面把 regime 名字显式写进三个 --out-* 路径。
campaign_out="tmp/run-all/gb1"
mkdir -p "$campaign_out/figures"
printf '[run-all] 3/3 campaign: four strategies on measured GB1 (hard regime); outputs go to %s/\n' "$campaign_out"
"$venv_python" -m evolution.campaign --cold-start low_hd --max-cold-hd 2 \
  --out-json "$campaign_out/campaign_hard.metrics.json" \
  --out-fig "$campaign_out/figures/campaign_hard.png" \
  --out-events "$campaign_out/campaign_hard.events.jsonl"

printf '%s\n' '[run-all] complete: smoke, predictor, and four-strategy campaign finished.'
printf '%s\n' '[run-all] 提交在 lab/reports/ 下的产物未被改动;本次结果在 tmp/run-all/,可与前者对比。'
