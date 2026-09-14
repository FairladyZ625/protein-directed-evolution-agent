# 新版Demo图表筛选

实际入口 http://localhost:8512，服务cwd为当前仓库，运行app/demo.py。8501为旧timeline看板，不用作当前Demo证据。主控临时8502服务已关闭。de-frontend完成部分界面截图后因标签定位反复失败停止，主控接手，亲自读取8512第⑤、第④、第②面板并截图。未触发新campaign或昂贵推荐。

| 候选素材 | 视觉证据 | 数据/代码来源 | 入稿安排 |
|---|---|---|---|
| alpha八组合扫描 | shots/14_tab5c_alpha_sweep.png、ceo-tab5-figure-3.png | workflow-v1.0/gb1/predictor_alpha_sweep.json；app/demo.py render_alpha_sweep_panel | 正文突出跨阶比较与验证集选参，完整八面板放附录；重绘 |
| 固定alpha标准化反转 | 第⑤页文字与表，tab5-text.txt | workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json | 与alpha扫描组成方法学对照 |
| 低阶完整覆盖率 | ceo-tab5-figure-1.png | analysis-v0.1/aav/mutation_order.json | 正文，突出HD2/3/4，避免原图2–28大范围空白；标题仅描述覆盖变化，不宣称高阶峰不可学习 |
| 保守性熵曲线 | ceo-tab5-figure-2.png | analysis-v0.1/aav/conservation.json | 正文，与D0Q/S17E/V18A及局部缺测图联读；统一窗口零/一基标注，移开重叠标签 |
| sparse四策略轨迹 | shots/03_tab1_sparse_chart.png | workflow-v1.1/gb1/campaign_sparse.metrics.json | 正文三场景主结果面板 |
| 随机多seed误差带 | shots/04_tab1_easy_band.png | campaign_easy.metrics.json strategies.random.multi_seed | 正文/附录，保留实际重复口径 |
| 四位点残基集中度 | ceo-tab4-full.png、tab4-text.txt | campaign_easy.metrics.json strategies.*.topk_concentration | 正文简洁热图或分组条形图，回答推荐集中在哪些位点 |
| DataAnalyst到候选库回放 | ceo-tab2-full.png、tab2-text.txt | workflow-v1.1/gb1/campaign_easy.events.jsonl.gz；app/demo.py | 选择一次真实运行的统计/假设/组合理由做紧凑实例，不整页截图贴正文 |

截图根：.harness/report-v06-demo-scratch/shots。已查看各独立图像与面板截图；面板长截图存在虚拟渲染留白，不作为成品图使用。核心图对应源文件前缀均为lab/reports/。

新增图表以解释力排序，不用页面装饰替代数据。最终正文图数量可高于v0.5的五张，整篇仍围绕研究问题组织。
