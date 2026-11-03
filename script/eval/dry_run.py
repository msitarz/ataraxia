# SPDX-License-Identifier: Apache-2.0
"""Human-readable presentation of an already estimated frozen plan."""

from script.eval.model import DirectoryOption, DryRunReport, TokenEstimate


def format_dry_run(report: DryRunReport) -> str:
    """Render every scheduled position and its estimates without further effects.

    Returns:
        A complete newline-terminated report.
    """
    plan = report.plan
    lines = [
        f"Dry run: {report.scheduled_call_count} calls; "
        "no Codex calls or output directory",
        "Inputs (in composition order):",
    ]
    directories = [
        option
        for option in plan.configuration.ordered_options
        if isinstance(option, DirectoryOption)
    ]
    for index, directory in enumerate(directories):
        count = sum(
            source.directory_position == directory.position for source in plan.snapshots
        )
        lines.append(f"  {str(directory.path)!r}: {count} selected files")
        if index < len(plan.boundary_bytes):
            lines.append(f"  separator: {plan.boundary_bytes[index].decode('utf-8')!r}")
    config = plan.configuration
    workspace = (
        str(report.resolved_working_directory)
        if report.resolved_working_directory is not None
        else "future owned empty directory per run"
    )
    lines.append(f"Working directory: {workspace}")
    lines.append(
        f"Sandbox: {config.sandbox_mode}; tools enabled: {config.enable_tools}"
    )
    lines.append(f"Models: {', '.join(plan.configuration.models)}")
    lines.append(f"Efforts: {', '.join(plan.configuration.efforts)}")
    if plan.instructions_file is not None:
        lines.append(
            f"Instructions file: {plan.instructions_file.repository_path!r} "
            "(estimated separately)"
        )
    lines.append("Calls (zero-based position; supplied-context tokens):")
    for call, estimate in zip(plan.calls, report.estimates, strict=True):
        context = _count(estimate.context)
        instructions = (
            f"; instructions tokens: {_count(estimate.instructions_file)}"
            if estimate.instructions_file is not None
            else ""
        )
        lines.append(
            f"  {call.position}: model={call.model} effort={call.effort} "
            f"context tokens={context}{instructions}"
        )
        lines.extend(
            f"    source: {plan.snapshots[index].repository_path!r}"
            for index in call.context_indices
        )
    lines.extend(_summary(report))
    lines.append(
        "Estimates cover supplied context only; they exclude automatic CLI/system "
        "bytes, framing and overhead. They are not a billing guarantee."
    )
    lines.append(
        "Default system instructions remain when no instructions file is supplied."
    )
    lines.extend(_methods(report))
    return "\n".join(lines) + "\n"


def _count(estimate: TokenEstimate) -> str:
    return "UNKNOWN" if estimate.token_count is None else str(estimate.token_count)


def _summary(report: DryRunReport) -> list[str]:
    counts = [estimate.context.token_count for estimate in report.estimates]
    known = [count for count in counts if count is not None]
    unknown = len(counts) - len(known)
    if not known:
        return [f"Supplied-context total: UNKNOWN ({unknown} unknown calls)"]
    label = "Known subtotal" if unknown else "Total"
    result = [
        f"Supplied-context {label.lower()}: {sum(known)} tokens across "
        f"{len(known)} known calls; {unknown} unknown"
    ]
    if known:
        result.append(
            f"Supplied-context known range: {min(known)}-{max(known)} tokens per call"
        )
    return result


def _methods(report: DryRunReport) -> list[str]:
    estimates = (
        estimate
        for call in report.estimates
        for estimate in (call.context, call.instructions_file)
        if estimate is not None
    )
    unique = dict.fromkeys(
        (
            e.model,
            e.method,
            e.library_version,
            e.tokenizer_version,
            e.compatibility,
            e.diagnostic,
        )
        for e in estimates
    )
    lines = ["Estimation methods:"]
    for model, method, library, tokenizer, compatibility, diagnostic in unique:
        lines.append(
            f"  {model}: {method}; compatibility={compatibility}; "
            f"library={library or 'unknown'}; tokenizer={tokenizer or 'unknown'}"
            + (f"; {diagnostic}" if diagnostic else "")
        )
    return lines
