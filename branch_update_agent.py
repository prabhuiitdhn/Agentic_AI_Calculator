from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


class GitCommandError(RuntimeError):
    pass


class BranchUpdateAgent:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        print("\nGitHub Branch Update Agent\n")
        repo_url = input("GitHub repo URL (https://github.com/user/repo.git): ").strip()
        if not repo_url:
            print("Repo URL is required.")
            return

        repo_name = self._repo_name_from_url(repo_url)
        repo_path = self.base_dir / repo_name

        self._clone_or_fetch(repo_url, repo_path)
        branches = self._get_remote_branches(repo_path)
        if not branches:
            print("No remote branches found.")
            return

        selected = self._choose_branches(branches)
        if not selected:
            print("No branches selected.")
            return

        file_path = input("File path to update (relative to repo): ").strip()
        if not file_path:
            print("File path is required.")
            return

        find_text = input("Find text: ")
        if find_text == "":
            print("Find text cannot be empty.")
            return

        replace_text = input("Replace with: ")
        commit_message = input("Commit message: ").strip() or "chore: branch-wise automated update"
        should_push = input("Push changes to origin? (y/n): ").strip().lower() == "y"

        for branch in selected:
            print(f"\n--- Processing branch: {branch} ---")
            try:
                changed = self._update_branch(
                    repo_path=repo_path,
                    branch=branch,
                    rel_file_path=file_path,
                    find_text=find_text,
                    replace_text=replace_text,
                    commit_message=commit_message,
                    should_push=should_push,
                )
                if changed:
                    print(f"Updated branch: {branch}")
                else:
                    print(f"No changes needed on branch: {branch}")
            except GitCommandError as exc:
                print(f"Failed on branch {branch}: {exc}")

    def _clone_or_fetch(self, repo_url: str, repo_path: Path) -> None:
        if repo_path.exists():
            print(f"Using existing repo at {repo_path}")
            if not (repo_path / ".git").exists():
                raise GitCommandError(
                    f"Path exists but is not a git repo: {repo_path}. Remove it or use a different repo URL."
                )
            self._git(["fetch", "--all", "--prune"], cwd=repo_path)
            return

        print(f"Cloning into {repo_path} ...")
        self._git(["clone", repo_url, str(repo_path)], cwd=self.base_dir)

    def _get_remote_branches(self, repo_path: Path) -> list[str]:
        remote_output = self._git(["branch", "-r"], cwd=repo_path)
        remote_branches: list[str] = []
        for line in remote_output.splitlines():
            item = line.strip()
            if not item or "->" in item:
                continue
            if item.startswith("origin/"):
                remote_branches.append(item.replace("origin/", "", 1))

        unique_remote = sorted(set(remote_branches))
        if unique_remote:
            print("Available branches:")
            for idx, branch in enumerate(unique_remote, start=1):
                print(f"  {idx}. {branch}")
            return unique_remote

        # Fallback: some repos or permissions expose local refs but not remote listing.
        local_output = self._git(["branch"], cwd=repo_path)
        local_branches: list[str] = []
        for line in local_output.splitlines():
            item = line.replace("*", "", 1).strip()
            if item:
                local_branches.append(item)

        unique_local = sorted(set(local_branches))
        if unique_local:
            print("Available branches (local fallback):")
            for idx, branch in enumerate(unique_local, start=1):
                print(f"  {idx}. {branch}")
            return unique_local

        try:
            current = self._git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path).strip()
            if current and current != "HEAD":
                print("Available branches (current fallback):")
                print(f"  1. {current}")
                return [current]
        except GitCommandError:
            # Repos with no commits/default branch can fail rev-parse HEAD.
            pass

        print(
            "No branches detected from remote/local/current refs. "
            "This usually means the repo has no commits yet or your fetch did not include refs."
        )

        return []

    def _choose_branches(self, branches: list[str]) -> list[str]:
        raw = input("Choose branches by number (comma) or type 'all': ").strip().lower()
        if raw == "all":
            return branches

        selected: list[str] = []
        for token in raw.split(","):
            token = token.strip()
            if not token.isdigit():
                continue
            idx = int(token)
            if 1 <= idx <= len(branches):
                selected.append(branches[idx - 1])
        return sorted(set(selected))

    def _update_branch(
        self,
        repo_path: Path,
        branch: str,
        rel_file_path: str,
        find_text: str,
        replace_text: str,
        commit_message: str,
        should_push: bool,
    ) -> bool:
        self._git(["checkout", branch], cwd=repo_path)
        self._git(["pull", "origin", branch], cwd=repo_path)

        target = repo_path / rel_file_path
        if not target.exists():
            raise GitCommandError(f"File not found: {rel_file_path}")

        original = target.read_text(encoding="utf-8")
        updated = original.replace(find_text, replace_text)
        if updated == original:
            return False

        target.write_text(updated, encoding="utf-8")
        self._git(["add", rel_file_path], cwd=repo_path)

        status = self._git(["status", "--porcelain"], cwd=repo_path)
        if not status.strip():
            return False

        self._git(["commit", "-m", commit_message], cwd=repo_path)
        if should_push:
            self._git(["push", "origin", branch], cwd=repo_path)
        return True

    def _git(self, args: list[str], cwd: Path) -> str:
        if not cwd.exists() or not cwd.is_dir():
            raise GitCommandError(f"Invalid working directory for git command: {cwd}")

        cmd = ["git", *args]
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                check=False,
            )
        except OSError as exc:
            raise GitCommandError(
                f"Failed to run git in '{cwd}': {exc}"
            ) from exc

        if result.returncode != 0:
            raise GitCommandError(result.stderr.strip() or result.stdout.strip() or str(cmd))
        return result.stdout.strip()

    def _repo_name_from_url(self, repo_url: str) -> str:
        parsed = urlparse(repo_url.strip())
        path = parsed.path if parsed.path else repo_url.strip()
        name = path.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        if not name:
            raise GitCommandError(
                "Could not derive a valid repo folder name from URL. Use format like https://github.com/user/repo.git"
            )
        return name


if __name__ == "__main__":
    agent = BranchUpdateAgent(base_dir=Path("./repos"))
    try:
        agent.run()
    except GitCommandError as exc:
        print(f"Error: {exc}")
