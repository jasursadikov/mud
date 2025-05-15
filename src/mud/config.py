import os
import re
import csv

from typing import List, Dict, Tuple

from mud import utils


class Config:
	def __init__(self):
		self.data = {}

	@staticmethod
	def find() -> Tuple[str, bool]:
		directory = os.getcwd()
		current_path = directory
		while os.path.dirname(current_path) != current_path:
			if os.path.exists(os.path.join(current_path, utils.CONFIG_FILE_NAME)):
				return current_path, False
			current_path = os.path.dirname(current_path)

		config_path = utils.settings.mud_settings['config_path']

		if config_path.startswith('~'):
			config_path = os.path.expanduser(config_path)

		if config_path != '' and os.path.exists(config_path):
			directory = os.path.dirname(config_path)
			if os.path.exists(config_path):
				return directory, True

		return '', False

	def save(self, file_path: str) -> None:
		def _filter_labels(label: str):
			return bool(re.match(r'^\w+$', label))

		with open(file_path, 'w', newline='') as tsvfile:
			writer = csv.writer(tsvfile, delimiter='\t')

			for path, labels in self.data.items():
				valid_labels = [label for label in labels if _filter_labels(label)]
				formatted_labels = ','.join(valid_labels) if valid_labels else ''
				writer.writerow([path, formatted_labels])

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

	def init(self):
		if self.data is None:
			self.data = {}

		index = 0
		git_repos = []

		for root, dirs, files in os.walk('.', topdown=True):
			if '.git' in dirs:
				git_repos.append(os.path.relpath(root, '.'))
				dirs.remove('.git')
			dirs[:] = [d for d in dirs if not d.startswith('.')]

		git_repos.sort()

		for repo in git_repos:
			if repo in self.data.keys():
				continue

			self.add(repo, '')
			index += 1
			print(repo)
		if index == 0 and len(self.data) == 0:
			utils.print_error(3)
			return

	def add(self, path: str, label: str) -> None:
		if path == '.':
			current_path = os.getcwd()
			config_dir = Config().find()[0]

			if config_dir == '':
				utils.print_error(5)

			config_path = os.path.join(config_dir, utils.CONFIG_FILE_NAME)
			path = os.path.relpath(current_path, config_path)
		if path is None:
			path = label
			label = None
		if not os.path.isdir(path):
			utils.print_error(7, meta=path)
			return
		if path not in self.data:
			self.data[path] = []
		if label is not None and label not in self.data[path]:
			self.data[path].append(label)

	def remove(self, label: str, path: str):
		if path and label:
			self.remove_label(path, label)
		elif path:
			self.remove_path(path)
		else:
			utils.print_error(4)

	def prune(self):
		for path, label in list(self.data.items()):
			if not os.path.exists(path):
				del self.data[path]
				print(path)

	def remove_path(self, path: str) -> None:
		if path in self.data.keys():
			del self.data[path]
			print(path)
			return
		utils.print_error(6, meta=path)

	def remove_label(self, path: str, label: str) -> None:
		if path in self.data and label in self.data[path]:
			self.data[path].remove(label)
			return
		utils.print_error(6, meta=f'{path}:{label}')
