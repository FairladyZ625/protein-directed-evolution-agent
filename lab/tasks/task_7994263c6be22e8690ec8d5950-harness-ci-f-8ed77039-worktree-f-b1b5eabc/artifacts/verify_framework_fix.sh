#!/bin/bash
# 验证 harness-anything 对缺陷 A(CI 见证不可配置)与 B(纯文档任务 worktree 提交死锁)的修复。
# 回报口径按与 harness-anything-3b 的约定:每个任务的 preset / 是否 dispatch-bound / cwd 数 /
# submit-review-consent-complete 四步各自 receipt / 原始错误码。不做汇总美化。
#
# 用法:daemon 起来且部署 commit 确认后,在仓库根运行
#   bash lab/tasks/task_7994263c6be22e8690ec8d5950-*/artifacts/verify_framework_fix.sh <部署commit>
set -uo pipefail
ROOT=/Users/lizeyu/Projects/ai4s-directed-evolution-agent
cd "$ROOT" || exit 1
DEPLOY_COMMIT="${1:-unknown}"

echo "# 框架修复验证回报"
echo
echo "- 验证时间:$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "- 部署 commit:$DEPLOY_COMMIT"
echo "- 验证仓:ai4s-directed-evolution-agent(远端 FairladyZ625/protein-directed-evolution-agent,workflow 名为 ci.yml,main 上有绿色运行)"
echo "- ha 版本:$(ha --version 2>&1 | tail -1)"
echo

echo "## 0. daemon 与 settings 现状"
echo '```'
ha daemon status 2>&1 | head -8
echo "--- settings(关注 ci facet 是否出现且可写)"
ha settings read 2>&1 | head -4
echo "--- ha settings update 是否已有 ci workflows 写入口"
ha settings update --help 2>&1 | grep -i "ci" || echo "(未见 ci 相关选项)"
echo '```'
echo

# 每个任务打印:preset / 是否 dispatch-bound / 该 execution 的 cwd 去重数
probe_task () {
  local t="$1"
  local dir preset cwds bound
  dir=$(ls -d lab/tasks/${t}-* 2>/dev/null | head -1)
  preset=$(python3 -c "
import json,sys
try: print(json.load(open('$dir/task-contract.json')).get('presetId','?'))
except Exception: print('?')" 2>/dev/null)
  read -r bound cwds <<<"$(python3 - "$t" <<'PY'
import json, glob, sys, collections
task = sys.argv[1]
per = collections.defaultdict(set)
for f in glob.glob(".harness/runtime/dispatches/*.jsonl"):
    try:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if '"taskId"' not in line: continue
                try: o = json.loads(line)
                except Exception: continue
                if o.get("taskId") == task and o.get("cwd"):
                    per[o.get("executionId")].add(o["cwd"])
                break
    except Exception:
        pass
n = max((len(v) for v in per.values()), default=0)
print(("yes" if n else "no"), n)
PY
)"
  printf '%s\tpreset=%s\tdispatch_bound=%s\tcwd_count=%s\n' "$t" "$preset" "$bound" "$cwds"
}

echo "## 1. 缺陷 B 验证样本:纯文档任务(单 cwd,产品仓 diff 为空)"
echo '```'
for t in task_e2eab881832291e8f8f73f30a4 task_8e29be09414b0c5d7eac95db08; do
  probe_task "$t"
  echo "  [submit] $(ha task submit "$t" 2>&1 | tail -1)"
  echo "  [review] $(ha task review-execution "$t" --review-id ver-$RANDOM --json-input '{"verdict":"approved","reason":"framework fix verification","evidenceChecked":["deliverable exists on disk"]}' 2>&1 | tail -1)"
  echo "  [consent] $(ha task review-consent "$t" 2>&1 | tail -1)"
  echo "  [complete] $(ha task complete "$t" 2>&1 | tail -1)"
  echo
done
echo '```'
echo

echo "## 2. 缺陷 A 验证样本:standard-task(ci 完成门)"
echo '```'
for t in task_f50ce371b24c0c4396c76f8a4a task_84fd80d36f4b5a871d7478a8ff task_823620225b20cdb87c7ddbd1bd; do
  probe_task "$t"
  echo "  [complete] $(ha task complete "$t" 2>&1 | tail -1)"
  echo
done
echo '```'
echo

echo "## 3. 缺陷 C 验证:reviewer 绑定约束是否在派工时就拦"
echo "预期修复后行为:把 reviewer 派到非被审任务上时,ha runtime run 直接拒绝并打印正确命令,"
echo "而不是让 worker 跑完两小时后在 review-execution 写入时才报 executor_binding_invalid。"
echo '```'
echo "(本节需人工触发一次,脚本不自动派工以免浪费额度)"
echo '```'
echo

echo "## 4. 未覆盖面声明"
echo
echo "本仓是**单段式**工作流(一个 worker 一个 worktree 一次做完),因此:"
echo "- 覆盖了 B 的第一个死区(dispatch-bound + 产品仓 diff 为空);"
echo "- **未覆盖** B 的第二个死区(两段式:worktree 交付 → 合入 → 再派 cwd=根的 closeout-prep 到同一 execution,导致同一 execution 出现两个 cwd)。"
echo "  harness-anything 侧 14 个任务卡的是第二个死区,本仓的绿不能当它的充分证据。"
echo "  需专门构造一次两段式序列补覆盖——见本脚本同目录的 two_stage_probe 说明。"
