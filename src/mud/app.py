import os
import sys
import asyncio

from mud import utils
from mud.commands import *
from mud.runner import Runner
from mud.config import Config
from argparse import ArgumentParser
from pygit2 import Repository


class App:
	def __init__(self):
		self.command: str | None = None
		self.config: Config | None = None
		self.parser: ArgumentParser = self._create_parser()

	@staticmethod
	def _create_parser() -> ArgumentParser:
		parser = ArgumentParser(description=f'mud allows you to run commands in multiple repositories.')
		subparsers = parser.add_subparsers(dest='command')

		subparsers.add_parser(LOG[0], aliases=LOG[1:], help='Displays log of latest commit messages for all repositories in a table view.')
		subparsers.add_parser(INFO[0], aliases=INFO[1:], help='Displays branch divergence and working directory changes')
		subparsers.add_parser(INIT[0], aliases=INIT[1:], help=f'Initializes the .mudconfig and adds all repositories in this directory to .mudconfig.')
		subparsers.add_parser(TAGS[0], aliases=TAGS[1:], help='Displays git tags in repositories.')
		subparsers.add_parser(LABELS[0], aliases=LABELS[1:], help='Displays mud labels across repositories.')
		subparsers.add_parser(STATUS[0], aliases=STATUS[1:], help='Displays working directory changes.')
		subparsers.add_parser(BRANCHES[0], aliases=BRANCHES[1:], help='Displays all branches in repositories.')
		subparsers.add_parser(REMOTE_BRANCHES[0], aliases=REMOTE_BRANCHES[1:], help='Displays all remote branches in repositories.')
		subparsers.add_parser(CONFIGURE[0], aliases=CONFIGURE[1:], help='Runs the interactive configuration wizard.')
		subparsers.add_parser(GET_CONFIG[0], aliases=GET_CONFIG[1:], help='Prints current .mudconfig path.')

		add_parser = subparsers.add_parser(ADD[0], aliases=ADD[1:], help='Adds repository or labels an existing repository.')
		add_parser.add_argument('path', help='Repository to add.', nargs='?', type=str)
		add_parser.add_argument('label', help='The label to add (optional).', nargs='?', default='', type=str)

		remove_parser = subparsers.add_parser(REMOVE[0], aliases=REMOVE[1:], help='Removes repository or removes the label from an existing repository.')
		remove_parser.add_argument('path', help='Repository to remove.', nargs='?', type=str)
		remove_parser.add_argument('label', help='Label to remove from repository (optional).', nargs='?', default='', type=str)

		subparsers.add_parser(PRUNE[0], help='Removes invalid paths from .mudconfig.')

		parser.add_argument(*COMMAND_ATTR, metavar='COMMAND', help=f'Explicit command argument. Use this when you want to run a command that has a special characters.', nargs='?', default='', type=str)
		parser.add_argument(*TABLE_ATTR, metavar='TABLE', help=f'Switches table view, runs in table view it is disabled in .mudsettings.', nargs='?', default='', type=str)
		parser.add_argument(*NAME_PREFIX, metavar='NAME', help='Includes repositories where name contains provided value.', nargs='?', default='', type=str)
		parser.add_argument(*LABEL_PREFIX, metavar='LABEL', help='Includes repositories with provided label.', nargs='?', default='', type=str)
		parser.add_argument(*NOT_LABEL_PREFIX, metavar='NOT_LABEL', help=f'Excludes repositories with provided label.', nargs='?', default='', type=str)
		parser.add_argument(*BRANCH_PREFIX, metavar='BRANCH', help='Includes repositories on a provided branch.', nargs='?', default='', type=str)
		parser.add_argument(*NOT_BRANCH_PREFIX, metavar='NOT_BRANCH', help='Excludes repositories on a provided branch.', nargs='?', default='', type=str)
		parser.add_argument(*MODIFIED_ATTR, action='store_true', help='Filters modified repositories.')
		parser.add_argument(*DIVERGED_ATTR, action='store_true', help='Filters repositories with diverged branches.')
		parser.add_argument(*ASYNC_ATTR, action='store_true', help='Switches asynchronous run feature.')
		parser.add_argument(SET_GLOBAL[0], help=f'Sets .mudconfig in the current repository as your fallback .mudconfig.', action='store_true')
		parser.add_argument('catch_all', help='Type any commands to execute among repositories.', nargs='*')
		return parser

	def run(self) -> None:
		# Displays default help message
		if len(sys.argv) == 1 or sys.argv[1] in HELP:
			utils.info()
			print()
			self.parser.print_help()
			return
		# Sets global repository in .mudsettings
		if sys.argv[1] in SET_GLOBAL:
			if len(sys.argv) > 2:
				config_path = sys.argv[2]
				if not os.path.isabs(config_path):
					config_path = os.path.abspath(config_path)
			else:
				config_path = os.path.join(os.getcwd(), utils.CONFIG_FILE_NAME)

			if os.path.exists(config_path):
				utils.settings.config.set('mud', 'config_path', config_path)
				utils.settings.save()
				print(config_path)
			else:
				utils.print_error(5)
			return
		# Runs configuration wizard
		elif sys.argv[1] in CONFIGURE:
			utils.configure()
			return

		self.config = Config()

		current_directory = os.getcwd()
		config_directory, fallback = self.config.find()
		config_path = os.path.join(config_directory, utils.CONFIG_FILE_NAME)

		os.environ['PWD'] = config_directory

		runner = Runner(self.config)

		if config_directory != '':
			os.chdir(config_directory)

		native_command = False
		for index, arg in enumerate(sys.argv[1:]):
			if any(arg.startswith(prefix) for prefix in COMMAND_ATTR):
				native_command = False
				break
			if arg.startswith('-'):
				continue
			elif arg in COMMANDS:
				native_command = True
			else:
				break

		# Handling commands
		if native_command:
			args = self.parser.parse_args()

			if args.command in INIT + ADD + REMOVE + PRUNE + GET_CONFIG:
				if args.command in GET_CONFIG:
					print(config_path)
					return

				if args.command in INIT:
					if fallback:
						config_path = os.path.join(current_directory, utils.CONFIG_FILE_NAME)
					elif config_path != '' and os.path.exists(config_path):
						self.config.load(config_path)
					self.config.init()
					self.config.save(config_path)
					return

				if not os.path.exists(config_path):
					utils.print_error(5, exit=True)

				self.config.load(config_path)
				if args.command in ADD:
					self.config.add(args.path, args.label)
				elif args.command in REMOVE:
					self.config.remove(args.label, args.path)
				elif args.command in PRUNE:
					self.config.prune()
				self.config.save(config_path)
				return

			if not os.path.exists(config_path):
				utils.print_error(5, exit=True)

			if config_path == '':
				utils.print_error(5, exit=True)

			self.config.load(config_path)
			self._filter_with_arguments()

			if len(self.repos) == 0:
				utils.print_error(1)
				return

			if args.command in INFO:
				runner.info(self.repos)
			elif args.command in LOG:
				runner.log(self.repos)
			elif args.command in REMOTE_BRANCHES:
				runner.branches(self.repos, True)
			elif args.command in BRANCHES:
				runner.branches(self.repos, False)
			elif args.command in LABELS:
				runner.labels(self.repos)
			elif args.command in TAGS:
				runner.tags(self.repos)
			elif args.command in STATUS:
				runner.status(self.repos)
		# Handling subcommands
		else:
			self.config.load(config_path)
			self._filter_with_arguments()

			del sys.argv[0]
			if self.command is None:
				if len(sys.argv) == 0:
					self.parser.print_help()
					return
				self.command = ' '.join(sys.argv)
				self._parse_aliases()
			try:
				if self.run_async:
					if self.table:
						asyncio.run(runner.run_async_table_view(self.repos.keys(), self.command))
					else:
						asyncio.run(runner.run_async(self.repos.keys(), self.command))
				else:
					runner.run_ordered(self.repos.keys(), self.command)
			except Exception as ex:
				print(ex)
				utils.print_error(2)

	# Filter out repositories if user provided filters
	def _filter_with_arguments(self) -> None:
		self.repos = self.config.data
		self.table = utils.settings.config['mud'].getboolean('run_table', fallback=True)
		self.run_async = utils.settings.config['mud'].getboolean('run_async', fallback=True)

		for path, labels in self.config.filter_label('ignore', self.config.data).items():
			del self.repos[path]
		include_labels = []
		exclude_labels = []
		contains_strings = []
		include_branches = []
		exclude_branches = []
		modified = False
		diverged = False
		index = 1
		while index < len(sys.argv):
			arg = sys.argv[index]
			if not arg.startswith('-'):
				break
			if any(arg.startswith(prefix) for prefix in LABEL_PREFIX):
				include_labels.append(arg.split('=', 1)[1])
			elif any(arg.startswith(prefix) for prefix in NOT_LABEL_PREFIX):
				exclude_labels.append(arg.split('=', 1)[1])
			elif any(arg.startswith(prefix) for prefix in BRANCH_PREFIX):
				include_branches.append(arg.split('=', 1)[1])
			elif any(arg.startswith(prefix) for prefix in NOT_BRANCH_PREFIX):
				exclude_branches.append(arg.split('=', 1)[1])
			elif any(arg.startswith(prefix) for prefix in NAME_PREFIX):
				contains_strings.append(arg.split('=', 1)[1])
			elif arg in MODIFIED_ATTR:
				modified = True
			elif arg in DIVERGED_ATTR:
				diverged = True
			elif arg in TABLE_ATTR:
				self.table = not self.table
			elif arg in ASYNC_ATTR:
				self.run_async = not self.run_async
			elif any(arg.startswith(prefix) for prefix in COMMAND_ATTR):
				self.command = arg.split('=', 1)[1]
			else:
				index += 1
				continue
			del sys.argv[index]

		directory = os.getcwd()
		to_delete = []

		for path, labels in self.repos.items():
			os.chdir(directory)
			abs_path = os.path.join(directory, path)
			repo = Repository(path)

			if not os.path.isdir(abs_path):
				utils.print_error(7, meta=path)
				to_delete.append(path)
				continue
			elif not os.path.isdir(os.path.join(abs_path, '.git')):
				utils.print_error(8, meta=path)
				to_delete.append(path)
				continue

			os.chdir(abs_path)
			delete = False

			if any(include_labels) and not any(item in include_labels for item in labels):
				delete = True
			if any(exclude_labels) and any(item in exclude_labels for item in labels):
				delete = True
			if any(contains_strings) and not any(substr in path for substr in contains_strings):
				delete = True

			if not delete and not repo.head_is_unborn and (any(include_branches) or any(exclude_branches)):
				if any(include_branches) and repo.head.shorthand not in include_branches:
					delete = True
				if any(exclude_branches) and repo.head.shorthand in exclude_branches:
					delete = True

			if not delete and modified:
				if not repo.head_is_unborn and not repo.status():
					delete = True

			if not delete and diverged and not repo.head_is_unborn:
				local_ref = repo.branches[repo.head.shorthand]
				upstream = local_ref.upstream
				if upstream:
					ahead, behind = repo.ahead_behind(local_ref.target, upstream.target)
					if ahead == 0 and behind == 0:
						delete = True

			if delete:
				to_delete.append(path)

		for path in to_delete:
			del self.repos[path]

		os.chdir(directory)

	def _parse_aliases(self) -> None:
		if utils.settings.alias_settings is None:
			return
		for alias, command in dict(utils.settings.alias_settings).items():
			args = self.command.split(' ')
			if args[0] == alias:
				del args[0]
				self.command = ' '.join(command.split(' ') + args)
