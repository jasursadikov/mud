BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
BLINK = '\033[5m'

STYLES = [BOLD, DIM, ITALIC, UNDERLINE, BLINK]

END_BOLD = '\033[22m'
END_DIM = '\033[22m'
END_ITALIC = '\033[23m'
END_UNDERLINE = '\033[24m'
END_BLINK = '\033[25m'

END = [END_BOLD, END_DIM, END_ITALIC, END_UNDERLINE, END_BLINK]

# Text colors
WHITE = '\033[37m'
GRAY = '\033[90m'
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
BRIGHT_WHITE = '\033[97m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'

TEXT = [WHITE, GRAY, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, BRIGHT_WHITE, BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE, BRIGHT_MAGENTA, BRIGHT_CYAN]

# Background colors
BKG_WHITE = '\033[47m'
BKG_MEDIUM_GRAY = '\033[100m'
BKG_BLACK = '\033[40m'
BKG_RED = '\033[41m'
BKG_GREEN = '\033[42m'
BKG_YELLOW = '\033[43m'
BKG_BLUE = '\033[44m'
BKG_MAGENTA = '\033[45m'
BKG_CYAN = '\033[46m'
BKG_BRIGHT_WHITE = '\033[107m'
BKG_BRIGHT_RED = '\033[101m'
BKG_BRIGHT_GREEN = '\033[102m'
BKG_BRIGHT_YELLOW = '\033[103m'
BKG_BRIGHT_BLUE = '\033[104m'
BKG_BRIGHT_MAGENTA = '\033[105m'
BKG_BRIGHT_CYAN = '\033[106m'

BKG = [BKG_WHITE, BKG_MEDIUM_GRAY, BKG_BLACK, BKG_RED, BKG_GREEN, BKG_YELLOW, BKG_BLUE, BKG_MAGENTA, BKG_CYAN, BKG_BRIGHT_WHITE, BKG_BRIGHT_RED, BKG_BRIGHT_GREEN, BKG_BRIGHT_YELLOW, BKG_BRIGHT_BLUE, BKG_BRIGHT_MAGENTA, BKG_BRIGHT_CYAN]

RESET = '\033[0m'

URL_START = '\033]8;;'
URL_TEXT = '\a'
URL_END = '\033]8;;\a'

ALL = BKG + TEXT + STYLES + END + [RESET, URL_START, URL_TEXT, URL_END]

GLYPHS = {
	'ahead':		['\uf062',	'Ahead'],
	'behind':		['\uf063',	'Behind'],
	'modified':		['\uf040',	'*'],
	'added':		['\uf067',	'+'],
	'removed':		['\uf1f8',	'-'],
	'moved':		['\uf064',	'M'],
	'clear':		['\uf00c',	'Clear'],
	'synced':		['\uf00c',	'Up to date'],
	'master':		['\uf015',	''],
	'bugfix':		['\uf188',	''],
	'release':		['\uf135',	''],
	'feature':		['\uf0ad',	''],
	'test':			['\uf0c3',	''],
	'branch':		['\ue725',	''],
	'failed':		['\uf00d',	'Failed'],
	'finished':		['\uf00c',	'Finished'],
	'running':		['\uf46a',	'Running'],
	'label':		['\uf435',	''],
	'tag':			['\uf02b',	'>'],
	'terminal':		['\ue795',	''],
	'directory':	['\uf4d4',	''],
	'(':			['\uE0B2',	''],
	')':			['\uE0B0',	''],
	'weight':		['\uee94',	''],
	'space':		[' ', 		''],
	'git':			['\uefa0',	''],
	'github':		['\uf09b',	''],
	'gitlab':		['\uf296',	''],
	'azure':		['\uebe8',	''],
	'bitbucket':	['\ue703',	'']
}