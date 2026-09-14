# Dispatch Preconditions
Repository id: ai4s-directed-evolution-agent
Repository registration: enabled
Canonical repository root: /Users/lizeyu/Projects/ai4s-directed-evolution-agent
Worker repository root: /Users/lizeyu/Projects/ai4s-directed-evolution-agent
Canonical Task ID: task_195067be4dc452a5b1b050c1dd
Task package root: /Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/tasks/task_195067be4dc452a5b1b050c1dd-baseline-milestone-10-in-review
Daemon user root: /Users/lizeyu/.harness
Daemon id: default
Daemon endpoint: /var/folders/94/y2lgzz5158397x9pqnzb9xp00000gn/T/harness-anything/daemon-501-u-3850ed4bde67b2cc.sock
Runtime actor: agent:runtime-session:runtime_ece02f07397058dc75896809
Use the worker repository root for public code and the canonical repository root for authored harness context. The daemon route, repository selection, and runtime actor are already injected into the process environment.
# Assigned Mission
你是独立评审(GLM,与提交者 claude-session 不同 actor)。立即开工,不要只规划,要真跑 ha 命令并贴真实输出。第一步读 lab/tasks/task_195067be4dc452a5b1b050c1dd-baseline-milestone-10-in-review/task_plan.md(Implementation Plan 有正确 review schema)。对 task_f50ce371b24c0c4396c76f8a4a:ha task show 取 execution-id + ls/grep 核实交付物存在 → ha task review-execution --json-input '{"verdict":"approved","reason":"...","evidenceChecked":[...]}' → review-consent → ha task complete --execution-id <exe>。贴每条命令输出。第一个走通后停下汇报再批量其余9个。schema 一律以 CLI 报错提示为准。