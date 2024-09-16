import os
import utils
import asyncio
import subprocess

from utils import glyphs
from typing import List, Dict
from collections import Counter

from styles import *

class Runner:
	_label_color_cache = {}
	_current_color_index = 0

	def __init__(self, repos):
		self._last_printed_lines = 0
		self.repos = repos

	# `mud info` command implementation
	def info(self, repos: Dict[str, List[str]]) -> None:
		def get_directory_size(directory):
			total_size = 0
			for dirpath, dirnames, filenames in os.walk(directory):
				for f in filenames:
					fp = os.path.join(dirpath, f)
					if os.path.isfile(fp):
						total_size += os.path.getsize(fp)
			return total_size

		def format_size(size_in_bytes):
			if size_in_bytes >= 1024 ** 3:
				return f'{RED}{glyphs("weight")}{glyphs("space")}{RESET}{BOLD}{size_in_bytes / (1024 ** 3):.2f}{RESET} GB'
			elif size_in_bytes >= 1024 ** 2:
				return f'{YELLOW}{glyphs("weight")}{glyphs("space")}{RESET}{BOLD}{size_in_bytes / (1024 ** 2):.2f}{RESET} MB'
			elif size_in_bytes >= 1024:
				return f'{GREEN}{glyphs("weight")}{glyphs("space")}{RESET}{BOLD}{size_in_bytes / 1024:.2f}{RESET} KB'
			else:
				return f'{BLUE}{glyphs("weight")}{glyphs("space")}{RESET}{BOLD}{size_in_bytes}{RESET} Bytes'

		def get_git_origin_host():
			try:
				result = subprocess.check_output('git remote get-url origin', shell=True, text=True, cwd=path)
				remote_url = result.strip()

				if '://' in remote_url:
					host = remote_url.split('/')[2]
				else:
					host = remote_url.split(':')[0].split('@')[1]

				icon = YELLOW + glyphs('git')

				if 'azure' in remote_url or 'visualstudio' in remote_url:
					icon = BLUE + glyphs('azure')
				elif 'github' in remote_url:
					icon = GRAY + glyphs('github')
				elif 'gitlab' in remote_url:
					icon = YELLOW + glyphs('gitlab')
				elif 'bitbucket' in remote_url:
					icon = CYAN + glyphs('bitbucket')

				icon += RESET + glyphs('space')

				return f'{icon}{host}'
			except Exception as e:
				return 'Unknown origin'

		table = utils.get_table()
		for path, labels in repos.items():
			output = self._get_status_porcelain(path)
			files = output.splitlines()

			formatted_path = self._get_formatted_path(path)
			size = f'{format_size(get_directory_size(path))}'
			origin = get_git_origin_host()
			branch = self._get_branch_status(path)
			status = self._get_status_string(files)
			colored_labels = self._get_formatted_labels(labels)
			origin_sync = self._get_origin_sync(path)

			table.add_row([formatted_path, origin, size, branch, origin_sync, status, colored_labels])

		utils.print_table(table)

	# `mud status` command implementation
	def status(self, repos: Dict[str, List[str]]) -> None:

		table = utils.get_table()
		for path, labels in repos.items():
			output = self._get_status_porcelain(path)
			files = output.splitlines()

			formatted_path = self._get_formatted_path(path)
			branch = self._get_branch_status(path)
			status = self._get_status_string(files)
			origin_sync = self._get_origin_sync(path)

			colored_output = []

			for file in files[:5]:
				file_status = file[:2].strip()
				filename = file[3:].strip()
				parts = filename.split(os.sep)
				if file_status == 'M':
					color = YELLOW
				elif file_status == 'A':
					color = GREEN
				elif file_status == 'R':
					color = BLUE
				elif file_status == 'D':
					color = RED
				else:
					color = CYAN

				shortened_parts = [part[0] if index < len(parts) - 1 and part else f'{RESET}{color}{part}' for index, part in enumerate(parts)]
				filename = os.sep.join(shortened_parts)
				colored_output.append(f'{color}{DIM}{filename}{RESET}')
			if len(files) > 5:
				colored_output.append('...')

			table.add_row([formatted_path, branch, origin_sync, status, ', '.join(colored_output)])

		utils.print_table(table)

	# `mud labels` command implementation
	def labels(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table()
		for path, labels in repos.items():
			formatted_path = self._get_formatted_path(path)
			colored_labels = self._get_formatted_labels(labels)
			table.add_row([formatted_path, colored_labels])

		utils.print_table(table)

	# `mud log` command implementation
	def log(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table()
		for path in repos.keys():
			formatted_path = self._get_formatted_path(path)
			branch = self._get_branch_status(path)
			author = self._get_authors_name(path)
			commit = self._get_commit_message(path)

			# Commit time
			commit_time_cmd = subprocess.run('git log -1 --pretty=format:%cd --date=relative', shell=True, text=True, cwd=path, capture_output=True)
			commit_time = commit_time_cmd.stdout.strip()

			table.add_row([formatted_path, branch, author, commit_time, commit])

		utils.print_table(table)

	# `mud branch` command implementation
	def branches(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table()
		all_branches = {}

		# Preparing branches for sorting to display them in the right order.
		for path in repos.keys():
			raw_branches = [line.strip() for line in subprocess.check_output('git branch', shell=True, text=True, cwd=path).split('\n') if line.strip()]
			for branch in raw_branches:
				branch = branch.replace(' ', '').replace('*', '')
				if branch not in all_branches:
					all_branches[branch] = 0
				all_branches[branch] += 1
		branch_counter = Counter(all_branches)

		for path, labels in repos.items():
			formatted_path = self._get_formatted_path(path)
			branches = subprocess.check_output('git branch', shell=True, text=True, cwd=path).splitlines()
			current_branch = next((branch.lstrip('* ') for branch in branches if branch.startswith('*')), None)
			branches = [branch.lstrip('* ') for branch in branches]
			sorted_branches = sorted(branches, key=lambda x: branch_counter.get(x, 0), reverse=True)

			if current_branch and current_branch in sorted_branches:
				sorted_branches.remove(current_branch)
				sorted_branches.insert(0, current_branch)

			formatted_branches = self._get_formatted_branches(sorted_branches, current_branch)
			table.add_row([formatted_path, formatted_branches])

		utils.print_table(table)

	# `mud tags` command implementation
	def tags(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table()

		for path, labels in repos.items():
			formatted_path = self._get_formatted_path(path)
			tags = [line.strip() for line in subprocess.check_output('git tag', shell=True, text=True, cwd=path).splitlines() if line.strip()]
			tags = [f'{glyphs("tag")}{glyphs("space")}{tag}' for tag in tags]
			tags = ' '.join(tags)
			table.add_row([formatted_path, tags])

		utils.print_table(table)

	# `mud <COMMAND>` when run_async = 0 and run_table = 0
	def run_ordered(self, repos: List[str], command: [str]) -> None:
		command_str = ' '.join(command)
		for path in repos:
			process = subprocess.run(command_str, shell=True, cwd=path, capture_output=True, text=True)
			self._print_process_header(path, ' '.join(command), process.returncode != 0, process.returncode)
			if process.stdout and not process.stdout.isspace():
				print(process.stdout)
			if process.stderr and not process.stderr.isspace():
				print(process.stderr)

	# `mud <COMMAND>` when run_async = 1 and run_table = 0
	async def run_async(self, repos: List[str], command: List[str]) -> None:
		sem = asyncio.Semaphore(len(repos))

		async def run_process(path: str) -> None:
			async with sem:
				process = await asyncio.create_subprocess_exec(*command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = await process.communicate()
				self._print_process_header(path, ' '.join(command), process.returncode != 0, process.returncode)
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
		table[repo_path] = ['', f'{YELLOW}{glyphs("running")}{RESET}']

		while True:
			line = await process.stdout.readline()
			if not line:
				line = await process.stderr.readline()
				if not line:
					break
			line = line.decode().strip()
			line = table[repo_path][0] if not line.strip() else line
			table[repo_path] = [line, f'{YELLOW}{glyphs("running")}{RESET}']
			self._print_process(table)

		return_code = await process.wait()

		if return_code == 0:
			status = f'{GREEN}{glyphs("finished")}{RESET}'
		else:
			status = f'{RED}{glyphs("failed")} Code: {return_code}{RESET}'

		table[repo_path] = [table[repo_path][0], status]
		self._print_process(table)

	def _print_process(self, info: Dict[str, List[str]]) -> None:
		table = utils.get_table()
		for path, (line, status) in info.items():
			formatted_path = self._get_formatted_path(path)
			table.add_row([formatted_path, status, line])

		table_str = utils.table_to_str(table)
		num_lines = table_str.count('\n') + 1
		self._clear_printed_lines()
		utils.print_table(table)
		self._last_printed_lines = num_lines

	def _clear_printed_lines(self) -> None:
		if self._last_printed_lines > 0:
			for _ in range(self._last_printed_lines):
				# Clear previous line
				print('\033[A\033[K', end='')
			self._last_printed_lines = 0

	@staticmethod
	def _get_status_porcelain(path: str) -> str:
		try:
			output = subprocess.check_output('git status --porcelain', shell=True, text=True, cwd=path)
			return output
		except Exception as e:
			return e

	@staticmethod
	def _get_status_string(files: List[str]) -> str:
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
			status += f'{BRIGHT_GREEN}{added} {glyphs("added")}{RESET} '
		if modified:
			status += f'{YELLOW}{modified} {glyphs("modified")}{RESET} '
		if moved:
			status += f'{BLUE}{moved} {glyphs("moved")}{RESET} '
		if removed:
			status += f'{RED}{removed} {glyphs("removed")}{RESET} '
		if not files:
			status = f'{GREEN}{glyphs("clear")}{RESET}'
		return status

	@staticmethod
	def _get_branch_status(path: str) -> str:
		try:
			branch_cmd = subprocess.run('git rev-parse --abbrev-ref HEAD', shell=True, text=True, cwd=path, capture_output=True)
			branch_stdout = branch_cmd.stdout.strip()
		except subprocess.CalledProcessError:
			branch_stdout = 'NA'
		if '/' in branch_stdout:
			branch_path = branch_stdout.split('/')
			icon = Runner._get_branch_icon(branch_path[0])
			branch_color = Runner._get_branch_color(branch_path[0])
			return f'{branch_color}{icon}{RESET}{glyphs("space")}{branch_path[0]}{RESET}/{BOLD}{("/".join(branch_path[1:]))}{RESET}'
		elif branch_stdout == 'HEAD':
			# check if we are on tag
			glyph = glyphs('tag')
			color = BRIGHT_MAGENTA
			info_cmd = subprocess.run('git describe --tags --exact-match', shell=True, text=True, cwd=path, capture_output=True)
			info_cmd = info_cmd.stdout.strip()

			if not info_cmd.strip():
				glyph = glyphs("branch")
				color = CYAN
				info_cmd = subprocess.run('git rev-parse --short HEAD', shell=True, text=True, cwd=path, capture_output=True)
				info_cmd = info_cmd.stdout.strip()

			return f'{color}{glyph}{RESET}{glyphs("space")}{DIM}{branch_stdout}{RESET}:{info_cmd}'
		else:
			return f'{Runner._get_branch_color(branch_stdout)}{Runner._get_branch_icon(branch_stdout)}{RESET}{glyphs("space")}{branch_stdout}'

	@staticmethod
	def _get_origin_sync(path: str) -> str:
		try:
			ahead_behind_cmd = subprocess.run('git rev-list --left-right --count HEAD...@{upstream}', shell=True, text=True, cwd=path, capture_output=True)
			stdout = ahead_behind_cmd.stdout.strip().split()
		except subprocess.CalledProcessError:
			stdout = ['0', '0']

		origin_sync = ''
		if len(stdout) >= 2:
			ahead, behind = stdout[0], stdout[1]
			if ahead and ahead != '0':
				origin_sync += f'{BRIGHT_GREEN}{glyphs("ahead")} {ahead}{RESET}'
			if behind and behind != '0':
				if origin_sync:
					origin_sync += ' '
				origin_sync += f'{BRIGHT_BLUE}{glyphs("behind")} {behind}{RESET}'

		if not origin_sync.strip():
			origin_sync = f'{BLUE}{glyphs("synced")}{RESET}'

		return origin_sync

	@staticmethod
	def _print_process_header(path: str, command: str, failed: bool, code: int) -> None:
		path = f'{BKG_BLACK}{Runner._get_formatted_path(path)}{RESET}'
		command = f'{BKG_WHITE}{BLACK}{glyphs(")")}{glyphs("space")}{glyphs("terminal")}{glyphs("space")}{BOLD}{command} {RESET}{WHITE}{RESET}'
		code = f'{WHITE}{BKG_RED if failed else BKG_GREEN}{glyphs(")")}{BRIGHT_WHITE}{glyphs("space")}{glyphs("failed") if failed else glyphs("finished")} {f"Code: {BOLD}{code}" if failed else ""}{glyphs("space")}{RESET}{RED if failed else GREEN}{glyphs(")")}{RESET}'
		print(f'{path} {command}{code}')

	@staticmethod
	def _get_formatted_path(path: str) -> str:
		collapse_paths = utils.settings.config['mud'].getboolean('collapse_paths')
		if os.path.isabs(path):
			home = os.path.expanduser('~')
			if path.startswith(home):
				path = path.replace(home, '~', 1)
			if path.startswith('/'):
				path = path[1:]
			parts = path.split('/')
			return DIM + WHITE + ('/'.join([p[0] for p in parts[:-1]] + [RESET + DIM + parts[-1]]) + RESET if collapse_paths else ('/'.join(parts[:-1])) + f'/{RESET}{DIM}' + parts[-1] + RESET)

		return f'{DIM}{path}{RESET}'

	@staticmethod
	def _get_authors_name(path: str) -> str:
		cmd = subprocess.run('git log -1 --pretty=format:%an', shell=True, text=True, cwd=path, capture_output=True)
		git_config_user_cmd = subprocess.run(['git', 'config', 'user.name'], text=True, capture_output=True)
		committer_color = '' if cmd.stdout.strip() == git_config_user_cmd.stdout.strip() else DIM
		return f'{committer_color}{cmd.stdout.strip()}{RESET}'

	@staticmethod
	def _get_commit_message(path: str) -> str:
		cmd = subprocess.run('git log -1 --pretty=format:%s', shell=True, text=True, cwd=path, capture_output=True)
		return cmd.stdout.strip()

	@staticmethod
	def _get_formatted_labels(labels: List[str]) -> str:
		if len(labels) == 0:
			return ''
		colored_label = ''
		for label in labels:
			color_index = Runner._get_color_index(label) % len(TEXT)
			colored_label += f'{TEXT[(color_index + 3) % len(TEXT)]}{glyphs("label")}{glyphs("space")}{label}{RESET} '

		return colored_label

	@staticmethod
	def _get_formatted_branches(branches: List[str], current_branch: str) -> str:
		if len(branches) == 0:
			return ''

		collapse_paths = utils.settings.config['mud'].getboolean('collapse_paths')
		output = ''

		for branch in branches:
			is_origin = branch.startswith('origin/')
			branch = branch.replace('origin/', '') if is_origin else branch
			current_prefix = f'{UNDERLINE}' if current_branch == branch else ''
			current_prefix = current_prefix + DIM if is_origin else current_prefix
			origin_prefix = f'{MAGENTA}{DIM}o/' if is_origin else ''
			color = WHITE
			icon = glyphs('branch')
			if branch == 'master' or branch == 'main':
				color = YELLOW
				icon = glyphs('master')
			elif branch == 'develop':
				color = GREEN
				icon = glyphs('feature')
			elif '/' in branch:
				parts = branch.split('/')
				end_dim = '' if is_origin else END_DIM
				branch = '/'.join([p[0] for p in parts[:-1]] + [end_dim + (
					parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])]) if collapse_paths else '/'.join(
					[p for p in parts[:-1]] + [end_dim + (parts[-1][:10] + '..' if len(parts[-1]) > 10 else parts[-1])])
				branch = f'{DIM}{branch}'
				color = Runner._get_branch_color(parts[0])
				icon = Runner._get_branch_icon(parts[0])
			output += f'{current_prefix}{color}{icon}{glyphs("space")}{origin_prefix}{color}{branch}{RESET} '
		return output

	@staticmethod
	def _get_branch_icon(branch_prefix: str) -> str:
		if branch_prefix in ['bugfix', 'bug', 'hotfix']:
			return glyphs('bugfix')
		elif branch_prefix in ['feature', 'feat', 'develop']:
			return glyphs('feature')
		elif branch_prefix == 'release':
			return glyphs('release')
		elif branch_prefix in ['master', 'main']:
			return glyphs('master')
		else:
			return glyphs('branch')

	@staticmethod
	def _get_branch_color(branch_name: str) -> str:
		if branch_name in ['bugfix', 'bug', 'hotfix']:
			return RED
		elif branch_name == 'release':
			return BLUE
		elif branch_name in ['feature', 'feat', 'develop']:
			return GREEN
		elif branch_name in ['master', 'main']:
			return YELLOW
		else:
			return CYAN

	@staticmethod
	def _get_color_index(label: str) -> (str, str):
		if label not in Runner._label_color_cache:
			Runner._label_color_cache[label] = Runner._current_color_index
			Runner._current_color_index = (Runner._current_color_index + 1) % len(BKG)
		return Runner._label_color_cache[label]
