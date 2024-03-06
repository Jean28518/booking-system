import os
import json

from django.conf import settings

file_path = os.path.join(settings.BASE_DIR, 'config.json')


def get_value(key, default_value):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get(key, default_value)
    return default_value


def set_value(key, value):
    data = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    data[key] = value
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    return value
