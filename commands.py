import utils
import asyncio
import subprocess

from typing import List, Dict
from collections import Counter
from colorama import Fore, Back, Style
from prettytable import PrettyTable, PLAIN_COLUMNS

class Commands:
    def __init__(self, repos):
        self.repos = repos
        self.label_color_cache = {}
        self.current_color_index = 0

    # `mud status` command implementation
    def status(self, repos: Dict[str, List[str]]):
        table = self.get_table()

        if repos == None:
            return

        for path, tags in repos.items():
            formatted_path = self.get_formatted_path(path)
            branch = self.get_branch_status(path)
            author = self.get_commiters_name(path)
            commit = self.get_commit_message(path, 25)
            colored_labels = self.format_labels(tags)

            # Sync with origin status
            ahead_behind_cmd = subprocess.run(['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], shell=True, text=True, cwd=path, capture_output=True)
            ahead, behind = self.parse_ahead_behind(ahead_behind_cmd.stdout.strip())
            origin_sync = ''
            if ahead and ahead != '0':
                origin_sync += f'{Fore.LIGHTGREEN_EX}{utils.glyph("ahead")} {ahead}{utils.n}'
            if behind and behind != '0':
                if origin_sync:
                    origin_sync += " "
                origin_sync += f'{Fore.LIGHTBLUE_EX}{utils.glyph("behind")} {behind}{utils.n}'

            # Git status
            status_cmd = subprocess.run(['git', 'status', '-s'], text=True, cwd=path, capture_output=True)
            files = [line.lstrip() for line in status_cmd.stdout.strip().splitlines()]

            modified, added, removed, moved = 0, 0, 0, 0

            for file in files:
                if file.startswith('M') or file.startswith('??'): modified += 1
                elif file.startswith('A'): added += 1
                elif file.startswith('D'): removed += 1
                elif file.startswith('R'): moved += 1

            status = ''
            if modified: status += f'{Fore.YELLOW}{modified} {utils.glyph("modified")}{utils.n} ' 
            if added:    status += f'{Fore.GREEN}{added} {utils.glyph("added")}{utils.n} '
            if removed:  status += f'{Fore.RED}{removed} {utils.glyph("removed")}{utils.n} '
            if moved:    status += f'{Fore.BLUE}{moved} {utils.glyph("moved")}{utils.n} '
            if not files: status = f'{Fore.GREEN}{utils.glyph("clear")}{utils.n}'

            table.add_row([formatted_path , branch, origin_sync, status, author, commit, colored_labels])

        table = self.print_table(table)
        if len(table) != 0:
            print(table)

    # `mud log` command implementation
    def log(self, repos: Dict[str, List[str]]):
        table = self.get_table()
        for path, labels in repos.items():
            formatted_path = self.get_formatted_path(path)
            branch = self.get_branch_status(path)
            author = self.get_commiters_name(path)
            commit = self.get_commit_message(path, 35)
            colored_labels = self.format_labels(labels)

            # Commit time
            commit_time_cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%cd', '--date=relative'], text=True, cwd=path, capture_output=True)
            commit_time = commit_time_cmd.stdout.strip()

            table.add_row([formatted_path , branch, author, commit_time, commit, colored_labels])

        table = self.print_table(table)
        if len(table) != 0:
            print(table)

    # `mud branch` command implementation
    def branches(self, repos: Dict[str, List[str]]):
        table = self.get_table()

        all_branches = {}
        for path in repos.keys():
            raw_branches = [line.strip() for line in subprocess.check_output(['git', 'branch'], text=True, cwd=path).split('\n') if line.strip()]
            for branch in raw_branches:
                branch = branch.replace(' ', '').replace('*', '')
                if branch not in all_branches:
                    all_branches[branch] = 0
                all_branches[branch] += 1
        branch_counter = Counter(all_branches)

        for path, labels in repos.items():
            formatted_path = self.get_formatted_path(path)
            branch = self.get_branch_status(path)

            branches = [line.strip() for line in subprocess.check_output(['git', 'branch'], text=True, cwd=path).split('\n') if line.strip()]
            branches = [branch[2:] if branch.startswith('* ') else branch for branch in branches]

            current_branch = next((branch for branch in branches if branch.startswith('*')), None)
            if current_branch:
                current_branch = current_branch[2:]

            sorted_branches = sorted(branches, key=lambda x: branch_counter.get(x.strip('* '), 0), reverse=True)

            if current_branch and current_branch in sorted_branches:
                sorted_branches.remove(current_branch)
                sorted_branches.insert(0, f'* {current_branch}')

            formatted_branches = self.format_branches(sorted_branches)
            colored_labels = self.format_labels(labels)

            table.add_row([formatted_path, branch, formatted_branches, colored_labels])

        table = self.print_table(table)
        if len(table) != 0:
            print(table)

    # `mud <COMMAND>` when run_async = 0 and run_table = 0
    def run_ordered(self, repos: List[str], command: [str]):
        for repo in repos:
            print(f'{Style.DIM}{Fore.LIGHTBLACK_EX}../{Fore.WHITE}{repo}>{utils.n} {command}{utils.n}')
            result = subprocess.run(command, shell=True, cwd=repo, capture_output=True, text=True)
            if result.stderr:
                print(result.stderr)
            if result.stdout and not result.stdout.isspace():
                print(result.stdout)

    # `mud <COMMAND>` when run_async = 1 and run_table = 0
    async def run_async(self, repos: List[str], command: str):
        sem = asyncio.Semaphore(len(repos))
        async def run_process(path):
            async with sem:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                print(f'{Style.DIM}{Fore.LIGHTBLACK_EX}../{Fore.WHITE}{path}>{utils.n} {command}{utils.n}')
                if stderr:
                    print(stderr.decode())
                if stdout and not stdout.isspace():
                    print(stdout.decode())

        await asyncio.gather(*(run_process(path) for path in repos))

    # `mud <COMMAND>` when run_async = 1 and run_table = 1
    async def run_async_table_view(self, repos: List[str], command: [str]):
        sem = asyncio.Semaphore(len(repos)) 
        table = {repo: '' for repo in repos}
        async def task(repo):
            async with sem:
                await self.run_process(repo, table, command)
        tasks = [asyncio.create_task(task(repo)) for repo in repos]
        await asyncio.gather(*tasks)

    async def run_process(self, repo_path, table, command: str):
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.decode().strip()
            table[repo_path] = line
            self.print_process(table)

    def print_process(self, info: Dict[str, str]):
        table = self.get_table()

        for path, output in info.items():
            formatted_path = self.get_formatted_path(path)
            table.add_row([formatted_path, output])

        print(f'\x1bc{self.print_table(table)}\n', end='')

    def get_table(self) -> PrettyTable:
        return PrettyTable(border=False, header=False, style=PLAIN_COLUMNS, align='l')

    def print_table(self, table: PrettyTable) -> str:
        table = table.get_string()
        table = "\n".join(line.lstrip() for line in table.splitlines())
        return table

    def get_formatted_path(self, path: str) -> str:
        return f'{Style.DIM}{Fore.LIGHTBLACK_EX}../{Fore.LIGHTWHITE_EX}{path}{utils.n}'

    # Displaying current branch
    def get_branch_status(self, path: str) -> str:
        branch_cmd = subprocess.run('git rev-parse --abbrev-ref HEAD', shell=True, text=True, cwd=path, capture_output=True)
        branch_stdout = branch_cmd.stdout.strip()
        branch = ''
        if branch_stdout == 'master' or branch_stdout == 'main':
            branch = f"{Fore.YELLOW}{utils.glyph('master')}{utils.n} {branch_stdout}"
        elif branch_stdout  == 'develop':
            branch = f"{Fore.GREEN}{utils.glyph('feature')}{utils.n} {branch_stdout}"
        elif '/' in branch_stdout:
            branch_path = branch_stdout.split('/')
            icon = branch_path[0]
            icon = f'{Fore.RED}{utils.glyph("bugfix")}{utils.n}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                f'{Fore.BLUE}{utils.glyph("release")}{utils.n}' if icon == 'release' else \
                f'{Fore.GREEN}{utils.glyph("feature")}{utils.n}' if icon in ['feature', 'feat', 'develop'] else \
                f'{Fore.GREEN}{utils.glyph("branch")}{utils.n}'
            branch = f"{icon} {Fore.WHITE}{branch_path[0]}{utils.n}/{('/'.join(branch_path[1:]))}"
        else:
            branch = f'{Fore.CYAN}{utils.glyph("branch")}{utils.n} {branch_stdout}'
        return branch

    # Last commiter name
    def get_commiters_name(self, path: str) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], text=True, cwd=path, capture_output=True)
        git_config_user_cmd = subprocess.run(['git', 'config', 'user.name'], text=True, capture_output=True)
        commiter_color = f'{Fore.LIGHTWHITE_EX}' if cmd.stdout.strip() == git_config_user_cmd.stdout.strip() else Fore.WHITE
        author = cmd.stdout.strip()
        author = author[:20] + '...' if len(author) > 20 else author
        author = f'{commiter_color}{author}{utils.n}'
        return author

    # Last commit message
    def get_commit_message(self, path: str, max_chars: int) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%s'], text=True, cwd=path, capture_output=True)
        log = cmd.stdout.strip()
        log = log[:max_chars] + '...' if len(log) > max_chars else log     
        return log

    # ahead/behind sorting
    def parse_ahead_behind(self, stdout : str) -> (str, str):
        if stdout:
            parts = stdout.split()
            if len(parts) == 2:
                return parts[0], parts[1]
        return '', ''

    def format_labels(self, labels: List[str]) -> str:
        if len(labels) == 0:
            return ''

        colored_label = ''
        for label in labels:
            color_index = self.get_color_index(label)
            background = utils.bg[color_index % len(utils.bg)]
            foreground = utils.fg[color_index % len(utils.fg)]
            colored_label += f"{foreground}{utils.glyph('(')}{utils.n}{background}{label}{utils.n}{foreground}{utils.glyph(')')}{utils.n}"

        return colored_label

    def format_branches(self, branches: List[str]) -> str:
        if len(branches) == 0:
            return ''

        output = ''
        for branch in branches:
            icon = utils.glyph('branch')
            if branch == 'master' or branch == 'main':
                icon = f"{Fore.YELLOW}{utils.glyph('master')}"
            elif branch == 'develop':
                icon = f"{Fore.GREEN}{utils.glyph('feature')}"
            elif '/' in branch:
                parts = branch.split('/')
                branch = '/'.join([p[0] for p in parts[:-1]] + [f'{Style.NORMAL}' + parts[-1]])
                branch = f'{Style.DIM}{branch}'
                icon = parts[0]
                icon = f'{Fore.RED}{utils.glyph("bugfix")}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                    f'{Fore.BLUE}{utils.glyph("release")}' if icon == 'release' else \
                    f'{Fore.GREEN}{utils.glyph("feature")}' if icon in ['feature', 'feat', 'develop'] else \
                    f'{Fore.GREEN}{utils.glyph("branch")}'

            output += f"{icon} {branch}{utils.n} "
        return output        

    def get_color_index(self, label: str) -> (str, str):
        if label not in self.label_color_cache:
            self.label_color_cache[label] = self.current_color_index
            self.current_color_index = (self.current_color_index + 1) % len(Back.__dict__.keys())
        return self.label_color_cache[label]