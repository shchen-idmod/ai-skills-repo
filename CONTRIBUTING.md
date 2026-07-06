# Contributing to the AI Skills Catalog

This catalog tracks skills owned by their teams. It does not become the home
for skill source code — that stays in the owning team's own repo. This keeps
maintenance burden off catalog maintainers and keeps ownership clear.

## Adding a skill

1. Make sure your skill has a `SKILL.md` and lives in your own team's repo,
   with a tagged release/version.
2. Fork this catalog and add a new folder under `skills/<tier>/<your-skill-name>/`
   — pick `project`, `group`, or `org-wide` for `<tier>`.
3. Add a `source.yaml` manifest (see template below). `org-wide` also needs
   an `evals.json` in the same folder.
4. Open a PR. The folder path (`skills/org-wide/...` vs `skills/project/...`)
   is what triggers the right reviewer group via `CODEOWNERS` — you don't
   need to request specific reviewers manually.

### `source.yaml` template

```yaml
name: your-skill-name
description: One sentence describing what the skill does.
owner: your-team-name
repo: https://github.com/your-org/your-skill-repo
version: v1.2.0
```

(Tier is implied by the folder it's in, so it isn't repeated in the YAML.)

## Review requirements by tier

- **`project`** — 1 approval from the owning team. Fastest path, lowest bar.
- **`group`** — 1 approval from the owning team. Should include a short note
  on which group/department benefits.
- **`org-wide`** — 2 approvals from the cross-functional reviewer group
  listed in `CODEOWNERS`, **and** a passing `evals.json` run in CI. This is
  the highest bar because it represents an organization-wide commitment.

## Promoting a skill to a higher tier

Start at `project` or `group`. Once a skill has real usage outside its home
team and an eval suite, open a PR *moving its folder* from
`skills/project/<name>/` (or `group/`) to `skills/org-wide/<name>/` and add
the required `evals.json`. The PR review is where the promotion gets
scrutinized — this is intentional; promotion should be earned by usage, not
requested upfront.

## Deprecating a skill

If an owning team goes silent (no response to issues/PRs for 60 days) or a
skill is superseded, any catalog maintainer can open a PR moving the skill's
folder to `skills/_deprecated/` with a short reason in the manifest. This
does not delete history — it just removes it from active discovery.

## What we deliberately don't do here

- We don't host skill source (`SKILL.md`, scripts, etc.) directly in this
  repo. Skills stay in their owners' repos; we track a pinned version.
- We don't require an eval suite for `project`/`group` tier skills. Evals
  are only a hard gate for `org-wide`, so we don't block small, low-stakes
  contributions with process meant for foundation-wide commitments.
