#!/usr/bin/env python3
"""Validate every skills/<tier>/<name>/source.yaml manifest.

Tier is taken from the folder path (skills/<tier>/...), so branch
protection + CODEOWNERS can enforce review rules by path. Run from the
repo root (that's how CI invokes it):

    python scripts/validate.py
"""

import glob
import os
import sys

import yaml

REQUIRED_FIELDS = {"name", "description", "owner", "repo", "version"}
VALID_TIERS = ("project", "group", "org-wide")


def validate() -> list[str]:
    errors: list[str] = []

    for path in glob.glob("skills/*/*/source.yaml"):
        # Normalize so this behaves the same on Windows and Linux.
        norm = path.replace(os.sep, "/")
        tier = norm.split("/")[1]

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            errors.append(f"{norm}: missing fields {missing}")

        if tier == "org-wide":
            evals_path = os.path.join(os.path.dirname(path), "evals.json")
            if not os.path.exists(evals_path):
                errors.append(
                    f"{norm}: tier is org-wide but no evals.json found "
                    f"at {evals_path}"
                )

        if tier not in VALID_TIERS:
            errors.append(f"{norm}: '{tier}' is not a valid tier folder")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Manifest validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("All manifests valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
