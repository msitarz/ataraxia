# Establish migration scope

## Purpose

Make every active contract and affected instruction discoverable before the
migration changes their format or removes acceptance bookkeeping.

## Goals

- Identify all active contracts and their supporting specifications.
- Distinguish current requirements from historical inputs.
- Locate tooling, test markers, guidance conflicts, and cross-contract
  references.

## Non-Goals

- Rewrite existing contracts, change tools, or remove tests.
- Create a permanent inventory service or per-revision journal.

## Acceptance criteria

### **AC-1 DONE** Complete active-contract inventory

The [migration inventory](../inventory.md) identifies every active Work README,
including planning parents without ACs, and classifies linked files as live
specifications or historical/supporting inputs. It groups contracts by rewrite
owner and distinguishes the two already converted reference Works. Review of
parent maps and linked contracts exposes omissions beyond filename discovery.

#### What exists

The initial inventory records 31 existing Work READMEs and three supporting
sandbox Markdown files at the planning baseline. This is a starting inventory,
not a claim that every linked requirement has already been reviewed.

### **AC-2 DONE** All migration-sensitive references identified

The inventory identifies current format/evidence conflicts, Make and script
entry points, marker registration and usages, dedicated tests/fixtures, and
cross-Work criterion references. Historical marker references to removed Works
are distinguished from active contract references. It states which artifacts
are rewritten, retired, or preserved and identifies any unresolved scope gap.

## Dependencies

None.

## Links

- [Migration parent](../README.md): approved scope and step ordering.
