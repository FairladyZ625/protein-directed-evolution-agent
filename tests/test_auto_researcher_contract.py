"""v0.9 工具契约:让残差证据有落点,而不改变 v0.8 的任何默认行为。

v0.8 的 2×2 证明强制注入残差对提名零影响(四臂批次逐位相同)。查代码后确认这不是
模型缺陷,是契约形状——四层原因里有三层是本仓自己设的:

1. 两个采集段落都写着「Prefer that default」,round prompt 把 `compose_batch(n=48)`
   写死、参数位上没有 `exploit_ratio`;
2. `_enforce_exploit_floor` 恰好只禁止残差该触发的「调低利用比」方向,后半程区间为空集;
3. `exploit_ratio` 是标量,**没有任何取值能表达「别选带 N21D 的候选」**(根因);
4. `test_composed_batch()` 无参数,连手工剔除都做不到。

本文件钉住 v0.9 的三处改造,以及**最要紧的那条**:v0.8 路径必须逐字节不变,
否则新旧契约的对照臂就不再是对照。
"""
from __future__ import annotations

import numpy as np
import pytest

from agent.auto_researcher import (
    _BACKTRACK_SEMI_NOTE,
    _V05_ACQUISITION_PARAGRAPH,
    _V06_ACQUISITION_PARAGRAPH,
    _V09_ACQUISITION_PARAGRAPH,
    _apply_exploit_floor,
    _exclude_motif_indices,
    compose_system_prompt,
    SYSTEM_PROMPT,
)
from events.reflexion import RoundReflexion, format_reflexion_prompt

WT = "AAAAAAAA"


# ---- 阴性对照:v0.8 路径逐字节不变 ------------------------------------------------

@pytest.mark.parametrize("contract", [None, "v08"])
def test_v08_prompts_are_byte_identical_under_the_new_parameter(contract):
    """新增 contract 参数不得移动任何已发布配置——否则对照臂不再是对照。"""
    v06_body = SYSTEM_PROMPT.replace(_V05_ACQUISITION_PARAGRAPH, _V06_ACQUISITION_PARAGRAPH)
    assert compose_system_prompt(None, None, contract) == SYSTEM_PROMPT
    assert compose_system_prompt("semi", None, contract) == v06_body + _BACKTRACK_SEMI_NOTE
    assert compose_system_prompt("semi", "v05", contract) == SYSTEM_PROMPT + _BACKTRACK_SEMI_NOTE
    assert compose_system_prompt("semi", "v06", contract) == v06_body + _BACKTRACK_SEMI_NOTE


def test_v08_floor_behaviour_is_untouched():
    # 与 test_auto_researcher_compose.py 的既有断言一致,enforced=True 即老行为
    assert _apply_exploit_floor(0.4, 0.5, 5, 6, enforced=True) == (0.9, 0.9)
    assert _apply_exploit_floor(0.4, 0.9, 1, 6, enforced=True) == (0.8, 0.8)


# ---- ① 提示词中性化 --------------------------------------------------------------

def test_v09_prompt_stops_discouraging_an_explicit_ratio():
    v09 = compose_system_prompt("semi", None, "v09")
    assert _V09_ACQUISITION_PARAGRAPH in v09
    # 「Prefer that default」正是 v0.8 里劝退 agent 的那句话
    assert "Prefer that default" not in v09
    assert "Prefer that default" in SYSTEM_PROMPT, "v0.5 原文必须保留,否则不可复现"
    # 新入口必须在提示词里被点名,否则 agent 不知道它存在
    assert "exclude_motifs" in v09
    # 其余条件不变:stall note 仍在,且仍在末尾
    assert v09.endswith(_BACKTRACK_SEMI_NOTE)


def test_v09_overrides_acquisition_so_the_contract_is_one_factor():
    # contract=v09 时两个采集档必须收敛到同一份提示词,否则 2×2 会变成 2×2×2
    assert compose_system_prompt("semi", "v05", "v09") == compose_system_prompt("semi", "v06", "v09")


# ---- ② 地板开关 ------------------------------------------------------------------

def test_v09_releases_the_floor_that_pins_the_dependent_variable():
    """v0.8 实测:CV 高时地板 0.80,末两轮 0.90,而默认值第 4 轮起就是 1.0。

    也就是说 agent 想「因为看到致死 motif 而多探索」在后半程**无法表达**。
    """
    # 老行为:请求 0.3 被抬到 0.9,agent 的意图被抹掉
    assert _apply_exploit_floor(0.3, 0.95, 5, 6, enforced=True) == (0.9, 0.9)
    # v0.9:请求原样通过,地板报 0.0
    assert _apply_exploit_floor(0.3, 0.95, 5, 6, enforced=False) == (0.3, 0.0)
    # 释放地板不等于改变默认:不传 ratio 时默认值本身没动(见 _default_exploit_ratio 的测试)
    assert _apply_exploit_floor(1.0, 0.95, 5, 6, enforced=False) == (1.0, 0.0)


# ---- ③ motif 排除入口(根因所在) --------------------------------------------------

def _toy_seqs():
    #            A0S   A1G   A2P
    return np.array([
        "SAAAAAAA",  # 0: A0S
        "AGAAAAAA",  # 1: A1G
        "SGAAAAAA",  # 2: A0S + A1G
        "AAPAAAAA",  # 3: A2P
        "AAAAAAAA",  # 4: wild type, no substitutions
    ])


def test_exclusion_drops_every_candidate_carrying_the_motif():
    kept, motifs = _exclude_motif_indices(_toy_seqs(), WT, range(5), ["A0S"])
    assert motifs == ["A0S"]
    assert kept == [1, 3, 4]  # 0 和 2 都带 A0S


def test_exclusion_is_a_union_not_an_intersection():
    kept, _ = _exclude_motif_indices(_toy_seqs(), WT, range(5), ["A0S", "A1G"])
    assert kept == [3, 4]  # 带任一 motif 的都要走


def test_exclusion_normalises_case_and_whitespace_and_dedupes():
    kept, motifs = _exclude_motif_indices(_toy_seqs(), WT, range(5), [" a0s ", "A0S"])
    assert motifs == ["A0S"] and kept == [1, 3, 4]


def test_exclusion_rejects_notation_it_cannot_honour():
    # 静默忽略一个写错的 motif = 假装排除了、实际没排除,比报错危险得多
    with pytest.raises(ValueError, match="zero-based position"):
        _exclude_motif_indices(_toy_seqs(), WT, range(5), ["N21"])
    with pytest.raises(ValueError, match="zero-based position"):
        _exclude_motif_indices(_toy_seqs(), WT, range(5), ["lethal ones"])


def test_empty_exclusion_is_a_no_op():
    kept, motifs = _exclude_motif_indices(_toy_seqs(), WT, range(5), [])
    assert kept == [0, 1, 2, 3, 4] and motifs == []


def test_exclusion_leaving_fewer_than_n_is_detectable_before_composing():
    """排除后候选不足 n 时,compose 层返回 exclusion_too_strict 而不是静默缩批。

    `_compose_batch_core` 是闭包(依赖 state/spec/gate_pass/rng 等九个自由变量),
    无法直接 import;但它那个分支的判定实质就是 `len(kept) < n`,而 kept 由本函数产出。
    所以这里钉住两件事:①不足的前提能被算出来;②真正危险的替代行为——让 compose
    在候选不足时照样返回一个短批次——确实会发生,因此那个 early return 是必需的。
    短批次在批次哈希上看起来像换了策略,实际只是候选集被排空了(auto_researcher.py:662-670)。
    """
    from agent.auto_researcher import _compose_batch_indices

    seqs = _toy_seqs()
    kept, motifs = _exclude_motif_indices(seqs, WT, range(5), ["A0S", "A1G"])
    assert kept == [3, 4] and motifs == ["A0S", "A1G"]

    n = 4
    assert len(kept) < n  # ① 前提成立:排除后只剩 2 条,少于请求的 4 条

    # ② 阳性对照:若不 early return,compose 会交出一个长度 2 的短批次而不报错
    rng = np.random.default_rng(0)
    mean = np.arange(len(seqs), dtype=float)
    var = np.ones(len(seqs))
    picks, _, _ = _compose_batch_indices(
        mean, var, eligible_indices=np.asarray(kept), exploit_ratio=1.0, n=n, rng=rng,
    )
    assert len(picks) < n, "短批次确实会被交出来,所以 exclusion_too_strict 这道闸不能省"


def test_exclusion_respects_a_prefiltered_eligible_set():
    # gate 已经筛过一轮,排除必须在其结果之上做,不能悄悄把 gate 拒掉的候选放回来
    kept, _ = _exclude_motif_indices(_toy_seqs(), WT, [1, 2, 3], ["A1G"])
    assert kept == [3]


def test_scalar_ratio_cannot_express_what_exclusion_expresses():
    """根因的可执行形式:任何 exploit_ratio 都无法表达「别选带 A0S 的」。

    这条测试不验证实现,验证的是**为什么需要这个实现**——它是 v0.9 存在的理由。
    """
    from agent.auto_researcher import _compose_batch_indices
    seqs = _toy_seqs()
    mean = np.array([9.0, 8.0, 7.0, 6.0, 5.0])  # 带 A0S 的恰好预测最高
    carriers = {i for i, s in enumerate(seqs) if s[0] == "S"}
    for ratio in np.linspace(0.0, 1.0, 11):
        picks, _, _ = _compose_batch_indices(
            mean, np.ones(5), eligible_indices=range(5),
            exploit_ratio=float(ratio), n=3, rng=np.random.default_rng(42),
        )
        assert carriers & set(picks), f"exploit_ratio={ratio} 竟然排除了 A0S —— 前提不成立"
    # 而排除入口一步做到
    kept, _ = _exclude_motif_indices(seqs, WT, range(5), ["A0S"])
    assert not (carriers & set(kept))


# ---- ④ 注入卡片指向新入口 -----------------------------------------------------------

def _card(**kw):
    return RoundReflexion(round_id=1, overestimated_fails=[], underestimated_hits=[],
                          motif_summary=[], **kw)


def test_v08_reflexion_card_is_byte_identical_by_default():
    text = format_reflexion_prompt(_card())
    assert text.endswith(
        "ACTION CONSTRAINT: before selecting this round, explicitly account for the lethal "
        "motifs above and avoid carrying them forward unless current measured evidence justifies it."
    )
    assert "exclude_motifs" not in text


def test_v09_reflexion_card_names_the_actionable_entry_point():
    text = format_reflexion_prompt(_card(), exclusion_entrypoint=True)
    assert "compose_batch(exclude_motifs=[...])" in text
    # 仍然要求它说明**故意保留**了哪些 —— 否则「全排除」是个廉价的通关姿势
    assert "deliberately kept" in text
    # 卡片主体(残差事实)不因开关而变
    assert "Residual definition: measured_fitness - nomination-time predicted_mean." in text
