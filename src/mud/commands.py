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
REMOTE_BRANCHES = ['remote-branch', 'remote-branches', 'rbr']
HELP = ['help', '--help', '-h']
CONFIGURE = ['configure', 'config']
SET_GLOBAL = ['--set-global']

COMMANDS = [ADD, REMOVE, LOG, INFO, INIT, TAGS, LABELS, STATUS, BRANCHES, REMOTE_BRANCHES, HELP, CONFIGURE, SET_GLOBAL]

# Filters
ASYNC_ATTR = '-a', '--async'
TABLE_ATTR = '-t', '--table'
COMMAND_ATTR = '-c', '--command'
MODIFIED_ATTR = '-m', '--modified'
DIVERGED_ATTR = '-d', '--diverged'
LABEL_PREFIX = '-l=', '--label='
NOT_LABEL_PREFIX = '-nl=', '--not-label='
BRANCH_PREFIX = '-b=', '--branch='
NOT_BRANCH_PREFIX = '-nb=', '--not-branch='
