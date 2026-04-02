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
        print("  1. Push current code to main")
        print("  2. Push current code to another/current branch")
        print("  3. Pull latest code to local repo")
        mode = input("mode> ").strip().lower()

        if mode in {"1", "main"}:
            self._push_to_main(self.repo_path)
        elif mode in {"2", "other", "branch"}:
            self._push_to_named_branch(self.repo_path)
        elif mode in {"3", "pull", "latest"}:
            self._pull_latest_to_local(self.repo_path)
        else:
            print("Invalid mode. Choose 1, 2 or 3.")

    # ------------------------------------------------------------------ modes

    def _push_to_main(self, repo_path: Path) -> None:
        commit_message = (
            input("Commit message [chore: update main]: ").strip() or "chore: update main"
        )
        self._checkout_branch_with_stash(repo_path, "main")
        self._stash_and_pull(repo_path, "main")
        if self._commit_all(repo_path, commit_message):
            self._safe_git(["push", "-u", "origin", "main"], repo_path)
            print("Pushed latest code to main.")
        else:
            print("No local changes to commit on main.")
        self._stash_and_pull(repo_path, "main")
        print("Local repo synced with latest main.")

    def _push_to_named_branch(self, repo_path: Path) -> None:
        default_branch = self._current_branch(repo_path) or "main"
        branch_name = (
            input(f"Branch name [{default_branch}]: ").strip().strip("\"'") or default_branch
        )
        if not branch_name:
            print("Branch name is required.")
            return
        commit_message = (
            input("Commit message [feat: advanced update]: ").strip().strip("\"'")
            or "feat: advanced update"
        )
        self._checkout_branch_with_stash(repo_path, branch_name)
        self._stash_and_pull(repo_path, branch_name)
        if self._commit_all(repo_path, commit_message):
            self._safe_git(["push", "-u", "origin", branch_name], repo_path)
            print(f"Pushed latest code to branch: {branch_name}")
        else:
            print(f"No local changes to commit on branch: {branch_name}")
        self._stash_and_pull(repo_path, branch_name)
        print(f"Local repo synced with latest {branch_name}.")

    def _pull_latest_to_local(self, repo_path: Path) -> None:
        default_branch = self._current_branch(repo_path) or "main"
        branch_name = (
            input(f"Branch to sync [{default_branch}]: ").strip() or default_branch
        )
        self._checkout_branch_with_stash(repo_path, branch_name)
        self._stash_and_pull(repo_path, branch_name)
        print(f"Local repo synced with latest {branch_name}.")

    # ---------------------------------------------------------- git helpers

    def _checkout_branch_with_stash(self, repo_path: Path, branch_name: str) -> None:
        stash_out = self._safe_git(["stash", "push", "-u", "-m", "agent-pre-checkout"], repo_path)
        stashed = "No local changes" not in stash_out
        try:
            self._checkout_branch(repo_path, branch_name)
        finally:
            if stashed:
                try:
                    self._safe_git(["stash", "pop"], repo_path)
                except GitCommandError as exc:
                    print(f"Warning: stash pop had conflicts - resolve manually.\n  {exc}")

    def _stash_and_pull(self, repo_path: Path, branch_name: str) -> None:
        stash_out = self._safe_git(["stash", "push", "-u", "-m", "agent-auto-stash"], repo_path)
        stashed = "No local changes" not in stash_out
        try:
            if self._remote_branch_exists(repo_path, branch_name):
                self._safe_git(["pull", "origin", branch_name], repo_path)
        finally:
            if stashed:
                try:
                    self._safe_git(["stash", "pop"], repo_path)
                except GitCommandError as exc:
                    print(f"Warning: stash pop had conflicts - resolve manually.\n  {exc}")

    def _commit_all(self, repo_path: Path, message: str) -> bool:
        self._safe_git(["add", "-A"], repo_path)
        status = self._safe_git(["status", "--porcelain"], repo_path)
        if not status.strip():
            return False
        self._safe_git(["commit", "-m", message], repo_path)
        return True

    def _checkout_branch(self, repo_path: Path, branch_name: str) -> None:
        if self._local_branch_exists(repo_path, branch_name):
            self._safe_git(["checkout", branch_name], repo_path)
            return
        if self._remote_branch_exists(repo_path, branch_name):
            self._safe_git(["checkout", "-b", branch_name, f"origin/{branch_name}"], repo_path)
            return
        base = self._detect_base_branch(repo_path)
        if base:
            if not self._local_branch_exists(repo_path, base):
                self._safe_git(["checkout", "-b", base, f"origin/{base}"], repo_path)
            else:
                self._safe_git(["checkout", base], repo_path)
            self._safe_git(["checkout", "-b", branch_name], repo_path)
        else:
            self._safe_git(["checkout", "--orphan", branch_name], repo_path)

    def _current_branch(self, repo_path: Path) -> str:
        try:
            branch = self._safe_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path).strip()
            if branch and branch != "HEAD":
                return branch
        except GitCommandError:
            pass
        return ""

    def _detect_base_branch(self, repo_path: Path) -> str:
        for candidate in ("main", "master"):
            if self._local_branch_exists(repo_path, candidate) or self._remote_branch_exists(repo_path, candidate):
                return candidate
        return ""

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

    # ------------------------------------------------ repo setup helpers

    def _resolve_working_repo(self, repo_url: str) -> Path:
        default = Path(__file__).resolve().parent
        raw = input(f"Local development repo path [{default}]: ").strip()
        candidate = Path(raw).expanduser().resolve() if raw else default

        if (candidate / ".git").exists():
            print(f"Using local repo: {candidate}")
            return candidate

        repo_name = self._repo_name_from_url(repo_url)
        clone_path = self.base_dir / repo_name
        if (clone_path / ".git").exists():
            print(f"Using cached clone: {clone_path}")
            return clone_path

        print(f"Cloning into {clone_path} ...")
        self._safe_git(["clone", repo_url, str(clone_path)], self.base_dir)
        return clone_path

    def _ensure_origin(self, repo_url: str, repo_path: Path) -> None:
        remotes = {
            line.strip()
            for line in self._safe_git(["remote"], repo_path).splitlines()
            if line.strip()
        }
        if "origin" not in remotes:
            self._safe_git(["remote", "add", "origin", repo_url], repo_path)
        else:
            self._safe_git(["remote", "set-url", "origin", repo_url], repo_path)

    def _repo_name_from_url(self, repo_url: str) -> str:
        parsed = urlparse(repo_url.strip())
        path = parsed.path if parsed.path else repo_url.strip()
        name = path.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        if not name:
            raise GitCommandError(
                "Could not derive repo folder name. Use format: https://github.com/user/repo.git"
            )
        return name

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


if __name__ == "__main__":
    agent = BranchUpdateAgent(base_dir=Path("./repos"))
    try:
        agent.run()
    except GitCommandError as exc:
        print(f"Error: {exc}")
