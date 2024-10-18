import os
import configparser

MAIN_SCOPE = 'mud'
ALIAS_SCOPE = 'alias'


class Settings:
	def __init__(self, file_name: str) -> None:
		self.file_name = file_name
		self.mud_settings = None
		self.alias_settings = None
		self.config = configparser.ConfigParser()
		self.settings_file = os.path.join(os.path.expanduser('~'), self.file_name)
		self.defaults = {
			'mud': {
				'config_path': '',
				'nerd_fonts': True,
				'run_async': True,
				'run_table': True,
				'simplify_branches': True
			},
			'alias': {
				'to': 'git checkout',
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
		with open(self.settings_file, 'w') as configfile:
			self.config.write(configfile)
