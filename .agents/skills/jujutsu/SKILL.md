---
name: jujutsu
description: Use when working in a Jujutsu (jj) repository, when the user requests jj version control, or when translating Git tasks into Jujutsu workflows.
---

# Jujutsu operations

Prefer the Squash Workflow. Use `jj` for repository mutations in jj repositories, including colocated Git repositories. Respect an explicitly requested workflow and project conventions.

## Orient before changing history

- Run `jj --version`, `jj status`, `jj log --limit 12`, and `jj bookmark list`. Use installed `jj <command> --help` for version-sensitive flags. If jj is unavailable, report that; do not silently substitute Git.
- `@` is a commit containing the working copy; commands normally snapshot edits automatically. There is no Git index or separate staging step. Ignored files are not automatically included.
- Prefer change IDs for targets that will be rewritten; commit hashes change on rewrite. Quote compound revsets. `@-` means parent(s), so use an explicit target when `@` has multiple parents.
- Identify the task base and any existing work before starting. `jj new BASE` preserves the previous change and switches to a new child of BASE. Never fold unrelated work into the task or abandon it to obtain a clean workspace.
- Bookmarks name commits; creating a child does not advance a bookmark. Rewriting its commit normally moves the bookmark with it. Remote bookmarks use `NAME@REMOTE`; inspect rather than assuming `main` or `origin`.

## Default: Squash Workflow

Keep a described task commit beneath an undescribed working child. From a verified BASE:

```sh
jj new BASE -m "Implement task"  # task commit; record its change ID as TASK
jj new                         # scratch working child
# Edit and run relevant checks.
jj diff
jj squash --into TASK --use-destination-message path/to/file
# Repeat as work becomes ready; squash all only when every remaining edit belongs.
jj squash --into TASK --use-destination-message
jj diff -r TASK
jj status
```

TASK and BASE are placeholders to replace with verified revisions. A full squash abandons the emptied source and creates a fresh empty working child; do not add `jj new` after every squash. Partial squashes leave unaccepted edits in `@`. If unrelated leftovers remain, preserve them and use `jj new TASK` to finish with an empty child; report the saved change ID.

For the next logical commit, create a described child of TASK, then its scratch child. For review fixes, use `jj new TASK` and squash back into TASK. If published history must stay unchanged, create a new described fix commit and move the PR bookmark forward instead.

## Common tasks: Git intent → idiomatic jj

Replace uppercase placeholders. Interactive commands require an available terminal/UI; prefer path selection for unattended operation.

| Git task | jj operation |
|---|---|
| Clone / initialize | `jj git clone URL DIR` / `jj git init DIR`; adopt an existing Git checkout with `jj git init --colocate` inside it. |
| Status / diff / show / log | `jj status`; `jj diff`; `jj show REV`; `jj log`. `jj diff -r TASK` reviews the task commit rather than scratch edits. |
| Add files and amend | `jj squash --into TASK --use-destination-message PATH...`. For hunks: `jj squash -i --into TASK --use-destination-message`. |
| Commit message / amend message | `jj describe -r TASK -m "Message"`; content already lives in commits. |
| Branch / switch / stash | `jj new BASE` creates an anonymous branch; `jj new SAVED` resumes work above a saved change. No stash needed. `jj edit REV` edits that existing commit directly; use deliberately. |
| Named branch / tracking | `jj bookmark set NAME -r TASK`; `jj bookmark track NAME@REMOTE`. |
| Fetch / pull --rebase | `jj git fetch --remote REMOTE`, inspect, then `jj rebase -s STACK_ROOT -o BASE`. `-s` moves the root and descendants; `-r REV` moves only selected revisions. `-b TIP` selects a branch relative to the destination. |
| Merge | `jj new LEFT RIGHT -m "Merge ..."`; resolve conflicts in the merge commit. |
| Cherry-pick | `jj duplicate REV -o DEST`; inspect the returned new change ID. This copies the diff without moving the original. |
| Interactive rebase: fixup / split / reorder | `jj squash --from FIXUP --into TASK --use-destination-message`; `jj split -r REV -m "Selected part" PATH...` (or `-i`); `jj rebase -r REV -A AFTER`. Inspect descendants afterward. |
| Restore file / discard scratch edit | `jj restore --from @- PATH` for a single-parent scratch change. This discards that path's scratch edits; scope it carefully. |
| Drop a commit | `jj abandon REV`; descendants are rebased. Review the selected commit first. |
| Revert published commit | `jj revert -r BAD -o TIP` creates a new inverse change; inspect its ID and use `jj new REVERT_ID` to continue above it. |
| Reflog / recovery | `jj op log`; `jj op show OP`; `jj undo` for the latest operation. For an earlier mistake with later work, `jj op revert OP --what repo` applies its inverse; inspect resulting conflicts. Older releases may expose this as `jj undo OP`; check help. `jj op restore OP` rolls back the entire local state. |
| Git worktree | `jj workspace add -r BASE DIR`; the new workspace has its own working child. Use separate workspaces for concurrent agents. |

## Conflicts, publishing, and recovery

- Rewrites automatically rebase descendants and can record conflicts without stopping. Inspect `jj log -r 'conflicts()'` and `jj resolve --list -r REV`. Resolve in the conflicted revision with `jj resolve -r REV`, or `jj edit REV`, edit markers, and snapshot with `jj status`; return to the scratch child afterward. There is no `rebase --continue` or `git add` resolution step. Verify affected descendants and tests.
- When publishing is authorized, point the PR bookmark at the task tip, not its empty scratch child: `jj bookmark set NAME -r TASK`, then `jj git push --remote REMOTE --bookmark NAME --dry-run`, then the same push without `--dry-run`. Use explicit bookmark scope. New bookmarks are tracked by current jj; consult help if an older release requires `--allow-new`.
- Push uses remote-state checks comparable to force-with-lease. On rejection, fetch and inspect remote changes or bookmark conflicts before retrying. Do not bypass immutability or overwrite collaborators' work to make a push succeed. A jj push updates Git refs; create PRs through the hosting service's tools.
- Local operation recovery does not undo remote pushes. Inspect the operation before recovery; prefer a targeted inverse when later work must survive. Recovery can create divergent versions of a change: inspect `jj log -r 'change_id(ID)'`, select versions by commit hash, and reconcile their contents before abandoning obsolete versions. Check status, graph, bookmarks, and affected diffs after history changes.

## Sources

Workflow adapted from [Steve Klabnik's Jujutsu tutorial](https://steveklabnik.github.io/jujutsu-tutorial/introduction/introduction.html), especially [The Squash Workflow](https://steveklabnik.github.io/jujutsu-tutorial/real-world-workflows/the-squash-workflow.html). Command spellings checked against jj 0.39.0; installed CLI help takes precedence over older tutorial examples. Consult [official documentation](https://docs.jj-vcs.dev/latest/) for additional details.
