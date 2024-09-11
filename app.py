import os
import sys
import asyncio
import argparse
import subprocess
import config
import utils

from styles import *
from commands import *
from argparse import ArgumentParser
from runner import Runner


class App:
	def __init__(self):
		self.cmd_runner = None
		self.config = None
		self.parser = self._create_parser()

	@staticmethod
	def _create_parser() -> ArgumentParser:
		parser = argparse.ArgumentParser(description=f'{BOLD}mud{RESET} allows you to run commands in multiple repositories.')
		subparsers = parser.add_subparsers(dest='command')

		subparsers.add_parser(LOG[0], aliases=LOG[1:], help='Displays log of latest commit messages for all repositories in a table view.')
		subparsers.add_parser(INFO[0], aliases=INFO[1:], help='Displays branch divergence and working directory changes')
		subparsers.add_parser(INIT[0], aliases=INIT[1:], help=f'Initializes the {BOLD}.mudconfig{RESET} and adds all repositories in this directory to {BOLD}.mudconfig{RESET}.')
		subparsers.add_parser(TAGS[0], aliases=TAGS[1:], help='Displays git tags in repositories.')
		subparsers.add_parser(UPDATE[0], aliases=UPDATE[1:], help='Update mud to the latest version.')
		subparsers.add_parser(LABELS[0], aliases=LABELS[1:], help='Displays mud labels across repositories.')
		subparsers.add_parser(STATUS[0], aliases=STATUS[1:], help='Displays working directory changes.')
		subparsers.add_parser(BRANCHES[0], aliases=BRANCHES[1:], help='Displays all branches in repositories.')
		subparsers.add_parser(CONFIGURE[0], aliases=CONFIGURE[1:], help='Runs the interactive configuration wizard.')

		add_parser = subparsers.add_parser(ADD[0], aliases=ADD[1:], help='Adds repository or labels an existing repository.')
		add_parser.add_argument('label', help='The label to add (optional).', nargs='?', default='', type=str)
		add_parser.add_argument('path', help='Repository to add (optional).', nargs='?', type=str)

		remove_parser = subparsers.add_parser(REMOVE[0], aliases=REMOVE[1:], help='Removes repository or removes the label from an existing repository.')
		remove_parser.add_argument('label', help='Label to remove from repository (optional).', nargs='?', default='', type=str)
		remove_parser.add_argument('path', help='Repository to remove (optional).', nargs='?', type=str)

		parser.add_argument(*TABLE_ATTR, metavar='TABLE', nargs='?', default='', type=str, help=f'Switches table view, runs in table view it is disabled in {BOLD}.mudsettings{RESET}.')
		parser.add_argument(*LABEL_PREFIX, metavar='LABEL', nargs='?', default='', type=str, help='Includes repositories with provided label.')
		parser.add_argument(*NOT_LABEL_PREFIX, metavar='NOT_LABEL', nargs='?', default='', type=str, help=f'Excludes repositories with provided label..')
		parser.add_argument(*BRANCH_PREFIX, metavar='BRANCH', nargs='?', default='', type=str, help='Includes repositories on a provided branch.')
		parser.add_argument(*NOT_BRANCH_PREFIX, metavar='NOT_BRANCH', nargs='?', default='', type=str, help='Excludes repositories on a provided branch.')
		parser.add_argument(*MODIFIED_ATTR, action='store_true', help='Filters modified repositories.')
		parser.add_argument(*DIVERGED_ATTR, action='store_true', help='Filters repositories with diverged branches.')
		parser.add_argument(*ASYNC_ATTR, action='store_true', help='Switches asynchronous run feature.')
		parser.add_argument(SET_GLOBAL[0], help=f'Sets {BOLD}.mudconfig{RESET} in the current repository as your fallback {BOLD}.mudconfig{RESET}.', action='store_true')
		parser.add_argument(VERSION[0], help='Displays the current version of mud.', action='store_true')
		parser.add_argument('catch_all', nargs='*', help='Type any commands to execute among repositories.')
		return parser

	def run(self) -> None:
		# Displays default help message
		if len(sys.argv) == 1 or sys.argv[1] in HELP:
			self.parser.print_help()
			return
		# Sets global repository in .mudsettings
		if sys.argv[1] in SET_GLOBAL:
			config_path = os.path.join(os.getcwd(), utils.CONFIG_FILE_NAME)
			if os.path.exists(config_path):
				utils.settings.config.set('mud', 'config_path', config_path)
				utils.settings.save()
				print(f'Current {BOLD}.mudconfig{RESET} set as a global configuration.')
			return
		# Prints version
		elif sys.argv[1] in VERSION:
			utils.version()
			return
		# Checks for available updates
		elif sys.argv[1] in UPDATE:
			utils.update(True)
			return
		# Runs configuration wizard
		elif sys.argv[1] in CONFIGURE:
			utils.configure()
			return

		current_directory = os.getcwd()
		self.config = config.Config()

		# Discovers repositories in current directory
		if sys.argv[1] in INIT:
			self.init(self.parser.parse_args())
			return

		self.config.find()
		self._parse_arguments()

		self.cmd_runner = Runner(self.config)
		# Handling commands
		if len(sys.argv) > 1 and sys.argv[1] in [cmd for group in COMMANDS for cmd in group]:
			args = self.parser.parse_args()
			if args.command in INIT:
				os.chdir(current_directory)
				self.init(args)
			elif args.command in ADD:
				self.add(args)
			elif args.command in REMOVE:
				self.remove(args)
			else:
				if len(self.repos) == 0:
					utils.print_error('No repositories are matching this filter.')
					return
				if args.command in INFO:
					self.cmd_runner.info(self.repos)
				elif args.command in LOG:
					self.cmd_runner.log(self.repos)
				elif args.command in BRANCHES:
					self.cmd_runner.branches(self.repos)
				elif args.command in LABELS:
					self.cmd_runner.labels(self.repos)
				elif args.command in TAGS:
					self.cmd_runner.tags(self.repos)
				elif args.command in STATUS:
					self.cmd_runner.status(self.repos)
		# Handling subcommands
		else:
			del sys.argv[0]
			if len(sys.argv) == 0:
				self.parser.print_help()
				return
			self._parse_aliases()
			if self.run_async:
				try:
					if self.table:
						asyncio.run(self.cmd_runner.run_async_table_view(self.repos.keys(), sys.argv))
					else:
						asyncio.run(self.cmd_runner.run_async(self.repos.keys(), sys.argv))
				except Exception as exception:
					utils.print_error('Invalid command.')
					print(type(exception))
			else:
				self.cmd_runner.run_ordered(self.repos.keys(), sys.argv)

	def init(self, args) -> None:
		table = utils.get_table()
		self.config.data = {}
		index = 0
		directories = [d for d in os.listdir('.') if os.path.isdir(d) and os.path.isdir(os.path.join(d, '.git'))]
		for directory in directories:
			if directory in self.config.paths():
				continue
			self.config.add_label(directory, getattr(args, 'label', ''))
			index += 1
			table.add_row([f'{DIM}{directory}{RESET}', f'{GREEN}{utils.GLYPHS["added"]}{RESET}'])
		if index == 0:
			utils.print_error('No git repositories were found in this directory.')
			return
		self.config.save(utils.CONFIG_FILE_NAME)
		utils.print_table(table)

	def add(self, args) -> None:
		self.config.add_label(args.path, args.label)
		self.config.save(utils.CONFIG_FILE_NAME)

	def remove(self, args) -> None:
		if args.path:
			self.config.remove_label(args.path, args.label)
		elif args.label:
			self.config.remove_path(args.label)
		else:
			utils.print_error(f'Invalid input. Please provide a value to remove.')
		self.config.save(utils.CONFIG_FILE_NAME)

	# Filter out repositories if user provided filters
	def _parse_arguments(self) -> None:
		self.repos = self.config.data
		self.table = utils.settings.config['mud'].getboolean('run_table')
		self.run_async = utils.settings.config['mud'].getboolean('run_async')

		for path, labels in self.config.filter_label('ignore', self.config.data).items():
			del self.repos[path]
		include_labels = []
		exclude_labels = []
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
			elif arg in MODIFIED_ATTR:
				modified = True
			elif arg in DIVERGED_ATTR:
				diverged = True
			elif arg in TABLE_ATTR:
				self.table = not self.table
			elif arg in ASYNC_ATTR:
				self.run_async = not self.run_async
			else:
				index += 1
				continue
			del sys.argv[index]
		directory = os.getcwd()
		to_delete = []
		for repo, labels in self.repos.items():
			os.chdir(os.path.join(directory, repo))
			branch = subprocess.check_output('git rev-parse --abbrev-ref HEAD', shell=True, text=True).splitlines()[0]
			delete = False
			delete |= any(include_branches) and branch not in include_branches
			delete |= any(exclude_branches) and branch in exclude_branches
			delete |= any(include_labels) and not any(item in include_labels for item in labels)
			delete |= any(exclude_labels) and any(item in exclude_labels for item in labels)
			delete |= modified and (not subprocess.check_output('git status --porcelain', shell=True, stderr=subprocess.DEVNULL))
			delete |= diverged and (not any('ahead' in line or 'behind' in line for line in subprocess.check_output('git status --branch --porcelain', shell=True, text=True).splitlines() if line.startswith('##')))
			if delete:
				to_delete.append(repo)

		for repo in to_delete:
			del self.repos[repo]

		os.chdir(directory)

	@staticmethod
	def _parse_aliases():
		if utils.settings.alias_settings is None:
			return
		for alias, command in dict(utils.settings.alias_settings).items():
			if sys.argv[0] == alias:
				del sys.argv[0]
				sys.argv = command.split(' ') + sys.argv
