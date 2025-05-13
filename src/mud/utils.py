import re
import sys
import shutil
import random

from typing import List
from prettytable import PrettyTable, PLAIN_COLUMNS

from mud.settings import *
from mud.styles import *

SETTINGS_FILE_NAME = 'settings.ini'
OLD_SETTINGS_FILE_NAME = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'

settings: Settings


def glyphs(key: str) -> str:
	return GLYPHS[key][0 if settings.config['mud'].getboolean('nerd_fonts', fallback=False) else 1]


def info() -> None:
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	colors = TEXT[3:]
	colors.remove(BRIGHT_WHITE)
	m = random.choice(colors)
	u = random.choice(colors)
	d = random.choice(colors)
	print(f'                 {d}__{RESET}')
	print(f'  {m}__ _  {u}__ __{d}___/ /{RESET}')
	print(f' {m}/  \' \\{u}/ // / {d}_  /{RESET}')
	print(f'{m}/_/_/_/{u}\\_,_/{d}\\_,_/  {RESET}')
	print(f'Jasur Sadikov <jasur@sadikoff.com>\nhttps://github.com/jasursadikov/mud')


def configure() -> None:
	try:
		settings.config['mud']['run_table'] = str(ask('Do you want to see command execution progress in table view? This will limit output content.'))
		settings.config['mud']['run_async'] = str(ask('Do you want to run commands simultaneously for multiple repositories?'))
		settings.config['mud']['nerd_fonts'] = str(ask(f'Do you want to use {BOLD}nerd-fonts{RESET}?'))
		settings.config['mud']['show_borders'] = str(ask(f'Do you want to see borders in table view?'))
		settings.config['mud']['collapse_paths'] = str(ask(f'Do you want to collapse paths, such as directory paths and branches? (ex. {BOLD}feature/name{RESET} -> {BOLD}f/name{RESET}'))
		settings.config['mud']['display_absolute_paths'] = str(ask(f'Do you want to display absolute paths for directories? (ex. {BOLD}~/Documents/repo{RESET} -> {BOLD}/home/user/Documents/repo{RESET}'))
	except KeyboardInterrupt:
		return

	settings.save()
	print('Your settings are updated!')


def ask(text: str) -> bool:
	try:
		answer = input(f"{text}? [Y/n]: ").strip().lower()
		if answer in ('y', 'yes', ''):
			return True
		elif answer in ('n', 'no'):
			return False
		else:
			print("Invalid input.")
			return True
	except KeyboardInterrupt:
		exit()


def print_table(table: PrettyTable) -> None:
	width, _ = shutil.get_terminal_size()

	def get_real_length(string):
		ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
		i = 0
		displayed_count = 0

		while displayed_count < width and i < len(string):
			match = ansi_escape.match(string, i)
			if match:
				i = match.end()
			else:
				displayed_count += 1
				i += 1
		return i

	rows = table_to_str(table).split('\n')
	for row in rows:
		stripped = row.strip()
		if len(stripped) != 0:
			if len(stripped) > width:
				print(stripped[:get_real_length(stripped)] + RESET)
			else:
				print(stripped)


def table_to_str(table: PrettyTable) -> str:
	table = table.get_string()
	table = '\n'.join(line.lstrip() for line in table.splitlines())
	return table


def get_table(field_names: List[str]) -> PrettyTable:
	def set_style(item: str) -> str:
		return f'{GRAY}{item}{RESET}'

	borders = settings.config['mud'].getboolean('show_borders', fallback=False)
	round_corners = settings.config['mud'].getboolean('round_corners', fallback=False)
	table = PrettyTable(border=borders, header=False, style=PLAIN_COLUMNS, align='l')
	if borders:
		table.horizontal_char = set_style('─')
		table.vertical_char = set_style('│')
		table.junction_char = set_style('┼')

		table.top_junction_char = set_style('┬')
		table.bottom_junction_char = set_style('┴')
		table.left_junction_char = set_style('├')
		table.right_junction_char = set_style('┤')

		if round_corners:
			table.top_left_junction_char = set_style('╭')
			table.top_right_junction_char = set_style('╮')
			table.bottom_left_junction_char = set_style('╰')
			table.bottom_right_junction_char = set_style('╯')
		else:
			table.top_left_junction_char = set_style('┌')
			table.top_right_junction_char = set_style('┐')
			table.bottom_left_junction_char = set_style('└')
			table.bottom_right_junction_char = set_style('┘')

	table.field_names = field_names

	return table


def print_error(code: int, exit: bool = False, meta: str = '') -> None:
	text = 'Unknown error code'

	match code:
		case 0:
			text = 'Stopped by user'
		case 1:
			text = 'No repositories are matching this filter'
		case 2:
			text = 'Invalid command'
		case 3:
			text = 'No git repositories were found in this directory'
		case 4:
			text = 'Invalid input. Please provide a value to remove'
		case 5:
			text = '.mudconfig not found'
		case 6:
			text = f'Item "{meta}" not found in .mudconfig'
		case 7:
			text = f'Invalid path "{meta}"'
		case 8:
			text = f'.git directory not found at target "{meta}"'

	print(f'{RED}Error [{code}]{RESET} {text}')
	if exit:
		sys.exit(code)
