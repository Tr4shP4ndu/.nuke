"""
    The purpose of this module is to detect context from file paths
"""

import os

from typing import List

from FlwlsVFXPipelinePanel import LogicEX


DEFAULT_FILESYSTEM_SCHEMA = "/Volumes/workspace/shows/{show}/episodes/{episode}/parts/{part}/shots/{shot}/languages/{language}/variants/{variant}"


def get_schema_token(token: str = "show", schema: str = DEFAULT_FILESYSTEM_SCHEMA) -> List[str]:
    token_index = schema.index("{" + token + "}")
    return schema[:token_index]


def get_level_contents(level_path: str, regex: str = "") -> List[str]:
    level_contents = []
    if os.path.exists(level_path):
        if regex:
            level_contents = LogicEX.UI_itera_file_names_only(level_path, regex)
        else:
            level_contents = os.listdir(level_path)
            level_contents.sort()
    return level_contents


def get_shows() -> List[str]:
    level_path = get_schema_token()
    return get_level_contents(level_path, regex=LogicEX.get_show_regex())


def get_episodes(show: str) -> List[str]:
    level = get_schema_token("episode")
    level_path = level.format(show=show)
    return get_level_contents(level_path, regex=LogicEX.get_episode_regex())


def get_parts(show: str, episode: str) -> List[str]:
    level = get_schema_token("part")
    level_path = level.format(show=show, episode=episode)
    return get_level_contents(level_path, regex=LogicEX.get_part_regex())


def get_shots(show: str, episode: str, part: str) -> List[str]:
    level = get_schema_token("shot")
    level_path = level.format(show=show, episode=episode, part=part)
    return get_level_contents(level_path, regex=LogicEX.get_shot_regex())


def get_languages(show: str, episode: str, part: str, shot: str) -> List[str]:
    level = get_schema_token("language")
    level_path = level.format(show=show, episode=episode, part=part, shot=shot)
    return get_level_contents(level_path, regex=LogicEX.get_language_regex())


def get_variants(show: str, episode: str, part: str, shot: str, language: str) -> List[str]:
    level = get_schema_token("variant")
    variant_paths = []
    if language == "all":
        for languages in get_languages(show, episode, part, shot):
            level_path = level.format(show=show, episode=episode, part=part, shot=shot, language=languages)
            variant_paths.extend(get_level_contents(level_path, regex=LogicEX.get_language_regex()))
    else:
        level_path = level.format(show=show, episode=episode, part=part, shot=shot, language=language)
        variant_paths = get_level_contents(level_path, regex=LogicEX.get_language_regex())
    return variant_paths


