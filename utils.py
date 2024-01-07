import random

SETTINGS_FILE_NAME = '.mudsettings'
CONFIG_FILE_NAME = '.mudconfig'
RESET = '\033[0m'
FOREGROUND = {
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
BACKGROUND = {
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
GLYPHS = {
    'ahead': ('\uf062', 'Ahead'),
    'behind': ('\uf063', 'Behind'),
    'modified': ('\uf040', '*'),
    'added': ('\uf067', '+'),
    'removed': ('\uf1f8', '-'),
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

def print_about() -> None:
    m = random.choice(FOREGROUND.values())
    u = random.choice(FOREGROUND.values())
    d = random.choice(FOREGROUND.values())
    a = random.choice(FOREGROUND.values())
    print(f'''
{m} __    __{u}  __  __{d}  _____   
{m}/\ '-./  \{u}/\ \/\ \{d}/\  __-.     {STYLES['bold']}{a}Multidirectory git runner{RESET} [v1.0.0]
{m}\ \ \-./\ \{u} \ \_\ \{d} \ \/\ \    {RESET}Jasur Sadikov 
{m} \ \_\ \ \_\{u} \_____\{d} \____-    {RESET}https://github.com/jasursadikov/mud
{m}  \/_/  \/_/{u}\/_____/{d}\/____/    {RESET}Type 'mud --help' for help
''')

def print_error(args: str) -> None:
    print(f'{FOREGROUND["red"]}Error:{RESET} {args}')

def glyph(key: str) -> None:
    return GLYPHS[key][0] if settings.mud_settings['nerd_fonts'] else GLYPHS[key][1]