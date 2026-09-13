#!/usr/bin/env python3
"""核对交付文档里的引用是否都指向真实存在的东西。

为什么需要这个脚本:这个仓库里「引用存在、被引用物不在」反复出现过至少五次——
README 指向迁移前的旧产物路径、知识消融报告的复现命令指向一个从未合入的模块、
manifest 指向一个随后被 gzip 归档的事件流、交接单按 fact ID 引用而那些 fact 文件
根本没进版本控制、报告目录里 v0.7 的数据其实落在任务包而非版本树。

每一次的共同点是:**写引用的人当时看得到那个东西,但读者看不到**。
靠人记得去核对是不可靠的,所以做成可执行的检查。

用法:
    python3 scripts/check_references.py            # 检查全部
    python3 scripts/check_references.py --strict   # 有任何失效引用即退出码 1

检查三类引用:
    1. Markdown 链接与反引号里的仓库相对路径 → 文件必须存在
    2. `F-XXXXXXXX` 形式的 fact ID → harness/facts/<id>.md 必须存在且已被 git 跟踪
    3. 40 位或 7 位十六进制 commit → git 里必须能解析
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 只检查交付面文档;任务包里的过程记录允许引用已消失的中间状态
TARGETS = [
    "README.md",
    "harness/reports/REPORT-HANDOFF.md",
    "harness/reports/migration-audit.md",
    *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "harness/reports").glob("*/report.md"))],
]

# 带目录分隔符才当路径;裸文件名(conservation.json 之类)在散文里是指代,不是路径
# 扩展名必须含字母:否则 `agentic-v0.1/v0.3/v0.5/v0.6/v0.7` 这种**版本枚举**
# 会因为末段 ".7" 命中 [A-Za-z0-9]{1,6} 而被当成路径,报出一个不存在的死链。
PATH_RE = re.compile(
    r"[`(]((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]{0,5}[A-Za-z][A-Za-z0-9]{0,5})[`)]")
FACT_RE = re.compile(r"\bF-[0-9A-F]{8}\b")
COMMIT_RE = re.compile(r"`([0-9a-f]{7,40})`")


def tracked(rel: str) -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", rel],
                          capture_output=True).returncode == 0


def resolvable(ref: str) -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", ref],
                          capture_output=True).returncode == 0


def check(doc: str) -> list[str]:
    path = ROOT / doc
    if not path.exists():
        return [f"{doc}: 文档本身不存在"]
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []

    for rel in sorted(set(PATH_RE.findall(text))):
        if rel.startswith(("http", "//")) or "{" in rel:
            continue
        # 一份版本报告写 `figures/x.png` 时,可能指自己同级的 figures/,也可能指
        # 数据集子目录下的 <dataset>/figures/。两种都算可达,否则误报淹没真死链。
        candidates = [ROOT / rel, path.parent / rel, *path.parent.glob(f"*/{rel}")]
        if any(c.exists() for c in candidates):
            continue
        # 再往深处找一次,并把结果分成两类。此前只 glob 一层,于是
        # REPORT-HANDOFF.md 里的 `figures/predictor_comparison.png`(实际在
        # workflow-v1.1/gb1/figures/ 下,深两层)被报成「路径不存在」——
        # 一个会喊狼来了的检查器,最后连真死链一起没人看。
        # 「不存在」与「写得不完整」是两种不同的毛病,不能混报。
        deep = [c for c in path.parent.rglob(rel) if c.is_file()]
        if len(deep) == 1:
            problems.append(
                f"{doc}: 路径写得不完整(文件在,但读者按字面找不到)→ {rel} "
                f"实际位于 {deep[0].relative_to(ROOT)}")
        elif len(deep) > 1:
            problems.append(
                f"{doc}: 路径有歧义,{len(deep)} 处同名文件 → {rel} "
                f"(如 {deep[0].relative_to(ROOT)})")
        else:
            problems.append(f"{doc}: 路径不存在 → {rel}")

    for fact in sorted(set(FACT_RE.findall(text))):
        rel = f"harness/facts/{fact}.md"
        if not (ROOT / rel).exists():
            problems.append(f"{doc}: fact 文件不存在 → {fact}")
        elif not tracked(rel):
            # 文件在本地但没进版本控制 = 读者 clone 下来查不到,与不存在等价
            problems.append(f"{doc}: fact 未进版本控制 → {fact}")

    for ref in sorted(set(COMMIT_RE.findall(text))):
        if len(ref) in (7, 8, 40) and not resolvable(ref):
            problems.append(f"{doc}: commit 无法解析 → {ref}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="有任何失效引用即以退出码 1 结束")
    args = parser.parse_args()

    all_problems: list[str] = []
    for doc in TARGETS:
        found = check(doc)
        status = f"{len(found)} 处失效" if found else "全部可达"
        print(f"  {'❌' if found else '✅'} {doc:52s} {status}")
        all_problems.extend(found)

    if all_problems:
        print(f"\n共 {len(all_problems)} 处失效引用:")
        for line in all_problems:
            print(f"  · {line}")
        return 1 if args.strict else 0
    print(f"\n{len(TARGETS)} 份交付文档的全部引用都指向真实存在且已入库的东西。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
