import utils
import asyncio
import subprocess

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

        if repos == None:
            return

        for path, tags in repos.items():
            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            author = self._get_commiters_name(path)
            commit = self._get_commit_message(path, 30)
            colored_labels = self._get_formatted_labels(tags)

            # Sync with origin status
            ahead_behind_cmd = subprocess.run(['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], shell=True, text=True, cwd=path, capture_output=True)
            ahead, behind = self._get_formatted_ahead_behind(ahead_behind_cmd.stdout.strip())
            origin_sync = ''
            if ahead and ahead != '0':
                origin_sync += f'{utils.FOREGROUND["bright_green"]}{utils.glyph("ahead")} {ahead}{utils.RESET}'
            if behind and behind != '0':
                if origin_sync:
                    origin_sync += ' '
                origin_sync += f'{utils.FOREGROUND["bright_blue"]}{utils.glyph("behind")} {behind}{utils.RESET}'

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
            if modified: status += f'{utils.FOREGROUND["yellow"]}{modified} {utils.glyph("modified")}{utils.RESET} ' 
            if added:    status += f'{utils.FOREGROUND["greeb"]}{added} {utils.glyph("added")}{utils.RESET} '
            if removed:  status += f'{utils.FOREGROUND["blue"]}{removed} {utils.glyph("removed")}{utils.RESET} '
            if moved:    status += f'{utils.FOREGROUND["blue"]}{moved} {utils.glyph("moved")}{utils.RESET} '
            if not files: status = f'{utils.FOREGROUND["green"]}{utils.glyph("clear")}{utils.RESET}'

            table.add_row([formatted_path , branch, origin_sync, status, author, commit, colored_labels])

        table = self._print_table(table)
        if len(table) != 0:
            print(table)

    # `mud log` command implementation
    def log(self, repos: Dict[str, List[str]]) -> None:
        table = self._get_table()
        for path, labels in repos.items():
            formatted_path = self._get_formatted_path(path)
            branch = self._get_branch_status(path)
            author = self._get_commiters_name(path)
            commit = self._get_commit_message(path, 35)
            colored_labels = self._get_formatted_labels(labels)

            # Commit time
            commit_time_cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%cd', '--date=relative'], text=True, cwd=path, capture_output=True)
            commit_time = commit_time_cmd.stdout.strip()

            table.add_row([formatted_path , branch, author, commit_time, commit, colored_labels])

        table = self._print_table(table)
        if len(table) != 0:
            print(table)

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
            branch = self._get_branch_status(path)

            branches = [line.strip() for line in subprocess.check_output(['git', 'branch'], text=True, cwd=path).split('\n') if line.strip()]
            branches = [branch[2:] if branch.startswith('* ') else branch for branch in branches]

            current_branch = next((branch for branch in branches if branch.startswith('*')), None)
            if current_branch:
                current_branch = current_branch[2:]

            sorted_branches = sorted(branches, key=lambda x: branch_counter.get(x.strip('* '), 0), reverse=True)

            if current_branch and current_branch in sorted_branches:
                sorted_branches.remove(current_branch)
                sorted_branches.insert(0, f'* {current_branch}')

            formatted_branches = self._get_formatted_branches(sorted_branches)
            colored_labels = self._get_formatted_labels(labels)

            table.add_row([formatted_path, branch, formatted_branches, colored_labels])

        table = self._print_table(table)
        if len(table) != 0:
            print(table)

    # `mud <COMMAND>` when run_async = 0 and run_table = 0
    def run_ordered(self, repos: List[str], command: [str]) -> None:
        for path in repos:
            print(f'{self._get_formatted_path(path)}{utils.RESET} {command}{utils.RESET}')
            result = subprocess.run(command, shell=True, cwd=path, capture_output=True, text=True)
            if result.stderr:
                print(result.stderr)
            if result.stdout and not result.stdout.isspace():
                print(result.stdout)

    # `mud <COMMAND>` when run_async = 1 and run_table = 0
    async def run_async(self, repos: List[str], command: str) -> None:
        sem = asyncio.Semaphore(len(repos))
        async def run_process(path: str) -> None:
            async with sem:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                print(f'{self._get_formatted_path(path)}>{utils.RESET} {command}{utils.RESET}')
                if stderr:
                    print(stderr.decode())
                if stdout and not stdout.isspace():
                    print(stdout.decode())
        await asyncio.gather(*(run_process(path) for path in repos))

    # `mud <COMMAND>` when run_async = 1 and run_table = 1
    async def _run_async_table_view(self, repos: List[str], command: [str]) -> None:
        sem = asyncio.Semaphore(len(repos)) 
        table = {repo: '' for repo in repos}
        async def task(repo: str) -> None:
            async with sem:
                await self._run_process(repo, table, command)
        tasks = [asyncio.create_task(task(repo)) for repo in repos]
        await asyncio.gather(*tasks)

    async def _run_process(self, repo_path, table, command: str) -> None:
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
            self._print_process(table)

    def _print_process(self, info: Dict[str, str]) -> None:
        table = self._get_table()

        for path, output in info.items():
            formatted_path = self._get_formatted_path(path)
            table.add_row([formatted_path, output])

        print(f'\x1bc{self._print_table(table)}\n', end='')

    def _print_table(self, table: PrettyTable) -> str:
        table = table.get_string()
        table = '\n'.join(line.lstrip() for line in table.splitlines())
        return table
    
    def _get_table(self) -> PrettyTable:
        return PrettyTable(border=False, header=False, style=PLAIN_COLUMNS, align='l')

    def _get_formatted_path(self, path: str) -> str:
        return f'{utils.STYLES["dim"]}{utils.FOREGROUND["gray"]}../{utils.RESET}{utils.STYLES["dim"]}{path}{utils.RESET}'

    # Displaying current branch
    def _get_branch_status(self, path: str) -> str:
        branch_cmd = subprocess.run('git rev-parse --abbrev-ref HEAD', shell=True, text=True, cwd=path, capture_output=True)
        branch_stdout = branch_cmd.stdout.strip()
        branch = ''
        if branch_stdout == 'master' or branch_stdout == 'main':
            branch = f'{utils.FOREGROUND["yellow"]}{utils.glyph("master")}{utils.RESET} {branch_stdout}'
        elif branch_stdout  == 'develop':
            branch = f'{utils.FOREGROUND["green"]}{utils.glyph("feature")}{utils.RESET} {branch_stdout}'
        elif '/' in branch_stdout:
            branch_path = branch_stdout.split('/')
            icon = branch_path[0]
            icon = f'{utils.FOREGROUND["red"]}{utils.glyph("bugfix")}{utils.RESET}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                f'{utils.FOREGROUND["blue"]}{utils.glyph("release")}{utils.RESET}' if icon == 'release' else \
                f'{utils.FOREGROUND["green"]}{utils.glyph("feature")}{utils.RESET}' if icon in ['feature', 'feat', 'develop'] else \
                f'{utils.FOREGROUND["green"]}{utils.glyph("branch")}{utils.RESET}'
            branch = f'{icon} {utils.STYLES["bold"]}{branch_path[0]}{utils.RESET}/{utils.FOREGROUND["blink"]}{("/".join(branch_path[1:]))}'
        else:
            branch = f'{utils.FOREGROUND["cyan"]}{utils.glyph("branch")}{utils.RESET} {branch_stdout}'
        return branch

    # Last commiter name
    def _get_commiters_name(self, path: str) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], text=True, cwd=path, capture_output=True)
        git_config_user_cmd = subprocess.run(['git', 'config', 'user.name'], text=True, capture_output=True)
        commiter_color = '' if cmd.stdout.strip() == git_config_user_cmd.stdout.strip() else utils.STYLES["dim"]
        author = cmd.stdout.strip()
        author = author[:20] + '...' if len(author) > 20 else author
        author = f'{commiter_color}{author}{utils.RESET}'
        return author

    # Last commit message
    def _get_commit_message(self, path: str, max_chars: int) -> str:
        cmd = subprocess.run(['git', 'log', '-1', '--pretty=format:%s'], text=True, cwd=path, capture_output=True)
        log = cmd.stdout.strip()
        log = log[:max_chars] + '...' if len(log) > max_chars else log     
        return log

    # ahead/behind sorting
    def _get_formatted_ahead_behind(self, stdout : str) -> (str, str):
        if stdout:
            parts = stdout.split()
            if len(parts) == 2:
                return parts[0], parts[1]
        return '', ''

    def _get_formatted_labels(self, labels: List[str]) -> str:
        if len(labels) == 0:
            return ''

        colored_label = ''
        for label in labels:
            color_index = self._get_color_index(label)
            background = utils.BACKGROUND[list(utils.BACKGROUND.keys())[color_index % len(utils.BACKGROUND) + 3]]
            foreground = utils.FOREGROUND[list(utils.FOREGROUND.keys())[color_index % len(utils.FOREGROUND) + 3]]
            colored_label += f"{foreground}{utils.glyph('(')}{utils.RESET}{background}{label}{utils.RESET}{foreground}{utils.glyph(')')}{utils.RESET}"

        return colored_label

    def _get_formatted_branches(self, branches: List[str]) -> str:
        if len(branches) == 0:
            return ''

        output = ''
        for branch in branches:
            icon = utils.glyph('branch')
            if branch == 'master' or branch == 'main':
                icon = f'{utils.FOREGROUND["yellow"]}{utils.glyph("master")}'
            elif branch == 'develop':
                icon = f'{utils.FOREGROUND["green"]}{utils.glyph("feature")}'
            elif '/' in branch:
                parts = branch.split('/')
                branch = '/'.join([p[0] for p in parts[:-1]] + [f'{utils.END_STYLES["dim"]}' + parts[-1]])
                branch = f'{utils.STYLES["dim"]}{branch}'
                icon = parts[0]
                icon = f'{utils.FOREGROUND["red"]}{utils.glyph("bugfix")}' if icon in ['bugfix', 'bug', 'hotfix'] else \
                    f'{utils.FOREGROUND["blue"]}{utils.glyph("release")}' if icon == 'release' else \
                    f'{utils.FOREGROUND["green"]}{utils.glyph("feature")}' if icon in ['feature', 'feat', 'develop'] else \
                    f'{utils.FOREGROUND["green"]}{utils.glyph("branch")}'

            output += f"{icon} {branch}{utils.RESET} "
        return output        

    def _get_color_index(self, label: str) -> (str, str):
        if label not in self.label_color_cache:
            self.label_color_cache[label] = self.current_color_index
            self.current_color_index = (self.current_color_index + 1) % len(utils.BACKGROUND.keys())
        return self.label_color_cache[label]