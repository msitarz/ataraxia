# SPDX-License-Identifier: Apache-2.0
"""Codex adapter wiring through the typed runner boundaries."""

from dataclasses import replace
from pathlib import Path
import subprocess
import tomllib

import pytest

from script.eval.model import (
    AttemptEvidence,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    PreparedEvidence,
    RetryAssessment,
    SeparatorOption,
    SourceSnapshot,
)
from script.eval.runner import CliBinding
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
    CodexOutcomeClassifier,
)
from script.process_supervisor import (
    AttemptCancelled,
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
)

type BuilderInputs = tuple[
    FrozenPlan, PlannedCall, CliBinding, Path | None, HarnessConfig
]


def assert_builder_inputs(
    received: BuilderInputs,
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    staged_path: Path | None,
    config: HarnessConfig,
) -> None:
    """Check the exact objects forwarded by both request-building steps."""
    assert received[0] is plan
    assert received[1] is call
    assert received[2] is binding
    assert received[3] is staged_path
    assert received[4] is config


def configuration(**overrides: object) -> HarnessConfig:
    """Build a valid execution configuration with explicit limits."""
    values: dict[str, object] = {
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("model-a",),
        "efforts": ("low",),
        "concurrency": 1,
        "output_directory": Path("out"),
        "dry_run": False,
        "timeout_seconds": 12.0,
        "cleanup_timeout_seconds": 5.0,
        "grace_seconds": 1.0,
        "output_limit_bytes": 4096,
        "instructions_file_path": Path("/repo/INSTRUCTIONS.md"),
    }
    values.update(overrides)
    return HarnessConfig.model_validate(values)


def plan_and_inputs(
    *, with_instructions: bool = True
) -> tuple[HarnessConfig, FrozenPlan, PlannedCall, CliBinding, PreparedEvidence]:
    """Create frozen inputs with distinct original and staged instruction paths."""
    instruction_path = Path("/repo/INSTRUCTIONS.md") if with_instructions else None
    config = configuration(instructions_file_path=instruction_path)
    call = PlannedCall(
        position=0,
        context_indices=(),
        model="model-a",
        effort="low",
        prompt_sha256="a" * 64,
        prompt=b"frozen prompt bytes",
    )
    plan = FrozenPlan(
        run_id="run-1",
        configuration=config,
        repository_root=Path("/repo"),
        head_commit="b" * 40,
        snapshots=(),
        boundary_bytes=(),
        instructions_file=InstructionsSnapshot(
            repository_path="INSTRUCTIONS.md",
            commit_blob_sha="c" * 40,
            content_sha256="d" * 64,
            content=b"frozen system instructions",
        )
        if with_instructions
        else None,
        calls=(call,),
    )
    binding = CliBinding(
        executable_path=Path("/bin/codex"),
        cli_version="codex version",
        runner_version="0.1.0",
        effective_settings=(("approval_policy", "never"),),
        quota_scope=None,
    )
    evidence = PreparedEvidence(
        output_directory=Path("/repo/out"),
        plan_artifact=Path("/repo/out/plan.json"),
        model_instructions_file=(
            Path("/repo/out/instructions.bin") if with_instructions else None
        ),
    )
    return config, plan, call, binding, evidence


def settled_evidence(config: HarnessConfig) -> AttemptEvidence:
    """Build one settled supervisor evidence value for classifier tests."""
    request = AttemptRequest(
        argv=("/bin/codex",),
        cwd=Path("/repo"),
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )
    return AttemptEvidence(
        control_flow="returned",
        outcome=None,
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc="2026-10-27T00:00:00Z",
        ended_at_utc="2026-10-27T00:00:01Z",
        usage_telemetry=None,
    )


def test_binding_uses_resolved_path_for_probe_and_settings_in_order() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    executable_path = Path("/verified/codex")
    events: list[str] = []
    probed_paths: list[Path] = []
    settings_inputs: list[tuple[Path, HarnessConfig]] = []

    def resolve_executable() -> Path:
        events.append("resolve")
        return executable_path

    def probe_version(path: Path) -> str:
        events.append("version")
        probed_paths.append(path)
        return "codex 1.2.3"

    settings = (("approval_policy", "never"),)

    def read_settings(
        path: Path, received_config: HarnessConfig
    ) -> tuple[tuple[str, str], ...]:
        events.append("settings")
        settings_inputs.append((path, received_config))
        return settings

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
        read_effective_settings=read_settings,
        runner_version=lambda: "0.1.0",
    )

    # When
    binding = resolver.resolve(config)

    # Then
    assert binding == CliBinding(
        executable_path=executable_path,
        cli_version="codex 1.2.3",
        runner_version="0.1.0",
        effective_settings=settings,
        quota_scope=None,
    )
    assert binding.executable_path is executable_path
    assert binding.effective_settings is settings
    assert events == ["resolve", "version", "settings"]
    assert probed_paths == [executable_path]
    assert probed_paths[0] is executable_path
    assert settings_inputs[0][0] is executable_path
    assert settings_inputs[0][1] is config


def test_binding_propagates_probe_failure_without_reading_settings_or_retrying() -> (
    None
):
    # Given
    config, _, _, _, _ = plan_and_inputs()
    failure = RuntimeError("version probe failed")
    events: list[str] = []
    probed_paths: list[Path] = []

    def resolve_executable() -> Path:
        events.append("resolve")
        return Path("/verified/codex")

    def probe_version(path: Path) -> str:
        events.append("probe")
        probed_paths.append(path)
        raise failure

    def read_settings(
        path: Path, received_config: HarnessConfig
    ) -> tuple[tuple[str, str], ...]:
        events.append("settings")
        raise AssertionError("settings must not be read after a failed probe")

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
        read_effective_settings=read_settings,
        runner_version=lambda: "0.1.0",
    )

    # When
    with pytest.raises(RuntimeError, match="version probe failed") as raised:
        resolver.resolve(config)

    # Then
    assert raised.value is failure
    assert events == ["resolve", "probe"]
    assert probed_paths == [Path("/verified/codex")]


def test_request_builder_forwards_frozen_context_and_staged_path_in_order() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    staged_path = evidence.model_instructions_file
    events: list[str] = []
    observed_inputs: list[BuilderInputs] = []
    request = AttemptRequest(
        argv=("/bin/codex", "--stubbed"),
        cwd=plan.repository_root,
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )

    def effective_call_id(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        events.append("identity")
        observed_inputs.append((
            received_plan,
            received_call,
            received_binding,
            received_staged_path,
            received_config,
        ))
        return "call-1"

    def build_attempt_request(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        events.append("request")
        observed_inputs.append((
            received_plan,
            received_call,
            received_binding,
            received_staged_path,
            received_config,
        ))
        return request

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)

    # Then
    assert effective_call.run_id is plan.run_id
    assert effective_call.call_id == "call-1"
    assert effective_call.planned_call is call
    assert effective_call.request is request
    assert events == ["identity", "request"]
    assert len(observed_inputs) == 2
    assert_builder_inputs(observed_inputs[0], plan, call, binding, staged_path, config)
    assert_builder_inputs(observed_inputs[1], plan, call, binding, staged_path, config)
    assert observed_inputs[0][1].prompt is call.prompt
    assert observed_inputs[0][3] is staged_path
    assert observed_inputs[1][3] is staged_path


def test_request_builder_forwards_no_instruction_path_when_unconfigured() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    request = AttemptRequest(
        argv=("/bin/codex",),
        cwd=plan.repository_root,
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )
    identity_paths: list[Path | None] = []
    request_paths: list[Path | None] = []

    def effective_call_id(
        frozen_plan: FrozenPlan,
        planned_call: PlannedCall,
        cli_binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        identity_paths.append(staged_path)
        return "call-with-default-instructions"

    def build_attempt_request(
        frozen_plan: FrozenPlan,
        planned_call: PlannedCall,
        cli_binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        request_paths.append(staged_path)
        return request

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)

    # Then
    assert plan.instructions_file is None
    assert config.instructions_file_path is None
    assert evidence.model_instructions_file is None
    assert identity_paths == [None]
    assert request_paths == [None]
    assert request.argv == ("/bin/codex",)
    assert effective_call.call_id == "call-with-default-instructions"
    assert effective_call.request is request


def test_request_preserves_prompt_and_escapes_staged_path_as_toml() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    unusual_path = Path('/repo/notes 😀 "draft"\\final\x01\x7f.md')
    staged_evidence = PreparedEvidence(
        output_directory=evidence.output_directory,
        plan_artifact=evidence.plan_artifact,
        model_instructions_file=unusual_path,
    )
    leading_hyphen_call = call.model_copy(update={"prompt": b"-literal prompt"})
    builder = CodexAttemptRequestBuilder()

    # When
    request = builder.build(
        plan, leading_hyphen_call, binding, staged_evidence, config
    ).request

    # Then
    assert request.argv[-2:] == ("--", "-literal prompt")
    settings = {
        request.argv[index + 1].split("=", 1)[0]: tomllib.loads(
            request.argv[index + 1]
        )[request.argv[index + 1].split("=", 1)[0]]
        for index, argument in enumerate(request.argv[:-1])
        if argument == "-c"
    }
    assert settings["model_instructions_file"] == str(unusual_path)
    assert settings["model_reasoning_effort"] == "low"
    assert settings["approval_policy"] == "never"
    assert request.cwd == plan.repository_root
    assert request.stdin == "devnull"
    assert request.timeout_seconds == config.timeout_seconds
    assert request.cleanup_timeout_seconds == config.cleanup_timeout_seconds
    assert request.output_limit_bytes == config.output_limit_bytes


def test_request_refuses_nul_in_argv_prompt() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    nul_prompt = call.model_copy(update={"prompt": b"before\x00after"})

    # When
    with pytest.raises(ValueError) as raised:
        CodexAttemptRequestBuilder().build(plan, nul_prompt, binding, evidence, config)

    # Then
    assert str(raised.value) == "Codex argv prompts cannot contain NUL characters"


def test_effective_identity_ignores_run_and_position_but_tracks_frozen_inputs() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    source = SourceSnapshot(
        directory_position=0,
        repository_path="context/a.txt",
        commit_blob_sha="e" * 40,
        content_sha256="f" * 64,
        content=b"frozen source",
    )
    call = call.model_copy(update={"context_indices": (0,)})
    plan = plan.model_copy(update={"snapshots": (source,)})
    builder = CodexAttemptRequestBuilder()
    second_position = call.model_copy(update={"position": 1})
    second_run = plan.model_copy(update={"run_id": "run-2"})
    changed_prompt = call.model_copy(update={"prompt": b"changed prompt"})

    # When
    first_identity = builder.build(plan, call, binding, evidence, config).call_id
    repeated_identity = builder.build(
        second_run, second_position, binding, evidence, config
    ).call_id
    changed_identity = builder.build(
        plan, changed_prompt, binding, evidence, config
    ).call_id

    # Then
    assert repeated_identity == first_identity
    assert changed_identity != first_identity


def test_effective_identity_tracks_context_and_explicit_separator_settings() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    source = SourceSnapshot(
        directory_position=0,
        repository_path="context/a.txt",
        commit_blob_sha="e" * 40,
        content_sha256="f" * 64,
        content=b"frozen source",
    )
    call = call.model_copy(update={"context_indices": (0,)})
    plan = plan.model_copy(update={"snapshots": (source,)})
    changed_source = source.model_copy(update={"content": b"updated source"})
    changed_plan_source = plan.model_copy(update={"snapshots": (changed_source,)})
    changed_separator = plan.model_copy(update={"boundary_bytes": (b"\n",)})
    second_source = source.model_copy(
        update={
            "directory_position": 2,
            "repository_path": "context-b/b.txt",
            "content": b"second source",
        }
    )
    omitted_separator_config = configuration(
        ordered_options=(
            DirectoryOption(position=0, path=Path("context-a")),
            DirectoryOption(position=2, path=Path("context-b")),
        )
    )
    explicit_separator_config = configuration(
        ordered_options=(
            DirectoryOption(position=0, path=Path("context-a")),
            SeparatorOption(position=1, value="\\n\\n"),
            DirectoryOption(position=2, path=Path("context-b")),
        )
    )
    two_context_call = call.model_copy(update={"context_indices": (0, 1)})
    omitted_separator_plan = plan.model_copy(
        update={
            "configuration": omitted_separator_config,
            "snapshots": (source, second_source),
            "boundary_bytes": (b"\n\n",),
        }
    )
    explicit_separator_plan = omitted_separator_plan.model_copy(
        update={"configuration": explicit_separator_config}
    )
    builder = CodexAttemptRequestBuilder()

    # When
    original = builder.build(plan, call, binding, evidence, config).call_id
    context_variant = builder.build(
        changed_plan_source, call, binding, evidence, config
    ).call_id
    separator_variant = builder.build(
        changed_separator, call, binding, evidence, config
    ).call_id
    omitted_separator_identity = builder.build(
        omitted_separator_plan, two_context_call, binding, evidence, config
    ).call_id
    explicit_separator_identity = builder.build(
        explicit_separator_plan, two_context_call, binding, evidence, config
    ).call_id

    # Then
    assert context_variant != original
    assert separator_variant != original
    assert explicit_separator_identity != omitted_separator_identity


def test_effective_identity_tracks_frozen_instruction_bytes() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    changed_instructions = InstructionsSnapshot(
        repository_path="INSTRUCTIONS.md",
        commit_blob_sha="c" * 40,
        content_sha256="1" * 64,
        content=b"updated instructions",
    )
    changed_plan = plan.model_copy(update={"instructions_file": changed_instructions})
    builder = CodexAttemptRequestBuilder()

    # When
    original = builder.build(plan, call, binding, evidence, config).call_id
    changed = builder.build(changed_plan, call, binding, evidence, config).call_id

    # Then
    assert changed != original


def test_effective_identity_tracks_model_effort_and_cli_binding() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    builder = CodexAttemptRequestBuilder()
    changed_model = call.model_copy(update={"model": "model-b"})
    changed_effort = call.model_copy(update={"effort": "high"})
    changed_path = replace(binding, executable_path=Path("/opt/codex"))
    changed_version = replace(binding, cli_version="codex 2.0")

    # When
    original = builder.build(plan, call, binding, evidence, config).call_id
    model_variant = builder.build(
        plan, changed_model, binding, evidence, config
    ).call_id
    effort_variant = builder.build(
        plan, changed_effort, binding, evidence, config
    ).call_id
    path_variant = builder.build(plan, call, changed_path, evidence, config).call_id
    version_variant = builder.build(
        plan, call, changed_version, evidence, config
    ).call_id

    # Then
    assert model_variant != original
    assert effort_variant != original
    assert path_variant != original
    assert version_variant != original


def test_effective_identity_tracks_binding_settings_but_not_run_policy() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    builder = CodexAttemptRequestBuilder()
    changed_settings = replace(
        binding,
        effective_settings=(("effective_model_reasoning_effort", "high"),),
    )
    settings_binding = replace(
        binding,
        effective_settings=(("z-setting", None), ("a-setting", "known")),
    )
    reordered_settings_binding = replace(
        settings_binding,
        effective_settings=tuple(reversed(settings_binding.effective_settings)),
    )
    changed_output = config.model_copy(
        update={"output_directory": Path("other-output")}
    )
    changed_policy = config.model_copy(
        update={
            "concurrency": 3,
            "retry_limit": 2,
            "capacity_retry_limit": 1,
            "capacity_backoff_base_seconds": 1.0,
            "capacity_backoff_cap_seconds": 2.0,
        }
    )

    # When
    original = builder.build(plan, call, binding, evidence, config).call_id
    setting_variant = builder.build(
        plan, call, changed_settings, evidence, config
    ).call_id
    settings_identity = builder.build(
        plan, call, settings_binding, evidence, config
    ).call_id
    reordered_settings_identity = builder.build(
        plan, call, reordered_settings_binding, evidence, config
    ).call_id
    policy_variant = builder.build(
        plan, call, binding, evidence, changed_policy
    ).call_id
    output_variant = builder.build(
        plan, call, binding, evidence, changed_output
    ).call_id
    changed_stage = PreparedEvidence(
        output_directory=Path("different-stage"),
        plan_artifact=Path("different-stage/plan.json"),
        model_instructions_file=None,
    )
    stage_variant = builder.build(plan, call, binding, changed_stage, config).call_id

    # Then
    assert setting_variant != original
    assert reordered_settings_identity == settings_identity
    assert policy_variant == original
    assert output_variant == original
    assert stage_variant == original


def test_classifier_confirms_absence_only_for_supervisor_not_started_evidence() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs(with_instructions=False)
    evidence = settled_evidence(config)
    not_started = InfrastructureFailure(
        AttemptObservation(
            output=CapturedOutput(b"", b""),
            elapsed_seconds=0.0,
            cleanup=CleanupEvidence("not_started", (), "not_started", None),
        ),
        exit_status=None,
        error_type="FileNotFoundError",
        diagnostic="Codex could not be launched",
    )
    evidence = AttemptEvidence(
        control_flow="returned",
        outcome=not_started,
        error_type=None,
        diagnostic=None,
        request=evidence.request,
        started_at_utc=evidence.started_at_utc,
        ended_at_utc=evidence.ended_at_utc,
        usage_telemetry=None,
    )
    classifier = CodexOutcomeClassifier()

    # When
    assessment = classifier.assess(evidence)

    # Then
    assert assessment.retry_class == "infrastructure"
    assert assessment.no_result_basis == "confident_absence"
    assert assessment.classification_basis == (
        "supervisor confirmed no process was launched"
    )


def classifier_scenario_evidence(
    scenario: str, base: AttemptEvidence
) -> AttemptEvidence:
    """Build one synthetic supervisor outcome for a classifier scenario."""
    observation = AttemptObservation(
        output=CapturedOutput(
            b"capacity reached" if scenario == "capacity-like-output" else b"",
            b"quota exhausted" if scenario == "quota-like-output" else b"",
        ),
        elapsed_seconds=1.0,
        cleanup=CleanupEvidence("owned", (), "reaped", None),
    )
    outcome = base.outcome
    control_flow = "returned"
    if scenario == "completed-nonzero":
        outcome = Completed(observation, 1)
    elif scenario in {"capacity-like-output", "quota-like-output"}:
        outcome = Completed(observation, 0)
    elif scenario == "cancelled":
        outcome = AttemptCancelled(observation, -15)
        control_flow = "cancelled"
    elif scenario == "timeout":
        outcome = TimedOut(observation, -9)
    elif scenario == "output-overflow":
        outcome = OutputLimitExceeded(observation, -9)
    elif scenario == "launched-infrastructure":
        outcome = InfrastructureFailure(
            observation, 1, "OSError", "failure after launch"
        )
    elif scenario == "uncertain-acquisition":
        outcome = None
        control_flow = "raised"
    evidence = replace(base, outcome=outcome, control_flow=control_flow)

    return evidence


@pytest.mark.parametrize(
    "scenario",
    (
        "completed-zero",
        "completed-nonzero",
        "cancelled",
        "timeout",
        "output-overflow",
        "launched-infrastructure",
        "uncertain-acquisition",
        "capacity-like-output",
        "quota-like-output",
    ),
)
def test_classifier_keeps_nonconfirmed_outcomes_unknown(scenario: str) -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs(with_instructions=False)
    evidence = classifier_scenario_evidence(scenario, settled_evidence(config))
    classifier = CodexOutcomeClassifier()

    # When
    assessment = classifier.assess(evidence)

    # Then
    assert assessment.retry_class == "unknown"
    assert assessment.no_result_basis == "present_or_unknown"


def test_request_builder_propagates_identity_failure_without_request_retry() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    failure = RuntimeError("identity unavailable")
    events: list[str] = []

    def effective_call_id(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        events.append("identity")
        raise failure

    def build_attempt_request(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        events.append("request")
        raise AssertionError("request must not be built after identity failure")

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    with pytest.raises(RuntimeError, match="identity unavailable") as raised:
        builder.build(plan, call, binding, evidence, config)

    # Then
    assert raised.value is failure
    assert events == ["identity"]


def test_outcome_classifier_forwards_only_one_settled_evidence_value() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    evidence = settled_evidence(config)
    assessment = RetryAssessment(
        retry_class="unknown",
        classification_basis=None,
        no_result_basis="present_or_unknown",
        diagnostic="Codex classifier contract is not verified",
    )
    calls: list[AttemptEvidence] = []

    def assess_settled_evidence(received: AttemptEvidence) -> RetryAssessment:
        calls.append(received)
        return assessment

    classifier = CodexOutcomeClassifier(assess_settled_evidence=assess_settled_evidence)

    # When
    result = classifier.assess(evidence)

    # Then
    assert result is assessment
    assert calls == [evidence]
    assert calls[0] is evidence


def test_default_request_and_classifier_use_conservative_codex_behavior() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    settled = settled_evidence(config)
    builder = CodexAttemptRequestBuilder()
    classifier = CodexOutcomeClassifier()

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)
    assessment = classifier.assess(settled)

    # Then
    assert effective_call.request.argv == (
        "/bin/codex",
        "exec",
        "--ignore-user-config",
        "--json",
        "--color",
        "never",
        "--model=model-a",
        "-c",
        'model_reasoning_effort="low"',
        "--sandbox",
        "read-only",
        "-c",
        'approval_policy="never"',
        "-c",
        'model_instructions_file="/repo/out/instructions.bin"',
        "--",
        "frozen prompt bytes",
    )
    assert assessment.retry_class == "unknown"
    assert assessment.no_result_basis == "present_or_unknown"


def test_default_settings_reader_runs_after_version_probe() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    executable_path = Path("/resolved/codex")
    events: list[str] = []
    probed_paths: list[Path] = []

    def probe_version(path: Path) -> str:
        events.append("version")
        probed_paths.append(path)
        return "codex 1.2.3"

    def resolve_executable() -> Path:
        events.append("resolve")
        return executable_path

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
    )

    # When
    binding = resolver.resolve(config)

    # Then
    assert events == ["resolve", "version"]
    assert probed_paths == [executable_path]
    assert probed_paths[0] is executable_path
    assert binding.effective_settings == (
        ("requested_approval_policy", "never"),
        ("requested_ignore_user_config", True),
        ("requested_sandbox_mode", "read-only"),
        ("effective_approval_policy", None),
        ("effective_model_reasoning_effort", None),
        ("effective_sandbox_mode", None),
        ("effective_tool_controls", None),
        ("automatic_system_instructions", None),
    )


def test_version_timeout_leaves_version_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs(with_instructions=False)
    executable_path = Path("/absolute/codex")

    def timed_out(
        command: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        assert command == (str(executable_path), "--version")
        assert kwargs.get("timeout") == 5
        raise subprocess.TimeoutExpired(command, 5.0)

    monkeypatch.setattr(subprocess, "run", timed_out)
    resolver = CodexCliBindingResolver(
        resolve_executable=lambda: executable_path,
        runner_version=lambda: "0.1.0",
    )

    # When
    binding = resolver.resolve(config)

    # Then
    assert binding.executable_path == executable_path
    assert binding.cli_version is None


def test_default_request_is_built_after_injected_identity() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()

    def effective_call_id(
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        return "call-1"

    builder = CodexAttemptRequestBuilder(effective_call_id=effective_call_id)

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)

    # Then
    assert effective_call.call_id == "call-1"
    assert effective_call.request.argv[0] == str(binding.executable_path)
    assert effective_call.request.argv[-2:] == ("--", call.prompt.decode("utf-8"))


def test_classifier_propagates_failure_without_retrying() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    evidence = settled_evidence(config)
    failure = RuntimeError("classification failed")
    calls: list[AttemptEvidence] = []

    def assess_settled_evidence(received: AttemptEvidence) -> RetryAssessment:
        calls.append(received)
        assert received is evidence
        raise failure

    classifier = CodexOutcomeClassifier(assess_settled_evidence=assess_settled_evidence)

    # When
    with pytest.raises(RuntimeError, match="classification failed") as raised:
        classifier.assess(evidence)

    # Then
    assert raised.value is failure
    assert calls == [evidence]
    assert calls[0] is evidence
