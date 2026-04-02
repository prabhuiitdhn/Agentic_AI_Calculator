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
        self.repo_path: Path | None = None

    def run(self) -> None:
        print("\nGitHub Helper Agent\n")
        repo_url = input("GitHub repo URL (https://github.com/user/repo.git): ").strip()
        if not repo_url:
            print("Repo URL is required.")
            return

        self.repo_path = self._resolve_working_repo(repo_url)
        self._ensure_origin(repo_url, self.repo_path)
        self._safe_git(["fetch", "--all", "--prune"], self.repo_path)

        print("\nChoose mode:")
<<<<<<< Updated upstream
        print("  1. Main branch")
        print("  2. Any other branch")
        print("  3. Pull latest code")
=======
        print("  1. Push current code to main")
        print("  2. Push current code to another branch")
        print("  3. Pull latest code to local repo")
>>>>>>> Stashed changes
        mode = input("mode> ").strip().lower()

        if mode in {"1", "main"}:
            self._push_to_main(self.repo_path)
            return

        if mode in {"2", "other", "branch"}:
            self._push_to_named_branch(self.repo_path)
            return

        if mode in {"3", "pull", "latest"}:
<<<<<<< Updated upstream
            self._run_pull_latest_mode(repo_path=repo_path, existing_branches=branches)
            return

        print("Invalid mode. Choose 1, 2 or 3.")

    def _run_publish_mode_main(self, repo_path: Path, existing_branches: list[str]) -> None:
        source_path, commit_message, should_push = self._collect_publish_inputs()
        if source_path is None:
=======
            self._pull_latest_to_local(self.repo_path)
>>>>>>> Stashed changes
            return

        print("Invalid mode. Choose 1, 2 or 3.")

    def _push_to_main(self, repo_path: Path) -> None:
        commit_message = input("Commit message [chore: update main]: ").strip() or "chore: update main"
        self._checkout_branch(repo_path, "main", base_branch="main")
        self._stash_and_pull(repo_path, "main")
        changed = self._commit_all(repo_path, commit_message)
        if changed:
            self._safe_git(["push", "-u", "origin", "main"], repo_path)
            print("Pushed latest code to main.")
        else:
            print("No local changes to commit on main.")
        self._stash_and_pull(repo_path, "main")
        print("Local repo synced with latest main.")

    def _push_to_named_branch(self, repo_path: Path) -> None:
        branch_name = input("Branch name: ").strip()
        if not branch_name:
            print("Branch name is required.")
            return

        commit_message = (
            input("Commit message [feat: advanced update]: ").strip()
            or "feat: advanced update"
        )
        self._checkout_branch(repo_path, branch_name, base_branch="main")
        self._stash_and_pull(repo_path, branch_name)
        changed = self._commit_all(repo_path, commit_message)
        if changed:
            self._safe_git(["push", "-u", "origin", branch_name], repo_path)
            print(f"Pushed latest code to branch: {branch_name}")
        else:
            print(f"No local changes to commit on branch: {branch_name}")
        self._stash_and_pull(repo_path, branch_name)
        print(f"Local repo synced with latest {branch_name}.")

    def _pull_latest_to_local(self, repo_path: Path) -> None:
        default_branch = self._current_branch(repo_path) or "main"
        branch_name = input(f"Branch to sync [{default_branch}]: ").strip() or default_branch
        self._checkout_branch(repo_path, branch_name, base_branch="main")
        self._stash_and_pull(repo_path, branch_name)
        print(f"Local repo synced with latest {branch_name}.")

    def _resolve_working_repo(self, repo_url: str) -> Path:
        default_repo = Path(__file__).resolve().parent
        repo_input = input(f"Local development repo path [{default_repo}]: ").strip()
        candidate = Path(repo_input).expanduser().resolve() if repo_input else default_repo

        if (candidate / ".git").exists():
            print(f"Using local repo: {candidate}")
            return candidate

        repo_name = self._repo_name_from_url(repo_url)
        clone_path = self.base_dir / repo_name
        if (clone_path / ".git").exists():
            print(f"Using cached clone: {clone_path}")
            return clone_path

        print(f"Local path is not a git repo. Cloning to {clone_path} ...")
        self._safe_git(["clone", repo_url, str(clone_path)], self.base_dir)
        return clone_path

    def _ensure_origin(self, repo_url: str, repo_path: Path) -> None:
        remote_output = self._safe_git(["remote"], repo_path)
        remotes = {line.strip() for line in remote_output.splitlines() if line.strip()}
        if "origin" not in remotes:
            self._safe_git(["remote", "add", "origin", repo_url], repo_path)
            return

        self._safe_git(["remote", "set-url", "origin", repo_url], repo_path)

    def _checkout_branch(self, repo_path: Path, branch_name: str, base_branch: str = "main") -> None:
        if self._local_branch_exists(repo_path, branch_name):
            self._safe_git(["checkout", branch_name], repo_path)
            return

        if self._remote_branch_exists(repo_path, branch_name):
            self._safe_git(["checkout", "-b", branch_name, f"origin/{branch_name}"], repo_path)
            return

        if self._local_branch_exists(repo_path, base_branch):
            self._safe_git(["checkout", base_branch], repo_path)
            self._safe_git(["checkout", "-b", branch_name], repo_path)
            return

        if self._remote_branch_exists(repo_path, base_branch):
            self._safe_git(["checkout", "-b", base_branch, f"origin/{base_branch}"], repo_path)
            self._safe_git(["checkout", "-b", branch_name], repo_path)
            return

        # Repo may be empty or not have main/master yet.
        self._safe_git(["checkout", "--orphan", branch_name], repo_path)

    def _stash_and_pull(self, repo_path: Path, branch_name: str) -> None:
        stash_output = self._safe_git(["stash", "push", "-u", "-m", "agent-auto-stash"], repo_path)
        stashed = "No local changes" not in stash_output
        try:
<<<<<<< Updated upstream
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

    def _run_pull_latest_mode(self, repo_path: Path, existing_branches: list[str]) -> None:
        default_branch = self._suggest_base_branch(existing_branches) or "main"
        branch_name = input(f"Branch to pull [{default_branch}]: ").strip() or default_branch
        try:
            self._pull_latest(repo_path=repo_path, branch_name=branch_name)
            print(f"Pulled latest code for branch: {branch_name}")
        except GitCommandError as exc:
            print(f"Failed to pull branch {branch_name}: {exc}")

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
=======
            self._safe_git(["pull", "origin", branch_name], repo_path)
        finally:
            if stashed:
>>>>>>> Stashed changes
                try:
                    self._safe_git(["stash", "pop"], repo_path)
                except GitCommandError as exc:
                    print(f"Warning: stash pop had conflicts — resolve manually: {exc}")

    def _commit_all(self, repo_path: Path, message: str) -> bool:
        self._safe_git(["add", "-A"], repo_path)
        status = self._safe_git(["status", "--porcelain"], repo_path)
        if not status.strip():
            return False
<<<<<<< Updated upstream

        self._git(["commit", "-m", commit_message], cwd=repo_path)
        if should_push:
            self._git(["push", "-u", "origin", new_branch], cwd=repo_path)
            try:
                self._pull_latest(repo_path=repo_path, branch_name=new_branch)
                print(f"Pulled latest after push for branch: {new_branch}")
            except GitCommandError:
                pass
        return True

    def _pull_latest(self, repo_path: Path, branch_name: str) -> None:
        if self._local_branch_exists(repo_path, branch_name):
            self._git(["checkout", branch_name], cwd=repo_path)
        elif self._remote_branch_exists(repo_path, branch_name):
            self._git(["checkout", "-b", branch_name, f"origin/{branch_name}"], cwd=repo_path)
        else:
            raise GitCommandError(f"Branch not found locally or on origin: {branch_name}")

        self._git(["fetch", "origin", branch_name], cwd=repo_path)
        self._git(["pull", "origin", branch_name], cwd=repo_path)

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
=======
        self._safe_git(["commit", "-m", message], repo_path)
        return True

    def _current_branch(self, repo_path: Path) -> str:
        try:
            branch = self._safe_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path).strip()
            if branch and branch != "HEAD":
                return branch
        except GitCommandError:
            pass
        return ""
>>>>>>> Stashed changes

    def _local_branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        try:
            self._safe_git(["show-ref", "--verify", f"refs/heads/{branch_name}"], repo_path)
            return True
        except GitCommandError:
            return False

    def _remote_branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        try:
            self._safe_git(["show-ref", "--verify", f"refs/remotes/origin/{branch_name}"], repo_path)
            return True
        except GitCommandError:
            return False

    def _safe_git(self, args: list[str], cwd: Path) -> str:
        if not cwd.exists() or not cwd.is_dir():
            raise GitCommandError(f"Invalid working directory: {cwd}")

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
            raise GitCommandError(f"Failed to run git in {cwd}: {exc}") from exc

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

