import os
import utils
import xml.etree.ElementTree as ElementTree
import re

from typing import List, Dict
from xml.dom import minidom


class Config:
    def __init__(self):
        self.data = {}
        self.find()

    def save(self, file_path: str) -> None:
        root = ElementTree.Element("mud")

        def _filter_labels(label: str):
            return bool(re.match(r'^\w+$', label))

        for path, labels in self.data.items():
            dir_element = ElementTree.SubElement(root, "dir")
            dir_element.set("path", path)

            valid_labels = [label for label in labels if _filter_labels(label)]
            if valid_labels:
                if len(valid_labels) == 1:
                    formatted_labels = valid_labels[0]
                else:
                    formatted_labels = ', '.join(valid_labels)
                dir_element.set("label", formatted_labels)

        rough_string = ElementTree.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="\t")

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(pretty_xml)

    def find(self) -> None:
        if os.path.exists(utils.CONFIG_FILE_NAME):
            self.load(utils.CONFIG_FILE_NAME)
            return

        if utils.settings.mud_settings['config_path'] != '' and os.path.exists(
                utils.settings.mud_settings['config_path']):
            directory = os.path.dirname(utils.settings.mud_settings['config_path'])
            os.chdir(directory)
            os.environ['PWD'] = directory
            self.load(utils.CONFIG_FILE_NAME)
            return

        utils.print_error('.mudconfig file was not found. Type `mud add --all` to create configuration file.')

    def load(self, file_path: str) -> None:
        self.data = {}
        tree = ElementTree.parse(file_path)
        root = tree.getroot()
        for dir_element in root.findall('dir'):
            path = dir_element.get('path')
            labels = [label.strip() for label in dir_element.get('label', '').split(',') if label.strip()]
            self.data[path] = labels

    def all(self) -> Dict[str, List[str]]:
        return self.data

    def paths(self) -> List[str]:
        return list(self.data.keys())

    def with_label(self, label: str) -> Dict[str, List[str]]:
        if label == '':
            return self.all()
        result = {}
        for path, labels in self.data.items():
            if label in labels:
                result[path] = labels
        return result

    def add_label(self, path: str, label: str) -> None:
        if path not in self.data:
            self.data[path] = []
        if label not in self.data[path]:
            self.data[path].append(label)

    def remove_path(self, path: str) -> None:
        if path in self.data:
            del self.data[path]

    def remove_label(self, path: str, label: str) -> None:
        if path in self.data and label in self.data[path]:
            self.data[path].remove(label)
            if not self.data[path]:
                del self.data[path]
