verdict：打回（changes_requested）

工具证据：

- iteration 4 artifact 与 canonical 文档一致。
- 文档第 5、135、142 行记录 UCB β=3 在池内命中 8.4162；但第 148–150 行又断言“没有任何笼内方案能让该峰进入可达区”，结论自相矛盾。
- 第 104 行称缺测 `D0Q+S17E` 需由提名 A 补；第 125–128、142–144 行又明确该组合全表不存在，A 无法补出。
- 文档第 87、161–162 行承认多数引用缺完整标题、DOI 或稳定链接；实际 URL 数为 0。EVmutation 与 MULTI-evolve 的一手出处确实可定位，但交付文档未提供定位信息：[EVmutation](https://www.nature.com/articles/nbt.3769)、[MULTI-evolve](https://pmc.ncbi.nlm.nih.gov/articles/PMC12991030/)。
- 本地数据行 `data/aav/full_data.csv:241593` 支持池内目标序列及 8.416205 数值。

具体缺陷与修复方向：

1. 统一“池内目标可命中”与“缺失二阶路径不可学习”的表述，删除算法无关不可达结论。
2. 修改候选清单：提名 A 只能补池内已有二阶组合；`D0Q+S17E` 必须明确列为需扩展 oracle 或湿实验。
3. 为每条方法补完整标题、作者、年份及 DOI/稳定论文或官方工具链接；无法核验的条目标为待核，不得作为已核证据。

已尝试执行 `ha task review-execution`，但 Harness 因 review-return budget 耗尽拒绝记录 `changes_requested`；未修改代码、文档或治理设置。