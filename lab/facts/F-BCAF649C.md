# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-BCAF649C

- Statement: artifact 交付锚点(Commit=none)会使 ci 与 code-doc-reconciliation 两道完成门不被要求:本会话三个进入 done 的任务(e2eab881、8e29be09、d5e9455a)的 accepted 执行全部显示 Checker witnesses=pending、Code-doc witness=pending,门链却判通过;而唯一使用 git commit 锚点的 task_feb731c779788be5bfff65e979 声明 completion gates=ci,code-doc-reconciliation 并确实持有两个真 witness(ci/op_261c0b69…、code-doc-b2b4592775827398)。据此两点:①本仓 ci 门至今没有一次端到端在完成链上被实际验证通过;②把已声明这两道门的任务改用 artifact 锚点,等于脱掉它已挣到的 witness,属于绕门,不得作为收口手段。
- Evidence source: executions: e2eab881/8e29be09/d5e9455a 三个 done 任务均 Commit=none (artifact delivery) 且 Checker witnesses=pending、Code-doc witness=pending; 对照 task_feb731c779788be5bfff65e979 的 exe_88c8c3ac08cfe7d768f0427de1 Commit=646ad491646005cc98dc48353fcfdcbc7b73656f 持有 ci/op_261c0b6950c04a214ae766fb058346b7b641d9aa596c367f968357324afb7f0f 与 code-doc-b2b4592775827398; ha task show feb731c7 completion gates: ci, code-doc-reconciliation
- Observed at: 2026-09-14T11:47:01.348Z
- Confidence: high
- State: standing

