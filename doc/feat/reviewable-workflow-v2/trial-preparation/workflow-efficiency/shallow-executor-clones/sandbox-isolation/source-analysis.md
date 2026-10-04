# Matching-version Seatbelt source analysis

Read-only inspection used official `openai/codex` tag `rust-v0.159.3`, peeled
commit `01fc69f4026735edfdf6789820549727a4867b11`, downloaded by the
orchestrator at `/private/tmp/codex-source-0.159.3`. No source build, test,
modification or source-repository tool ran. This supplements the
[retained outcomes](symlink-runtime-r2.md#actual-result-and-stop); it does not
qualify a candidate or change AC-1/AC-2.

## Source facts

Configuration compilation turns ordinary permission strings into absolute
filesystem paths. The local macOS policy matcher normalizes trusted system
aliases while deliberately preserving mutable nested symlinks at that layer. See
[config compilation](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/core/src/config/permissions.rs#L656)
and
[local matching](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/protocol/src/permissions/local_aliases.rs#L54).

Seatbelt lowering behaves differently for reads. Its
[normalization helper](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L217)
calls filesystem canonicalization and returns the canonical path when it
succeeds; otherwise it retains the absolute input. It does **not** return both.
The
[read branch](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L504)
uses this helper, emits one `READABLE_ROOT` parameter per root, and matches it
with `subpath` under `file-read*`. It does not emit an additional logical-alias
or symlink-component metadata rule. The restricted-read caller feeds the
[resolved readable roots](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L1006)
to that same branch. Thus successfully canonicalized Homebrew opt file/package
grants become Cellar grants during this construction path; the supplied alias
grant is not preserved alongside its target.

There is an internal special-case allowlist for symlink metadata/test-existence:
the
[minimal macOS defaults](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt_read_only_platform_defaults.sbpl#L52)
name `/etc`, `/tmp`, `/var` and `/private/etc/localtime`. Homebrew opt aliases
are absent. These defaults are included when the selected filesystem policy
requests minimal platform access. This is a fixed internal list, not a general
permission-profile symlink allowlist.

The
[profile filesystem schema](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/config/src/permissions_toml.rs#L223)
supports access/scoped entries and glob scan depth; no independent readable
symlink-metadata list was found in the traced schema/lowering. The distinct
[`allow_symlinked_codex_home` setting](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/config/src/config_toml.rs#L223)
concerns writable roots at/beneath CODEX_HOME. The
[write-root implementation](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L440)
limits that exception accordingly; it is not a library-read workaround.

Upstream tests cover
[explicit read-root exclusions and generated parameters](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt_tests.rs#L1037),
[canonicalized deny-glob prefixes](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt_tests.rs#L1168),
and
[rejected symlinked writable roots](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt_tests.rs#L2126).
The bounded search found no restricted-read alias-inode regression test. These
are inspected test definitions, not observed passing executions.

## Interpretation and smallest next check

Canonicalization is present; missing alias preservation is the concrete issue
in this lowering path. It strongly explains why resolved reads passed while
opt read/stat/readlink failed, and why granting the opt package itself did not
help: that grant is canonicalized too. The effective generated rules and exact
macOS denied operation were not captured, so this is a source-backed explanation
consistent with observations, not complete syscall-level causation. It does not
prove all configuration was ignored or resolve later loader/Git write limits.

The smallest separately reviewed check is a disposable alias/target fixture
with only the alias declared readable: inspect the generated Seatbelt parameter
and compare alias metadata/read with direct-target read. No Homebrew-wide grant
or production change is needed to isolate alias loss. A potential upstream fix
would retain only necessary alias-component metadata/test-existence access while
keeping target reads, denials and mutable-symlink protections intact; it needs a
focused regression and security review rather than blindly allowing both trees.
Alternatively, a resolved-path/relocatable runtime is a separately declared
workaround candidate. No next probe, fix, profile or runner is implemented here.

## Exact 0.160.0 comparison

Read-only comparison used official `rust-v0.160.0`, peeled commit
`a956835d020762cb2b570053af06f643a11c0ecc`, at
`/private/tmp/codex-source-0.160.0`, against the 0.159.3 commit above.
The read-root canonicalization/builder is
[unchanged in 0.160.0](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/sandboxing/src/seatbelt.rs#L504).
The following whole files are byte-identical; each SHA256 applies to both tags:

| File under `codex-rs/sandboxing/src` | SHA256 |
| --- | --- |
| `seatbelt.rs` | `03beaaaac24b6b856d4860ba4c1a6e3818e8cd2432dac7f23eddaef77e745ab5` |
| `seatbelt_read_only_platform_defaults.sbpl` | `6c5c0ae4361e738053f172b635f4e1ab6287087f3d9b6e5882b0bc06922a7199` |
| `seatbelt_base_policy.sbpl` | `5103332ddb8885ee5e1926de6c0ef23a61f4e55e31297506ae05fa4e0b24ba74` |

Also byte-identical: local permission alias matching, core permission
compilation, permission-path parsing, permission-profile TOML schema,
absolute-path utilities and Seatbelt tests. The config TOML diff adds Guardian
history-prompt/token fields and their import; it does not change the
symlinked-CODEX_HOME field or relevant filesystem configuration.

There is therefore **no source evidence that upgrading to exactly 0.160.0 fixes
this alias-preservation behavior**. The same relevant implementation and static
metadata list remain. This supports expecting the same issue on the same
runtime/condition, rather than recommending upgrade as its remedy. It does not
prove runtime outcomes of an unexecuted binary or assess unrelated release
fixes. No 0.160.0 executable was installed or run; no build, test or probe ran.

The user subsequently authorized a separate
[`/usr` read diagnostic](usr-read-r3.md), not a production isolation policy.
