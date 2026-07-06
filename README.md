# AI Skills Catalog

A governed catalog of Claude / AI tool skills shared across teams. Skills are
**owned by their teams and live in their teams' own repos** — this catalog
tracks them, pins versions, records ownership/tier, and runs their evals. It
does not host skill source code directly (see `CONTRIBUTING.md` for why).

## Structure

```
skills/
  project/<skill-name>/source.yaml
  group/<skill-name>/source.yaml
  org-wide/<skill-name>/source.yaml   # requires evals.json too
.github/
  workflows/
    validate.yml     # CI: validates manifests + runs evals
CONTRIBUTING.md       # how to propose/add a skill, review requirements
CODEOWNERS            # who must approve which tier of changes
```

Tier lives in the **folder path**, not just the YAML field, so GitHub's
branch protection + `CODEOWNERS` can actually enforce the approval rules
automatically — GitHub can't read a YAML field to decide who must review,
but it can read a path.

## Tiers

| Tier | Meaning | Approvals required |
|---|---|---|
| `project` | Used by a single project/team | 1 (owning team) |
| `group` | Shared across a group (e.g. a department) | 1 (owning team) |
| `org-wide` | Shared across the whole organization | 2 (cross-functional, see CODEOWNERS) |

See `CONTRIBUTING.md` for the full process.
