# SPDX-License-Identifier: Apache-2.0
"""Bounded Codex CLI binding, request construction, and outcome classification.

Native settings that cannot be observed without reading private user state are
reported as unknown. Quota recognition accepts only a bounded JSONL sequence.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from uuid import UUID

from script.eval.model import (
    AttemptEvidence,
    CallId,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    RetryAssessment,
    SeparatorOption,
    SettingValue,
)
from script.eval.runner.adapters.codex_version import supports_quota_version
from script.eval.runner.ports import (
    AttemptRequestBuilder,
    CliBinding,
    CliBindingResolver,
    EffectiveCall,
    OutcomeClassifier,
)
from script.process_supervisor import AttemptRequest, Completed, InfrastructureFailure

type ResolveExecutable = Callable[[], Path]
type ProbeVersion = Callable[[Path], str | None]
type ReadEffectiveSettings = Callable[
    [Path, HarnessConfig], tuple[tuple[str, SettingValue], ...]
]
type StagedInstructionsPath = Path | None
type EffectiveCallId = Callable[
    [FrozenPlan, PlannedCall, CliBinding, StagedInstructionsPath, HarnessConfig],
    CallId,
]
type BuildAttemptRequest = Callable[
    [FrozenPlan, PlannedCall, CliBinding, StagedInstructionsPath, HarnessConfig],
    AttemptRequest,
]
type AssessSettledEvidence = Callable[[AttemptEvidence], RetryAssessment]


@dataclass(frozen=True)
class CodexCliBindingResolver(CliBindingResolver):
    """Resolve the executable before probing it and reading its settings.

    The path passed to both later operations is the exact resolved binding
    candidate. Provider quota identity remains unknown until verified.

    Attributes:
        resolve_executable: Find the CLI executable for this process.
        probe_version: Observe the version using the resolved executable path.
        read_effective_settings: Return sanitized requested controls and
            verified native settings; unavailable native settings remain None.
        runner_version: Return the installed harness package version.
    """

    resolve_executable: ResolveExecutable = field(
        default_factory=lambda: _resolve_codex_executable
    )
    probe_version: ProbeVersion = field(default_factory=lambda: _probe_codex_version)
    read_effective_settings: ReadEffectiveSettings = field(
        default_factory=lambda: _read_effective_settings
    )
    runner_version: Callable[[], str] = field(default_factory=lambda: _runner_version)

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve CLI identity through the injected operations in order.

        Returns:
            A binding with an unverified quota scope left unknown.

        """
        executable_path = self.resolve_executable()
        cli_version = self.probe_version(executable_path)
        effective_settings = self.read_effective_settings(executable_path, config)
        return CliBinding(
            executable_path=executable_path,
            cli_version=cli_version,
            runner_version=self.runner_version(),
            effective_settings=effective_settings,
            quota_scope=None,
        )


@dataclass(frozen=True)
class CodexAttemptRequestBuilder(AttemptRequestBuilder):
    """Bind frozen call identity and prepared evidence to one request.

    The injected operations receive immutable plan/call/binding values, only the
    staged instruction path, and supervisor settings. They must not open source
    or staged files. The default request uses an argv prompt; operating-system
    argument-size limits and NUL's inability to appear in an argument apply.

    Attributes:
        effective_call_id: Derive an identity from frozen plan/call inputs,
            binding, staged instruction path, and config without opening files.
        build_attempt_request: Build argv and supervisor limits from the same
            values; source bytes come from the frozen plan and the staged path
            is passed through without reading it.
    """

    effective_call_id: EffectiveCallId = field(
        default_factory=lambda: _effective_call_id
    )
    build_attempt_request: BuildAttemptRequest = field(
        default_factory=lambda: _build_attempt_request
    )

    def build(
        self,
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        evidence: PreparedEvidence,
        config: HarnessConfig,
        /,
    ) -> EffectiveCall:
        """Build an effective call from the exact prepared inputs.

        Returns:
            The plan's run identity, calculated call identity, and request.

        """
        staged_instructions_path = evidence.model_instructions_file
        call_id = self.effective_call_id(
            plan, call, binding, staged_instructions_path, config
        )
        request = self.build_attempt_request(
            plan, call, binding, staged_instructions_path, config
        )
        return EffectiveCall(
            run_id=plan.run_id,
            call_id=call_id,
            planned_call=call,
            request=request,
        )


@dataclass(frozen=True)
class CodexOutcomeClassifier(OutcomeClassifier):
    """Pass one settled supervisor observation to a classifier operation.

    This boundary assesses captured output after settlement and never parses answers.
    Its supported quota sequence establishes a provisional no-result candidate;
    the correlated scope must be verified before recovery. Capacity remains unknown.

    Attributes:
        cli_version: Observed version governing supported quota recognition.
        assess_settled_evidence: Classify other settled supervisor evidence.
    """

    cli_version: str | None = field(default=None, kw_only=True)
    assess_settled_evidence: AssessSettledEvidence = field(
        default_factory=lambda: _assess_settled_evidence
    )

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Assess one settled attempt and return its classification.

        Returns:
            The injected classifier result.
        """
        if supports_quota_version(self.cli_version) and _quota_failure(evidence):
            return RetryAssessment(
                retry_class="quota",
                classification_basis="supported Codex quota failure event sequence",
                no_result_basis="confident_absence",
                diagnostic=None,
            )
        return self.assess_settled_evidence(evidence)


def _quota_failure(evidence: AttemptEvidence) -> bool:
    """Recognize the reviewed complete no-result Codex event sequence.

    Returns:
        Whether the complete supported sequence proves the narrow candidate.
    """
    outcome = evidence.outcome
    if evidence.control_flow != "returned" or not isinstance(outcome, Completed):
        return False
    output = outcome.observation.output
    if (
        outcome.exit_status <= 0
        or not outcome.observation.cleanup.dispatch_permitted
        or output is None
        or output.stderr != b""
    ):
        return False
    try:
        rows = [
            json.loads(line, object_pairs_hook=_unique_object)
            for line in output.stdout.decode("utf-8").splitlines()
        ]
    except UnicodeDecodeError, ValueError:
        return False
    if len(rows) != 4 or not all(isinstance(row, dict) for row in rows):
        return False
    return _quota_event_sequence(rows)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON keys at every level of the quota envelope.

    Returns:
        The object with its unique keys.

    Raises:
        ValueError: An object repeats a key.
    """
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _quota_event_sequence(rows: list[dict[str, object]]) -> bool:
    """Validate the complete supported operational failure events.

    Returns:
        Whether the sequence matches the supported quota failure.
    """
    first, second, third, fourth = rows
    if set(first) != {"type", "thread_id"} or first["type"] != "thread.started":
        return False
    try:
        thread_id = first["thread_id"]
        if not isinstance(thread_id, str) or str(UUID(thread_id)) != thread_id:
            return False
    except ValueError:
        return False
    if second != {"type": "turn.started"} or set(third) != {"type", "message"}:
        return False
    if third["type"] != "error" or set(fourth) != {"type", "error"}:
        return False
    error = fourth["error"]
    if fourth["type"] != "turn.failed" or not isinstance(error, dict):
        return False
    if set(error) != {"message"} or error["message"] != third["message"]:
        return False
    message = third["message"]
    return isinstance(message, str) and bool(
        re.fullmatch(
            r"You\u2019ve hit your usage limit\. Upgrade to Pro "
            r"\(https://chatgpt\.com/explore/pro\), visit "
            r"https://chatgpt\.com/settings/usage to purchase more credits "
            r"or try again at (?:1[0-2]|[1-9]):[0-5][0-9] [AP]M\.",
            message,
        )
    )


def _resolve_codex_executable() -> Path:
    """Resolve one executable Codex CLI path from this process's PATH.

    Returns:
        The absolute executable path selected from ``PATH``.

    Raises:
        FileNotFoundError: No executable Codex CLI is available on ``PATH``.
    """
    located = shutil.which("codex")
    if located is None:
        raise FileNotFoundError("Codex CLI executable was not found on PATH")
    executable_path = Path(located).resolve(strict=True)
    if not executable_path.is_file() or not os.access(executable_path, os.X_OK):
        raise FileNotFoundError(f"Codex CLI is not executable: {executable_path}")
    return executable_path


def _probe_codex_version(executable_path: Path, /) -> str | None:
    """Probe the exact resolved executable with a bounded version command.

    Returns:
        The successful command's output, or ``None`` when it is unavailable.
    """
    try:
        result = subprocess.run(
            (str(executable_path), "--version"),
            check=False,
            capture_output=True,
            timeout=5.0,
        )
    except OSError, subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.decode("utf-8", errors="replace").strip()
    return output or None


def _read_effective_settings(
    executable_path: Path, config: HarnessConfig, /
) -> tuple[tuple[str, SettingValue], ...]:
    """Report native settings as unavailable without reading private config.

    Returns:
        Requested explicit controls and unknown native effective settings.
    """
    del executable_path, config
    return (
        ("requested_approval_policy", "never"),
        ("requested_ignore_user_config", True),
        ("requested_sandbox_mode", "read-only"),
        ("effective_approval_policy", None),
        ("effective_model_reasoning_effort", None),
        ("effective_sandbox_mode", None),
        ("effective_tool_controls", None),
        ("automatic_system_instructions", None),
    )


def _runner_version() -> str:
    """Return the installed harness distribution version."""
    return version("ataraxia")


def _effective_call_id(
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    staged_instructions_path: StagedInstructionsPath,
    config: HarnessConfig,
    /,
) -> CallId:
    """Hash frozen provenance and known invocation settings, independent of run.

    Run identity, scheduled position, staged artifact location, output limits,
    concurrency, and retry allowances do not change this model invocation.

    Returns:
        A stable SHA-256 identity for the frozen call and known invocation.
    """
    del staged_instructions_path
    components = _effective_call_components(plan, call, binding, config)
    payload = b"".join(
        _encode_identity_component(label, value) for label, value in components
    )
    return hashlib.sha256(payload).hexdigest()


def _effective_call_components(
    plan: FrozenPlan, call: PlannedCall, binding: CliBinding, config: HarnessConfig, /
) -> tuple[tuple[str, bytes], ...]:
    """Collect ordered identity fields without run or staging-location data.

    Returns:
        Labeled bytes whose exact contents define the effective invocation.
    """
    sources = tuple(plan.snapshots[index] for index in call.context_indices)
    source_fields = tuple(
        component
        for source in sources
        for component in (
            ("source-directory-position", str(source.directory_position).encode()),
            ("source-path", source.repository_path.encode("utf-8")),
            ("source-commit-blob", source.commit_blob_sha.encode("ascii")),
            ("source-content", source.content),
        )
    )
    separator_fields = tuple(
        component
        for option in plan.configuration.ordered_options
        if isinstance(option, SeparatorOption)
        for component in (
            ("separator-option-position", str(option.position).encode("ascii")),
            ("separator-option-value", option.value.encode("utf-8")),
        )
    )
    instruction_fields = (
        (("instructions-configured", b"false"),)
        if plan.instructions_file is None
        else (
            ("instructions-configured", b"true"),
            (
                "instructions-path",
                plan.instructions_file.repository_path.encode("utf-8"),
            ),
            (
                "instructions-commit-blob",
                plan.instructions_file.commit_blob_sha.encode("ascii"),
            ),
            ("instructions-content", plan.instructions_file.content),
        )
    )
    setting_fields = tuple(
        component
        for key, value in sorted(
            binding.effective_settings,
            key=lambda setting: (setting[0], _encode_setting_value(setting[1])),
        )
        for component in (
            ("binding-setting-key", key.encode("utf-8")),
            ("binding-setting-value", _encode_setting_value(value)),
        )
    )
    return (
        ("format", b"ataraxia-codex-effective-call-v1"),
        ("repository-root", str(plan.repository_root).encode("utf-8")),
        ("repository-head", plan.head_commit.encode("ascii")),
        ("model", call.model.encode("utf-8")),
        ("effort", call.effort.encode("utf-8")),
        ("prompt", call.prompt),
        *source_fields,
        *separator_fields,
        *(("separator", boundary) for boundary in plan.boundary_bytes),
        *instruction_fields,
        ("codex-path", str(binding.executable_path).encode("utf-8")),
        ("codex-version", (binding.cli_version or "unknown").encode("utf-8")),
        ("invocation-cwd", str(plan.repository_root).encode("utf-8")),
        ("command", b"exec"),
        ("output-protocol", b"jsonl"),
        ("color", b"never"),
        ("ignore-user-config", b"true"),
        ("approval-policy", b"never"),
        ("sandbox-mode", b"read-only"),
        (
            "instructions-override",
            b"configured" if config.instructions_file_path is not None else b"default",
        ),
        *setting_fields,
    )


def _encode_identity_component(label: str, value: bytes, /) -> bytes:
    """Encode one labeled byte field with unambiguous lengths.

    Returns:
        Length-prefixed UTF-8 label and exact value bytes.
    """
    label_bytes = label.encode("utf-8")
    return (
        len(label_bytes).to_bytes(8, "big")
        + label_bytes
        + len(value).to_bytes(8, "big")
        + value
    )


def _build_attempt_request(
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    staged_instructions_path: StagedInstructionsPath,
    config: HarnessConfig,
    /,
) -> AttemptRequest:
    """Construct one JSONL exec request and its configured supervisor limits.

    Returns:
        The argv request with exact frozen prompt bytes and process limits.

    Raises:
        ValueError: The staged path mismatches the plan or the argv prompt
            contains NUL, which cannot be represented as a native argument.
    """
    if (plan.instructions_file is None) != (staged_instructions_path is None):
        raise ValueError("staged instructions must match the frozen plan")
    prompt = call.prompt.decode("utf-8")
    if "\x00" in prompt:
        raise ValueError("Codex argv prompts cannot contain NUL characters")
    argv = [
        str(binding.executable_path),
        "exec",
        "--ignore-user-config",
        "--json",
        "--color",
        "never",
        f"--model={call.model}",
        "-c",
        f"model_reasoning_effort={_toml_string(call.effort)}",
        "--sandbox",
        "read-only",
        "-c",
        'approval_policy="never"',
    ]
    if staged_instructions_path is not None:
        argv.extend((
            "-c",
            "model_instructions_file=" + _toml_string(str(staged_instructions_path)),
        ))
    argv.extend(("--", prompt))
    return AttemptRequest(
        argv=tuple(argv),
        cwd=plan.repository_root,
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
        grace_seconds=config.grace_seconds,
    )


def _assess_settled_evidence(evidence: AttemptEvidence, /) -> RetryAssessment:
    """Recognize only supervisor-confirmed prelaunch failures as no-result.

    Returns:
        A confident infrastructure absence or a fail-closed unknown result.
    """
    outcome = evidence.outcome
    if (
        evidence.control_flow == "returned"
        and isinstance(outcome, InfrastructureFailure)
        and outcome.observation.cleanup.process == "not_started"
    ):
        return RetryAssessment(
            retry_class="infrastructure",
            classification_basis="supervisor confirmed no process was launched",
            no_result_basis="confident_absence",
            diagnostic=outcome.diagnostic,
        )
    return RetryAssessment(
        retry_class="unknown",
        classification_basis=None,
        no_result_basis="present_or_unknown",
        diagnostic="Codex outcome has no verified structured classification signal",
    )


def _toml_string(value: str, /) -> str:
    """Encode Unicode text as a valid TOML basic string.

    Returns:
        The quoted TOML string value.

    Raises:
        ValueError: The value contains an invalid Unicode surrogate code point.
    """
    escaped: list[str] = ['"']
    for character in value:
        codepoint = ord(character)
        if character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append("\\\\")
        elif character == "\b":
            escaped.append("\\b")
        elif character == "\t":
            escaped.append("\\t")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\f":
            escaped.append("\\f")
        elif character == "\r":
            escaped.append("\\r")
        elif codepoint < 0x20 or 0x7F <= codepoint <= 0x9F:
            escaped.append(f"\\u{codepoint:04X}")
        elif 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError("TOML strings cannot contain surrogate code points")
        else:
            escaped.append(character)
    escaped.append('"')
    return "".join(escaped)


def _encode_setting_value(value: SettingValue, /) -> bytes:
    """Encode a known/unknown setting with a stable type tag.

    Returns:
        A tagged value that distinguishes unknown, strings, and scalar types.
    """
    if value is None:
        return b"unknown"
    if isinstance(value, bool):
        return b"bool:true" if value else b"bool:false"
    if isinstance(value, int):
        return b"int:" + str(value).encode("ascii")
    if isinstance(value, float):
        return b"float:" + value.hex().encode("ascii")
    return b"str:" + value.encode("utf-8")
