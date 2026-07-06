#!/usr/bin/env python3
"""Install a catalogued skill into a Claude Code skills directory.

This catalog only stores pointers (source.yaml). This script reads a
skill's manifest, fetches the real skill folder from the owning repo at
the pinned version, and copies it where Claude Code discovers skills.

Usage:
    python scripts/install.py <skill-name>              # -> ~/.claude/skills/
    python scripts/install.py <skill-name> --project    # -> ./.claude/skills/
    python scripts/install.py <skill-name> --dest DIR    # -> DIR/<name>/

Exit codes: 0 ok, 1 usage/not-found, 2 fetch/copy failure.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

import yaml


def find_manifest(skill_name: str) -> str | None:
    """Return the source.yaml path for a skill name, or None."""
    for path in glob.glob("skills/*/*/source.yaml"):
        norm = path.replace(os.sep, "/")
        # folder name is the second-to-last path component
        if norm.split("/")[-2] == skill_name:
            return path
    return None


def ref_exists(repo: str, ref: str) -> bool:
    """True if ref resolves to a tag or branch in the remote repo."""
    result = subprocess.run(
        ["git", "ls-remote", repo, f"refs/tags/{ref}", f"refs/heads/{ref}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def run(cmd: list[str], cwd: str | None = None) -> None:
    """Run a command, raising RuntimeError with context on failure."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"{result.stderr.strip()}"
        )


def fetch_skill(repo: str, ref: str, subpath: str, work: str) -> str:
    """Sparse-checkout subpath at ref into work/; return path to the folder."""
    clone_dir = os.path.join(work, "src")
    run([
        "git", "clone", "--no-checkout", "--depth", "1",
        "--filter=blob:none", "--branch", ref, repo, clone_dir,
    ])
    run(["git", "sparse-checkout", "set", subpath], cwd=clone_dir)
    run(["git", "checkout", ref], cwd=clone_dir)

    fetched = os.path.join(clone_dir, subpath.replace("/", os.sep))
    if not os.path.isdir(fetched):
        raise RuntimeError(
            f"path '{subpath}' not found in {repo} at {ref} "
            f"(is the manifest's path: field correct?)"
        )
    if not os.path.isfile(os.path.join(fetched, "SKILL.md")):
        raise RuntimeError(f"no SKILL.md in {subpath} — not a valid skill folder")
    return fetched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="skill name (the folder under skills/<tier>/)")
    dest = parser.add_mutually_exclusive_group()
    dest.add_argument("--project", action="store_true",
                      help="install into ./.claude/skills/ instead of ~/.claude/skills/")
    dest.add_argument("--dest", metavar="DIR",
                      help="install into a custom skills directory")
    args = parser.parse_args()

    manifest_path = find_manifest(args.skill)
    if not manifest_path:
        print(f"error: no skill named '{args.skill}' in this catalog", file=sys.stderr)
        print("       (looked under skills/*/<name>/source.yaml)", file=sys.stderr)
        return 1

    with open(manifest_path) as f:
        m = yaml.safe_load(f) or {}

    repo = m.get("repo")
    version = m.get("version")
    subpath = m.get("path")
    if not repo:
        print(f"error: {manifest_path} is missing the repo field", file=sys.stderr)
        return 1
    if not subpath:
        # Skill lives at the repo root when no path: field is present.
        subpath = "."

    # Resolve the version; fall back to the default branch if it is missing
    # or is not an actual tag/branch in the source repo.
    if version and ref_exists(repo, version):
        ref = version
    else:
        reason = ("no version pinned in the manifest" if not version
                  else f"version '{version}' is not a tag/branch in {repo}")
        print(f"warning: {reason}; falling back to the default branch. The "
              f"installed skill will NOT be pinned - ask the owner to tag a "
              f"release.", file=sys.stderr)
        default = subprocess.run(
            ["git", "ls-remote", "--symref", repo, "HEAD"],
            capture_output=True, text=True,
        ).stdout
        ref = "main"
        for line in default.splitlines():
            if line.startswith("ref:"):
                ref = line.split("refs/heads/")[-1].split()[0]
                break

    if args.dest:
        skills_dir = args.dest
    elif args.project:
        skills_dir = os.path.join(".claude", "skills")
    else:
        skills_dir = os.path.join(os.path.expanduser("~"), ".claude", "skills")

    target = os.path.join(skills_dir, args.skill)

    try:
        with tempfile.TemporaryDirectory() as work:
            fetched = fetch_skill(repo, ref, subpath, work)
            if os.path.exists(target):
                print(f"note: replacing existing {target}")
                shutil.rmtree(target)
            os.makedirs(skills_dir, exist_ok=True)
            shutil.copytree(fetched, target)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"Installed '{args.skill}' ({ref}) -> {target}")
    print("Restart Claude Code (or start a new session) to pick it up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
