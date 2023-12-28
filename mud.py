#!/usr/bin/env python3

import os
import sys
import utils
import asyncio
import argparse
import colorama
import subprocess

from config import Config
from commands import Commands

help = [ 'help', '--help', '-h' ]
version = '--version'
set_global = '--set-global'
# Filters
label_prefix = '-l=', '--label='
branch_prefix = '-b=', '--branch='
modified_attr = '-m', '--modified'
diverged_attr = '-d', '--diverged'
# Commands
commands = {
    'init' : ['init'],
    'add': ['add', 'a'],
    'remove':  ['remove', 'rm'],
    'branches': ['branch', 'branches', 'br'],
    'status': ['status', 'st'],
    'log': ['log', 'l'],
}

colorama.init()

class MudCLI:
    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):
        parser = argparse.ArgumentParser(description=f'mud allows you to run commands in multiple directories.')
        subparsers = parser.add_subparsers(dest='command')

        subparsers.add_parser(commands['init'][0], aliases=commands['init'][1:], help='Initializing .mudconfig, adds all repositories in this directory to .mudconfig')
        subparsers.add_parser(commands['status'][0], aliases=commands['status'][1:], help='Displays git status in a table view')
        subparsers.add_parser(commands['branches'][0], aliases=commands['branches'][1:], help='Displays all branches in a table view')
        subparsers.add_parser(commands['log'][0], aliases=commands['log'][1:], help='Displays log of last commit for all repos in a table view')

        add_parser = subparsers.add_parser(commands['add'][0], aliases=commands['add'][1:], help='Register directory')
        add_parser.add_argument('label', help='The label to add (optional)', nargs='?', default='', type=str)
        add_parser.add_argument('path', help='Directory to add (optional)', nargs='?', type=str,)

        remove_parser = subparsers.add_parser(commands['remove'][0], aliases=commands['remove'][1:], help='Remove label from directory or directory in .mudconfig')
        remove_parser.add_argument('label', help='Label to remove from directory (optional)', nargs='?', default='', type=str)
        remove_parser.add_argument('path', help='Directory to remove (optional)', nargs='?', type=str)
        
        parser.add_argument(*label_prefix, metavar='LABEL', nargs='?', default='', type=str, help='Filter repos with provided label')
        parser.add_argument(*branch_prefix, metavar='BRANCH', nargs='?', default='', type=str, help='Filter repos with provided branch')
        parser.add_argument(*modified_attr, action='store_true', help='Filter modified repos')
        parser.add_argument(*diverged_attr, action='store_true', help='Filter diverged repos')
        parser.add_argument(set_global, help='Sets \'.mudconfig\' in current directory as your global \'.mudconfig\' so you can use it anywhere', action='store_true')
        parser.add_argument(version, help='Displays current version of mud', action='store_true')
        parser.add_argument('catch_all', nargs='*', help='Type any commands to execute among repositories.')
        return parser

    def run(self):
        # Displays default help message
        if len(sys.argv) == 1 or sys.argv[1] in help:
            self.parser.print_help()
            return
        if sys.argv[1] in set_global:
            config_path = os.path.join(os.getcwd(), utils.CONFIG_FILE_NAME)
            if os.path.exists(config_path):
                utils.settings.config.set('mud', 'config_path', config_path)
                utils.settings.save()
                print('Current .mudconfig set as a global configuration')
            return
        if sys.argv[1] in version:
            utils.print_about()
            return

        self.config = Config()
        # Filter out repositories if user provided filters
        self.filter_repos()

        if len(self.repos) == 0:
            utils.print_error("No repositories are matching this filter")
            return

        self.cmd_runner = Commands(self.config)
        # Handling commands
        if len(sys.argv) > 1 and sys.argv[1] in [cmd for group in commands.values() for cmd in group]:
            args = self.parser.parse_args()
            if args.command in commands['init']:
                self.add(args)
            elif args.command in commands['add']:
                self.add(args)
            elif args.command in commands['remove']:
                self.remove(args)
            else:
                if utils.settings.config['mud'].getboolean('auto_fetch') == True:
                    self.fetch_all()
                if args.command in commands['status']:
                    self.cmd_runner.status(self.repos)
                elif args.command in commands['log']:
                    self.cmd_runner.log(self.repos)
                elif args.command in commands['branches']:
                    self.cmd_runner.branches(self.repos)
        # Handling general commands
        else:
            del sys.argv[0]
            self.parse_aliases()
            command_str = ' '.join(sys.argv)
            if utils.settings.config['mud'].getboolean('run_async'):
                if utils.settings.config['mud'].getboolean('run_table'):
                    asyncio.run(self.cmd_runner.run_async_table_view(self.repos.keys(), command_str))
                else:
                    asyncio.run(self.cmd_runner.run_async(self.repos.keys(), command_str))
            else:
                self.cmd_runner.run_ordered(self.repos.keys(), command_str)

    def filter_repos(self):
        self.repos = self.config.all()
        branch = None
        modified = False
        diverged = False
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith('-') == False:
                break
            arg = sys.argv[1:][i - 1]
            if any(arg.startswith(prefix) for prefix in label_prefix):
                label = arg.split('=', 1)[1]
                self.repos = self.config.with_label(label)
            elif any(arg.startswith(prefix) for prefix in branch_prefix):
                branch = arg.split('=', 1)[1]
            elif arg in modified_attr:
                modified = True
            elif arg in diverged_attr:
                diverged = True
            else:
                i += 1
                continue
            del sys.argv[i]
        dir = os.getcwd()
        to_delete = []
        for repo in self.repos:
            os.chdir(os.path.join(dir, repo))
            has_modifications = subprocess.check_output(['git', 'status', '--porcelain'])
            branch_filter = branch is not None and branch.strip() and subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode('utf-8') != branch
            is_diverged = not any('ahead' in line or 'behind' in line for line in subprocess.check_output(['git', 'status', '--branch', '--porcelain']).decode('utf-8').splitlines() if line.startswith('##'))
            if (modified and not has_modifications) or (branch and branch_filter) or (diverged and is_diverged):
                to_delete.append(repo)

        for repo in to_delete:
            del self.repos[repo]
        os.chdir(dir)

    def fetch_all(self):
        if utils.settings.config['mud'].getboolean('run_async'):
            asyncio.run(self.fetch_all_async())
        else:
            for repo in self.repos:
                subprocess.run(['git', 'fetch'], cwd=repo, capture_output=True)

    async def fetch_all_async(self):
        await asyncio.gather(*(self.fetch_repo(repo) for repo in self.repos))

    async def fetch_repo(self, repo: str):
        await asyncio.create_subprocess_exec('git', 'fetch', cwd=repo)

    def init(self, args):
        index = 0
        directories = [d for d in os.listdir('.') if os.path.isdir(d) and os.path.isdir(os.path.join(d, '.git'))]
        for dir in directories:
            self.config.add_label(dir, getattr(args, 'label', ''))
            index += 1
            print(f'{dir} added')
        if index == 0:
            utils.print_error('No git repositories were found in this directory')
            return
        self.config.save(utils.CONFIG_FILE_NAME)
    
    def add(self, args):
        self.config.add_label(args.path, args.label)
        self.config.save(utils.CONFIG_FILE_NAME)
    
    def remove(self, args):
        if args.path:
            self.config.remove_label(args.path, args.label)
        elif args.label:
            self.config.remove_path(args.label)
        else:
            utils.print_error(f"Invalid input. Please provide a value to remove.")
        self.config.save(utils.CONFIG_FILE_NAME)
    
    def parse_aliases(self):
        for alias, command in dict(utils.settings.alias_settings).items():
            if sys.argv[0] == alias:
                sys.argv[0] = command

if __name__ == "__main__":
    cli = MudCLI()
    cli.run()