import configparser
import os
import subprocess
import sys
from pathlib import Path

from helpers import run_mud


def test_import_does_not_create_settings(home: Path):
	result = subprocess.run(
		[sys.executable, '-c', 'import mud'], cwd=home,
		env={**os.environ, 'HOME': str(home)}, capture_output=True, text=True,
	)
	assert result.returncode == 0, result.stderr
	assert list(home.iterdir()) == []


def test_first_launch_creates_modern_settings(home: Path):
	result = run_mud(cwd=home, home=home)
	assert result.returncode == 0, result.stderr
	settings = configparser.ConfigParser()
	assert settings.read(home / '.config' / 'mud' / 'settings.ini')
	assert settings.getboolean('mud', 'run_async') is True
	assert settings['alias']['fetch'] == 'git fetch'
	assert not (home / '.mudsettings').exists()
	assert not (home / '.mudsetting').exists()


def test_legacy_settings_move_on_launch(home: Path, tmp_path: Path):
	config = tmp_path / '.mudconfig'
	config.write_text('')
	legacy = home / '.mudsettings'
	contents = f'# Personal settings\n[mud]\nconfig_path = {config}\nrun_async = False\n[alias]\ncustom = git status\n'
	legacy.write_text(contents)

	result = run_mud('get-config', cwd=home, home=home)
	assert result.returncode == 0, result.stderr
	assert result.stdout.strip() == str(config)
	modern = home / '.config' / 'mud' / 'settings.ini'
	assert modern.read_text() == contents
	settings = configparser.ConfigParser()
	assert settings.read(modern)
	assert settings['mud']['config_path'] == str(config)
	assert settings.getboolean('mud', 'run_async') is False
	assert settings['alias']['custom'] == 'git status'
	assert not legacy.exists()


def test_failed_migration_preserves_legacy_settings(home: Path):
	legacy = home / '.mudsettings'
	contents = '[mud]\nrun_async = False\n[alias]\ncustom = git status\n'
	legacy.write_text(contents)
	(home / '.config').write_text('not a directory\n')

	result = run_mud('help', cwd=home, home=home)
	assert result.returncode != 0
	assert legacy.read_text() == contents
	assert not (home / '.config' / 'mud' / 'settings.ini').exists()


def test_modern_settings_take_precedence_and_receive_updates(home: Path, tmp_path: Path):
	config = tmp_path / '.mudconfig'
	config.write_text('')
	legacy = home / '.mudsettings'
	contents = '[mud]\nrun_async = True\n[alias]\ncustom = git status\n'
	legacy.write_text(contents)
	modern = home / '.config' / 'mud' / 'settings.ini'
	modern.parent.mkdir(parents=True)
	modern.write_text('[mud]\nrun_async = False\n[alias]\ncustom = git diff\n')

	result = run_mud('set-global', str(config), cwd=home, home=home)
	assert result.returncode == 0, result.stderr
	settings = configparser.ConfigParser()
	settings.read(modern)
	assert settings['mud']['config_path'] == str(config)
	assert settings.getboolean('mud', 'run_async') is False
	assert settings['alias']['custom'] == 'git diff'
	assert legacy.read_text() == contents
