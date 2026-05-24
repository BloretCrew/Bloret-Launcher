import os
from pathlib import Path
from dulwich import porcelain
from dulwich.repo import Repo


class ResourcePackGit:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self._repo = None

    def init_if_needed(self):
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self._repo = Repo.init(str(self.repo_path))
            gitignore_path = self.repo_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(
                    ".DS_Store\nThumbs.db\n*.log\ntemp/\n__pycache__/\n"
                )
            porcelain.add(self._repo, paths=[".gitignore"])
            porcelain.commit(
                self._repo,
                message="Initial commit: Bloret Resource Pack Editor",
            )
            return True
        self._repo = Repo(str(self.repo_path))
        return False

    def get_status(self):
        if self._repo is None:
            self.init_if_needed()
        status = porcelain.status(self._repo)
        result = {}
        for f in status.staged.get("add", []):
            result[f] = "A"
        for f in status.staged.get("modify", []):
            result[f] = "M"
        for f in status.staged.get("delete", []):
            result[f] = "D"
        for f in status.unstaged:
            existing = result.get(f, "")
            if existing == "A":
                result[f] = "M"
            else:
                result[f] = "M"
        for f in status.untracked:
            result[f] = "U"
        return result

    def get_file_status(self, file_path):
        statuses = self.get_status()
        return statuses.get(file_path, "")

    def stage_file(self, file_path):
        if self._repo is None:
            self.init_if_needed()
        porcelain.add(self._repo, paths=[file_path])
        return True

    def unstage_file(self, file_path):
        if self._repo is None:
            self.init_if_needed()
        try:
            porcelain.unstage_file(self._repo, file_path)
        except Exception:
            pass
        return True

    def commit(self, message):
        if self._repo is None:
            self.init_if_needed()
        porcelain.commit(self._repo, message=message)
        return True

    def get_commit_count(self):
        if self._repo is None:
            return 0
        try:
            count = 0
            for _ in self._repo.get_walker(self._repo.head()):
                count += 1
            return count
        except Exception:
            return 0
