import os
import utils
import asyncio
import subprocess

from utils import TEXT, BACK, RESET, STYLES, END_STYLES
from typing import List, Dict
from collections import Counter
from prettytable import PrettyTable, PLAIN_COLUMNS


class Commands:
    _label_color_cache = {}
    _current_color_index = 0

    def __init__(self, repos):
        self._last_printed_lines = 0
        self.repos = repos

    # `mud info` command implementation
    def info(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        for path, labels in repos.items():
            output = subprocess.check_output(['git', 'status', '--porcelain'], text=True, cwd=path)
            files = output.splitlines()

            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            status = self._get_status_string(files)
            colored_labels = self._get_formatted_labels(labels, utils.GLYPHS["label"])

            # Sync with origin status
            ahead_behind_cmd = subprocess.run(['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], text=True, cwd=path, capture_output=True)
            stdout = ahead_behind_cmd.stdout.strip().split()
            origin_sync = ''
            if len(stdout) >= 2:
                ahead, behind = stdout[0], stdout[1]
                if ahead and ahead != '0':
                    origin_sync += f'{TEXT["bright_green"]}{utils.GLYPHS["ahead"]} {ahead}{RESET}'
                if behind and behind != '0':
                    if origin_sync:
                        origin_sync += ' '
                    origin_sync += f'{TEXT["bright_blue"]}{utils.GLYPHS["behind"]} {behind}{RESET}'

            if not origin_sync.strip():
                origin_sync = f'{TEXT["blue"]}{utils.GLYPHS["synced"]}{RESET}'

            table.add_row([formatted_path, branch, origin_sync, status, colored_labels])

        self._print_table(table)

    # `mud status` command implementation
    def status(self, repos: Dict[str, List[str]]):
        table = self._get_table()
        for path, labels in repos.items():
            output = subprocess.check_output(['git', 'status', '--porcelain'], text=True, cwd=path)
            files = output.splitlines()

            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            status = self._get_status_string(files)

            colored_output = []

            for file in files[:5]:
                file_status = file[:2].strip()
                filename = file[3:].strip()
                parts = filename.split(os.sep)
                if file_status == 'M':
                    color = TEXT['yellow']
                elif file_status == 'A':
                    color = TEXT['green']
                elif file_status == 'R':
                    color = TEXT['blue']
                elif file_status == 'D':
                    color = TEXT['red']
                else:
                    color = TEXT['cyan']

                shortened_parts = [part[0] if index < len(parts) - 1 and part else f'{RESET}{color}{part}' for index, part in enumerate(parts)]
                filename = os.sep.join(shortened_parts)
                colored_output.append(f'{color}{STYLES["dim"]}{filename}{RESET}')
            if len(files) > 5:
                colored_output.append('...')

            table.add_row([formatted_path, branch, status, ', '.join(colored_output)])

        self._print_table(table)

    # `mud labels` command implementation
    def labels(self, repos: Dict[str, List[str]]):
        table = self._get_table()
        for path, labels in repos.items():
            formatted_path = self._get_formatted_path(path)
            colored_labels = self._get_formatted_labels(labels, utils.GLYPHS["label"])
            table.add_row([formatted_path, colored_labels])

        self._print_table(table)

    # `mud log` command implementation
    def log(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        for path in repos.keys():
            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            author = self._get_authors_name(path)
            commit = self._get_commit_message(path, 35)

            # Commit time
            commit_time_cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%cd', '--date=relative'], text=True, cwd=path, capture_output=True)
            commit_time = commit_time_cmd.stdout.strip()

            table.add_row([formatted_path, branch, author, commit_time, commit])

        self._print_table(table)

    # `mud branch` command implementation
    def branches(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        all_branches = {}

        # Preparing branches for sorting to display them in the right order.
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
            table.add_row([formatted_path, formatted_branches])

        self._print_table(table)

    # `mud tags` command implementation
    def tags(self, repos: Dict[str, List[str]]):
        table = self._get_table()

        for path, labels in repos.items():
            formatted_path = self._get_formatted_path(path)
            tags = [line.strip() for line in subprocess.check_output(['git', 'tag'], text=True, cwd=path).splitlines() if line.strip()]
            tags = [f"{utils.GLYPHS['tag']} {tag}" for tag in tags]
            tags = ' '.join(tags)
            table.add_row([formatted_path, tags])

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
                print(f'{self._get_formatted_path(path)}{TEXT["gray"]}>{RESET} {TEXT["yellow"]}{" ".join(command)}{RESET}')
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
        table[repo_path] = ['', f'{TEXT["yellow"]}{utils.GLYPHS["running"]}']

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.decode().strip()
            line = table[repo_path][0] if not line.strip() else line
            table[repo_path] = [line, f'{TEXT["yellow"]}{utils.GLYPHS["running"]}']
            self._print_process(table)

        return_code = await process.wait()
        if return_code == 0:
            status = f'{TEXT["green"]}{utils.GLYPHS["finished"]}'
        else:
            status = f'{TEXT["red"]}{utils.GLYPHS["failed"]} Code: {return_code}'

        table[repo_path] = [table[repo_path][0], status]
        self._print_process(table)

    def _print_process(self, info: Dict[str, List[str]]) -> None:
        table = self._get_table()

        for path, (line, status) in info.items():
            formatted_path = self._get_formatted_path(path)
            table.add_row([formatted_path, line, status])

        table_str = self._table_to_str(table)
        num_lines = table_str.count('\n') + 1

        if hasattr(self, '_last_printed_lines') and self._last_printed_lines > 0:
            for _ in range(self._last_printed_lines):
                print('\033[A\033[K', end='')

        print(f'{table_str}\n', end='')
        self._last_printed_lines = num_lines

    def _print_table(self, table: PrettyTable):
        table = self._table_to_str(table)
        if len(table) != 0:
            print(table)

    @staticmethod
    def _get_status_string(files: List[str]):
        modified, added, removed, moved = 0, 0, 0, 0

        for file in files:
            file = file.lstrip()
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
            status += f'{TEXT["bright_green"]}{added} {utils.GLYPHS["added"]}{RESET} '
        if modified:
            status += f'{TEXT["yellow"]}{modified} {utils.GLYPHS["modified"]}{RESET} '
        if moved:
            status += f'{TEXT["blue"]}{moved} {utils.GLYPHS["moved"]}{RESET} '
        if removed:
            status += f'{TEXT["red"]}{removed} {utils.GLYPHS["removed"]}{RESET} '
        if not files:
            status = f'{TEXT["green"]}{utils.GLYPHS["clear"]}{RESET}'
        return status

    @staticmethod
    def _table_to_str(table: PrettyTable) -> str:
        table = table.get_string()
        table = '\n'.join(line.lstrip() for line in table.splitlines())
        return table

    @staticmethod
    def _get_table() -> PrettyTable:
        return PrettyTable(border=False, header=False, style=PLAIN_COLUMNS, align='l')

    @staticmethod
    def _get_formatted_path(path: str) -> str:
        return f'{STYLES["dim"]}{TEXT["gray"]}../{RESET}{STYLES["dim"]}{path}{RESET}'

    @staticmethod
    def _get_branch_status(path: str) -> str:
        branch_cmd = subprocess.run('git rev-parse --abbrev-ref HEAD', shell=True, text=True, cwd=path, capture_output=True)
        branch_stdout = branch_cmd.stdout.strip()
        if branch_stdout == 'master' or branch_stdout == 'main':
            branch = f'{TEXT["yellow"]}{utils.GLYPHS["master"]}{RESET}{utils.GLYPHS["space"]}{branch_stdout}'
        elif branch_stdout == 'develop':
            branch = f'{TEXT["green"]}{utils.GLYPHS["feature"]}{RESET}{utils.GLYPHS["space"]}{branch_stdout}'
        elif '/' in branch_stdout:
            branch_path = branch_stdout.split('/')
            icon = Commands._get_branch_icon(branch_path[0])
            branch_color = Commands._get_branch_color(branch_path[0])
            branch = f'{TEXT[branch_color]}{icon}{RESET}{utils.GLYPHS["space"]}{branch_path[0]}{RESET}/{STYLES["bold"]}{("/".join(branch_path[1:]))}'
        else:
            branch = f'{TEXT["cyan"]}{utils.GLYPHS["branch"]}{RESET}{utils.GLYPHS["space"]}{branch_stdout}'
        return branch

    @staticmethod
    def _get_authors_name(path: str) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], text=True, cwd=path, capture_output=True)
        git_config_user_cmd = subprocess.run(['git', 'config', 'user.name'], text=True, capture_output=True)
        committer_color = '' if cmd.stdout.strip() == git_config_user_cmd.stdout.strip() else STYLES['dim']
        author = cmd.stdout.strip()
        author = author[:20] + '...' if len(author) > 20 else author
        author = f'{committer_color}{author}{RESET}'
        return author

    @staticmethod
    def _get_commit_message(path: str, max_chars: int) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%s'], text=True, cwd=path, capture_output=True)
        log = cmd.stdout.strip()
        log = log[:max_chars] + '...' if len(log) > max_chars else log
        return log

    @staticmethod
    def _get_formatted_labels(labels: List[str], glyph: str) -> str:
        if len(labels) == 0:
            return ''
        colored_label = ''
        for label in labels:
            color_index = Commands._get_color_index(label) % len(TEXT)
            colored_label += f'{TEXT[list(TEXT.keys())[color_index + 3]]}{glyph} {label}{RESET} '
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
            current_prefix = f'{STYLES["underline"]}' if current_branch == branch else ''
            current_prefix = current_prefix + STYLES['dim'] if is_origin else current_prefix
            origin_prefix = f'{TEXT["magenta"]}{STYLES["dim"]}o/' if is_origin else ''
            color = 'white'
            icon = utils.GLYPHS['branch']
            if branch == 'master' or branch == 'main':
                color = 'yellow'
                icon = f'{utils.GLYPHS["master"]}'
            elif branch == 'develop':
                color = 'green'
                icon = f'{utils.GLYPHS["feature"]}'
            elif '/' in branch:
                parts = branch.split('/')
                end_dim = '' if is_origin else END_STYLES['dim']
                branch = '/'.join([p[0] for p in parts[:-1]] + [end_dim + (
                    parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])]) if simplify_branches else '/'.join(
                    [p for p in parts[:-1]] + [end_dim + (parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])])
                branch = f'{STYLES["dim"]}{branch}'
                color = Commands._get_branch_color(parts[0])
                icon = Commands._get_branch_icon(parts[0])
            output += f'{current_prefix}{TEXT[color]}{icon}{utils.GLYPHS["space"]}{origin_prefix}{TEXT[color]}{branch}{RESET} '
        return output

    @staticmethod
    def _get_branch_icon(branch_prefix: str) -> str:
        return f'{utils.GLYPHS["bugfix"]}' if branch_prefix in ['bugfix', 'bug', 'hotfix'] else \
            f'{utils.GLYPHS["release"]}' if branch_prefix == 'release' else \
                f'{utils.GLYPHS["feature"]}' if branch_prefix in ['feature', 'feat', 'develop'] else \
                    f'{utils.GLYPHS["branch"]}'

    @staticmethod
    def _get_branch_color(branch_name: str) -> str:
        return 'red' if branch_name in ['bugfix', 'bug', 'hotfix'] else \
            'blue' if branch_name == 'release' else \
                'green' if branch_name in ['feature', 'feat', 'develop'] else \
                    'green'

    @staticmethod
    def _get_color_index(label: str) -> (str, str):
        if label not in Commands._label_color_cache:
            Commands._label_color_cache[label] = Commands._current_color_index
            Commands._current_color_index = (Commands._current_color_index + 1) % len(BACK.keys())
        return Commands._label_color_cache[label]
