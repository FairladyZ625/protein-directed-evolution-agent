# 文风与引用核验规范（v0.3 校订）

采用客观中文学术写作；观察、机制推断与未来设计分开。禁止将单次最好值写成普适优势，将确定性seed重复写成独立试验，将预测误差直接写成分子结构机理。

主报告列30篇真实正式发表的文献：28篇期刊文章和2篇NeurIPS会议论文。按正文首次出现排序、GB/T 7714-2015顺序编码，前三作者后加et al（多于三人时），列年、卷期、页码或文章号及原文链接。补充报告独立编号16篇；与主报告的映射记录在bibliography-audit.json。

原始库含错误或未核实条目，不能照抄其“已核验”声明。校订采用出版方DOI登记及正式会议PDF；如ProteinGym前三作者为Notin/Kollasch/Ritter，Wittmann训练集设计论文作者为Wittmann/Yue/Arnold，Rives第三作者为Sercu，ProteinMPNN第三作者为Bennett。Bran论文发表于Nature Machine Intelligence；Biswas题名为Low-N protein engineering with data-efficient deep learning。

Otte 2026及其他未获得可靠出版记录的原库条目不引用，不推定不存在。对这类条目既不捏造作者，也不以近似DOI替代。原库与技能书目存在冲突时，以用户“真实文献”要求和实际核验为准。

核验资料：evidence/ref-01.json至ref-30.json，bibliography-audit.json，正式会议源文件。Friedman页码由Project Euclid核为1189—1232；FLIP作者按PDF消除网页重复。

引用脚本只证明数字闭环；另用交付校验检查恰好30条、无重复编号、按首次引用顺序编号及正文/文末双向集合相等。实际运行日志见verification.log。图形渲染与最终PDF分页不在引用脚本验证范围。
