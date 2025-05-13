import os
import configparser

MAIN_SCOPE = 'mud'
ALIAS_SCOPE = 'alias'


class Settings:
	def __init__(self, file_name: str, old_file_name: str) -> None:
		use_old = os.path.exists(os.path.join(os.path.expanduser('~'), old_file_name))
		file_name = old_file_name if use_old else file_name
		directory = os.path.expanduser('~' if use_old else '~/.config/mud')

		self.mud_settings = None
		self.alias_settings = None
		self.config = configparser.ConfigParser()
		self.settings_file = os.path.join(directory, file_name)
		self.defaults = {
			'mud': {
				'config_path': '',
				'nerd_fonts': True,
				'run_async': True,
				'run_table': True,
				'show_borders': True,
				'round_corners': False,
				'simplify_branches': True,
				'display_absolute_paths': False
			},
			'alias': {
				'fetch': 'git fetch',
				'pull': 'git pull',
				'push': 'git push'
			}
		}
		self.load_settings()

	def load_settings(self) -> None:
		if not os.path.exists(self.settings_file):
			self.config.read_dict(self.defaults)
			self.save()
		else:
			self.config.read(self.settings_file)

		self.mud_settings = {}
		for key in self.defaults[MAIN_SCOPE]:
			if isinstance(self.defaults[MAIN_SCOPE][key], bool):
				self.mud_settings[key] = self.config.getboolean(MAIN_SCOPE, key, fallback=self.defaults[MAIN_SCOPE][key])
			else:
				self.mud_settings[key] = self.config.get(MAIN_SCOPE, key, fallback=self.defaults[MAIN_SCOPE][key])

		if ALIAS_SCOPE in self.config:
			self.alias_settings = self.config[ALIAS_SCOPE]

	def save(self) -> None:
		os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
		with open(self.settings_file, 'w') as config_file:
			self.config.write(config_file)
