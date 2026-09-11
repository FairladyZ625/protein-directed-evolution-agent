"""Fitness predictor ladder."""
from .train_ladder import RidgePredictor, XGBoostPredictor, MLPPredictor, metrics

__all__ = ["RidgePredictor", "XGBoostPredictor", "MLPPredictor", "metrics"]
