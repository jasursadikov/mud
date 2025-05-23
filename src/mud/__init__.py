#!/usr/bin/env python3

import mud.utils
import mud.settings

from .app import App


def run():
	try:
		utils.settings = settings.Settings(utils.SETTINGS_FILE_NAME, utils.OLD_SETTINGS_FILE_NAME)

		app: App = App()
		app.run()
	except KeyboardInterrupt:
		utils.print_error(0)


if __name__ == '__main__':
	run()
