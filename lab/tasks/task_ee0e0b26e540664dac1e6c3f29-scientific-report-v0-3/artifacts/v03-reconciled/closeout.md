## Summary

交付主报告（精确八章、30篇正式文献）、补充报告（16篇独立编号文献）、四份校订工件和证据包。主报告3499个汉字、补充报告4747个汉字；统计包含文后部分，另见verification.log的非空白字符数与字节数。作者资料按项目底本保留，使用语言模型辅助写作已在正文披露。

初始四份工件保留作为历史输入；任务 artifacts/v03-reconciled/ 下四份工件及本报告为校订口径。纠正GB1轮次、AAV确定性重复、缺测分母、FULL结果及文献元数据。

本地分支codex/scientific-report-v0-3；交接提交64dd653ed1f26a0ead990372d1888473c2c7f563。遵守任务“不提交公共仓库工件”指令，提交为仅标记交接的空提交；报告通过Harness文档同步提交并镜像到指定目录，不在Git提交中。没有推送、PR或合并。

## Verification

rebase前fetch origin main成功。任务基线与origin/main无共同祖先，使用显式范围 `git rebase --onto origin/main ec3f6d56b96723f4c6d10ce9e431f94a6ac68295` 仅移植本任务交接提交，未拼接或改写原仓历史。最终origin/main为be62937a8b7a7bc3e6e9e7d67fba33e67e8f3bc2，已是交接提交祖先；产品diff为空。

rebase后两次指定引用脚本均exit0；严格校验器检查八章、首次引用顺序、30/30和16/16闭环、五图锚点、120条GB1 Top10重构曲线、比例及0.5872差值，全部通过。worker、canonical authored以及双仓reports两份正文逐字节相同。真实输出见evidence/verification.log，哈希见evidence/delivery-manifest.json。

文献28篇通过Crossref出版方登记核对，2篇通过正式NeurIPS来源核对；未将编号闭环称为文献真实性验证。Crossref首次限流一条后重试成功。Harness首次工件源在worktree外于登记根被拒；改用指定报告镜像作为源后，旧目标碰撞，最终追加至v03-reconciled/并成功登记；未覆盖旧工件。

## Residual Risk

未重跑蛋白campaign、ESM、LLM、湿实验或全CI。AAV30-seed逐轮目录未在指定canonical路径找到，统计依赖历史专题报告；主报告对该限制明确披露。理论公式有假设条件，不是当前bootstrap Ridge的保证。五图本任务只交图注与锚点，最终图形和PDF 3—5页分页尚未验收。独立review-execution、review-consent及complete由有权审阅方执行，未自审。

## Same Mechanism Elsewhere

旧v0.2、通俗HTML及figure-manifest仍含被纠正的首轮达峰、贪心达峰或连续鞍点叙述；本任务没有改写这些非指定交付文件。四份原始事实底本有同类问题，保留历史并由v03-reconciled校订工件明确替代使用。后续制图必须读新图注和figures_data，避免把旧图重新带回正文。
