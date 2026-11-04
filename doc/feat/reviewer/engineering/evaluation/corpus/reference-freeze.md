# Initial private reference freeze

On 2026-11-04 the root Codex orchestrator accepted a reference-only freeze on
maintainer delegation, after independent review by Codex executor
`/root/review_freeze_reference`. Both reviews were agent reviews, not human
review. The root reviewer knew a stopped historical series existed; neither
reviewer inspected model outputs for this review, so the review was not blind to
that series' existence.

- Reviewed public fixture and rule revision:
  `2991ba04a09a43a558166a8f5f3032a72c5f0c48`.
- Guidance extraction base: `30155f93e89e47cf0ffb580677277e0ae786eabf`.
  This is the guidance base, not the revision containing the authored fixtures.
- Frozen private index SHA-256:
  `ddc084c2f2c168bef1dead140e508953688e3d721b7de56ee4e5aa53644febd8`.
- Independent private review SHA-256:
  `0992ec3f65fdc4dbd498fb62da2a33d0d4c7acc9aac3e0e510d9e6c9f9d7c8ab`.

The [manifest](manifest.md) records fixture provenance and the guidance
excerpts. The examples are authored, not historical incidents, and do not
establish incident diversity. This record freezes the private reference only;
the protocol, complete inputs, invocation boundary, and trial remain subject to
separate review and authorization. All Evaluation acceptance criteria remain
TODO.

The current private scorer conservatively reports the reference as draft and
unreviewed. Its report status does not verify this review or freeze; use this
record and the retained private provenance for that distinction.
