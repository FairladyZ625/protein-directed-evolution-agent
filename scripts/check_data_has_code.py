#!/usr/bin/env python3
"""核对:主线上的每个实验版本,产生它的代码是否也在主线。

为什么需要这个脚本:「把 worktree 里的数据抢救进主线」和「把产生它的代码合进主线」
是两个动作,本仓已经两次只做了前一个:

- `knowledge-ablation`:1.5MB 产物在主线,而 `knowledge/ablation.py`(404 行)
  从未合入,报告里的复现命令必报 ModuleNotFoundError(fact `F-94CBEC61`,已修 `b78bac5`)。
- `agentic-v0.6`:数据在主线,而产生它的 backtrack 实现(`redirect_batch` /
  `top10_max_history` / `rounds_since_improvement`)在 `471536b` 上,该 commit 未合入 main。

第一次是人工逐个 `git grep` 查出来的,并且当时得出了「这是唯一缺口」的结论 —— 那个结论
是错的,因为人工检查只覆盖了 metrics 类产物到生产脚本的映射,没覆盖每个版本各自依赖的
特性代码。所以做成脚本。

判据(故意保守,宁可误报不可漏报):
    对每个 `harness/reports/<line>-v<version>/`,
    从它的 report.md / manifest.json 里抽出提到的**仓库内代码路径**与**commit**,
    逐个检查:代码路径在 HEAD 上存在吗?commit 在 HEAD 的祖先链上吗?

用法:
    python3 scripts/check_data_has_code.py
    python3 scripts/check_data_has_code.py --strict   # 有缺口即退出码 1
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "harness/reports"

CODE_RE = re.compile(r"`((?:agent|analysis|app|data|evolution|events|features|knowledge|models|scripts|tests)"
                     r"/[A-Za-z0-9_./-]+\.py)`")
COMMIT_RE = re.compile(r"`([0-9a-f]{7,40})`")


def is_ancestor(ref: str) -> bool | None:
    """commit 是否在 HEAD 的祖先链上。None = 这个 commit 在本仓解析不了。"""
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{ref}^{{commit}}"],
                      capture_output=True).returncode != 0:
        return None
    return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", ref, "HEAD"],
                          capture_output=True).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    gaps: list[str] = []
    for version_dir in sorted(p for p in REPORTS.iterdir() if p.is_dir() and p.name != "cache"):
        texts = []
        for name in ("report.md", "manifest.json"):
            f = version_dir / name
            if f.exists():
                texts.append(f.read_text(encoding="utf-8", errors="replace"))
        if not texts:
            continue
        blob = "\n".join(texts)

        missing_code = sorted({rel for rel in CODE_RE.findall(blob) if not (ROOT / rel).exists()})
        unmerged: list[str] = []
        for ref in sorted(set(COMMIT_RE.findall(blob))):
            if len(ref) not in (7, 8, 40):
                continue
            state = is_ancestor(ref)
            if state is False:
                unmerged.append(ref)

        if missing_code or unmerged:
            print(f"  ❌ {version_dir.name}")
            for rel in missing_code:
                print(f"       代码不在主线 → {rel}")
                gaps.append(f"{version_dir.name}: {rel}")
            for ref in unmerged:
                subject = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%s", ref],
                                         capture_output=True, text=True).stdout.strip()
                print(f"       commit 未合入主线 → {ref}  {subject[:60]}")
                gaps.append(f"{version_dir.name}: commit {ref}")
        else:
            print(f"  ✅ {version_dir.name}")

    if gaps:
        print(f"\n共 {len(gaps)} 处「数据在主线、代码不在主线」的缺口。")
        print("每一处都意味着:读者按报告里的说明去跑,会拿不到那份数据。")
        return 1 if args.strict else 0
    print("\n所有版本目录提到的代码与 commit 都在主线上。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
