.PHONY: data baseline train campaign demo test
data:            ## 下载数据（已缓存则跳过）
	python data/download_gb1.py
baseline:        ## 随机策略基线 eval（M1/T1）
	python evolution/random_baseline.py
train:           ## 训练适应度模型梯队（M1）
	python models/train_ladder.py
campaign:        ## 四策略×3轮闭环仿真（M3）
	python evolution/campaign.py
demo:            ## Streamlit 看板（M4）
	streamlit run app/demo.py
test:            ## 事件流内核测试
	pytest tests/ -q
