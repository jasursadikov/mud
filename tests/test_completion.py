import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import make_detached_repo, make_empty_repo, make_git_repo, mud_command, run_mud


@pytest.fixture
def complete(repos_labeled: Path, home: Path):
	def invoke(*arguments, cwd=repos_labeled):
		env = {key: value for key, value in os.environ.items() if not key.startswith('C_ARG')}
		env['HOME'] = str(home)
		env['C_VALUE'] = arguments[-1]
		env.update({f'C_ARG{index}': argument for index, argument in enumerate(arguments[:-1])})
		result = subprocess.run(
			mud_command('completion', 'values'),
			cwd=cwd, env=env, capture_output=True, text=True, check=True,
		)
		assert result.stderr == ''
		return [line.split('\t', 1)[0] for line in result.stdout.splitlines()]
	return invoke


def test_command_and_flag_inventory(complete):
	from mud.app import App
	from mud.commands import COMMANDS

	values = complete('')
	assert set(COMMANDS) <= set(values)
	for action in App._create_parser()._actions:
		assert {flag + ('=' if action.nargs != 0 else '') for flag in action.option_strings} <= set(values)
	assert {'fetch', 'pull', 'push', '--'} <= set(values)
	assert '-l=' in complete('-l')
	assert '--not-name=' in complete('--not-n')
	assert complete('completion', '') == ['carapace']


@pytest.mark.parametrize('prefix', ['-l=', '-L=', '--label=', '--not-label='])
def test_label_values(complete, repos_labeled: Path, prefix):
	(repos_labeled / '.mudconfig').write_text('repo_a\twork, shared\nrepo_b\tpersonal,shared\n')
	assert complete(prefix) == [prefix + label for label in ['personal', 'shared', 'work']]
	assert complete('-l=work', prefix + 'sh') == [prefix + 'shared']


@pytest.mark.parametrize('prefix', ['-n=', '-N=', '--name=', '--not-name='])
def test_name_values(complete, repos_labeled: Path, prefix):
	(repos_labeled / 'repo_a').rename(repos_labeled / 'repo with spaces')
	(repos_labeled / '.mudconfig').write_text('repo with spaces\twork\nrepo_b\tpersonal\n')
	assert complete(prefix) == [prefix + 'repo with spaces', prefix + 'repo_b']


@pytest.mark.parametrize('prefix', ['-b=', '-B=', '--branch=', '--not-branch='])
def test_all_branch_values(complete, repos_labeled: Path, prefix):
	for name in ['repo_a', 'repo_b']:
		path = repos_labeled / name
		for command in [
			['branch', '-M', 'master'],
			['branch', 'feature/inactive'],
			['update-ref', 'refs/remotes/origin/release/remote', 'HEAD'],
			['symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/release/remote'],
		]:
			subprocess.run(['git', *command], cwd=path, capture_output=True, check=True)
	assert complete(prefix) == [prefix + name for name in ['feature/inactive', 'master', 'release/remote']]
	assert complete(prefix + 'feature/') == [prefix + 'feature/inactive']


@pytest.mark.parametrize('arguments', [
	('--', ''), ('--', '-l='), ('--', 'git', ''),
	('-c=',), ('--command=git ',), ('-c=git status', 'git', ''),
	('git', ''), ('git', '-l='), ('fetch', ''), ('status', '-l='), ('add', '--', ''),
	('-l=work', 'completion', ''),
	('add', 'repo_a', 'work', ''),
])
def test_opaque_commands(complete, arguments):
	assert complete(*arguments) == []


def test_filters_after_explicit_command(complete):
	values = complete('-c=git status', '')
	assert '-l=' in values
	assert not {'status', 'fetch', 'init'} & set(values)
	assert complete('--command=git status', '-L=') == ['-L=label_a', '-L=label_b']


def test_native_positionals(complete, repos_labeled: Path):
	assert complete('remove', '') == ['repo_a', 'repo_b']
	assert complete('rm', 'repo_a', '') == ['label_a', 'label_b']
	assert complete('a', 'repo_') == ['repo_a/', 'repo_b/']
	assert complete('add', 'repo_a', 'label_') == ['label_a', 'label_b']
	assert complete('set-global', '.mud') == ['.mudconfig']
	assert complete('add', 'repo_', cwd=repos_labeled / 'repo_a') == ['repo_a/', 'repo_b/']
	assert complete('status', '--h') == ['--help']
	assert 'completion' not in complete('-l=work', '')


def test_read_only_discovery(complete, repos_labeled: Path, home: Path, tmp_path_factory):
	assert complete('-l=', cwd=repos_labeled / 'repo_a') == ['-l=label_a', '-l=label_b']
	assert not (home / '.config').exists()
	assert not (home / '.mudsettings').exists()
	settings = home / '.config' / 'mud' / 'settings.ini'
	settings.parent.mkdir(parents=True)
	settings.write_text(f'[mud]\nconfig_path = {repos_labeled / ".mudconfig"}\n[alias]\nto = git checkout\n')
	assert complete('-n=', cwd=tmp_path_factory.mktemp('outside-config')) == ['-n=repo_a', '-n=repo_b']
	assert 'to' in complete('')


@pytest.mark.parametrize('modern_exists', [False, True])
def test_settings_precedence_without_migration(complete, home: Path, modern_exists):
	legacy = home / '.mudsettings'
	legacy_contents = '[mud]\n[alias]\nlegacy = git status\n'
	legacy.write_text(legacy_contents)
	modern = home / '.config' / 'mud' / 'settings.ini'
	modern_contents = '[mud]\n[alias]\nmodern = git diff\n'
	if modern_exists:
		modern.parent.mkdir(parents=True)
		modern.write_text(modern_contents)

	values = complete('')
	assert ('modern' in values) == modern_exists
	assert ('legacy' in values) != modern_exists
	assert legacy.read_text() == legacy_contents
	if modern_exists:
		assert modern.read_text() == modern_contents
	else:
		assert not (home / '.config').exists()


def test_invalid_and_empty_configs(complete, repos_labeled: Path, home: Path):
	config = repos_labeled / '.mudconfig'
	config.unlink()
	assert complete('-l=', cwd=home) == []
	config.write_text('missing\tbad\nrepo_a\tgood\n')
	assert complete('-l=') == ['-l=good']
	for contents in ['', '\n', 'missing\tbad\n']:
		config.write_text(contents)
		assert complete('-b=') == []
		assert complete('-l=') == []


def test_unborn_and_detached_repositories(complete, repos_labeled: Path):
	make_empty_repo(repos_labeled / 'unborn')
	make_detached_repo(repos_labeled / 'detached')
	(repos_labeled / '.mudconfig').write_text('unborn\tx\ndetached\ty\n')
	assert complete('-l=') == ['-l=x', '-l=y']
	assert all('HEAD' not in value for value in complete('-b='))


@pytest.fixture
def carapace(repos_labeled: Path, home: Path):
	if not shutil.which('carapace'):
		pytest.skip('carapace is not installed')
	spec = run_mud('completion', 'carapace', cwd=home, home=home)
	assert spec.returncode == 0, spec.stderr
	assert not (home / '.config').exists()
	assert not (home / '.mudsettings').exists()
	spec_directory = home / '.config' / 'carapace' / 'specs'
	spec_directory.mkdir(parents=True)
	(spec_directory / 'mud.yaml').write_text(spec.stdout)
	env = os.environ.copy()
	env.update({
		'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config'),
		'XDG_CACHE_HOME': str(home / '.cache'), 'CARAPACE_BRIDGES': '',
		'PATH': str(Path(mud_command()[0]).parent) + os.pathsep + env['PATH'],
	})

	def invoke(*arguments, shell='export'):
		result = subprocess.run(
			['carapace', 'mud', shell, 'mud', *arguments], cwd=repos_labeled,
			env=env, capture_output=True, text=True, check=True,
		)
		assert result.stderr == ''
		return json.loads(result.stdout) if shell in ['export', 'nushell'] else result.stdout
	return invoke


def test_carapace_protocol(carapace):
	result = carapace('-l=')
	assert [value['value'] for value in result['values']] == ['-l=label_a', '-l=label_b']
	assert all(value['description'] == 'Label' for value in result['values'])


@pytest.mark.parametrize('prefix', [
	'-l=', '-L=', '--label=', '--not-label=',
	'-n=', '-N=', '--name=', '--not-name=',
	'-b=', '-B=', '--branch=', '--not-branch=',
])
def test_carapace_dynamic_flags(carapace, complete, prefix):
	assert [item['value'] for item in carapace(prefix)['values']] == complete(prefix)


@pytest.mark.parametrize('arguments', [
	('--', ''), ('--', '-l='), ('--', 'git', ''),
	('-c=',), ('--command=git ',), ('git', ''), ('git', '-l='),
])
def test_carapace_opaque_commands(carapace, arguments):
	assert carapace(*arguments)['values'] == []
	assert carapace(*arguments, shell='nushell') == []


def test_carapace_filters_after_command(carapace):
	values = {item['value'] for item in carapace('-c=git status', '')['values']}
	assert {'-l=', '--not-name='} <= values
	assert not {'status', 'fetch'} & values
	assert [item['value'] for item in carapace('-c=git status', '-N=')['values']] == ['-N=repo_a', '-N=repo_b']


@pytest.mark.parametrize('shell', ['nushell', 'bash', 'zsh', 'fish'])
def test_carapace_shell_formats(carapace, shell):
	result = carapace('-l=label_a', shell=shell)
	if shell == 'nushell':
		assert [item['value'] for item in result] == ['-l=label_a ']
	else:
		assert '-l=label_a' in result


def test_carapace_quoting_and_no_execution(carapace, repos_labeled: Path, home: Path):
	(repos_labeled / 'repo_a').rename(repos_labeled / 'repo with spaces')
	(repos_labeled / '.mudconfig').write_text('repo with spaces\twork\nrepo_b\tpersonal\n')
	values = carapace('-n=', shell='nushell')
	assert [item['value'] for item in values] == ['"-n=repo with spaces" ', '-n=repo_b ']
	assert [item['value'] for item in carapace('-n', shell='nushell')] == ['-n=']
	marker = home / 'executed'
	for command in [f'$(touch {marker})', f'`touch {marker}`', f'"; touch {marker}; #']:
		assert carapace('-c=' + command)['values'] == []
		assert len(carapace('-c=' + command, '-l=')['values']) == 2
		assert carapace('--', command, '')['values'] == []
	assert not marker.exists()
	assert not (home / '.config' / 'mud').exists()


def test_nushell_completion_round_trip(carapace, repos_labeled: Path, home: Path):
	if not shutil.which('nu'):
		pytest.skip('nushell is not installed')
	(repos_labeled / 'repo_a').rename(repos_labeled / 'repo with spaces')
	(repos_labeled / '.mudconfig').write_text('repo with spaces\twork\n')
	value = carapace('-n=', shell='nushell')[0]['value']
	result = subprocess.run(
		['nu', '--no-config-file', '-c',
		 f'^{sys.executable} -c \'import json, sys; print(json.dumps(sys.argv[1:]))\' {value}'],
		cwd=home, env={**os.environ, 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config')},
		capture_output=True, text=True, check=True,
	)
	assert json.loads(result.stdout) == ['-n=repo with spaces']


def test_carapace_alias_description_is_single_line(carapace, home: Path):
	(home / '.mudsettings').write_text('[alias]\ncustom = git status\n forged-token\tForged description\x1b\n')
	values = carapace('')['values']
	assert 'forged-token' not in {item['value'] for item in values}
	assert all('\x1b' not in item['description'] for item in values)
