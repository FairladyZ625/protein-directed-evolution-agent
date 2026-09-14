# Closeout

## Summary

评委现在可以在 Linux 或 macOS 上跑两条命令装好并复现主结果。交付提交 `c763e7f`,
合入主线于 `995c094`。

- `scripts/install.sh`:检测 `python3` ≥3.11、建 `.venv`、装轻量档、验证 import;
  `--full` 追加 torch/fair-esm。POSIX 兼容,只用 bash 3.2 有的特性(macOS 自带的就是 3.2)。
- `scripts/run_all.sh`:分阶段跑 smoke → 预测器 → 四策略闭环,缺 GB1 真值表时自动降级到
  smoke 路径并明说,而不是报错退出。
- `requirements.txt` 收窄为轻量档(11 条),torch/fair-esm 移入 `requirements-full.txt`。
- Makefile 加 `install` / `run-all` 目标;README 安装与运行小节改写。
- 补齐 7 个缺失的 `manifest.json`;复现脊柱 `experiment_log.jsonl` 补 9 条历史运行记录。

## Verification

- **干净环境实测(worker 未能完成、由 CEO 接手补做)**:从主线 commit 新建 detached
  worktree(无 `.venv`、无 GB1 真值表),跑 `./scripts/install.sh` → 建 venv、装 70 个包、
  `[install] verified imports: numpy, pandas, scipy, sklearn, yaml, networkx, pydantic,
  streamlit, matplotlib`,exit 0。
- **阴性对照**:同一干净环境跑 `./scripts/run_all.sh` → smoke 五个产物齐出(含
  `verified hash chain` 与 116 条投影事件),随后打印
  `GB1 CSV is absent: completed the self-contained smoke path only.` 并给出
  `data/README.md` 的具体指引,exit 0。**缺前置时是明确降级提示,不是崩栈也不是静默空跑。**
- **manifest 独立重算**:遍历 `lab/reports/*/manifest.json`,逐文件重算 sha256 并与
  声明值比对 —— **71 个对得上,0 个对不上**。
- **脊柱**:`EventStore.verify()` 通过,26 条,链完整。
- **测试**:CI 同款六文件 47 passed。

## Residual Risk

1. **Linux 与 `--full` 档未实测**。脚本按 POSIX 与 bash 3.2 写,但 CEO 只在 macOS 上验过;
   `--full` 会拉 torch(约 2GB),本轮未跑。
2. **脊柱里有 4 条 `command: null`**。这是按计划要求的诚实选项——那几次历史运行的确切命令
   在任务包与 git log 里都查不到,写 `null` 加 `provenance_note`,而不是猜一条命令写上去
   让读者以为跑得出来。
3. **`workflow-v1.1/manifest.json` 有一处失效引用**:它指向 `campaign_easy.events.jsonl`,
   而该文件在 worker 读取之后被 CEO 改成了 `.gz` 归档(commit `8b6c6a8`)。四个 regime
   齐全后由 CEO 统一重写该 manifest。这是竞态,不是 worker 的错。
4. 旧的描述型 manifest(`agentic-v0.1`–`v0.4`/`v0.6`、`final-report-v0.1`/`v0.2`、
   `workflow-v1.0`)没有 `artifacts` 校验字典,与新写的完整性型 manifest 形状不一致。
   不是缺陷,但版本树里两种形状并存,读者需要知道。

## Same Mechanism Elsewhere

worker 交付后 CEO 复核抓到两处它没察觉的产物覆盖,都属同一机制——
**「跑一遍」和「跑一遍且不破坏已提交的证据」是两件事**:

1. 原 `run_all.sh` 第 3 步传了 `--cold-start low_hd` 却不传 `--out-*`,会把 hard regime
   的数据写进默认的 `campaign_easy.*` 文件名,产出一份张冠李戴的产物。
2. 原第 2、3 步都写进 `lab/reports/` 版本化产物树,会覆盖随报告一起提交的证据,
   读者从此无法把报告里的数字和仓库里的文件对上。

现在两步都写 `tmp/run-all/`,regime 名字显式落在三个 `--out-*` 路径里。
同一形态在 `models/train_ladder.py` 等所有默认输出指向版本树的脚本上都存在:
**默认输出路径指向「证据」而不是「草稿」,任何一次本地重跑都会静默改写交付物。**
