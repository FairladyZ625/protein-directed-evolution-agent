"""Feature and pool interfaces shared by fitness models and campaigns."""

from .one_hot import OneHotEncoder, encode_one_hot
from .pools import PoolSplit, build_three_pools, load_three_pools, write_three_pools

__all__ = ["OneHotEncoder", "PoolSplit", "build_three_pools", "encode_one_hot", "load_three_pools", "write_three_pools"]
