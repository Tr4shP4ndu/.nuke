
import json

from pathlib import Path


def get_preference_file(tool_name: str = "review_importer"):
    settings_file = Path.home() / ".flwls-pipeline" / "{tool_name}.json"
    if not settings_file.parent.exists():
        settings_file.parent.mkdir(parents=True)
    return settings_file


def set(key: str, value: str, tool_name: str = "review_importer"):
    preferences = {}
    preference_file = get_preference_file(tool_name)
    if preference_file.exists():
        with open(preference_file.as_posix()) as h:
            preferences = json.load(h)
    preferences[key] = value
    with open(preference_file.as_posix(), "w+") as h:
        json.dump(preferences, h)


def get(key: str, tool_name: str = "review_importer"):
    preferences = {}
    preference_file = get_preference_file(tool_name)
    if preference_file.exists():
        with open(preference_file.as_posix()) as h:
            preferences = json.load(h)
    return preferences.get(key)
