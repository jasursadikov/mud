import sys
import shutil
import random
import subprocess

from styles import *
from settings import *
from prettytable import PrettyTable, PLAIN_COLUMNS

SETTINGS_FILE_NAME = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'
GLYPHS = {}
ICON_GLYPHS = {
	'ahead': '\uf062',
	'behind': '\uf063',
	'modified': '\uf040',
	'added': '\uf067',
	'removed': '\uf1f8',
	'moved': '\uf064',
	'clear': '\uf00c',
	'synced': '\uf00c',
	'master': '\uf015',
	'bugfix': '\uf188',
	'release': '\uf135',
	'feature': '\uf0ad',
	'branch': '\ue725',
	'failed': '\uf00d',
	'finished': '\uf00c',
	'running': '\uf46a',
	'label': '\uf435',
	'tag': '\uf02b',
	'terminal': '\ue795',
	'(': '\uE0B2',
	')': '\uE0B0',
	'space': ' ',
}
TEXT_GLYPHS = {
	'ahead': 'Ahead',
	'behind': 'Behind',
	'modified': '*',
	'added': '+',
	'removed': '-',
	'moved': 'M',
	'clear': 'Clear',
	'synced': 'Up to date',
	'master': '',
	'bugfix': '',
	'release': '',
	'feature': '',
	'branch': '',
	'failed': 'Failed',
	'finished': 'Finished',
	'running': 'Running',
	'label': '',
	'tag': '',
	'terminal': '',
	'(': '',
	')': ' ',
	'space': '',
}

settings: Settings


def setup():
	global GLYPHS
	GLYPHS = ICON_GLYPHS if settings.mud_settings['nerd_fonts'] else TEXT_GLYPHS

	if settings.config['mud'].getboolean('ask_updates') and update():
		sys.exit()


def version() -> None:
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	hash = subprocess.check_output('git rev-parse --short HEAD', shell=True, text=True).splitlines()[0]
	m = random.choice(TEXT[3:])
	u = random.choice(TEXT[3:])
	d = random.choice(TEXT[3:])
	t = random.choice(TEXT[3:])
	v = random.choice(TEXT[3:])
	print(fr'''
{m} __    __{u}  __  __{d}  _____   
{m}/\ '-./  \{u}/\ \/\ \{d}/\  __-.     {BOLD}{t}Multi-directory runner{RESET} [{v}{hash}{RESET}]
{m}\ \ \-./\ \{u} \ \_\ \{d} \ \/\ \    {RESET}Jasur Sadikov 
{m} \ \_\ \ \_\{u} \_____\{d} \____-    {RESET}https://github.com/jasursadikov/mud
{m}  \/_/  \/_/{u}\/_____/{d}\/____/    {RESET}Type 'mud --help' for help
''')


def update(explicit: bool = False) -> bool:
	target_directory = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	subprocess.run('git fetch', shell=True, check=True)
	result = subprocess.run('git status -uno', shell=True, capture_output=True, text=True)

	if 'Your branch is behind' in result.stdout:
		m = random.choice(TEXT[3:])
		u = random.choice(TEXT[3:])
		d = random.choice(TEXT[3:])
		print(fr'''
        {m} __    __{u}  __  __{d}  _____   
        {m}/\ '-./  \{u}/\ \/\ \{d}/\  __-.{RESET}
        {m}\ \ \-./\ \{u} \ \_\ \{d} \ \/\ \{RESET}
        {m} \ \_\ \ \_\{u} \_____\{d} \____-{RESET}
        {m}  \/_/  \/_/{u}\/_____/{d}\/____/{RESET}
        ''')
		print(f'{BOLD}New update(s) is available!{RESET}\n')

		log = subprocess.run('git log HEAD..@{u} --oneline --color=always', shell=True, text=True, stdout=subprocess.PIPE).stdout
		print(log)

		if ask('Do you want to update?'):
			update_process = subprocess.run('git pull --force', shell=True, text=False, stdout=subprocess.DEVNULL)
			if update_process.returncode == 0:
				print(f'{GREEN}{BOLD}Update successful!{RESET}')
			else:
				print_error('Update failed', update_process.returncode)
		os.chdir(target_directory)
		return True

	if explicit:
		print('No updates available')

	os.chdir(target_directory)
	return False


def configure():
	try:
		settings.config['mud']['run_table'] = str(ask('Do you want to see command execution progress in table view? This will limit output content.'))
		settings.config['mud']['run_async'] = str(ask('Do you want to run commands simultaneously for multiple repositories?'))
		settings.config['mud']['nerd_fonts'] = str(ask(f'Do you want to use {BOLD}nerd-fonts{RESET}?'))
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
		import tty, termios
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			response = sys.stdin.read(1).lower()
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

	print()
	return response in ['y', '\r', '\n']


def print_table(table: PrettyTable):
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
	return PrettyTable(border=False, header=False, style=PLAIN_COLUMNS, align='l')


def print_error(text: str, code: int = 255) -> None:
	print(f'{RED}Error:{RESET} {text}')
	sys.exit(code)
