import sys
from pathlib import Path

# 让 `pytest tests/`（Makefile 的 make test）能 import 仓库根下的 evolution/ 等包
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
