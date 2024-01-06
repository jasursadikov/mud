import os
import configparser

class Settings:
	def __init__(self, file_name: str) -> None:
		self.file_name = file_name
		self.config = configparser.ConfigParser()
		self.settings_file = os.path.join(os.path.expanduser('~'), self.file_name)
		self.defaults = {
			'mud': {
				'config_path': '',
				'nerd_fonts': True,
				'auto_fetch': False,
				'run_async': True,
				'run_table': True
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
		for key in self.defaults['mud']:
			if isinstance(self.defaults['mud'][key], bool):
				self.mud_settings[key] = self.config.getboolean('mud', key, fallback=self.defaults['mud'][key])
			else:
				self.mud_settings[key] = self.config.get('mud', key, fallback=self.defaults['mud'][key])

		self.alias_settings = self.config['alias']

	def save(self) -> None:
		with open(self.settings_file, 'w') as configfile:
			self.config.write(configfile)