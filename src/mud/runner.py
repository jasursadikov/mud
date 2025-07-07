import asyncio
import subprocess
import pygit2

from typing import Dict
from asyncio import Semaphore
from datetime import datetime, timezone, timedelta
from collections import Counter

from pygit2 import Repository, Commit
from pygit2.enums import FileStatus

from mud import utils
from mud.utils import *
from mud.styles import *


class Runner:
	_force_color_env: dict[str, str] = {'GIT_PAGER': 'cat', 'TERM': 'xterm-256color', 'GIT_CONFIG_PARAMETERS': '\'color.ui=always\''}
	_current_color_index: int = 0
	_label_color_cache = {}

	def __init__(self, repos):
		self._force_color_env = self._force_color_env | os.environ.copy()
		self._printed_lines_count = 0
		self.repos = repos

	# `mud info` command implementation
	def info(self, repos: Dict[str, List[str]]) -> None:
		def get_directory_size(directory: str) -> int:
			total_size = 0
			for directory_path, directory_names, file_names in os.walk(directory):
				for f in file_names:
					fp: str = str(os.path.join(directory_path, f))
					if os.path.isfile(fp):
						total_size += os.path.getsize(fp)
			return total_size

		def format_size(size_in_bytes: int) -> str:
			if size_in_bytes >= 1024 ** 3:
				return f'{BOLD}{size_in_bytes / (1024 ** 3):.2f}{RESET} GB{glyphs('space')}{RED}{glyphs('weight')}{RESET}'
			elif size_in_bytes >= 1024 ** 2:
				return f'{BOLD}{size_in_bytes / (1024 ** 2):.2f}{RESET} MB{glyphs('space')}{YELLOW}{glyphs('weight')}{RESET}'
			elif size_in_bytes >= 1024:
				return f'{BOLD}{size_in_bytes / 1024:.2f}{RESET} KB{glyphs('space')}{GREEN}{glyphs('weight')}{RESET}'
			else:
				return f'{BOLD}{size_in_bytes}{RESET} Bytes{glyphs('space')}{BLUE}{glyphs('weight')}{RESET}'

		def get_git_origin_host_icon(url: str) -> str:
			if 'azure' in url or 'visualstudio' in url:
				return BLUE + glyphs('azure') + RESET
			elif 'github' in url:
				return GRAY + glyphs('github') + RESET
			elif 'gitlab' in url:
				return YELLOW + glyphs('gitlab') + RESET
			elif 'bitbucket' in url:
				return CYAN + glyphs('bitbucket') + RESET
			elif len(url) == 0:
				return ''
			else:
				return YELLOW + glyphs('git') + RESET

		table: PrettyTable = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{BRIGHT_RED}{glyphs('git')}{glyphs('space')}{RESET}Url',
			f'{BLUE}{glyphs('commit')}{glyphs('space')}{RESET}Commits',
			f'{BLUE}{glyphs('commit')}{glyphs('space')}{RESET}User Commits',
			f'{MAGENTA}{glyphs('weight')}{glyphs('space')}{RESET}Size',
			f'{MAGENTA}{glyphs('labels')}{glyphs('space')}{RESET}Labels'])
		table.align[f'{BLUE}{glyphs('commit')}{glyphs('space')}{RESET}Commits'] = 'r'
		table.align[f'{BLUE}{glyphs('commit')}{glyphs('space')}{RESET}User Commits'] = 'r'
		table.align[f'{MAGENTA}{glyphs('weight')}{glyphs('space')}{RESET}Size'] = 'r'

		for path, labels in repos.items():
			repo = Repository(path)
			origin_url = '' if repo.head_is_unborn or len(repo.remotes) == 0 else repo.remotes[0].url
			if repo.head_is_unborn:
				total_commits_count = None
			else:
				walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL)
				total_commits_count = sum(1 for _ in walker)

			user_name = repo.config['user.name']
			if repo.head_is_unborn or user_name is None:
				user_commits_count = None
			else:
				walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL)
				user_commits_count = sum(1 for c in walker if c.author.name == user_name)

			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			url = f'{get_git_origin_host_icon(origin_url)}{glyphs('space')}{link(origin_url.split('://', 1)[-1].split("/", 1)[0], origin_url)}'
			size = format_size(get_directory_size(path))
			total_commits = '' if total_commits_count is None else f'{BOLD}{total_commits_count}{RESET} {DIM}commits{RESET}'
			user_commits = '' if user_commits_count is None else f'{GREEN}{BOLD}{user_commits_count}{RESET} {DIM}by you{RESET}'
			colored_labels = self._get_formatted_labels(labels)

			table.add_row([formatted_path, url, total_commits, user_commits, size, colored_labels])

		utils.print_table(table)

	# `mud status` command implementation
	def status(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{GREEN}{glyphs('branch')}{glyphs('space')}{RESET}Branch',
			f'{CYAN}{glyphs('origin-sync')}{glyphs('space')}{RESET}Origin Sync',
			f'{RED}{glyphs('stash')}{glyphs('space')}{RESET}Stash',
			f'{BRIGHT_YELLOW}{glyphs('info')}{glyphs('space')}{RESET}Status',
			f'{BRIGHT_GREEN}{glyphs('git-modified')}{glyphs('space')}{RESET}Modified Files'])

		for path, labels in repos.items():
			repo_path = os.path.abspath(path)
			repo = Repository(repo_path)
			status = repo.status()
			modified = status.items()
			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			head_info = self._get_head_info(repo)
			origin_sync = self._get_origin_sync(repo)
			stash_count = self._stash_count(repo)
			mini_status = self._get_status_string(modified)
			colored_output = []

			for file, flag in modified:
				if flag == FileStatus.WT_MODIFIED or flag == FileStatus.WT_TYPECHANGE or flag == FileStatus.INDEX_MODIFIED or flag == FileStatus.INDEX_TYPECHANGE:
					color = YELLOW
				elif flag == FileStatus.WT_NEW or flag == FileStatus.INDEX_NEW:
					color = BRIGHT_GREEN
				elif flag == FileStatus.WT_DELETED or flag == FileStatus.INDEX_DELETED:
					color = RED
				elif flag == FileStatus.WT_RENAMED or flag == FileStatus.INDEX_RENAMED:
					color = BLUE
				else:
					color = CYAN
				colored_output.append(link(self._get_formatted_path(file, False, color), os.path.join(repo_path, file)))
			table.add_row([formatted_path, head_info, origin_sync, stash_count, mini_status, ', '.join(colored_output)])

		utils.print_table(table)

	# `mud labels` command implementation
	def labels(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{MAGENTA}{glyphs('labels')}{glyphs('space')}{RESET}Labels'])

		for path, labels in repos.items():
			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			colored_labels = self._get_formatted_labels(labels)
			table.add_row([formatted_path, colored_labels])

		utils.print_table(table)

	# `mud log` command implementation
	def log(self, repos: Dict[str, List[str]]) -> None:
		table = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{GREEN}{glyphs('branch')}{glyphs('space')}{RESET}Branch',
			f'{BRIGHT_YELLOW}{glyphs('hash')}{glyphs('space')}{RESET}Hash',
			f'{BRIGHT_GREEN}{glyphs('author')}{glyphs('space')}{RESET}Author',
			f'{BRIGHT_CYAN}{glyphs('time')}{glyphs('space')}{RESET}Time',
			f'{BRIGHT_BLUE}{glyphs('message')}{glyphs('space')}{RESET}Message'])

		for path in repos.keys():
			repo = Repository(path)

			if repo.head_is_unborn:
				author, commit_hash, time, message = '', '', '', ''
			else:
				commit: Commit = repo.revparse_single('HEAD')
				author = f'{BOLD if commit.author.name == repo.config.__getitem__('user.name') else DIM}{commit.author.name}{RESET}'
				commit_hash = f'{YELLOW}{str(commit.id)[-8:]}{RESET}'
				time = datetime.fromtimestamp(commit.commit_time, timezone(timedelta(minutes=commit.commit_time_offset))).strftime('%Y-%m-%d %H:%M:%S')
				message = commit.message.splitlines()[0]

			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			head_info = self._get_head_info(repo)

			table.add_row([formatted_path, head_info, commit_hash, author, time, message])

		utils.print_table(table)

	# `mud branch` command implementation
	def branches(self, paths: Dict[str, List[str]], remote: bool) -> None:
		table = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{BLUE}{glyphs('branch')}{glyphs('space')}{RESET}Branches'])
		all_branches = {}
		repos = [[path, Repository(path)] for path in paths]
		prefix = 'refs/remotes/' if remote else 'refs/heads/'

		# Preparing branches for sorting to display them in the right order.
		for path, repo in repos:
			for branch in [ref.replace(prefix + (repo.remotes[0].name + '/' if remote else ''), '') for ref in repo.references if ref.startswith(prefix + (repo.remotes[0].name + '/' if remote else ''))]:
				if branch not in all_branches:
					all_branches[branch] = 0
				all_branches[branch] += 1
		branch_counter = Counter(all_branches)

		for path, repo in repos:
			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			branches = [ref.replace(prefix + (repo.remotes[0].name + '/' if remote else ''), '') for ref in repo.references if ref.startswith(prefix + (repo.remotes[0].name + '/' if remote else ''))]
			current_branch = '' if repo.head_is_unborn or repo.head_is_detached else repo.head.shorthand
			sorted_branches = sorted(branches, key=lambda x: branch_counter.get(x, 0), reverse=True)

			if current_branch and current_branch in sorted_branches:
				sorted_branches.remove(current_branch)
				sorted_branches.insert(0, current_branch)

			formatted_branches = self._get_formatted_branches(sorted_branches, current_branch)
			table.add_row([formatted_path, formatted_branches])

		utils.print_table(table)

	# `mud tags` command implementation
	def tags(self, repos: Dict[str, List[str]]) -> None:
		COLORS = [196, 202, 208, 214, 220, 226, 118, 154, 190, 33, 39, 45, 51, 87, 93, 99, 105, 111, 27, 63, 69, 75, 81, 87, 123, 129, 135, 141, 147, 183, 189, 225]
		tag_colors = {}

		def assign_color(tag: str) -> str:
			if tag not in tag_colors:
				color_code = COLORS[len(tag_colors) % len(COLORS)]
				tag_colors[tag] = f'\033[38;5;{color_code}m'
			return tag_colors[tag]

		table = utils.get_table([
			f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory',
			f'{BRIGHT_BLUE}{glyphs('tags')}{glyphs('space')}{RESET}Tags'])

		for path, labels in repos.items():
			repo = Repository(path)

			if repo.head_is_unborn:
				tags = []
			else:
				tags = [
					ref.replace('refs/tags/', '', 1)
					for ref in repo.references
					if ref.startswith('refs/tags/')
				]
				tags.sort()

			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))

			tags = [f'{assign_color(tag)}{glyphs('tag')} {RESET}{tag}' for tag in tags]
			table.add_row([formatted_path, ' '.join(tags)])

		utils.print_table(table)

	# `mud <COMMAND>` when run_async = 0 and run_table = 0
	def run_ordered(self, repos: List[str], command: str) -> None:
		for path in repos:
			process = subprocess.run(command, cwd=path, universal_newlines=True, shell=True, capture_output=True, text=True, env=self._force_color_env)
			self._print_process_header(path, command, process.returncode != 0, process.returncode)
			if process.stdout and not process.stdout.isspace():
				print(process.stdout)
			if process.stderr and not process.stderr.isspace():
				print(process.stderr)

	# `mud <COMMAND>` when run_async = 1 and run_table = 0
	async def run_async(self, repos: List[str], command: str) -> None:
		sem: Semaphore = Semaphore(len(repos))

		async def run_process(path: str) -> None:
			async with sem:
				process = await asyncio.create_subprocess_shell(command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self._force_color_env)
				stdout, stderr = await process.communicate()
				self._print_process_header(path, command, process.returncode != 0, process.returncode)
				if stderr:
					print(stderr.decode())
				if stdout and not stdout.isspace():
					print(stdout.decode())

		await asyncio.gather(*(run_process(path) for path in repos))

	# `mud <COMMAND>` when run_async = 1 and run_table = 1
	async def run_async_table_view(self, repos: List[str], command: str) -> None:
		sem: Semaphore = Semaphore(len(repos))
		table = {repo: ['', ''] for repo in repos}

		async def task(repo: str) -> None:
			async with sem:
				await self._run_process(repo, table, command)

		tasks = [asyncio.create_task(task(repo)) for repo in repos]
		await asyncio.gather(*tasks)

	async def _run_process(self, path: str, table: Dict[str, List[str]], command: str) -> None:
		process = await asyncio.create_subprocess_shell(command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self._force_color_env)
		table[path] = ['', f'{YELLOW}{glyphs('running')}{RESET}']

		while True:
			line = await process.stdout.readline()
			if not line:
				line = await process.stderr.readline()
				if not line:
					break
			line = line.decode().strip()
			line = table[path][0] if not line.strip() else line
			table[path] = [line, f'{YELLOW}{glyphs('running')}{RESET}']
			self._print_process(table)

		return_code = await process.wait()

		if return_code == 0:
			status = f'{GREEN}{glyphs('finished')}{RESET}'
		else:
			status = f'{RED}{glyphs('failed')} Code: {return_code}{RESET}'

		table[path] = [table[path][0], status]
		self._print_process(table)

	def _print_process(self, info: Dict[str, List[str]]) -> None:
		table = utils.get_table([f'{YELLOW}{glyphs('git-repo')}{glyphs('space')}{RESET}Directory', f'{BRIGHT_YELLOW}{glyphs('info')}{glyphs('space')}{RESET}Status', 'Output'])
		table.header = False
		for path, (line, status) in info.items():
			formatted_path = link(self._get_formatted_path(path), os.path.abspath(path))
			table.add_row([formatted_path, status, line])

		table_str = utils.table_to_str(table)
		num_lines = table_str.count('\n') + 1
		self._clear_printed_lines()
		utils.print_table(table)
		self._printed_lines_count = num_lines

	def _clear_printed_lines(self) -> None:
		if self._printed_lines_count > 0:
			for _ in range(self._printed_lines_count):
				# Clear previous line
				print('\033[A\033[K', end='')
			self._printed_lines_count = 0

	@staticmethod
	def _get_status_string(files: Dict[str, int]) -> str:
		modified, new, deleted, moved = 0, 0, 0, 0

		for file, status in files:
			if status == FileStatus.WT_MODIFIED or status == FileStatus.WT_TYPECHANGE or status == FileStatus.INDEX_MODIFIED or status == FileStatus.INDEX_TYPECHANGE:
				modified += 1
			elif status == FileStatus.WT_NEW or status == FileStatus.INDEX_NEW:
				new += 1
			elif status == FileStatus.WT_DELETED or status == FileStatus.WT_DELETED:
				deleted += 1
			elif status == FileStatus.WT_RENAMED or status == FileStatus.INDEX_RENAMED:
				moved += 1
		status = ''
		if new:
			status += f'{BRIGHT_GREEN}{new} {glyphs('added')}{RESET} '
		if modified:
			status += f'{YELLOW}{modified} {glyphs('modified')}{RESET} '
		if moved:
			status += f'{BLUE}{moved} {glyphs('moved')}{RESET} '
		if deleted:
			status += f'{RED}{deleted} {glyphs('removed')}{RESET} '
		if not files:
			return ''
		return status

	@staticmethod
	def _get_head_info(repo: Repository) -> str:
		if repo.head_is_unborn:
			return ''

		if repo.head_is_detached:
			head_target = repo.head.target
			for ref_name in repo.references:
				if ref_name.startswith('refs/tags/'):
					ref = repo.references[ref_name]
					tag_obj = repo[ref.target]
					tag_commit = tag_obj.target if isinstance(tag_obj, pygit2.Tag) else ref.target
					if tag_commit == head_target:
						tag_name = ref_name.replace('refs/tags/', '')
						return f'{BRIGHT_MAGENTA}{glyphs("tag")}{RESET}{glyphs("space")}{tag_name}{RESET}'

			# fallback: show short commit hash
			return f'{CYAN}{glyphs("commit")}{RESET}{glyphs("space")}{str(head_target)[-8:]}'

		# normal branch
		branch = repo.head.shorthand
		if '/' in branch:
			parts = branch.split('/')
			icon = Runner._get_branch_icon(parts[0])
			return f'{icon}{RESET}{glyphs("space")}{parts[0]}{RESET}/{BOLD}{"/".join(parts[1:])}{RESET}'
		return f'{Runner._get_branch_icon(branch)}{RESET}{glyphs("space")}{branch}'

	@staticmethod
	def _stash_count(repo: Repository) -> str:
		count: int = len(repo.listall_stashes())
		return '' if count == 0 else f'{BRIGHT_RED}{glyphs("stash")}{RESET}{glyphs('space')}x{str(count)}'


	@staticmethod
	def _get_origin_sync(repo: Repository) -> str:
		sync_str = ''

		if not repo.head_is_unborn and not repo.head_is_detached:
			local_ref = repo.branches[repo.head.shorthand]
			upstream = local_ref.upstream
			if upstream:
				ahead, behind = repo.ahead_behind(local_ref.target, upstream.target)
				if ahead != 0:
					sync_str += f'{BRIGHT_GREEN}{glyphs('ahead')} {ahead}{RESET}'
				if behind != 0:
					sync_str += f'{BRIGHT_BLUE}{glyphs('behind')} {behind}{RESET}'
				if ahead == 0 and behind == 0:
					sync_str = f'{GREEN}{glyphs('synced')}{RESET}'
			return sync_str

		return f'{RED}{glyphs('question')}{RESET}'

	@staticmethod
	def _print_process_header(path: str, command: str, failed: bool, code: int) -> None:
		command = f'{BKG_WHITE}{BLACK}{glyphs('space')}{glyphs('terminal')} {BOLD}{command} {END_BOLD}{WHITE}{RESET}'
		code = f'{WHITE}{BKG_RED if failed else BKG_GREEN}{glyphs(')')} {glyphs('failed') if failed else glyphs('finished')} {f'{BOLD}{code}' if failed else ''}{glyphs('space')}{RESET}'
		path = f'{BKG_BLACK}{RED if failed else GREEN}{glyphs(')')}{RESET}{BKG_BLACK}{glyphs('space')}{WHITE}{glyphs('directory')}{END_DIM} {Runner._get_formatted_path(path)}{BKG_BLACK} {RESET}{BLACK}{glyphs(')')}{RESET}'
		print(f'{command}{code}{path}')

	@staticmethod
	def _get_formatted_path(path: str, file_system: bool = True, color: str = '') -> str:
		collapse_paths = utils.settings.config['mud'].getboolean('collapse_paths', fallback=False)
		abs_path = utils.settings.config['mud'].getboolean('display_absolute_paths', fallback=False)

		in_quotes = path.startswith('\'') and path.endswith('\'')
		quote = '\'' if in_quotes else ''

		if in_quotes:
			path = path.replace('\'', '')

		def apply_styles(text: str) -> str:
			return color + quote + text + quote + END_FRG

		if file_system and abs_path:
			parts = os.path.abspath(path).split('/')
			return apply_styles((DIM + '/'.join(parts[:-1]) + '/' + END_DIM + parts[-1]))

		if os.path.isabs(path):
			home = os.path.expanduser('~')
			if path.startswith(home):
				path = path.replace(home, '~', 1)
			if path.startswith('/'):
				path = path[1:]
			parts = path.split('/')
			if collapse_paths:
				return apply_styles((DIM + '/'.join([p[0] for p in parts[:-1]] + [END_DIM + parts[-1]])))
			else:
				return apply_styles((DIM + '/'.join(parts[:-1]) + '/' + END_DIM + parts[-1]))
		if '/' not in path:
			return apply_styles(path)

		parts = path.split('/')
		if collapse_paths:
			return apply_styles((DIM + '/'.join([p[0] for p in parts[:-1]] + [END_DIM + parts[-1]])))
		else:
			return apply_styles((DIM + '/'.join(parts[:-1]) + '/' + END_DIM + parts[-1]))

	@staticmethod
	def _get_formatted_labels(labels: List[str]) -> str:
		if len(labels) == 0:
			return ''
		colored_labels = ''
		for label in labels:
			color_index = Runner._get_color_index(label) % len(TEXT)
			colored_labels += f'{TEXT[(color_index + 3) % len(TEXT)]}{glyphs('label')}{glyphs('space')}{label}{END_FRG} '

		return colored_labels.rstrip()

	@staticmethod
	def _get_formatted_branches(branches: List[str], current_branch: str) -> str:
		if len(branches) == 0:
			return ''

		output = ''
		for branch in branches:
			prefix = f'{BOLD}{RED}*{RESET}' if current_branch == branch else ''
			icon = Runner._get_branch_icon(branch.split('/')[0])
			branch = Runner._get_formatted_path(branch, False)
			output += f'{icon}{glyphs('space')}{prefix}{branch}{RESET} '
		return output

	@staticmethod
	def _get_branch_icon(branch_prefix: str) -> str:
		if branch_prefix in ['bugfix', 'bug', 'hotfix']:
			return RED + glyphs('bugfix') + RESET
		elif branch_prefix in ['feature', 'feat', 'develop']:
			return GREEN + glyphs('feature') + RESET
		elif branch_prefix in ['release']:
			return BLUE + glyphs('release') + RESET
		elif branch_prefix in ['master', 'main']:
			return YELLOW + glyphs('master') + RESET
		elif branch_prefix in ['test']:
			return MAGENTA + glyphs('test') + RESET
		else:
			return CYAN + glyphs('branch') + RESET

	@staticmethod
	def _get_color_index(label: str) -> (str, str):
		if label not in Runner._label_color_cache:
			Runner._label_color_cache[label] = Runner._current_color_index
			Runner._current_color_index = (Runner._current_color_index + 1) % len(BKG)
		return Runner._label_color_cache[label]
