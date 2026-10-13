# Optional reviewed registry selection

Read this document when using the retained internal registry selector. It owns
usage, preparation record schema and trust boundary until the separate
[cleanup Work](../../registry-selector-cleanup/README.md) removes obsolete
tooling. The [implementation plan](../README.md) has abandoned snapshot
reconstruction; this delivered partial capability remains available and produces
only a selected-entry inventory, not an operational offline sandbox. It is not a
prerequisite of manual native clone preparation.

`make registry-select CACHE=/absolute/dedicated-cache RECORD=/absolute/record.json PREPARATION_SHA256=<externally-accepted-sha256> DESTINATION=/absolute/new-result`
validates a registry selection for later snapshot composition. It produces
`selection.json`, not a copied cache or prepared environment. Failure retains
`failure.txt` in the new destination; an existing destination is never changed.
Reprepare or obtain independent review of corrected inputs, then choose another
new destination. The command runs offline and never installs dependencies.

The orchestrator independently reviews and provisions the preparation record and
its expected digest before selection. A digest supplied by the record, an
`approved` field or automatically discovered cache does not establish
acceptance. The selector preserves provenance rooted in that reviewed
preparation; it does not authenticate arbitrary caches or verify upstream wheel
signatures/hashes against extracted files. METADATA matching is a consistency
check.

The JSON record binds `condition` to the supported adapter condition in
`script/registry_selection.py`, `declarations` to SHA256 of `uv.lock`,
`pyproject.toml` and `.pre-commit-config.yaml`, and `evidence` to relative
file/SHA256 entries beside the record. Evidence must establish actual successful
pinned Make setup/hook preparation, resolved tool hashes, default PyPI with uv
configuration disabled, and the declared platform/cache layout. `derivation`
explains how every package and resolver entry follows from that evidence.
`packages` declares `root`, `name`, `version`, registry `origin`, `wheel` link
and extracted `archive`, plus preparation `basis` and METADATA `trace`, for each
dependency, including frozen hook/build
dependencies outside the project lock. `files` and `links` enumerate all
selected relative entries with SHA256 or link targets. The reviewer verifies
the allowed package boundary and complete resolver inventory before accepting
the record; filenames or path scans alone cannot do this.

The adapter supports the tested macOS x86_64/Python 3.14 cache with its pinned
tools and default index. Other conditions fail; obtain separate reviewed
support rather than relabeling inputs. Selected payloads and opaque resolver
records remain unchanged. Hook Git sources and final snapshot delivery are
separate operations; this utility leaves the standard worktree policy intact.

Under this supported preparation condition, the locked project cache requires
wheel HTTP records, while the hook resolver cache also requires simple-index
records. The reviewed preparation inventory determines completeness; the
selector preserves their bytes without decoding them. Its result enumerates
files and links for later filter-on-copy delivery, leaving unrelated raw cache
entries unselected. It rejects result destinations inside the input cache.
