import configparser
import io
import os
from argparse import ArgumentParser, _SubParsersAction
from contextlib import redirect_stdout
from pathlib import Path

from pygit2 import GitError

from mud import utils
from mud.commands import (
	ADD, REMOVE, SET_GLOBAL, CONFIGURE, COMPLETION, HELP, COMMAND_ATTR,
	LABEL_PREFIX, NOT_LABEL_PREFIX, BRANCH_PREFIX, NOT_BRANCH_PREFIX,
	NAME_PREFIX, NOT_NAME_PREFIX,
)
from mud.config import Config
from mud.runner import Runner
from mud.settings import Settings


def complete(parser: ArgumentParser) -> None:
	args = parser.parse_args()
	if args.shell == 'carapace':
		print('''name: mud
description: Run commands across multiple repositories
parsing: disabled
completion:
  positionalany:
    - "$(mud completion values)"
    - "$nospace(=/)"
  dashany: []''')
		return

	arguments = []
	while f'C_ARG{len(arguments)}' in os.environ:
		arguments.append(os.environ[f'C_ARG{len(arguments)}'])
	value = os.environ.get('C_VALUE', '')
	try:
		utils.settings = Settings(utils.SETTINGS_FILE_NAME, utils.OLD_SETTINGS_FILE_NAME, read_only=True)
		candidates = _candidates(parser, arguments, value)
	except (OSError, ValueError, configparser.Error, GitError):
		return

	for candidate, description in sorted(set(candidates), key=lambda item: (item[0].casefold(), item[0])):
		if candidate.startswith(value) and candidate.isprintable():
			description = ''.join(char if char.isprintable() else ' ' for char in description)
			print(f'{candidate}\t{description}')


def _repositories() -> dict[str, list[str]]:
	config = Config()
	directory, _ = config.find()
	if not directory:
		return {}

	previous_directory = os.getcwd()
	try:
		os.chdir(directory)
		# Missing paths must not turn diagnostics into completion candidates.
		with redirect_stdout(io.StringIO()):
			config.load(os.path.join(directory, utils.CONFIG_FILE_NAME))
	except (OSError, ValueError, IndexError):
		return {}
	finally:
		os.chdir(previous_directory)
	return config.data


def _candidates(parser: ArgumentParser, arguments: list[str], value: str) -> list[tuple[str, str]]:
	if '--' in arguments:
		return []
	subparsers = next(action.choices for action in parser._actions if isinstance(action, _SubParsersAction))
	explicit_command = False
	for index, argument in enumerate(arguments):
		if argument.startswith(COMMAND_ATTR):
			explicit_command = True
		if not argument.startswith('-'):
			if explicit_command:
				return []
			positionals = arguments[index:]
			if argument in SET_GLOBAL + CONFIGURE + COMPLETION + HELP and index != 0:
				return []
			if value.startswith('-') and argument in subparsers and argument not in SET_GLOBAL + CONFIGURE:
				return [
					(flag, action.help or '') for action in subparsers[argument]._actions
					for flag in action.option_strings
				]
			if argument in COMPLETION and len(positionals) == 1:
				return [('carapace', 'Export the Carapace spec')]
			if argument in ADD + REMOVE and len(positionals) == 2:
				return [(label, 'Label') for labels in _repositories().values() for label in labels]
			if argument in REMOVE and len(positionals) == 1:
				return [(path, 'Repository') for path in _repositories()]
			if argument in ADD + SET_GLOBAL and len(positionals) == 1:
				parent = os.path.dirname(value)
				directory = Path(parent or '.').expanduser()
				if argument in ADD:
					directory = Path(Config.find()[0]) / directory
				return [
					(os.path.join(parent, path.name) + ('/' if path.is_dir() else ''), '')
					for path in directory.iterdir()
					if argument in SET_GLOBAL or path.is_dir()
				]
			return []

	if value.startswith(COMMAND_ATTR):
		return []
	if value.startswith(LABEL_PREFIX + NOT_LABEL_PREFIX + NAME_PREFIX + NOT_NAME_PREFIX):
		prefix = value.split('=', 1)[0] + '='
		repos = _repositories()
		if value.startswith(LABEL_PREFIX + NOT_LABEL_PREFIX):
			return [(prefix + label, 'Label') for labels in repos.values() for label in labels]
		return [(prefix + path, 'Repository') for path in repos]
	if value.startswith(BRANCH_PREFIX + NOT_BRANCH_PREFIX):
		prefix = value.split('=', 1)[0] + '='
		directory, _ = Config.find()
		branches = []
		for path in _repositories():
			path = os.path.join(directory, path)
			if not os.path.isdir(os.path.join(path, '.git')):
				continue
			try:
				branches.extend(Runner._get_unique_branch_names([path], include_remote=True))
			except (OSError, ValueError, GitError):
				continue
		return [(prefix + branch, 'Branch') for branch in branches]

	candidates = []
	for action in parser._actions:
		candidates.extend((flag + ('=' if action.nargs != 0 else ''), action.help or '') for flag in action.option_strings)
		if isinstance(action, _SubParsersAction) and not explicit_command and not value.startswith('-'):
			for command in action._choices_actions:
				candidates.extend(
					(name, command.help or '') for name, subparser in action.choices.items()
					if subparser is action.choices[command.dest]
					and not (arguments and name in SET_GLOBAL + CONFIGURE + COMPLETION)
				)
	if not explicit_command and not value.startswith('-'):
		if not arguments:
			candidates.append((HELP[0], 'Show help'))
		candidates.extend((alias, command) for alias, command in (utils.settings.alias_settings or {}).items())
	candidates.append(('--', 'Run an opaque shell command'))
	return candidates
