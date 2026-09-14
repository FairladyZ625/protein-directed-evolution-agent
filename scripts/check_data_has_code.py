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
    对每个 `lab/reports/<line>-v<version>/`,
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
REPORTS = ROOT / "lab/reports"

CODE_RE = re.compile(r"`((?:agent|analysis|app|data|evolution|events|features|knowledge|models|scripts|tests)"
                     r"/[A-Za-z0-9_./-]+\.py)`")
COMMIT_RE = re.compile(r"`([0-9a-f]{7,40})`")

# 显式豁免。一份报告有时**必须**提到一个没合入主线的 commit —— 典型情形是事后更正:
# 「当年记的出处是 X,X 从未合入,能力实际由 Y 和 Z 落地」。这种文字里不可避免会出现 X,
# 而它恰恰是在修复问题而不是制造问题。
#
# 豁免是显式的、要写理由的、可 grep 的,不是把判据放松:
#     <!-- check-data-has-code: allow-unmerged <commit> reason=<一句话> -->
# 没有 reason 的豁免不生效 —— 否则它就退化成一个静音开关,
# 而静音开关正是这个脚本存在的理由的反面。
ALLOW_RE = re.compile(
    r"<!--\s*check-data-has-code:\s*allow-unmerged\s+([0-9a-f]{7,40})\s+reason=(\S[^>]*?)\s*-->")


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
        # 一个豁免覆盖该 commit 的全部写法(短 sha 与全长 sha 指同一个对象)
        allowed = {}
        for ref, reason in ALLOW_RE.findall(blob):
            full = subprocess.run(["git", "-C", str(ROOT), "rev-parse", ref],
                                  capture_output=True, text=True).stdout.strip()
            allowed[full or ref] = reason
        unmerged: list[str] = []
        for ref in sorted(set(COMMIT_RE.findall(blob))):
            if len(ref) not in (7, 8, 40):
                continue
            state = is_ancestor(ref)
            if state is not False:
                continue
            full = subprocess.run(["git", "-C", str(ROOT), "rev-parse", ref],
                                  capture_output=True, text=True).stdout.strip()
            if full in allowed:
                print(f"       (已显式豁免 {ref}:{allowed[full][:70]})")
                continue
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
