#!/usr/bin/env python3

from . import utils, settings
from .app import App


def run():
	try:
		utils.settings = settings.Settings(utils.SETTINGS_FILE_NAME)

		app = App()
		app.run()
	except KeyboardInterrupt:
		utils.print_error('Stopped by user.', 0)


if __name__ == '__main__':
	run()
