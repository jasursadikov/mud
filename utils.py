import random

from colorama import Fore, Back, Style
from settings import Settings

SETTINGS_FILE_NMAE = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'

n = Style.RESET_ALL
bg = [Back.RED, Back.GREEN, Back.BLUE, Back.MAGENTA, Back.YELLOW, Back.CYAN]
fg = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.MAGENTA, Fore.YELLOW, Fore.CYAN]
bgl = [Back.LIGHTRED_EX, Back.LIGHTGREEN_EX, Back.LIGHTBLUE_EX, Back.LIGHTMAGENTA_EX, Back.LIGHTYELLOW_EX, Back.LIGHTCYAN_EX]
fgl = [Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTCYAN_EX]

glyphs = {
    'ahead': ('\uf062', 'Ahead'),
    'behind': ('\uf063', 'Behind'),
    'modified': ('\uf040', '*'),
    'added': ('\uf055', '+'),
    'removed': ('\uf056', '-'),
    'moved': ('\uf0b2', 'M'),
    'clear': ('\uf00c', 'Clear'),
    'master': ('\uf015', ''),
    'bugfix': ('\uf188', ''),
    'release': ('\uf135', ''),
    'feature': ('\uf0ad', ''),
    'branch': ('\ue725', ''),
    '(': ('\ue0b6', ''),
    ')': ('\ue0b4', ' ')
}

settings = Settings(SETTINGS_FILE_NMAE)

def print_about():
    m = random.choice(fg + fgl)
    u = random.choice(fg + fgl)
    d = random.choice(fg + fgl)
    a = random.choice(fg + fgl)
    print(f'''
{m} __    __{u}  __  __{d}  _____   
{m}/\ "-./  \{u}/\ \/\ \{d}/\  __-.     {Style.BRIGHT}{a}Multidirectory git runner{n} [v1.0.0]
{m}\ \ \-./\ \{u} \ \_\ \{d} \ \/\ \    {n}Jasur Sadikov 
{m} \ \_\ \ \_\{u} \_____\{d} \____-    {n}https://github.com/jasursadikov/mud
{m}  \/_/  \/_/{u}\/_____/{d}\/____/    {n}Type 'mud --help' for help
''')

def print_error(args: str):
    print(f"{Fore.LIGHTRED_EX}Error:{n} {args}")

def glyph(key: str):
    return glyphs[key][0] if settings.mud_settings['nerd_fonts'] else glyphs[key][1]