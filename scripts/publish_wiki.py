#!/usr/bin/env python3
"""
publish_wiki.py - Deploy docs/wiki/*.md directly to the GitHub Wiki git repository.
Usage: python scripts/publish_wiki.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIKI_REMOTE = "https://github.com/adamm285-dev/Spec-Driven-Cognitive-Scaffolding-SDCS.wiki.git"
SOURCE_DIR = Path(__file__).resolve().parent.parent / "docs" / "wiki"


def main() -> None:
    if not SOURCE_DIR.is_dir():
        print(f"Error: Source wiki directory not found at {SOURCE_DIR}")
        sys.exit(1)

    print(f"Deploying SDCS Wiki from: {SOURCE_DIR}")
    print(f"Target Remote: {WIKI_REMOTE}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Clone existing wiki repo
        print("Cloning GitHub Wiki repository...")
        clone_res = subprocess.run(
            ["git", "clone", WIKI_REMOTE, str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if clone_res.returncode != 0:
            print("\n❌ Failed to clone wiki repository:")
            print(clone_res.stderr)
            print(
                "\nNOTE: If this is the first time setting up the wiki, visit:"
                "\n  https://github.com/adamm285-dev/Spec-Driven-Cognitive-Scaffolding-SDCS/wiki"
                "\nand click 'Create the first page', then 'Save page' to initialize the wiki repository on GitHub."
            )
            sys.exit(1)

        # Copy all markdown files from docs/wiki
        files_copied = 0
        for md_file in SOURCE_DIR.glob("*.md"):
            dest_file = tmp_path / md_file.name
            shutil.copy2(md_file, dest_file)
            files_copied += 1

        print(f"Copied {files_copied} wiki pages.")

        # Commit and push
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.name", "Adam Murphy"], check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "config",
                "user.email",
                "316069397+adamm285-dev@users.noreply.github.com",
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)

        diff_res = subprocess.run(
            ["git", "-C", str(tmp_path), "diff", "--cached", "--quiet"],
            check=False,
        )
        if diff_res.returncode == 0:
            print("✓ Wiki is already up to date. No changes to commit.")
            return

        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-m",
                "docs: deploy SDCS v1.8.0 wiki knowledge base",
            ],
            check=True,
        )

        # Push to remote (GitHub wikis default to 'master')
        push_res = subprocess.run(
            ["git", "-C", str(tmp_path), "push", "origin", "master"],
            capture_output=True,
            text=True,
            check=False,
        )
        if push_res.returncode != 0:
            # Fallback to 'main' if GitHub uses main
            push_res = subprocess.run(
                ["git", "-C", str(tmp_path), "push", "origin", "main"],
                capture_output=True,
                text=True,
                check=False,
            )

        if push_res.returncode == 0:
            print("\n🎉 GitHub Wiki successfully published live!")
            print(
                "View it at: https://github.com/adamm285-dev/Spec-Driven-Cognitive-Scaffolding-SDCS/wiki"
            )
        else:
            print("\n❌ Failed to push wiki changes:")
            print(push_res.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
