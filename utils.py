import random
import shutil
import subprocess
import sys

from prettytable import PrettyTable, PLAIN_COLUMNS

from settings import *
from styles import *

SETTINGS_FILE_NAME = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'

settings: Settings


def glyphs(key: str) -> str:
	return GLYPHS[key][0 if settings.config['mud'].getboolean('nerd_fonts', fallback=False) else 1]


def version() -> None:
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	hash = subprocess.check_output('git rev-parse HEAD', shell=True, text=True).splitlines()[0]
	logo = get_logo()
	info = f'Jasur Sadikov\nhttps://github.com/jasursadikov/mud\n{BOLD}{random.choice(TEXT[3:])}{hash}{RESET}\n'
	print(logo)
	print(info)


def get_logo() -> str:
	colors = TEXT[3:]
	colors.remove(BRIGHT_WHITE)
	m = random.choice(colors)
	u = random.choice(colors)
	d = random.choice(colors)
	logo = f'                 {d}__{RESET}\n'
	logo += f'  {m}__ _  {u}__ __{d}___/ /{RESET}\n'
	logo += f' {m}/  \' \\{u}/ // / {d}_  /{RESET}\n'
	logo += f'{m}/_/_/_/{u}\\_,_/{d}\\_,_/  {RESET}'
	return logo


def update(explicit: bool = False) -> bool:
	if explicit:
		print(get_logo())

	target_directory = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	subprocess.run('git fetch', shell=True, check=True)
	result = subprocess.run('git status -uno', shell=True, capture_output=True, text=True)

	if 'Your branch is behind' in result.stdout:
		print(f'{BOLD}New update(s) is available!{RESET}\n')

		log = subprocess.run('git log HEAD..@{u} --oneline --color=always', shell=True, text=True, stdout=subprocess.PIPE).stdout
		print(log)

		if ask('Do you want to update?'):
			update_process = subprocess.run('git pull --force', shell=True, text=False, stdout=subprocess.DEVNULL)
			if update_process.returncode == 0:
				print(f'{GREEN}{BOLD}Update successful!{RESET}')
			else:
				print_error('Update failed', 30)
		os.chdir(target_directory)
		return True

	if explicit:
		print('No updates available')

	os.chdir(target_directory)
	return False


def configure() -> None:
	try:
		settings.config['mud']['run_table'] = str(ask('Do you want to see command execution progress in table view? This will limit output content.'))
		settings.config['mud']['run_async'] = str(ask('Do you want to run commands simultaneously for multiple repositories?'))
		settings.config['mud']['nerd_fonts'] = str(ask(f'Do you want to use {BOLD}nerd-fonts{RESET}?'))
		settings.config['mud']['nerd_fonts'] = str(ask(f'Do you want to see borders in table view?'))
		settings.config['mud']['collapse_paths'] = str(ask(f'Do you want to collapse paths, such as directory paths and branches? (ex. {BOLD}feature/name{RESET} -> {BOLD}f/name{RESET}'))
		settings.config['mud']['ask_updates'] = str(ask(f'Do you want to get information about latest updates?'))
	except KeyboardInterrupt:
		return

	settings.save()
	print('Your settings are updated!')


def ask(text: str) -> bool:
	print(f'{text} [Y/n] ', end='', flush=True)
	if sys.platform.startswith('win'):
		from msvcrt import getch
		response = getch().decode().lower()
	else:
		import tty
		import termios
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			response = sys.stdin.read(1).lower()
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

	print()
	return response in ['y', '\r', '\n']


def print_table(table: PrettyTable) -> None:
	width, _ = shutil.get_terminal_size()
	rows = table_to_str(table).split('\n')
	for row in rows:
		if len(row) != 0:
			if len(sterilize(row)) > width:
				styles_count = len(row) - len(sterilize(row))
				count = width + styles_count - 1
				print(row[:count] + RESET)
			else:
				print(row)


def table_to_str(table: PrettyTable) -> str:
	table = table.get_string()
	table = '\n'.join(line.lstrip() for line in table.splitlines())
	return table


def get_table() -> PrettyTable:
	def set_style(item: str) -> str:
		return f'{DIM}{item}{RESET}'
	table = PrettyTable(border=settings.config['mud'].getboolean('show_borders', fallback=False), header=False, style=PLAIN_COLUMNS, align='l')

	table.horizontal_char = set_style('─')
	table.vertical_char = set_style('│')
	table.junction_char = set_style('┼')

	table.top_junction_char = set_style('┬')
	table.bottom_junction_char = set_style('┴')
	table.left_junction_char = set_style('├')
	table.right_junction_char = set_style('┤')

	table.top_left_junction_char = set_style('╭')
	table.top_right_junction_char = set_style('╮')
	table.bottom_left_junction_char = set_style('╰')
	table.bottom_right_junction_char = set_style('╯')
	return table


def print_error(text: str, code: int = 255) -> None:
	print(f'{BKG_RED}{BRIGHT_WHITE}{glyphs("space")}Error {code}{glyphs("space")}{RESET}{RED}{glyphs(")")}{RESET} {text}')
	sys.exit(code)
