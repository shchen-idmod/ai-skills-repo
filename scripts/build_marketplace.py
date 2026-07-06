#!/usr/bin/env python3
"""Generate a Claude Code plugin marketplace from the catalog manifests.

This catalog stores only pointers (source.yaml). Claude Desktop / Code,
however, install skills from a *marketplace* (a repo with
.claude-plugin/marketplace.json). This script bridges the two: it reads
every skills/<tier>/<name>/source.yaml, fetches each skill from its
owning repo at the pinned version, and assembles a marketplace tree:

    <out>/
      .claude-plugin/marketplace.json
      plugins/<plugin>/.claude-plugin/plugin.json
      plugins/<plugin>/skills/<name>/SKILL.md (+ supporting files)

Skills are grouped into one plugin per manifest `owner` (so each team's
skills ship as a single installable plugin). Push <out> to a repo and
users add it with:  /plugin marketplace add <repo>

Usage:
    python scripts/build_marketplace.py --out dist/marketplace
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

# install.py lives alongside this script; reuse its fetch logic.
from install import fetch_skill, ref_exists

MARKETPLACE_NAME = "gf-skills"
MARKETPLACE_OWNER = "bmgf"
SCHEMA_MARKET = "https://json.schemastore.org/claude-code-marketplace.json"
SCHEMA_PLUGIN = "https://json.schemastore.org/claude-code-plugin.json"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "skills"


def plugin_name_for(owner: str) -> str:
    """Derive a plugin name from an owner field (email or team name)."""
    return slugify((owner or "").split("@")[0]) or "skills"


def resolve_ref(repo: str, version: str | None) -> tuple[str, str | None]:
    """Return (ref, warning). Use the pinned version if it exists as a
    tag/branch; otherwise fall back to the repo's default branch."""
    if version and ref_exists(repo, version):
        return version, None
    out = subprocess.run(
        ["git", "ls-remote", "--symref", repo, "HEAD"],
        capture_output=True, text=True,
    ).stdout
    ref = "main"
    for line in out.splitlines():
        if line.startswith("ref:"):
            ref = line.split("refs/heads/")[-1].split()[0]
            break
    reason = ("no version pinned" if not version
              else f"version '{version}' not a tag/branch")
    return ref, f"{reason}; used default branch '{ref}' (unpinned)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist/marketplace",
                    help="output directory for the marketplace (default: dist/marketplace)")
    args = ap.parse_args()

    manifests = sorted(glob.glob("skills/*/*/source.yaml"))
    if not manifests:
        print("error: no manifests under skills/*/*/source.yaml", file=sys.stderr)
        return 1

    # Group manifests into plugins by owner.
    plugins: dict[str, list[dict]] = {}
    for mp in manifests:
        with open(mp) as f:
            data = yaml.safe_load(f) or {}
        data["_name"] = data.get("name") or os.path.basename(os.path.dirname(mp))
        data["_manifest"] = mp.replace(os.sep, "/")
        plugins.setdefault(plugin_name_for(data.get("owner", "")), []).append(data)

    out = args.out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, ".claude-plugin"))

    market = {
        "$schema": SCHEMA_MARKET,
        "name": MARKETPLACE_NAME,
        "owner": {"name": MARKETPLACE_OWNER},
        "description": "Generated from the AI Skills Catalog - do not edit by hand.",
        "plugins": [],
    }
    warnings: list[str] = []
    installed = 0

    with tempfile.TemporaryDirectory() as work:
        for pname, entries in sorted(plugins.items()):
            pdir = os.path.join(out, "plugins", pname)
            os.makedirs(os.path.join(pdir, ".claude-plugin"))
            skills_dir = os.path.join(pdir, "skills")
            os.makedirs(skills_dir)
            owner = entries[0].get("owner", "unknown")
            plugin_skills = 0

            for data in entries:
                name, repo = data["_name"], data.get("repo")
                subpath = data.get("path") or "."
                if not repo:
                    warnings.append(f"{data['_manifest']}: no repo field, skipped")
                    continue
                ref, warn = resolve_ref(repo, data.get("version"))
                if warn:
                    warnings.append(f"{name}: {warn}")
                skill_work = tempfile.mkdtemp(dir=work)
                try:
                    fetched = fetch_skill(repo, ref, subpath, skill_work)
                except RuntimeError as e:
                    warnings.append(f"{name}: fetch failed ({repo}@{ref}): {e}")
                    continue
                shutil.copytree(fetched, os.path.join(skills_dir, name))
                installed += 1
                plugin_skills += 1

            # A plugin with no successfully-fetched skills is useless — drop it.
            if plugin_skills == 0:
                warnings.append(f"plugin '{pname}': no skills fetched, omitted")
                shutil.rmtree(pdir)
                continue

            with open(os.path.join(pdir, ".claude-plugin", "plugin.json"), "w") as f:
                json.dump({
                    "$schema": SCHEMA_PLUGIN,
                    "name": pname,
                    "version": "0.1.0",
                    "description": f"Skills owned by {owner}.",
                    "author": {"name": MARKETPLACE_OWNER},
                }, f, indent=2)

            market["plugins"].append({
                "name": pname,
                "description": f"Skills owned by {owner}.",
                "source": f"./plugins/{pname}",
            })

    with open(os.path.join(out, ".claude-plugin", "marketplace.json"), "w") as f:
        json.dump(market, f, indent=2)

    print(f"Wrote {out}/ - {len(market['plugins'])} plugin(s), {installed} skill(s).")
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)
    print(f"\nAdd it in Claude Desktop/Code:  /plugin marketplace add <repo-or-path>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
