import random
import subprocess
import sys

from settings import *
from styles import *

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


def set_up():
    global GLYPHS
    GLYPHS = ICON_GLYPHS if settings.mud_settings['nerd_fonts'] else TEXT_GLYPHS

    if settings.config['mud'].getboolean('ask_updates') and check_updates():
        sys.exit()


def check_updates(explicit: bool = False) -> bool:
    target_directory = os.curdir
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    subprocess.run(['git', 'fetch'], check=True)

    result = subprocess.run(['git', 'status', '-uno'], capture_output=True, text=True)

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

        log = subprocess.run(['git', 'log', 'HEAD..@{u}', '--oneline', '--color=always'], text=True, stdout=subprocess.PIPE).stdout
        print(log)

        if ask('Do you want to update?'):
            update_process = subprocess.run(['git', 'pull', '--force'], text=False, stdout=subprocess.DEVNULL)
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


def ask(text: str) -> bool:
    print(f"{text} [Y/n] ", end='', flush=True)
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


def print_error(text: str, code: int = 255) -> None:
    print(f'{RED}Error:{RESET} {text}')
    sys.exit(code)


def print_version() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).splitlines()[0]
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
