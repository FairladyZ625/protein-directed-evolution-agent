#!/usr/bin/env python3
"""
verify_citations.py: 校验 Markdown 报告中的正文引用 [N] 与文末参考文献表是否 1:1 严格对齐。
用法: python verify_citations.py <path_to_report.md>
"""

import sys
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_citations.py <path_to_report.md>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    # 分离正文与参考文献部分
    ref_split = re.split(r'#+\s*参考文献|##\s*参考文献', text)
    if len(ref_split) < 2:
        print("Warning: 未找到 '## 参考文献' 章节")
        sys.exit(1)

    body = ref_split[0]
    refs_section = ref_split[1]

    # 正文中匹配 [1], [2], ..., [30]
    body_citations = set(map(int, re.findall(r'\[(\d{1,2})\]', body)))

    # 参考文献中匹配 [1], [2], ..., [30]
    ref_entries = set(map(int, re.findall(r'\[(\d{1,2})\]', refs_section)))

    print(f"=== 引用校验报告: {path.name} ===")
    print(f"正文中出现的引用数量: {len(body_citations)} (最大编号: {max(body_citations) if body_citations else 0})")
    print(f"参考文献表中的条目数量: {len(ref_entries)} (最大编号: {max(ref_entries) if ref_entries else 0})")

    missing_in_refs = body_citations - ref_entries
    unused_in_body = ref_entries - body_citations

    if missing_in_refs:
        print(f"❌ 严重错误: 正文引用了但参考文献中缺失的标号: {sorted(missing_in_refs)}")
    else:
        print("✅ 正文中所有引用在参考文献表中均有对应条目。")

    if unused_in_body:
        print(f"⚠️ 提示: 参考文献列出但正文未显式引用的标号: {sorted(unused_in_body)}")
    else:
        print("✅ 参考文献表中所有条目均在正文中被引用。")

    if not missing_in_refs and not unused_in_body:
        print("🎉 完美！正文与文末参考文献实现 100% 严格 1:1 双向对齐！")
        sys.exit(0)
    elif missing_in_refs:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
