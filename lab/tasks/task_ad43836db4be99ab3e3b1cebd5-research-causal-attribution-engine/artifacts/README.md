# Causal attribution design artifacts

The blueprint is a research design, not an implemented autonomous engine.

- `causal-attribution-engine-blueprint.md`: Chinese engineering blueprint, causal protocols, 13-state machine, contracts, sandbox and recovery design.
- `source-manifest.json`: content hashes for the four required readings and governance/task context.
- `contracts.schema.json`: named Pydantic-generated schema documents; select the named model, rather than treating the outer mapping as one JSON Schema.
- `verify_blueprint.py`: static graph and contract verification. Run `python verify_blueprint.py` with Pydantic 2.13.5; regenerates schemas and `verification.json`.
- `verification.json`: final static results. No runtime isolation, fault injection, statistical calibration or biological experiment was executed.

Canonical task package: `lab/tasks/task_ad43836db4be99ab3e3b1cebd5-research-causal-attribution-engine/artifacts/`.
The final report there is named `verification-final.json`; the original `verification.json` remains as an immutable earlier result, before the documentation-only correction of the installed CLI closeout route.

Governance evidence: `F-9648FFB0` (static checks), `F-F84D79D7` (retrospective answer leakage in the required source).
Decision proposal: `dec_956152B50EA1B4EC050D9C7FAF`, validated with both claims evidenced; not accepted and not a deployment authorization.
