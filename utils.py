import sys
import random
import subprocess

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


def check_updates(explicit: bool = False) -> bool:
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
    settings.config['mud']['run_async'] = str(ask('Do you want to run commands simultaneously for multiple repositories?'))
    settings.config['mud']['run_table'] = str(ask('Do you want to see command execution progress in table view? This will limit output content.'))
    settings.config['mud']['auto_fetch'] = str(ask(f'Do you want to automatically run {BOLD}\'git fetch\'{RESET} whenever you run commands such as {BOLD}\'mud info\'{RESET}?'))
    settings.config['mud']['ask_updates'] = str(ask(f'Do you want to get information about latest updates?'))
    settings.config['mud']['nerd_fonts'] = str(ask(f'Do you want to use {BOLD}nerd-fonts{RESET}?'))
    settings.config['mud']['simplify_branches'] = str(ask(f'Do you want to simplify branches? (ex. {BOLD}feature/name{RESET} -> {BOLD}f/name{RESET}'))
    settings.save()
    print('Your settings are updated!')
    pass


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


def print_error(text: str, code: int = 255) -> None:
    print(f'{RED}Error:{RESET} {text}')
    sys.exit(code)