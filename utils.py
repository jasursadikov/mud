import sys
import random
import subprocess

from settings import Settings

SETTINGS_FILE_NAME = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'
RESET = '\033[0m'
TEXT = {
    'white': '\033[37m',
    'gray': '\033[90m',
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'bright_white': '\033[97m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
}
BACK = {
    'white': '\033[47m',
    'medium_gray': '\033[100m',
    'black': '\033[40m',
    'red': '\033[41m',
    'green': '\033[42m',
    'yellow': '\033[43m',
    'blue': '\033[44m',
    'magenta': '\033[45m',
    'cyan': '\033[46m',
    'bright_white': '\033[107m',
    'bright_red': '\033[101m',
    'bright_green': '\033[102m',
    'bright_yellow': '\033[103m',
    'bright_blue': '\033[104m',
    'bright_magenta': '\033[105m',
    'bright_cyan': '\033[106m',
}
STYLES = {
    'bold': '\033[1m',
    'dim': '\033[2m',
    'italic': '\033[3m',
    'underline': '\033[4m',
    'blink': '\033[5m',
}
END_STYLES = {
    'bold': '\033[22m',
    'dim': '\033[22m',
    'italic': '\033[23m',
    'underline': '\033[24m',
    'blink': '\033[25m',
}
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
    'label': '\uf412',
    'tag': '\uf02b',
    '(': '\ue0b6',
    ')': '\ue0b4',
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
    'tag': ' ',
    '(': '',
    ')': ' ',
    'space': '',
}

settings: Settings


def remove_colors():
    for index in range(len(TEXT)):
        TEXT[index] = ''
    for index in range(len(BACK)):
        BACK[index] = ''


def set_up():
    global GLYPHS
    GLYPHS = ICON_GLYPHS if settings.mud_settings['nerd_fonts'] else TEXT_GLYPHS


def print_error(args: str) -> None:
    print(f'{TEXT["red"]}Error:{RESET} {args}')
    sys.exit()


def print_version() -> None:
    hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).splitlines()
    m = random.choice(list(TEXT.values())[3:])
    u = random.choice(list(TEXT.values())[3:])
    d = random.choice(list(TEXT.values())[3:])
    t = random.choice(list(TEXT.values())[3:])
    v = random.choice(list(TEXT.values())[3:])
    print(fr'''
{m} __    __{u}  __  __{d}  _____   
{m}/\ '-./  \{u}/\ \/\ \{d}/\  __-.     {STYLES['bold']}{t}Multi-directory runner{RESET} [{v}{hash}{RESET}]
{m}\ \ \-./\ \{u} \ \_\ \{d} \ \/\ \    {RESET}Jasur Sadikov 
{m} \ \_\ \ \_\{u} \_____\{d} \____-    {RESET}https://github.com/jasursadikov/mud
{m}  \/_/  \/_/{u}\/_____/{d}\/____/    {RESET}Type 'mud --help' for help
''')
