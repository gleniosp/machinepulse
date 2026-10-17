---
name: pull-request
description: Prepare or raise a MachinePulse pull request against main with an evidence-backed summary and issue-closing references.
---

# Pull Request

Use this skill when the maintainer asks to prepare or raise a pull request for
MachinePulse. For phase work, also follow the [phase-delivery skill](../phase-delivery/SKILL.md).

1. Read the [working agreement](../../../docs/working-agreement.md). Confirm the
   intended base is `main`, inspect the latest `origin/main`, and review the
   complete branch diff plus staged, unstaged, and untracked changes.
2. Write a short title without Conventional Commit prefixes such as `feat:` or
   `docs:`. Summarize the actual scope in the description, list validation that
   passed, and state material limits. Do not claim work absent from the diff or
   evidence.
3. Verify each referenced GitHub issue and its acceptance evidence. Add
   `Closes #N` for issues this PR completes; GitHub closes them on merge. Do not
   close issues manually before merge.
4. The maintainer owns branches and commits. If asked only to prepare PR
   content, return the title and description without publishing. Create a PR
   only when explicitly asked, and only after its intended changes are
   committed and pushed; use `gh pr create --base main` and check for an
   existing PR first.
