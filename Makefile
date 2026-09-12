.DEFAULT_GOAL := help

.PHONY: help data baseline train campaign demo smoke test
help:            ## show available commands
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
data:            ## validate a local GB1 CSV; does not download data
	python data/download_gb1.py
baseline:        ## 随机策略基线 eval（M1/T1）
	python evolution/random_baseline.py
train:           ## run the executable predictor-ladder evaluation (needs local GB1 data)
	python -m models.evaluate_all
campaign:        ## 四策略×3轮闭环仿真（M3）
	python evolution/campaign.py
demo:            ## Streamlit 看板（M4）
	streamlit run app/demo.py
smoke:           ## CPU-only 16-variant end-to-end campaign smoke; no source CSV
	python -m pytest tests/test_campaign.py -q
test:            ## 事件流内核测试
	pytest tests/ -q
