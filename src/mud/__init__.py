#!/usr/bin/env python3

import mud.utils
import mud.settings
import sys

from mud.app import App
from mud.commands import COMPLETION


def run():
	try:
		app: App = App()
		if sys.argv[1:2] == COMPLETION:
			from mud.completion import complete

			complete(app.parser)
			return

		utils.settings = settings.Settings(utils.SETTINGS_FILE_NAME, utils.OLD_SETTINGS_FILE_NAME)

		app.run()
	except KeyboardInterrupt:
		utils.print_error(0)


if __name__ == '__main__':
	run()
