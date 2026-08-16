import pytest
from pathlib import Path
from helpers import make_git_repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
	"""An isolated home directory so the mud subprocess gets clean default settings."""
	h = tmp_path / "home"
	h.mkdir()
	return h


@pytest.fixture
def repos(tmp_path: Path) -> Path:
	"""Two git repos (repo_a, repo_b) with a .mudconfig in tmp_path."""
	make_git_repo(tmp_path / "repo_a")
	make_git_repo(tmp_path / "repo_b")
	(tmp_path / ".mudconfig").write_text("repo_a\t\nrepo_b\t\n")
	return tmp_path


@pytest.fixture
def repos_labeled(tmp_path: Path) -> Path:
	"""Same as repos but each repo has a distinct label."""
	make_git_repo(tmp_path / "repo_a")
	make_git_repo(tmp_path / "repo_b")
	(tmp_path / ".mudconfig").write_text("repo_a\tlabel_a\nrepo_b\tlabel_b\n")
	return tmp_path
