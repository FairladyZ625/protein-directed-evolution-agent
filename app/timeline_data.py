"""Pure, read-only adapters. No Streamlit, model fitting or campaign execution."""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

EVIDENCE = Path(__file__).parent / 'timeline_evidence'
VERSIONS = {
    'v0.1': ('自由探索', '高方差，不等于高价值', '自由工具调用追逐预测不确定性，高阶突变将探索引向失活区域。', '为候选空间引入物理化学约束。'),
    'v0.2': ('物理门禁', '先守住可行边界', 'HD≤4 与 BLOSUM62 双门禁恢复发现效率，但仍停在加性模型的前沿。', '瓶颈是否来自表征与代理模型，而非决策？'),
    'v0.3': ('代理诊断', '看不见的峰', '六组表征 × 代理扫描均未将真峰排入 288 预算范围。此代未运行 LLM campaign。', '显式建模残基之间的成对交互。'),
    'v0.4': ('上位感知', '让交互进入模型', '成对代理让候选池峰的门内排名从 2776 提升至 429；LLM 新发现最高 7.829。', '高置信度模型下，探索配额究竟付出了多少代价？'),
    'v0.5': ('批次退火', '探索配额的代价', '小批量与自适应配额改变早期观测集合，最终最高 6.5309：这是一次阴性结果。', '将固定探索分配转向状态化调度与回溯实验。'),
    'v0.7': ('交替参考', '一次跨峰的实证', 'alternating · seed42 在第 4 个测定批次命中候选池峰 8.4162。原始日志标记为确定性参考运行。', '参考调度证明该路径可达；自主停滞回溯的因果归因仍需独立消融。'),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def parse_events(path: Path) -> list[dict]:
    """Reject malformed or tampered streams, including an invalid final record."""
    events, previous = [], ''
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip(): continue
        try:
            event = json.loads(line)
            body = {k: event[k] for k in ('seq', 'ts', 'event_type', 'round_id', 'strategy', 'actor', 'payload')}
            digest = hashlib.sha256((previous + json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True)).encode()).hexdigest()
            if event['seq'] != len(events) + 1 or event['prev_hash'] != previous or event['hash'] != digest:
                raise ValueError('hash chain mismatch')
            if not isinstance(event['payload'], dict): raise ValueError('payload must be an object')
            previous = digest
            events.append(event)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'{path.name}: line {number}: {exc}') from exc
    if not events: raise ValueError(f'{path.name}: empty event stream')
    return events


def load_version(version: str, root: Path = EVIDENCE) -> dict:
    if version not in VERSIONS: raise ValueError(f'Unknown version: {version}')
    if version == 'v0.3':
        return {'metrics': None, 'events': [], 'scan': read_json(root / version / 'surrogate_scan.json')}
    return {'metrics': read_json(root / version / 'agentic.metrics.json'),
            'events': parse_events(root / version / 'agentic.events.jsonl')}


def indicators(metrics: dict, baseline: float) -> dict:
    summary = metrics['summary']
    best = summary['final_cum_top10_max']
    strong = summary['final_cum_n_strong']
    spent = metrics['budget_spent']
    return {'best': best, 'strong': strong, 'spent': spent,
            'rate': strong / spent if spent else None,
            'peak_round': next(r['round'] for r in metrics['rounds'] if r['cum_top10_max'] == best),
            'gap': baseline - best, 'gain': best - 7.5301}


def variants(metrics: dict) -> dict[str, dict]:
    result = {}
    for row in metrics['rounds']:
        for seq, fitness in row.get('top10', []):
            result.setdefault(seq, {'fitness': fitness, 'round': row['round']})
    return dict(sorted(result.items(), key=lambda pair: -pair[1]['fitness']))


def mutations(sequence: str, wt: str) -> list[dict]:
    if len(sequence) != len(wt):
        raise ValueError('长度与 WT 不同；不进行未经比对的位点或成对互作推断。')
    return [{'position': i, 'WT': a, 'variant': b, 'mutation': f'{a}{i}{b}'}
            for i, (a, b) in enumerate(zip(wt, sequence)) if a != b]


def pairwise_effects(sequence: str, wt: str, measured: dict) -> list[dict]:
    """Observed fitness epistasis on the WT background; never physical energy."""
    muts = mutations(sequence, wt)
    rows = []
    for a, b in itertools.combinations(muts, 2):
        def seq_for(items):
            s = list(wt)
            for item in items: s[item['position']] = item['variant']
            return ''.join(s)
        keys = [wt, seq_for([a]), seq_for([b]), seq_for([a, b])]
        vals = [measured.get(k) for k in keys]
        epsilon = vals[3] - vals[1] - vals[2] + vals[0] if all(v is not None for v in vals) else None
        rows.append({'pair': f"{a['mutation']} × {b['mutation']}", 'f(WT)': vals[0], 'f(i)': vals[1], 'f(j)': vals[2], 'f(ij)': vals[3], 'epsilon': epsilon})
    return rows
