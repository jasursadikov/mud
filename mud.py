#!/usr/bin/env python3

import os
import sys
import asyncio
import argparse
import subprocess
from argparse import ArgumentParser

import utils
from utils import TEXT, RESET, STYLES
from config import Config
from settings import Settings
from commands import Commands

# Filters
LABEL_PREFIX = '-l=', '--label='
BRANCH_PREFIX = '-b=', '--branch='
MODIFIED_ATTR = '-m', '--modified'
DIVERGED_ATTR = '-d', '--diverged'
# Commands
COMMANDS = {
    'help': ['help', '--help', '-h'],
    'version': ['--version'],
    'set-global': ['--set-global'],
    'init': ['init'],
    'add': ['add', 'a'],
    'remove': ['remove', 'rm'],
    'branches': ['branch', 'branches', 'br'],
    'status': ['status', 'st'],
    'log': ['log', 'l'],
}


class MudCLI:
    def __init__(self):
        self.cmd_runner = None
        self.config = None
        self.parser = self._create_parser()

    @staticmethod
    def _create_parser() -> ArgumentParser:
        parser = argparse.ArgumentParser(description=f'mud allows you to run commands in multiple directories.')
        subparsers = parser.add_subparsers(dest='command')

        subparsers.add_parser(COMMANDS['init'][0], aliases=COMMANDS['init'][1:], help='Initializing .mudconfig, adds all repositories in this directory to .mudconfig')
        subparsers.add_parser(COMMANDS['status'][0], aliases=COMMANDS['status'][1:], help='Displays git status in a table view')
        subparsers.add_parser(COMMANDS['branches'][0], aliases=COMMANDS['branches'][1:], help='Displays all branches in a table view')
        subparsers.add_parser(COMMANDS['log'][0], aliases=COMMANDS['log'][1:], help='Displays log of last commit for all repos in a table view')

        add_parser = subparsers.add_parser(COMMANDS['add'][0], aliases=COMMANDS['add'][1:], help='Register directory')
        add_parser.add_argument('label', help='The label to add (optional)', nargs='?', default='', type=str)
        add_parser.add_argument('path', help='Directory to add (optional)', nargs='?', type=str)

        remove_parser = subparsers.add_parser(COMMANDS['remove'][0], aliases=COMMANDS['remove'][1:], help='Remove label from directory or directory in .mudconfig')
        remove_parser.add_argument('label', help='Label to remove from directory (optional)', nargs='?', default='', type=str)
        remove_parser.add_argument('path', help='Directory to remove (optional)', nargs='?', type=str)

        parser.add_argument(*LABEL_PREFIX, metavar='LABEL', nargs='?', default='', type=str, help='Filter repos with provided label')
        parser.add_argument(*BRANCH_PREFIX, metavar='BRANCH', nargs='?', default='', type=str, help='Filter repos with provided branch')
        parser.add_argument(*MODIFIED_ATTR, action='store_true', help='Filter modified repos')
        parser.add_argument(*DIVERGED_ATTR, action='store_true', help='Filter diverged repos')
        parser.add_argument(COMMANDS['set-global'][0], help='Sets \'.mudconfig\' in current directory as your global \'.mudconfig\' so you can use it anywhere', action='store_true')
        parser.add_argument(COMMANDS['version'][0], help='Displays current version of mud', action='store_true')
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
                print('Current .mudconfig set as a global configuration')
            return
        # Prints version
        if sys.argv[1] in COMMANDS['version']:
            utils.print_version()
            return

        current_directory = os.getcwd()
        self.config = Config()
        self._filter_repos()

        if len(self.repos) == 0:
            utils.print_error('No repositories are matching this filter')
            return

        self.cmd_runner = Commands(self.config)
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
                if utils.settings.config['mud'].getboolean('auto_fetch'):
                    self._fetch_all()
                if args.command in COMMANDS['status']:
                    self.cmd_runner.status(self.repos)
                elif args.command in COMMANDS['log']:
                    self.cmd_runner.log(self.repos)
                elif args.command in COMMANDS['branches']:
                    self.cmd_runner.branches(self.repos)
        # Handling general commands
        else:
            del sys.argv[0]
            self._parse_aliases()
            if utils.settings.config['mud'].getboolean('run_async'):
                if utils.settings.config['mud'].getboolean('run_table'):
                    asyncio.run(self.cmd_runner.run_async_table_view(self.repos.keys(), sys.argv))
                else:
                    asyncio.run(self.cmd_runner.run_async(self.repos.keys(), sys.argv))
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
            utils.print_error('No git repositories were found in this directory')
            return
        self.config.save(utils.CONFIG_FILE_NAME)

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
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith('-'):
                arg = sys.argv[1:][i - 1]
                if any(arg.startswith(prefix) for prefix in LABEL_PREFIX):
                    label = arg.split('=', 1)[1]
                    self.repos = self.config.with_label(label)
                elif any(arg.startswith(prefix) for prefix in BRANCH_PREFIX):
                    branch = arg.split('=', 1)[1]
                elif arg in MODIFIED_ATTR:
                    modified = True
                elif arg in DIVERGED_ATTR:
                    diverged = True
                else:
                    i += 1
                    continue
                del sys.argv[i]
                continue
            break
        directory = os.getcwd()
        to_delete = []
        for repo in self.repos:
            os.chdir(os.path.join(directory, repo))
            has_modifications = subprocess.check_output(['git', 'status', '--porcelain'])
            branch_filter = (branch is not None and branch.strip() and subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode('utf-8') != branch)
            is_diverged = not any('ahead' in line or 'behind' in line for line in subprocess.check_output(['git', 'status', '--branch', '--porcelain']).decode('utf-8').splitlines() if line.startswith('##'))
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
        await asyncio.to_thread(subprocess.run, ['git', 'fetch'], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)

    @staticmethod
    def _parse_aliases():
        for alias, command in dict(utils.settings.alias_settings).items():
            if sys.argv[0] == alias:
                sys.argv[0] = command


if __name__ == '__main__':
    utils.settings = Settings(utils.SETTINGS_FILE_NAME)
    cli = MudCLI()
    cli.run()
