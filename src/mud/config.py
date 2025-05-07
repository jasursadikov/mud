import os
import re
import csv

from typing import List, Dict, Any

from mud import utils
from mud.styles import *


class Config:
	def __init__(self):
		self.data = {}

	def save(self, file_path: str) -> None:
		def _filter_labels(label: str):
			return bool(re.match(r'^\w+$', label))

		with open(file_path, 'w', newline='') as tsvfile:
			writer = csv.writer(tsvfile, delimiter='\t')

			for path, labels in self.data.items():
				valid_labels = [label for label in labels if _filter_labels(label)]
				formatted_labels = ','.join(valid_labels) if valid_labels else ''
				writer.writerow([path, formatted_labels])

	def find(self) -> str:
		directory = os.getcwd()
		current_path = directory
		while os.path.dirname(current_path) != current_path:
			os.chdir(current_path)
			if os.path.exists(utils.CONFIG_FILE_NAME):
				self.load(utils.CONFIG_FILE_NAME)
				return current_path
			current_path = os.path.dirname(current_path)

		if utils.settings.mud_settings['config_path'] != '' and os.path.exists(utils.settings.mud_settings['config_path']):
			directory = os.path.dirname(utils.settings.mud_settings['config_path'])
			os.chdir(directory)
			os.environ['PWD'] = directory
			self.load(utils.CONFIG_FILE_NAME)
			return current_path

		utils.print_error(f'{BOLD}{utils.CONFIG_FILE_NAME}{RESET} was not found. Run \'mud init\' to create a configuration file.', 11, exit=True)

	def load(self, file_path: str) -> None:
		self.data = {}
		with open(file_path, 'r') as tsvfile:
			reader = csv.reader(tsvfile, delimiter='\t')
			for row in reader:
				path = row[0]

				if path.startswith('~'):
					path = os.path.expanduser(path)

				labels = [label.strip() for label in row[1].split(',') if len(row) > 1 and label.strip()] if len(row) > 1 else []
				self.data[path] = labels

	def paths(self) -> List[str]:
		return list(self.data.keys())

	def filter_label(self, label: str, repos: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
		if repos is None:
			repos = self.data
		if label == '':
			return repos
		result = {}
		for path, labels in repos.items():
			if label in labels:
				result[path] = labels
		return result

	def add_label(self, path: str, label: str) -> None:
		if path == '.':
			conf_path = Config().find()
			path = os.path.relpath(conf_path, os.getcwd())
		if path is None:
			path = label
			label = None
		if not os.path.isdir(path):
			utils.print_error(f'Invalid path {BOLD}{path}{RESET}. Remember that path should be relative.', 14)
			return
		if path not in self.data:
			self.data[path] = []
		if label is not None and label not in self.data[path]:
			self.data[path].append(label)

	def prune(self, config_dir: str):
		for path, label in list(self.data.items()):
			abs_path = path if os.path.abspath(path) else os.path.join(config_dir, path)
			if not os.path.exists(abs_path):
				del self.data[path]
				print(path)

	def remove_path(self, path: str) -> None:
		if path in self.data:
			del self.data[path]

	def remove_label(self, path: str, label: str) -> None:
		if path in self.data and label in self.data[path]:
			self.data[path].remove(label)
			if not self.data[path]:
				del self.data[path]
