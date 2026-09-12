"""Static design verification only; run with Python and pydantic==2.13.5.

Usage: python verify_blueprint.py
No production service, sandbox isolation or biological claims are tested.
"""
import hashlib
import json
import re
from pathlib import Path
from typing import get_args
import pydantic

ROOT = Path(__file__).resolve().parent
DOC = ROOT / 'causal-attribution-engine-blueprint.md'
body = DOC.read_text()
blocks = re.findall(r'```python\n(.*?)\n```', body, re.S)
assert len(blocks) == 1
namespace = {'__name__': 'blueprint_contracts'}
exec(compile(blocks[0], str(DOC), 'exec'), namespace)
classes = {k: v for k, v in namespace.items()
           if isinstance(v, type) and issubclass(v, pydantic.BaseModel)
           and k not in {'BaseModel', 'Contract'}}
schemas = {name: model.model_json_schema() for name, model in classes.items()}
(ROOT / 'contracts.schema.json').write_text(json.dumps(schemas, indent=2) + '\n')

state_block = next(b for b in re.findall(r'```mermaid\n(.*?)\n```', body, re.S)
                   if b.startswith('stateDiagram-v2'))
edges = re.findall(r'^\s*(\[\*\]|[A-Z]+) --> (\[\*\]|[A-Z]+)', state_block, re.M)
states = set(get_args(namespace['State']))
assert {v for edge in edges for v in edge} - {'[*]'} == states
adj = {s: set() for s in states}
for source, target in edges:
    if source != '[*]':
        adj[source].add(target)
def reachable(start):
    seen, pending = set(), [start]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(adj.get(node, set()) - seen)
    return seen
assert states <= reachable('OBSERVE')
assert all('[*]' in reachable(s) for s in states)
assert all(adj[s] for s in states - {'HALTED'})
assert adj['HALTED'] == {'[*]'}
assert all('ROLLBACK' in adj[s] for s in ['PREPARE', 'CANARY', 'COMMIT'])

pin = {'ref': 'example/snapshot', 'digest': 'a' * 64}
checks = []
def rejects(name, model, value):
    try:
        namespace[model].model_validate(value)
    except pydantic.ValidationError:
        checks.append(name)
    else:
        raise AssertionError(f'{name} was not rejected')

def node(name, seq, parents=()):
    return dict(id=name, sequence=seq, kind='observation', parents=parents,
                payload=pin, split='development', issuer='verifier', signature='example')

namespace['EvidenceDAG'].model_validate({'nodes': [node('a', 0), node('b', 1, ['a'])]})
rejects('cycle', 'EvidenceDAG', {'nodes': [node('a', 0, ['b']), node('b', 1, ['a'])]})
rejects('missing_parent', 'EvidenceDAG', {'nodes': [node('b', 1, ['missing'])]})
rejects('duplicate_node', 'EvidenceDAG', {'nodes': [node('a', 0), node('a', 1)]})
rejects('same_sequence_parent', 'EvidenceDAG', {'nodes': [node('a', 0), node('b', 0, ['a'])]})
rejects('nan', 'Metric', {'value': float('nan')})
rejects('infinity', 'Metric', {'value': float('inf')})
rejects('null_without_reason', 'Metric', {'value': None})
rejects('value_with_missing_reason', 'Metric', {'value': 2., 'unavailable_reason': 'missing'})
namespace['Metric'].model_validate({'value': None, 'unavailable_reason': 'no_replicates'})
rejects('negative_budget', 'Cost', dict(assays=-1, cpu_seconds=0, gpu_seconds=0, tokens=0, money=0))
rejects('invalid_digest', 'Pin', dict(ref='x', digest='bad'))
rejects('extra_field', 'Pin', dict(**pin, secret='unexpected'))
rejects('invalid_interval', 'Estimate', dict(value=2., lower=3., upper=4., method=pin,
                                            independent_blocks=1, alpha=.05))
cert = dict(candidate=pin, parent=pin, policy=pin, environment=pin, split_protocol=pin,
            evaluation_protocol=pin, result=pin, resource_receipt=pin,
            issued_unix_ms=100, expires_unix_ms=200, issuer='verifier', signature='example',
            verdict='pass')
namespace['Certificate'].model_validate(cert)
rejects('invalid_certificate_expiry_order', 'Certificate', dict(cert, expires_unix_ms=99))

assert body.count('```') % 2 == 0
assert all(token in body for token in ['prediction_direct', 'closed_loop_total',
    'factorial_interaction', 'UNKNOWN_SIDE_EFFECT', 'fencing_token', 'outbox',
    'noise_free', 'unidentified', 'Goodhart', 'Rollback Transaction'])
report = {
    'scope': 'Static document/schema validation; not runtime or biological validation',
    'blueprint_sha256': hashlib.sha256(DOC.read_bytes()).hexdigest(),
    'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'pydantic_version': pydantic.__version__,
    'schema_models': sorted(classes),
    'states': sorted(states), 'state_count': len(states), 'edge_count': len(edges),
    'all_states_reachable': True, 'all_states_have_terminal_path': True,
    'transaction_states_have_rollback_edges': True,
    'negative_cases_passed': checks,
    'not_executed': ['Mermaid rendering', 'runtime fault injection', 'sandbox escape tests',
                     'statistical calibration', 'protein landscape experiments',
                     'signature and ACL enforcement', 'independent execution review'],
}
(ROOT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
