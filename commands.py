import utils
import asyncio
import subprocess

from utils import TEXT, BACK, RESET, STYLES, END_STYLES, glyph
from typing import List, Dict
from collections import Counter
from prettytable import PrettyTable, PLAIN_COLUMNS


class Commands:
    def __init__(self, repos):
        self.repos = repos
        self.label_color_cache = {}
        self.current_color_index = 0

    # `mud status` command implementation
    def status(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        for path, tags in repos.items():
            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            colored_labels = self._get_formatted_labels(tags)

            # Sync with origin status
            ahead_behind_cmd = subprocess.run(['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], text=True, cwd=path, capture_output=True)
            stdout = ahead_behind_cmd.stdout.strip().split()
            if len(stdout) >= 2:
                ahead, behind = stdout[0], stdout[1]
                origin_sync = ''
                if ahead and ahead != '0':
                    origin_sync += f'{TEXT["bright_green"]}{glyph("ahead")} {ahead}{RESET}'
                if behind and behind != '0':
                    if origin_sync:
                        origin_sync += ' '
                    origin_sync += f'{TEXT["bright_blue"]}{glyph("behind")} {behind}{RESET}'
            else:
                origin_sync = ''
            # Git status
            status_cmd = subprocess.run(['git', 'status', '-s'], text=True, cwd=path, capture_output=True)
            files = [line.lstrip() for line in status_cmd.stdout.strip().splitlines()]

            modified, added, removed, moved = 0, 0, 0, 0

            for file in files:
                if file.startswith('M'):
                    modified += 1
                elif file.startswith('A') or file.startswith('??'):
                    added += 1
                elif file.startswith('D'):
                    removed += 1
                elif file.startswith('R'):
                    moved += 1
            status = ''
            if added:
                status += f'{TEXT["bright_green"]}{added} {glyph("added")}{RESET} '
            if modified:
                status += f'{TEXT["yellow"]}{modified} {glyph("modified")}{RESET} '
            if moved:
                status += f'{TEXT["blue"]}{moved} {glyph("moved")}{RESET} '
            if removed:
                status += f'{TEXT["red"]}{removed} {glyph("removed")}{RESET} '
            if not files:
                status = f'{TEXT["green"]}{glyph("clear")}{RESET}'

            table.add_row([formatted_path, branch, origin_sync, status, colored_labels])

        self._print_table(table)

    # `mud log` command implementation
    def log(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        for path, labels in repos.items():
            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            author = self._get_authors_name(path)
            commit = self._get_commit_message(path, 35)
            colored_labels = self._get_formatted_labels(labels)

            # Commit time
            commit_time_cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%cd', '--date=relative'], text=True, cwd=path, capture_output=True)
            commit_time = commit_time_cmd.stdout.strip()

            table.add_row([formatted_path, branch, author, commit_time, commit, colored_labels])

        self._print_table(table)

    # `mud branch` command implementation
    def branches(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
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
            formatted_path = self._get_formatted_path(path)
            branches = subprocess.check_output(['git', 'branch'], text=True, cwd=path).splitlines()
            current_branch = next((branch.lstrip('* ') for branch in branches if branch.startswith('*')), None)
            branches = [branch.lstrip('* ') for branch in branches]
            sorted_branches = sorted(branches, key=lambda x: branch_counter.get(x, 0), reverse=True)

            if current_branch and current_branch in sorted_branches:
                sorted_branches.remove(current_branch)
                sorted_branches.insert(0, current_branch)

            formatted_branches = self._get_formatted_branches(sorted_branches, current_branch)

            colored_labels = self._get_formatted_labels(labels)
            table.add_row([formatted_path, formatted_branches, colored_labels])

        self._print_table(table)

    # `mud <COMMAND>` when run_async = 0 and run_table = 0
    def run_ordered(self, repos: List[str], command: [str]) -> None:
        for path in repos:
            print(f'{self._get_formatted_path(path)}{RESET} {command}{RESET}')
            result = subprocess.run(command, shell=True, cwd=path, capture_output=True, text=True)
            if result.stderr:
                print(result.stderr)
            if result.stdout and not result.stdout.isspace():
                print(result.stdout)

    # `mud <COMMAND>` when run_async = 1 and run_table = 0
    async def run_async(self, repos: List[str], command: List[str]) -> None:
        sem = asyncio.Semaphore(len(repos))

        async def run_process(path: str) -> None:
            async with sem:
                process = await asyncio.create_subprocess_exec(*command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = await process.communicate()
                print(f'{self._get_formatted_path(path)}>{RESET} {command}')
                if stderr:
                    print(stderr.decode())
                if stdout and not stdout.isspace():
                    print(stdout.decode())

        await asyncio.gather(*(run_process(path) for path in repos))

    # `mud <COMMAND>` when run_async = 1 and run_table = 1
    async def run_async_table_view(self, repos: List[str], command: List[str]) -> None:
        sem = asyncio.Semaphore(len(repos))
        table = {repo: ['', ''] for repo in repos}

        async def task(repo: str) -> None:
            async with sem:
                await self._run_process(repo, table, command)

        tasks = [asyncio.create_task(task(repo)) for repo in repos]
        await asyncio.gather(*tasks)

    async def _run_process(self, repo_path: str, table: Dict[str, List[str]], command: List[str]) -> None:
        process = await asyncio.create_subprocess_exec(*command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        table[repo_path] = ['', f'{TEXT["yellow"]}{glyph("running")}']

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.decode().strip()
            line = table[repo_path][0] if not line.strip() else line
            table[repo_path] = [line, f'{TEXT["yellow"]}{glyph("running")}']
            self._print_process(table)

        return_code = await process.wait()
        if return_code == 0:
            status = f'{TEXT["green"]}{glyph("finished")}'
        else:
            status = f'{TEXT["red"]}{glyph("failed")} Code: {return_code}'

        table[repo_path] = [table[repo_path][0], status]
        self._print_process(table)

    def _print_process(self, info: Dict[str, List[str]]) -> None:
        table = self._get_table()

        for path, (line, status) in info.items():
            formatted_path = self._get_formatted_path(path)
            table.add_row([formatted_path, line, status])

        print(f'\x1bc{self._table_to_str(table)}\n', end='')

    def _print_table(self, table: PrettyTable):
        table = self._table_to_str(table)
        if len(table) != 0:
            print(table)

    @staticmethod
    def _table_to_str(table: PrettyTable) -> str:
        table = table.get_string()
        table = '\n'.join(line.lstrip() for line in table.splitlines())
        return table

    @staticmethod
    def _get_table() -> PrettyTable:
        return PrettyTable(border=False, header=False, style=PLAIN_COLUMNS, align='l')

    # Prettified repository path
    @staticmethod
    def _get_formatted_path(path: str) -> str:
        return f'{STYLES["dim"]}{TEXT["gray"]}../{RESET}{STYLES["dim"]}{path}{RESET}'

    # Displaying current branch
    @staticmethod
    def _get_branch_status(path: str) -> str:
        branch_cmd = subprocess.run('git rev-parse --abbrev-ref HEAD', shell=True, text=True, cwd=path,
                                    capture_output=True)
        branch_stdout = branch_cmd.stdout.strip()
        if branch_stdout == 'master' or branch_stdout == 'main':
            branch = f'{TEXT["yellow"]}{glyph("master")}{RESET} {branch_stdout}'
        elif branch_stdout == 'develop':
            branch = f'{TEXT["green"]}{glyph("feature")}{RESET} {branch_stdout}'
        elif '/' in branch_stdout:
            branch_path = branch_stdout.split('/')
            icon = branch_path[0]
            icon = f'{TEXT["red"]}{glyph("bugfix")}{RESET}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                f'{TEXT["blue"]}{glyph("release")}{RESET}' if icon == 'release' else \
                f'{TEXT["green"]}{glyph("feature")}{RESET}' if icon in ['feature', 'feat', 'develop'] else \
                f'{TEXT["green"]}{glyph("branch")}{RESET}'
            branch = f'{icon} {STYLES["bold"]}{branch_path[0]}{RESET}/{STYLES["bold"]}{("/".join(branch_path[1:]))}'
        else:
            branch = f'{TEXT["cyan"]}{glyph("branch")}{RESET} {branch_stdout}'
        return branch

    # Last author's name
    @staticmethod
    def _get_authors_name(path: str) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], text=True, cwd=path, capture_output=True)
        git_config_user_cmd = subprocess.run(['git', 'config', 'user.name'], text=True, capture_output=True)
        committer_color = '' if cmd.stdout.strip() == git_config_user_cmd.stdout.strip() else STYLES["dim"]
        author = cmd.stdout.strip()
        author = author[:20] + '...' if len(author) > 20 else author
        author = f'{committer_color}{author}{RESET}'
        return author

    # Last commit message
    @staticmethod
    def _get_commit_message(path: str, max_chars: int) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%s'], text=True, cwd=path, capture_output=True)
        log = cmd.stdout.strip()
        log = log[:max_chars] + '...' if len(log) > max_chars else log
        return log

    def _get_formatted_labels(self, labels: List[str]) -> str:
        if len(labels) == 0:
            return ''

        colored_label = ''
        for label in labels:
            color_index = self._get_color_index(label) % len(TEXT)
            colored_label += f'{TEXT[list(TEXT.keys())[color_index + 3]]}{glyph("label")}{RESET} {label} '

        return colored_label

    @staticmethod
    def _get_formatted_branches(branches: List[str], current_branch: str) -> str:
        if len(branches) == 0:
            return ''

        simplify_branches = utils.settings.config['mud'].getboolean('simplify_branches') is True
        output = ''
        for branch in branches:
            is_origin = branch.startswith('origin/')
            branch = branch.replace('origin/', '') if is_origin else branch
            current_prefix = f'{STYLES["italic"]}{STYLES["bold"]}' if current_branch == branch else ''
            current_prefix = current_prefix + STYLES['dim'] if is_origin else current_prefix
            origin_prefix = f'{TEXT["magenta"]}{STYLES["dim"]}o/' if is_origin else ''
            color = 'white'
            icon = glyph('branch')
            if branch == 'master' or branch == 'main':
                color = 'yellow'
                icon = f'{glyph("master")}'
            elif branch == 'develop':
                color = 'green'
                icon = f'{glyph("feature")}'
            elif '/' in branch:
                parts = branch.split('/')
                end_dim = '' if is_origin else END_STYLES["dim"]
                branch = '/'.join([p[0] for p in parts[:-1]] + [end_dim + (
                    parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])]) if simplify_branches else '/'.join(
                    [p for p in parts[:-1]] + [end_dim + (parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])])
                branch = f'{STYLES["dim"]}{branch}'
                icon = parts[0]
                color = 'red' if icon in ['bugfix', 'bug', 'hotfix'] else \
                    'blue' if icon == 'release' else \
                    'green' if icon in ['feature', 'feat', 'develop'] else \
                    'green'
                icon = f'{glyph("bugfix")}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                    f'{glyph("release")}' if icon == 'release' else \
                    f'{glyph("feature")}' if icon in ['feature', 'feat', 'develop'] else \
                    f'{glyph("branch")}'
            output += f'{current_prefix}{TEXT[color]}{icon} {origin_prefix}{TEXT[color]}{branch}{RESET} '
        return output

    def _get_color_index(self, label: str) -> (str, str):
        if label not in self.label_color_cache:
            self.label_color_cache[label] = self.current_color_index
            self.current_color_index = (self.current_color_index + 1) % len(BACK.keys())
        return self.label_color_cache[label]
