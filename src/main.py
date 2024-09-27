import utils
import settings

from app import App

if __name__ == '__main__':
	try:
		utils.settings = settings.Settings(utils.SETTINGS_FILE_NAME)
		app = App()
		app.run()
	except KeyboardInterrupt:
		utils.print_error('Stopped by user.', 0)
