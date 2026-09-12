#!/usr/bin/env python3
"""产出 Harness 的 CI 观测工件(ci-run-artifact/v1)。

Harness 的任务完成门要求一条「CI checker 见证」:main 分支上一次成功的 workflow
运行,并且该运行上传了名为 ``ci-observation-*`` 的工件。判定 pass/fail 只看 GitHub
运行本身的 conclusion,与工件里的 tests/gates 内容无关,因此这两个字段允许为空数组。

真正要对上的是 ``run`` 段,否则 daemon 侧的 verification 为 null、直接判 invalid_proof:

- ``run.runId``  必须是 ``${GITHUB_RUN_ID}.${GITHUB_RUN_ATTEMPT}``
- ``run.sha``    必须等于该运行的 headSha(即 ``GITHUB_SHA``)
- ``run.branch`` 必须是 ``main``,且该运行的 headBranch 也是 main
- 该 workflow 的 ``name:`` 必须在 ``settings.ci.workflows`` 里(本仓为 ``ci``)

用法(CI 内):
    python tools/write_ci_observation.py
输出路径可用 HARNESS_CI_OBSERVATION_OUTPUT 覆盖,默认 tmp/ci-observation/observation.json。
"""

from __future__ import annotations

import json
import os
import pathlib
import time


def _run_id() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        return f"local-{int(time.time() * 1000)}"
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    return f"{run_id}.{attempt}" if attempt else run_id


def _optional_positive_int(value: str | None) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def build_artifact() -> dict:
    started_ms = _optional_positive_int(os.environ.get("HARNESS_CI_JOB_STARTED_MS"))
    started_ms = started_ms if started_ms is not None else int(time.time() * 1000)
    return {
        "schema": "ci-run-artifact/v1",
        "run": {
            "runId": _run_id(),
            "sha": os.environ.get("GITHUB_SHA", "local"),
            # pull_request 事件下 GITHUB_REF_NAME 是 "<n>/merge",用 HEAD_REF 更准。
            "branch": os.environ.get("GITHUB_HEAD_REF")
            or os.environ.get("GITHUB_REF_NAME")
            or "local",
            "prNumber": _optional_positive_int(os.environ.get("HARNESS_PR_NUMBER")),
            "job": os.environ.get("GITHUB_JOB", "local"),
            "wallclockMs": max(0, int(time.time() * 1000) - started_ms),
            "runner": os.environ.get("RUNNER_NAME")
            or os.environ.get("RUNNER_OS")
            or "local",
        },
        # 判定只看运行的 conclusion;留空是被读取侧显式接受的形状(daemon 自己合成的
        # ledger-publication 观测同样是空数组)。本仓是 pytest,不产 vitest 结构。
        "tests": [],
        "gates": [],
    }


def main() -> None:
    output = pathlib.Path(
        os.environ.get("HARNESS_CI_OBSERVATION_OUTPUT", "tmp/ci-observation/observation.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_artifact(), indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
