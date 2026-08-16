"""
Tests for read-only display commands: status, info, log, labels, branches, tags.

Each command should exit 0 and include the repo directory names in its output.
Output contains ANSI colour codes but plain text like "repo_a" is always present.
"""
from pathlib import Path
from helpers import run_mud


def test_status(repos: Path, home: Path):
	result = run_mud("status", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_info(repos: Path, home: Path):
	result = run_mud("info", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_log(repos: Path, home: Path):
	result = run_mud("log", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_labels(repos: Path, home: Path):
	result = run_mud("labels", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_labels_shows_label_values(repos_labeled: Path, home: Path):
	result = run_mud("labels", cwd=repos_labeled, home=home)
	assert result.returncode == 0
	assert "label_a" in result.stdout
	assert "label_b" in result.stdout


def test_branches(repos: Path, home: Path):
	result = run_mud("branches", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_tags(repos: Path, home: Path):
	result = run_mud("tags", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout
