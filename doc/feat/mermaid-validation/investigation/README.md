# Compare fenced Mermaid validation candidates

Own a concise investigation report here, using
[mermaidx](https://github.com/MohammadRaziei/mermaidx),
[official Mermaid CLI](https://github.com/mermaid-js/mermaid-cli),
[pymermaider](https://github.com/diceroll123/pymermaider) and GitHub's
[creating diagrams guidance](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
as seed sources. Compare mermaidx with official Mermaid parsing and rendering:
distinguish syntax recognition from successful rendering and identify the
actually used Mermaid engine/version. Briefly assess whether pymermaider's
documented diagram-generator purpose fits validation of existing fenced
Markdown; do not assume generation provides such validation.

Exercise only small disposable probes: the original semicolon-containing
Work-tree sequence failure and its corrected conjunction version; valid
sequence, class, state and flowchart diagrams; malformed syntax; multiple
Mermaid fences in one Markdown file; and a file without diagrams. Record exact
inputs, exercised tool/engine versions, commands, outcomes and diagnostic
locations. Preserve uncertainty when a candidate cannot be exercised; do not
represent documentation claims or unrun cases as passing probe evidence.

Assess GitHub renderer version compatibility and diagram coverage without
claiming exact parity unless demonstrated. Assess Python 3.14 and supported
project platforms, setup dependencies, offline execution after setup, licenses,
maintenance and usable file/line diagnostics. Inspect the existing `make
doc-check` implementation, its `ARGS` selection and CI route to propose the
smallest coherent integration, including multi-fence errors and no-diagram
success. Include browser/Node requirements when applicable; do not add them.

Return a concise evidence-based recommendation, limitations and a proposed
bounded adoption contract with acceptance/validation methods. Count report and
probe-support changes toward the five-minute review; escalate additional scope.
No checker/dependency adoption, CI changes or product repair in this leaf.

- **AC-1 TODO** Given the named candidates and probe matrix, the reviewed report
  distinguishes parsing, rendering and generation, preserves actual results and
  uncertainty, and proposes a justified `doc-check` adoption boundary with
  explicit compatibility, diagnostic and execution limitations.

  Validation: independently inspect recorded probe inputs/results and source
  support, reproduce the exercised small probes where available, assess the
  proposed contract against existing Make/CI ownership, then run doc/ac checks.
