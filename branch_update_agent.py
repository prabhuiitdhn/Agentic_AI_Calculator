from __future__ import annotations

import os
import re
import shutil
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

        print("\nChoose mode:")
        print("  1. Main branch")
        print("  2. Any other branch")
        mode = input("mode> ").strip().lower()

        if mode in {"1", "main"}:
            self._run_publish_mode_main(repo_path=repo_path, existing_branches=branches)
            return

        if mode in {"2", "other", "branch"}:
            self._run_publish_mode_other(repo_path=repo_path, existing_branches=branches)
            return

        print("Invalid mode. Choose 1 or 2.")

    def _run_publish_mode_main(self, repo_path: Path, existing_branches: list[str]) -> None:
        source_path, commit_message, should_push = self._collect_publish_inputs()
        if source_path is None:
            return

        print("\n--- Publishing source to branch: main ---")
        try:
            base_branch = self._suggest_base_branch(existing_branches)
            changed = self._publish_source_to_branch(
                repo_path=repo_path,
                source_path=source_path,
                new_branch="main",
                base_branch=base_branch,
                commit_message=commit_message,
                should_push=should_push,
            )
            if changed:
                print("Published updates on branch: main")
            else:
                print("No content changes on branch: main")
        except GitCommandError as exc:
            print(f"Failed on branch main: {exc}")

    def _run_publish_mode_other(self, repo_path: Path, existing_branches: list[str]) -> None:
        branch_name = input("Branch name: ").strip()
        if not branch_name:
            print("Branch name is required.")
            return

        source_path, commit_message, should_push = self._collect_publish_inputs()
        if source_path is None:
            return

        print(f"\n--- Publishing source to branch: {branch_name} ---")
        try:
            base_branch = self._suggest_base_branch(existing_branches)
            changed = self._publish_source_to_branch(
                repo_path=repo_path,
                source_path=source_path,
                new_branch=branch_name,
                base_branch=base_branch,
                commit_message=commit_message,
                should_push=should_push,
            )
            if changed:
                print(f"Published updates on branch: {branch_name}")
            else:
                print(f"No content changes on branch: {branch_name}")
        except GitCommandError as exc:
            print(f"Failed on branch {branch_name}: {exc}")

    def _collect_publish_inputs(self) -> tuple[Path | None, str, bool]:
        source_default = Path(__file__).resolve().parent
        source_raw = input(
            f"Source project path to upload [{source_default}]: "
        ).strip()
        source_path = Path(source_raw).expanduser().resolve() if source_raw else source_default
        if not source_path.exists() or not source_path.is_dir():
            print(f"Invalid source path: {source_path}")
            return None, "", False

        commit_message = input("Commit message: ").strip() or "feat: project snapshot update"
        should_push = input("Push branches to origin? (y/n): ").strip().lower() == "y"
        return source_path, commit_message, should_push

    def _suggest_base_branch(self, existing_branches: list[str]) -> str:
        if "main" in existing_branches:
            return "main"
        if "master" in existing_branches:
            return "master"
        if existing_branches:
            return existing_branches[0]
        return ""

    def _publish_source_to_branch(
        self,
        repo_path: Path,
        source_path: Path,
        new_branch: str,
        base_branch: str,
        commit_message: str,
        should_push: bool,
    ) -> bool:
        if self._local_branch_exists(repo_path, new_branch):
            self._git(["checkout", new_branch], cwd=repo_path)
            try:
                self._git(["pull", "origin", new_branch], cwd=repo_path)
            except GitCommandError:
                pass
        elif self._remote_branch_exists(repo_path, new_branch):
            self._git(["checkout", "-b", new_branch, f"origin/{new_branch}"], cwd=repo_path)
        else:
            if base_branch and self._branch_exists(repo_path, base_branch):
                if self._local_branch_exists(repo_path, base_branch):
                    self._git(["checkout", base_branch], cwd=repo_path)
                else:
                    self._git(["checkout", "-b", base_branch, f"origin/{base_branch}"], cwd=repo_path)
                try:
                    self._git(["pull", "origin", base_branch], cwd=repo_path)
                except GitCommandError:
                    pass
                self._git(["checkout", "-b", new_branch], cwd=repo_path)
            else:
                self._git(["checkout", "--orphan", new_branch], cwd=repo_path)

        self._sync_source_to_repo(source_path=source_path, repo_path=repo_path)
        self._git(["add", "-A"], cwd=repo_path)

        status = self._git(["status", "--porcelain"], cwd=repo_path)
        if not status.strip():
            if should_push:
                try:
                    self._git(["push", "-u", "origin", new_branch], cwd=repo_path)
                except GitCommandError:
                    pass
            return False

        self._git(["commit", "-m", commit_message], cwd=repo_path)
        if should_push:
            self._git(["push", "-u", "origin", new_branch], cwd=repo_path)
        return True

    def _sync_source_to_repo(self, source_path: Path, repo_path: Path) -> None:
        exclude_dirs = {
            ".git",
            "repos",
            "__pycache__",
            ".venv",
            ".mypy_cache",
            ".pytest_cache",
        }

        copied_rel_paths: set[str] = set()
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            root_path = Path(root)
            for filename in files:
                if filename.endswith(".pyc"):
                    continue
                src_file = root_path / filename
                rel = src_file.relative_to(source_path)
                rel_posix = rel.as_posix()
                copied_rel_paths.add(rel_posix)

                dst_file = repo_path / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            root_path = Path(root)
            for filename in files:
                rel = (root_path / filename).relative_to(repo_path).as_posix()
                if rel not in copied_rel_paths:
                    (root_path / filename).unlink()

        for root, dirs, _ in os.walk(repo_path, topdown=False):
            for dirname in dirs:
                dir_path = Path(root) / dirname
                if dir_path.name in exclude_dirs:
                    continue
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()

    def _branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        return self._local_branch_exists(repo_path, branch_name) or self._remote_branch_exists(
            repo_path, branch_name
        )

    def _local_branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        try:
            self._git(["show-ref", "--verify", f"refs/heads/{branch_name}"], cwd=repo_path)
            return True
        except GitCommandError:
            return False

    def _remote_branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        try:
            self._git(["show-ref", "--verify", f"refs/remotes/origin/{branch_name}"], cwd=repo_path)
            return True
        except GitCommandError:
            return False

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
