# Preserved trial evidence

This archive accompanies the maintainer-requested single preservation commit.
The explicit request to retain all findings/evidence authorizes this larger
review surface as a scope exception. It is no completion/adoption claim and no
cleanup commit: all Work contracts and incomplete criteria remain.

Original temporary paths are provenance, not required links. The committed
[inventory](inventory.json) maps every retained artifact to its source path,
original SHA256 where applicable, retained SHA256, transformation and size.
The archive contains selected owned evidence, not credentials or complete
temporary repositories. Archived Python/TOML use `.txt` suffixes deliberately:
they are reviewable trial source, not production tools or automatically runnable
code. Existing absolute paths in archived plans must never be reused for a new
trial; follow the [fresh-path recipe](../successful-recipe.md).

## Selection and transformations

- Owned logs, plans, configs, runner source, prompts, dependency inventories
  and review sentinels are exact copies except the declared extracts and
  whitespace/EOF normalization below, across successes and failures.
  Cache inventories are metadata/hashes; no dependency payloads, caches or venvs
  are copied. State selection is limited to explicitly owned `config.toml` and
  filtered session extracts; no auth file was read/copied or credential hashed.
- Event JSONL retains thread/turn/actual command items, tool output,
  warning/error items and usage. Generated reasoning summaries are replaced by
  an omission marker. Re-serialization changes bytes; original and retained
  hashes are both recorded. Relevant actual commands and outputs remain
  inspectable.
- Rollout extracts retain original line numbers, actual custom/function tool
  calls/outputs, usage and selected lifecycle events. Turn context retains only
  model/effort, approval, filesystem/network profiles, workspace roots and
  relevant runtime flags. Session metadata, system/user/assistant messages,
  world-state content, reasoning and unrelated instructions are omitted.
- Raw stderr files are not copied; relevant error diagnostics already present
  in owned structured logs/actual tool outputs are retained. Auth/state values,
  unrelated sessions, control repository objects and binary caches are excluded.
- [Commit extracts](git-extracts/integrated-commits.patch.txt) come from
  read-only accepted disposable repositories, preserving
  author/parent/patch/binary/mode evidence. Adjacent provenance records the
  exact Git argv and output SHA.
  [Source excerpts](source-excerpts/version-comparison.json) retain matching
  Codex revision/whole-file hashes and numbered relevant lines; no build or
  binary upgrade ran. Public source links remain in the source-analysis report.

## Installed-hook normalization

The first approved preservation commit attempt exited one because the normal
installed trailing-whitespace and end-of-file-fixer hooks modified 45 archived
files. No commit was created and no hook was bypassed. The retained copies now
follow those hooks: line-end spaces/tabs stripped and exactly one final LF
(empty files stay empty). No JSON value, code statement or trial result changed.

The inventory preserves original source SHA256, prior selected/extracted
SHA256 where normalization changed bytes, and new retained SHA256/size. All
275 prior retained versions were compared with the approved staged index blobs;
only this declared normalization changed. Selected original source hashes were
also rechecked, without reading credentials. Historical plans/hashes embedded
inside exact evidence still name the original trial bytes; the outer inventory
names the normalized archival bytes. New reproduction must re-freeze adapted
artifacts and must not equate these two hashes.

There is no existing Make target for the complete whitespace/EOF hook set.
Those normal installed hooks will run again on the next separately approved
commit; this artifact correction does not retry or re-stage the commit.

## Trial groups

| Original fixture group | Retained files | Bytes | Inspectable entry |
| --- | ---: | ---: | --- |
| `ataraxia-delivery-9f2b7c18db15` | 10 | 210636 | [record](retained/ataraxia-delivery-9f2b7c18db15/launch-a82276367bc0482a82f7cacfcc4a31ce.jsonl) |
| `ataraxia-isolation-20261003` | 2 | 1783 | [record](retained/ataraxia-isolation-20261003/config.toml.txt) |
| `ataraxia-isolation-executor-12f0f185970b` | 36 | 179941 | [record](retained/ataraxia-isolation-executor-12f0f185970b/model-launch-a5096a1045f745fe9f62bd82b8309baf.jsonl) |
| `ataraxia-isolation-executor-replacement-a66f231bd50c` | 21 | 122405 | [record](retained/ataraxia-isolation-executor-replacement-a66f231bd50c/model-launch-f54adabf3e6d4a7ca9e962a3dbb383ef.jsonl) |
| `ataraxia-isolation-git-retry-18092082117a` | 65 | 212519 | [record](retained/ataraxia-isolation-git-retry-18092082117a/batch-launch-0deed16ff6134592b7de8a0a226e2745.jsonl) |
| `ataraxia-isolation-history-cb88dea8f876` | 26 | 35357 | [record](retained/ataraxia-isolation-history-cb88dea8f876/batch-launch-72d58aef34b9419c9476632432059d4e.jsonl) |
| `ataraxia-isolation-offline-c2afe48e926a` | 9 | 924676 | [record](retained/ataraxia-isolation-offline-c2afe48e926a/offline-recreation/launch-eff2bfaf40bd47ef9464a1869e68e323.jsonl) |
| `ataraxia-isolation-online-c44d9fef9c6a` | 4 | 514437 | [record](retained/ataraxia-isolation-online-c44d9fef9c6a/online-launch-09b9619f3b174521b8bbbf288ae955af.jsonl) |
| `ataraxia-isolation-restart-71ca4e8451c3` | 14 | 14012 | [record](retained/ataraxia-isolation-restart-71ca4e8451c3/external-launch-e53b7bc632954affa2c8c0f4fd1e4269.jsonl) |
| `ataraxia-isolation-scratch-d388fe8a28bd` | 9 | 932273 | [record](retained/ataraxia-isolation-scratch-d388fe8a28bd/scratch-r1/launch-b73a3ccc61904c11b73d225a0dcac6de.jsonl) |
| `ataraxia-isolation-setup-7a26d72bb1c7` | 13 | 1328792 | [record](retained/ataraxia-isolation-setup-7a26d72bb1c7/setup-condition/launch-6d0fc9ed5c164c349c8c81abce4fb5cd.jsonl) |
| `ataraxia-isolation-setup-hookcache-9d90aa43928b` | 8 | 991922 | [record](retained/ataraxia-isolation-setup-hookcache-9d90aa43928b/setup-hookcache-r1/launch-0a6f9bc1be9d40d39df70e8fd40b689c.jsonl) |
| `ataraxia-isolation-sibling-08b8a6fe2ef8` | 13 | 35168 | [record](retained/ataraxia-isolation-sibling-08b8a6fe2ef8/launch-36c4d9efc1214f40b9768c1473f66f3d.jsonl) |
| `ataraxia-isolation-tmpprefix-2df60f7109cc` | 24 | 263176 | [record](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/model-launch-c44e2fe0ff0544d28825e27b7d1902bf.jsonl) |
| `ataraxia-isolation-zsh-c8d8e5373287` | 4 | 23958 | [record](retained/ataraxia-isolation-zsh-c8d8e5373287/launch-4046046704bd4f66a8d3f2470f94bd0a.jsonl) |

## Successful result anchors

- [Actual TMPPREFIX initial events](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/events-c44e2fe0ff0544d28825e27b7d1902bf-initial.jsonl),
  [resumed events](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/events-c44e2fe0ff0544d28825e27b7d1902bf-resume.jsonl),
  [runtime config](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/runtime.config.toml.txt),
  [model plan](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/model-plan.json)
  and
  [session extract](retained/ataraxia-isolation-tmpprefix-2df60f7109cc/session-extracts/rollout-2026-10-04T04-57-46-01a10622-312d-7332-88f8-fddda82dda94.jsonl).
- [Offline setup/scratch result](retained/ataraxia-isolation-scratch-d388fe8a28bd/scratch-r1/launch-b73a3ccc61904c11b73d225a0dcac6de.jsonl),
  including full static checks, 16 focused tests and retained missing-cache
  failure; this is deterministic project setup, separate from the tiny model
  task.
- [Delivery recovery](retained/ataraxia-delivery-9f2b7c18db15/recovery-launch-46589f3a7e194d64a83bdda64c193ee5.jsonl)
  and [conflict commit extract](git-extracts/conflict-commits.patch.txt).

## Interpretation limits

Logs/hash inventories are retained observations, not substitute CI or new
execution. Private raw session content is not needed for the committed claims,
but omissions mean this archive cannot establish every possible prompt/tool
surface. Predeclaration, independent reviews and prior failed attempts remain
documented in the linked reports. Normal orchestrator PR/CI/maintainer review
are downstream delivery responsibilities, not a requirement to run a separate
live GitHub smoke trial before preserving these findings.
