"""Git utilities: branch/commit info and .gitignore-based file filtering."""

import fnmatch
import logging
import subprocess
from pathlib import Path


def get_git_info(input_dir: Path) -> str:
    if not (input_dir / ".git").exists():
        return "No Git"
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch_name = branch.stdout.strip() if branch.returncode == 0 else "N/A"

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = commit.stdout.strip() if commit.returncode == 0 else "N/A"

        return f"Branch: {branch_name} | Last Commit: {commit_hash}"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return "No Git"


def should_skip_gitignore(input_dir: Path, file_path: Path) -> bool:
    try:
        rel = file_path.relative_to(input_dir)
    except ValueError:
        return False

    parts = rel.parts
    current_dir = input_dir

    for i in range(len(parts)):
        gitignore_path = current_dir / ".gitignore"
        if gitignore_path.exists():
            sub_rel = "/".join(parts[i:])
            try:
                skip = False
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        rule = line.strip()
                        if rule.startswith("#") or not rule:
                            continue
                        negate = rule.startswith("!")
                        effective_rule = rule[1:] if negate else rule
                        if "*" in effective_rule:
                            matched = fnmatch.fnmatch(sub_rel, effective_rule)
                        elif effective_rule.endswith("/"):
                            base = effective_rule.rstrip("/")
                            matched = sub_rel == base or sub_rel.startswith(base + "/")
                        else:
                            matched = sub_rel == effective_rule
                        if matched:
                            skip = not negate
                if skip:
                    return True
            except Exception:
                pass
        if i < len(parts) - 1:
            current_dir = current_dir / parts[i]

    return False
