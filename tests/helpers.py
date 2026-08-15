import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helper — runs a shell command inside a directory
# ---------------------------------------------------------------------------

def _run(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
	return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, check=check)


# ---------------------------------------------------------------------------
# Repo factory helpers
# ---------------------------------------------------------------------------

def make_git_repo(path: Path) -> None:
	"""A normal repo: initialised, one commit, on the default branch."""
	path.mkdir(parents=True, exist_ok=True)
	(path / "README.md").write_text(f"# {path.name}\n")
	_run("git init", path)
	_run("git config user.name 'Test User'", path)
	_run("git config user.email 'test@example.com'", path)
	_run("git add .", path)
	_run("git commit -m 'Initial commit'", path)


def make_empty_repo(path: Path) -> None:
	"""A repo that has been initialised but has no commits (HEAD is unborn)."""
	path.mkdir(parents=True, exist_ok=True)
	_run("git init", path)
	_run("git config user.name 'Test User'", path)
	_run("git config user.email 'test@example.com'", path)


def make_detached_repo(path: Path) -> None:
	"""A repo whose HEAD is detached at a plain commit (not a tag)."""
	make_git_repo(path)
	commit = _run("git rev-parse HEAD", path).stdout.strip()
	_run(f"git checkout {commit}", path)


def make_tagged_repo(path: Path) -> None:
	"""A repo checked out at an annotated tag, leaving HEAD detached."""
	make_git_repo(path)
	_run("git tag v1.0", path)
	_run("git checkout v1.0", path)


def make_rebasing_repo(path: Path) -> None:
	"""A repo that is mid-rebase because of a conflict.

	Creates two branches with a conflicting edit to the same file,
	then starts a rebase on the feature branch so the repo is left in
	the 'rebasing' state (HEAD detached, .git/REBASE_HEAD present).
	"""
	path.mkdir(parents=True, exist_ok=True)
	(path / "file.txt").write_text("original\n")
	_run("git init", path)
	_run("git config user.name 'Test User'", path)
	_run("git config user.email 'test@example.com'", path)
	_run("git add .", path)
	_run("git commit -m 'initial'", path)

	main_branch = _run("git branch --show-current", path).stdout.strip()

	_run("git checkout -b feature", path)
	(path / "file.txt").write_text("feature change\n")
	_run("git add .", path)
	_run("git commit -m 'feature'", path)

	_run(f"git checkout {main_branch}", path)
	(path / "file.txt").write_text("main change\n")
	_run("git add .", path)
	_run("git commit -m 'main change'", path)

	_run("git checkout feature", path)
	# Intentionally not check=True — the rebase stops mid-way on the conflict.
	_run(f"git rebase {main_branch}", path, check=False)


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

def run_mud(*args: str, cwd: Path, home: Path) -> subprocess.CompletedProcess:
	"""Run ``python -m mud <args>`` inside *cwd* and return the result.

	HOME is pointed at an empty temp directory so the subprocess gets
	clean default mud settings, isolated from the developer's own machine.
	"""
	env = os.environ.copy()
	env["HOME"] = str(home)
	return subprocess.run(
		[sys.executable, "-m", "mud", *args],
		cwd=cwd,
		capture_output=True,
		text=True,
		env=env,
	)
