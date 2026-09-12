"""Feature and pool interfaces shared by fitness models and campaigns."""

from .one_hot import OneHotEncoder, encode_one_hot
from .pools import (
    EvaluationProtocol,
    PoolSplit,
    build_evaluation_protocol,
    build_three_pools,
    load_three_pools,
    write_three_pools,
)

__all__ = [
    "EvaluationProtocol",
    "OneHotEncoder",
    "PoolSplit",
    "build_evaluation_protocol",
    "build_three_pools",
    "encode_one_hot",
    "load_three_pools",
    "write_three_pools",
]
