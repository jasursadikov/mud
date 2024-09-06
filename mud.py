import os
import sys
import asyncio
import argparse
import subprocess
import commands
import config
import utils

from argparse import ArgumentParser
from utils import TEXT, RESET, STYLES

# Filters
TABLE_ATTR = '-t', '--table'
LABEL_PREFIX = '-l=', '--label='
BRANCH_PREFIX = '-b=', '--branch='
MODIFIED_ATTR = '-m', '--modified'
DIVERGED_ATTR = '-d', '--diverged'
# Commands
COMMANDS = {
    'help': ['help', '--help', '-h'],
    'update': ['update'],
    'configure': ['configure', 'config'],
    'version': ['--version', '-v', 'version'],
    'set-global': ['--set-global'],
    'init': ['init'],
    'add': ['add', 'a'],
    'remove': ['remove', 'rm'],
    'info': ['info', 'i'],
    'log': ['log', 'l'],
    'tags': ['tags', 'tag', 't'],
    'labels': ['labels', 'lb'],
    'status': ['status', 'st'],
    'branches': ['branch', 'branches', 'br'],
}


class Mud:
    def __init__(self):
        self.cmd_runner = None
        self.config = None
        self.parser = self._create_parser()

    @staticmethod
    def _create_parser() -> ArgumentParser:
        parser = argparse.ArgumentParser(description=f'{STYLES["bold"]}mud{RESET} allows you to run commands in multiple repositories.')
        subparsers = parser.add_subparsers(dest='command')

        subparsers.add_parser(COMMANDS['configure'][0], aliases=COMMANDS['configure'][1:], help='Runs the interactive configuration wizard.')
        subparsers.add_parser(COMMANDS['update'][0], aliases=COMMANDS['update'][1:], help='Update mud to the latest version.')
        subparsers.add_parser(COMMANDS['init'][0], aliases=COMMANDS['init'][1:], help=f'Initializes the {STYLES["bold"]}.mudconfig{RESET} and adds all repositories in this directory to {STYLES["bold"]}.mudconfig{RESET}.')
        subparsers.add_parser(COMMANDS['info'][0], aliases=COMMANDS['info'][1:], help='Displays branch divergence and working directory changes')
        subparsers.add_parser(COMMANDS['log'][0], aliases=COMMANDS['log'][1:], help='Displays log of latest commit messages for all repositories in a table view.')
        subparsers.add_parser(COMMANDS['tags'][0], aliases=COMMANDS['tags'][1:], help='Displays git tags in repositories.')
        subparsers.add_parser(COMMANDS['labels'][0], aliases=COMMANDS['labels'][1:], help='Displays mud labels across repositories.')
        subparsers.add_parser(COMMANDS['status'][0], aliases=COMMANDS['status'][1:], help='Displays working directory changes.')
        subparsers.add_parser(COMMANDS['branches'][0], aliases=COMMANDS['branches'][1:], help='Displays all branches in repositories.')

        add_parser = subparsers.add_parser(COMMANDS['add'][0], aliases=COMMANDS['add'][1:], help='Adds repository or labels an existing repository.')
        add_parser.add_argument('label', help='The label to add (optional).', nargs='?', default='', type=str)
        add_parser.add_argument('path', help='Repository to add (optional).', nargs='?', type=str)

        remove_parser = subparsers.add_parser(COMMANDS['remove'][0], aliases=COMMANDS['remove'][1:], help='Removes repository or removes the label from an existing repository.')
        remove_parser.add_argument('label', help='Label to remove from repository (optional).', nargs='?', default='', type=str)
        remove_parser.add_argument('path', help='Repository to remove (optional).', nargs='?', type=str)

        parser.add_argument(*TABLE_ATTR, metavar='TABLE', nargs='?', default='', type=str, help=f'Switches table view, runs in table view it is disabled in {STYLES["bold"]}.mudsettings{RESET}.')
        parser.add_argument(*LABEL_PREFIX, metavar='LABEL', nargs='?', default='', type=str, help='Filters repositories by provided label.')
        parser.add_argument(*BRANCH_PREFIX, metavar='BRANCH', nargs='?', default='', type=str, help='Filter repositories by provided branch.')
        parser.add_argument(*MODIFIED_ATTR, action='store_true', help='Filters modified repositories.')
        parser.add_argument(*DIVERGED_ATTR, action='store_true', help='Filters repositories with diverged branches.')
        parser.add_argument(COMMANDS['set-global'][0], help=f'Sets {STYLES["bold"]}.mudconfig{RESET} in the current repository as your fallback {STYLES["bold"]}.mudconfig{RESET}.', action='store_true')
        parser.add_argument(COMMANDS['version'][0], help='Displays the current version of mud.', action='store_true')
        parser.add_argument('catch_all', nargs='*', help='Type any commands to execute among repositories.')
        return parser

    def run(self) -> None:
        # Displays default help message
        if len(sys.argv) == 1 or sys.argv[1] in COMMANDS['help']:
            self.parser.print_help()
            return
        # Sets global repository in .mudsettings
        if sys.argv[1] in COMMANDS['set-global']:
            config_path = os.path.join(os.getcwd(), utils.CONFIG_FILE_NAME)
            if os.path.exists(config_path):
                utils.settings.config.set('mud', 'config_path', config_path)
                utils.settings.save()
                print(f'Current {STYLES["bold"]}.mudconfig{RESET} set as a global configuration.')
            return
        # Prints version
        elif sys.argv[1] in COMMANDS['version']:
            utils.print_version()
            return
        elif sys.argv[1] in COMMANDS['configure']:
            self.configure()
            return
        elif sys.argv[1] in COMMANDS['update']:
            utils.check_updates(True)
            return

        current_directory = os.getcwd()
        self.config = config.Config()

        if len(sys.argv) > 1 and sys.argv[1] in [cmd for group in COMMANDS.values() for cmd in group]:
            args = self.parser.parse_args()
            if args.command in COMMANDS['init']:
                self.init(args)
                return

        self.config.find()
        self._filter_repos()

        self.cmd_runner = commands.Commands(self.config)
        # Handling commands
        if len(sys.argv) > 1 and sys.argv[1] in [cmd for group in COMMANDS.values() for cmd in group]:
            args = self.parser.parse_args()
            if args.command in COMMANDS['init']:
                os.chdir(current_directory)
                self.init(args)
            elif args.command in COMMANDS['add']:
                self.add(args)
            elif args.command in COMMANDS['remove']:
                self.remove(args)
            else:
                if len(self.repos) == 0:
                    utils.print_error('No repositories are matching this filter.')
                    return
                if utils.settings.config['mud'].getboolean('auto_fetch'):
                    self._fetch_all()
                if args.command in COMMANDS['info']:
                    self.cmd_runner.info(self.repos)
                elif args.command in COMMANDS['log']:
                    self.cmd_runner.log(self.repos)
                elif args.command in COMMANDS['branches']:
                    self.cmd_runner.branches(self.repos)
                elif args.command in COMMANDS['labels']:
                    self.cmd_runner.labels(self.repos)
                elif args.command in COMMANDS['tags']:
                    self.cmd_runner.tags(self.repos)
                elif args.command in COMMANDS['status']:
                    self.cmd_runner.status(self.repos)
        # Handling subcommands
        else:
            del sys.argv[0]
            if len(sys.argv) == 0:
                self.parser.print_help()
                return
            self._parse_aliases()
            if utils.settings.config['mud'].getboolean('run_async'):
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
        self.config.data = {}
        index = 0
        directories = [d for d in os.listdir('.') if os.path.isdir(d) and os.path.isdir(os.path.join(d, '.git'))]
        for directory in directories:
            if directory in self.config.paths():
                continue
            self.config.add_label(directory, getattr(args, 'label', ''))
            index += 1
            path = f'{STYLES["dim"]}{TEXT["gray"]}../{RESET}{STYLES["dim"]}{directory}{RESET}'
            print(f'{path} {TEXT["green"]}added{RESET}')
        if index == 0:
            utils.print_error('No git repositories were found in this directory.')
            return
        self.config.save(utils.CONFIG_FILE_NAME)

    def configure(self):
        utils.settings.config['mud']['run_async'] = str(utils.ask('Do you want to run commands simultaneously for multiple repositories?'))
        utils.settings.config['mud']['run_table'] = str(utils.ask('Do you want to see command execution progress in table view? This will limit output content.'))
        utils.settings.config['mud']['auto_fetch'] = str(utils.ask(f'Do you want to automatically run {STYLES["bold"]}\'git fetch\'{RESET} whenever you run commands such as {STYLES["bold"]}\'mud info\'{RESET}?'))
        utils.settings.config['mud']['ask_updates'] = str(utils.ask(f'Do you want to get information about latest updates?'))
        utils.settings.config['mud']['nerd_fonts'] = str(utils.ask(f'Do you want to use {STYLES["bold"]}nerd-fonts{RESET}?'))
        utils.settings.config['mud']['simplify_branches'] = str(utils.ask(f'Do you want to simplify branches? (ex. {STYLES["bold"]}feature/name{RESET} -> {STYLES["bold"]}f/name{RESET}'))
        utils.settings.save()
        print('Your settings are updated!')
        pass

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
    def _filter_repos(self) -> None:
        self.repos = self.config.all()
        branch = None
        modified = False
        diverged = False
        self.table = utils.settings.config['mud'].getboolean('run_table')
        index = 1
        while index < len(sys.argv):
            arg = sys.argv[index]
            if arg.startswith('-'):
                arg = sys.argv[1:][index - 1]
                if any(arg.startswith(prefix) for prefix in LABEL_PREFIX):
                    label = arg.split('=', 1)[1]
                    self.repos = self.config.with_label(label)
                elif any(arg.startswith(prefix) for prefix in BRANCH_PREFIX):
                    branch = arg.split('=', 1)[1]
                elif arg in TABLE_ATTR:
                    self.table = not self.table
                elif arg in MODIFIED_ATTR:
                    modified = True
                elif arg in DIVERGED_ATTR:
                    diverged = True
                else:
                    index += 1
                    continue
                del sys.argv[index]
                continue
            break
        directory = os.getcwd()
        to_delete = []
        for repo in self.repos:
            os.chdir(os.path.join(directory, repo))
            has_modifications = subprocess.check_output(['git', 'status', '--porcelain'])
            branch_filter = (branch is not None and branch.strip() and subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).splitlines()[0] != branch)
            is_diverged = not any('ahead' in line or 'behind' in line for line in subprocess.check_output(['git', 'status', '--branch', '--porcelain'], text=True).splitlines() if line.startswith('##'))
            if (modified and not has_modifications) or (branch and branch_filter) or (diverged and is_diverged):
                to_delete.append(repo)

        for repo in to_delete:
            del self.repos[repo]
        os.chdir(directory)

    def _fetch_all(self) -> None:
        if utils.settings.config['mud'].getboolean('run_async'):
            asyncio.run(self._fetch_all_async())
        else:
            for repo in self.repos:
                subprocess.run(['git', 'fetch'], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def _fetch_all_async(self) -> None:
        tasks = [self._fetch_repo_async(repo) for repo in self.repos]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _fetch_repo_async(repo: str) -> None:
        await asyncio.create_subprocess_exec(['git', 'fetch'], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def _parse_aliases():
        if utils.settings.alias_settings is None:
            return
        for alias, command in dict(utils.settings.alias_settings).items():
            if sys.argv[0] == alias:
                del sys.argv[0]
                sys.argv = command.split(' ') + sys.argv
