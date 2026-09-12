.PHONY: data baseline train campaign demo smoke test check-gb1-data
data:            ## 校验本地 GB1 数据（不下载）
	python data/download_gb1.py
check-gb1-data:
	@test -f data/four_mutations_full_data.csv || { \
		echo "Missing data/four_mutations_full_data.csv for the full GB1 run." >&2; \
		echo "See data/README.md for the Wu et al. source and placement instructions." >&2; \
		echo "For a self-contained synthetic demonstration, run: make smoke" >&2; \
		exit 2; \
	}
baseline:        ## 随机策略基线 eval（M1/T1）
	@$(MAKE) --no-print-directory check-gb1-data
	python evolution/random_baseline.py
train:           ## 训练适应度模型梯队（M1）
	python -m models.train_ladder --feature one_hot
campaign:        ## 四策略×3轮闭环仿真（M3）
	@$(MAKE) --no-print-directory check-gb1-data
	python evolution/campaign.py
smoke:           ## 合成小规模端到端流程（无需数据、缓存或 API key）
	python scripts/smoke.py
demo:            ## Streamlit 看板（M4）
	streamlit run app/demo.py
test:            ## 与 CI 一致的自包含测试集合
	pytest -q tests/test_events.py tests/test_knowledge.py tests/test_agent.py tests/test_campaign.py tests/test_demo.py tests/test_predictor.py
