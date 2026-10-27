# SPDX-License-Identifier: Apache-2.0
"""Typed Codex invocation adapter skeletons.

The adapters wire reviewed runner values to explicit leaf operations. The
Codex CLI details remain unfinished until their external contracts are
verified; default leaves therefore fail visibly instead of guessing.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path

from script.process_supervisor import AttemptRequest

from ...model import (  # ruff: ignore[relative-imports]
    AttemptEvidence,
    CallId,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    RetryAssessment,
    SettingValue,
)
from ..ports import (  # ruff: ignore[relative-imports]
    AttemptRequestBuilder,
    CliBinding,
    CliBindingResolver,
    EffectiveCall,
    OutcomeClassifier,
)

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
        read_effective_settings: Return sanitized settings observed for that
            executable and this run configuration.
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
    or staged files; no request operation is implemented by default.

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

    This boundary receives no stream events and has no semantic answer parser.
    Until Codex outcome signals and confident no-result evidence are verified,
    classification remains an unfinished leaf operation.

    Attributes:
        assess_settled_evidence: Classify one settled supervisor evidence value.
    """

    assess_settled_evidence: AssessSettledEvidence = field(
        default_factory=lambda: _assess_settled_evidence
    )

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Assess one settled attempt and return its classification.

        Returns:
            The injected classifier result.
        """
        return self.assess_settled_evidence(evidence)


def _resolve_codex_executable() -> Path:
    """Resolve the Codex executable from the current execution environment."""
    raise NotImplementedError("Codex executable discovery is not implemented")


def _probe_codex_version(executable_path: Path, /) -> str | None:
    """Probe the resolved executable's observable version."""
    raise NotImplementedError("Codex version probing is not implemented")


def _read_effective_settings(
    executable_path: Path, config: HarnessConfig, /
) -> tuple[tuple[str, SettingValue], ...]:
    """Read observable Codex settings without retaining credential data."""
    del executable_path, config
    raise NotImplementedError("Codex effective-settings discovery is not implemented")


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
    """Identify effective frozen inputs and invocation settings."""
    del plan, call, binding, staged_instructions_path, config
    raise NotImplementedError("effective-call identity is not implemented")


def _build_attempt_request(
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    staged_instructions_path: StagedInstructionsPath,
    config: HarnessConfig,
    /,
) -> AttemptRequest:
    """Construct one Codex argv and its supervisor request limits."""
    del plan, call, binding, staged_instructions_path, config
    raise NotImplementedError("Codex argv and request construction are not implemented")


def _assess_settled_evidence(evidence: AttemptEvidence, /) -> RetryAssessment:
    """Classify verified captured output after the supervisor settles."""
    del evidence
    raise NotImplementedError("Codex outcome signal recognition is not implemented")
