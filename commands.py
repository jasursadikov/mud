# Commands
ADD = ['add', 'a']
REMOVE = ['remove', 'rm']
LOG = ['log', 'l']
INFO = ['info', 'i']
INIT = ['init']
TAGS = ['tags', 'tag', 't']
LABELS = ['labels', 'lb']
STATUS = ['status', 'st']
BRANCHES = ['branch', 'branches', 'br']
HELP = ['help', '--help', '-h']
UPDATE = ['update']
VERSION = ['--version', '-v', 'version']
CONFIGURE = ['configure', 'config']
SET_GLOBAL = ['--set-global']

COMMANDS = [ADD, REMOVE, LOG, INFO, INIT, TAGS, LABELS, STATUS, BRANCHES, HELP, UPDATE, VERSION, CONFIGURE, SET_GLOBAL]

# Filters
TABLE_ATTR = '-t', '--table'
LABEL_PREFIX = '-l=', '--label='
NOT_LABEL_PREFIX = '-nl=', '--not-label='
BRANCH_PREFIX = '-b=', '--branch='
MODIFIED_ATTR = '-m', '--modified'
DIVERGED_ATTR = '-d', '--diverged'