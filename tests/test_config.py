"""
Tests for config-management commands: init, add, remove, prune.

Each test runs `mud <command>` as a real subprocess and checks the
exit code plus the contents of .mudconfig on disk.
"""
from pathlib import Path
from helpers import make_git_repo, run_mud


# ---------------------------------------------------------------------------
# mud init
# ---------------------------------------------------------------------------

def test_init_creates_mudconfig(tmp_path: Path, home: Path):
	"""mud init creates .mudconfig and adds all git repos it finds."""
	make_git_repo(tmp_path / "repo_a")
	make_git_repo(tmp_path / "repo_b")

	result = run_mud("init", cwd=tmp_path, home=home)

	assert result.returncode == 0
	mudconfig = (tmp_path / ".mudconfig").read_text()
	assert "repo_a" in mudconfig
	assert "repo_b" in mudconfig


def test_init_is_idempotent(tmp_path: Path, home: Path):
	"""Running mud init twice does not duplicate repos in .mudconfig."""
	make_git_repo(tmp_path / "repo_a")

	run_mud("init", cwd=tmp_path, home=home)
	run_mud("init", cwd=tmp_path, home=home)

	mudconfig = (tmp_path / ".mudconfig").read_text()
	assert mudconfig.count("repo_a") == 1


# ---------------------------------------------------------------------------
# mud add
# ---------------------------------------------------------------------------

def test_add_repo(repos: Path, home: Path):
	"""mud add <path> registers a new repo in .mudconfig."""
	make_git_repo(repos / "repo_c")

	result = run_mud("add", "repo_c", cwd=repos, home=home)

	assert result.returncode == 0
	assert "repo_c" in (repos / ".mudconfig").read_text()


def test_add_repo_with_label(repos: Path, home: Path):
	"""mud add <path> <label> registers a repo with a label."""
	make_git_repo(repos / "repo_c")

	run_mud("add", "repo_c", "my_label", cwd=repos, home=home)

	# Verify label appears in the labels command output
	result = run_mud("labels", cwd=repos, home=home)
	assert "my_label" in result.stdout


# ---------------------------------------------------------------------------
# mud remove
# ---------------------------------------------------------------------------

def test_remove_repo(repos: Path, home: Path):
	"""mud remove <path> drops the repo from .mudconfig."""
	result = run_mud("remove", "repo_a", cwd=repos, home=home)

	assert result.returncode == 0
	mudconfig = (repos / ".mudconfig").read_text()
	assert "repo_a" not in mudconfig
	assert "repo_b" in mudconfig  # sibling repo must be untouched


# ---------------------------------------------------------------------------
# mud prune
# ---------------------------------------------------------------------------

def test_prune_removes_missing_paths(tmp_path: Path, home: Path):
	"""mud prune removes entries whose paths no longer exist on disk."""
	make_git_repo(tmp_path / "repo_a")
	# ghost_repo is listed in .mudconfig but does not exist on disk
	(tmp_path / ".mudconfig").write_text("repo_a\t\nghost_repo\t\n")

	result = run_mud("prune", cwd=tmp_path, home=home)

	assert result.returncode == 0
	mudconfig = (tmp_path / ".mudconfig").read_text()
	assert "repo_a" in mudconfig
	assert "ghost_repo" not in mudconfig
