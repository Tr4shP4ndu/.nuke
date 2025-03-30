from typing import Union
import nuke
from pathlib import Path
import os
import re
import itertools
import nuke_utils
import shutil
import task_set_up
from typing import Any, Callable, List, Dict

class LogicEX():
    def UI_itera_full(folder, pattern = "") -> List[str]:
        none = ["NONE"]
        folder = LogicEX.folder_keyword_replacement(folder)
        if not LogicEX.folder_exists(folder):
            return none
        results = LogicEX.itera(folder, pattern)
        if not results:
            return none
        return results
    def UI_itera_file_names_only(folder, pattern = "") ->List[str]:
        results = LogicEX.UI_itera_full(folder, pattern)
        return [os.path.basename(res) for res in results]
    def get_show_regex() -> str:
        return "^[a-z]{4}[0-9]{2}$"
    def get_episode_regex() -> str:
        return "^ep[0-9]{2}$"
    def get_part_regex() -> str:
        return "^pt[0-9]{2}$"
    def get_shot_regex() -> str:
        return "^[0-9]{4}$"
    def get_language_regex() -> str:
        return ""
    def get_variant_regex() -> str:
        return ""
    def get_version_regex() -> str:
        return "^[v][0-9]{3}$"
    def get_subversion_regex() -> str:
        return "^((?!autosave).)*.(?<!~)$"
    def join(folder, folder2) -> str:
        return os.path.join(LogicEX.folder_keyword_replacement(str(folder)), LogicEX.folder_keyword_replacement(str(folder2)))
    def itera(folder : str, regex = "") -> List[str]:
        results = sorted([os.path.join(folder, file) for file in os.listdir(folder)])
        if regex == "":
            return results
        return  [file for file in results if re.match(regex, os.path.basename(file)) is not None]
    def get_full_name(folder):
        return os.path.basename(folder)
    def folder_keyword_replacement(folder) -> str:
        if "$FINDFIRSTFOLDER$" in folder:
            try:
                while "$FINDFIRSTFOLDER$" in folder:
                    folder = folder.replace("$FINDFIRSTFOLDER$", sorted(os.listdir(folder.split("$FINDFIRSTFOLDER$")[0]))[-1], 1)
            except FileNotFoundError:
                pass # path does not exist / there is no folder to find
        return folder
    def folder_exists(folder : str) -> bool:
        return os.path.exists(folder)
    def remake(folder : str) -> None:
        if LogicEX.folder_exists(folder):
            shutil.rmtree(folder)
        LogicEX.make(folder)
    def make(folder : str) -> None:
        folder = str(folder)
        folder = LogicEX.folder_keyword_replacement(folder)
        if not LogicEX.folder_exists(folder):
            os.makedirs(folder, exist_ok=True)
    def cap_first_letter(string : str) -> str:
        return string[0].upper() + string[1:].lower()
    def from_dict_to_string(a_dict : Dict, keys : List[str], separator : List[str]):
        result = ""
        for key in keys:
            result+= a_dict[key] + separator
        return result[0:len(separator)*-1]
    def get_all_task_types() -> List[str]:
        return [getattr(task_set_up.TaskType, task).value for task in dir(task_set_up.TaskType) if task[0:2] != "__"]
    def get_released_task_types(override = "") -> List[str]:
        tasks = ["vfx_nr_cleanup","object_replacement", "vfx_occlusion"]
        if override == "review":
            tasks = ["vfx_nr_cleanup", "vfx_vendor"]
        return [task for task in LogicEX.get_all_task_types() if task in tasks]
    def attempt_resolve_path(func : Callable) -> str:
        try:
            return func()
        except Exception as EX:
            return "None"
    def get_context_based_on_current_path() -> Dict[str,str]:
        """When reloading a script there may be no context choices in the panel.
        This guesses the context based on where the script was saved.
        Will fail if saved somewhere outside the pipeline."""
        return LogicEX.get_context_based_on_this_path(nuke.root()['name'].value())
    def get_context_based_on_this_path(file_path : str) -> Dict[str,str]:
        split = Path(file_path).parts
        results = {}
        for to_find in ["shows","episodes","parts","shots","languages","variants", "tasks"]:
            if to_find in split:
                index = split.index(to_find)
                results[to_find[:-1]] = split[index+1]
        if not results.keys():
            raise Exception("Not a valid save path to get a context.")
        results["version"] = split[split.index(results["task"])+1]
        return results
    def convert_string_to_context_agnostic(raw_context : str, splitter : str) -> Dict[str,str]:
        function_map = {
            4 : lambda : LogicEX.convert_string_to_shot(raw_context),
            5 : lambda : LogicEX.convert_string_to_shot_language(raw_context),
            7 : lambda : LogicEX.convert_string_to_shot_language_variant(raw_context),
        }
        cardinality = len(raw_context.split(splitter))
        if cardinality not in function_map.keys():
            raise Exception("No known method of parsing this context: " + raw_context)
        return function_map[cardinality]()
    def convert_string_to_shot_language_variant(raw_context : str) -> Dict[str,str]:
        results = {
            "show" : raw_context.split("_")[0],
            "episode" : raw_context.split("_")[1],
            "part" : raw_context.split("_")[2],
            "shot" : raw_context.split("_")[3],
            "language" : raw_context.split("_")[4],
            "variant" : raw_context.split("_")[5] + "_" + raw_context.split("_")[6],
        }
        results["context_type"] = "shot_language_variant"
        results["full_shot"] = results["episode"] + "_" + results["part"] + "_" + results["shot"]
        results["shot_variant"] = results["show"] + "_" + results["full_shot"] + "_" + results["variant"]
        results["workspace"] = LogicEX.get_shows_root() + f"{results['show']}/episodes/{results['episode']}/parts/{results['part']}/shots/{results['shot']}" +\
        f"/languages/{results['language']}/variants/{results['variant']}"
        return results
    def convert_string_to_shot_language(raw_context : str) -> Dict[str,str]:
        results = {
            "show" : raw_context.split("_")[0],
            "episode" : raw_context.split("_")[1],
            "part" : raw_context.split("_")[2],
            "shot" : raw_context.split("_")[3],
            "language" : raw_context.split("_")[4],
        }
        results["context_type"] = "shot_language_variant"
        results["full_shot"] = results["episode"] + "_" + results["part"] + "_" + results["shot"]
        results["workspace"] = LogicEX.get_shows_root() + f"{results['show']}/episodes/{results['episode']}/parts/{results['part']}/shots/{results['shot']}" +\
        f"/languages/{results['language']}"
        return results
    def convert_string_to_shot(raw_context : str) -> Dict[str,str]:
        results = {
            "show" : raw_context.split("_")[0],
            "episode" : raw_context.split("_")[1],
            "part" : raw_context.split("_")[2],
            "shot" : raw_context.split("_")[3],
        }
        results["context_type"] = "shot_language_variant"
        results["full_shot"] = results["episode"] + "_" + results["part"] + "_" + results["shot"]
        results["workspace"] = LogicEX.get_shows_root() + f"{results['show']}/episodes/{results['episode']}/parts/{results['part']}/shots/{results['shot']}"
        return results
    def get_shows_root():
        return os.environ["FLWLS_WORKSPACE_ROOT"] + "/shows/"
    def write_text(contents, filepath):
        with open(filepath, "w") as file:
            file.write(contents)
    def hard_copy(source_file : str, dest_folder : str) -> None:
        while os.path.islink(source_file):
            source_file = os.readlink(source_file)
        destination = LogicEX.join(str(dest_folder), str(source_file).split("/")[-1])
        shutil.copy(source_file, destination)
    def copy_with_mono_symlinks(source_file : str, dest_folder : str) -> None:
        destination = os.path.join(str(dest_folder), str(source_file).split("/")[-1])
        while os.path.islink(source_file):
            source_file = os.readlink(source_file)
        os.symlink(source_file, destination)

class VFXPipelinePanelBasic():
    def get_option_names() -> List[Any]:
        return ["task","show","episode","part","shot","language","variant","version","subversion"]

    def get_locations_of_user_choices(choices : Dict[Any,Any], prefix : str = "") -> Dict[Any, Any]:
        shows_root = os.environ["FLWLS_WORKSPACE_ROOT"] + "/shows/"
        task = choices[prefix+"task"]
        results = {
            prefix+"show" : shows_root,
            prefix+"episode" : LogicEX.attempt_resolve_path(
                lambda : LogicEX.join(shows_root, f"""{choices[prefix+"show"]}/episodes/""")),
            prefix+"part" : LogicEX.attempt_resolve_path(
                lambda : LogicEX.join(shows_root, f"""{choices[prefix+"show"]}/episodes/{choices[prefix+"episode"]}/parts""")),
            prefix+"shot" : LogicEX.attempt_resolve_path(
                lambda : LogicEX.join(shows_root, f"""{choices[prefix+"show"]}/episodes/{choices[prefix+"episode"]}/parts/{choices[prefix+"part"]}/shots""")),
            prefix+"language" : LogicEX.attempt_resolve_path(
                lambda : LogicEX.join(shows_root, f"""{choices[prefix+"show"]}/episodes/{choices[prefix+"episode"]}/parts/{choices[prefix+"part"]}/shots/{choices[prefix+"shot"]}/languages""")),
            prefix+"variant" : LogicEX.attempt_resolve_path(
                lambda : LogicEX.join(shows_root, f"""{choices[prefix+"show"]}/episodes/{choices[prefix+"episode"]}/parts/{choices[prefix+"part"]}/shots/{choices[prefix+"shot"]}/languages/{choices[prefix+"language"]}/variants""")),
        }
        task_level = task_set_up.get_task_definition(task).task_level
        context_levels = task_set_up.get_task_definition(task).context_levels
        for optional_context in ["language","variant"]:
            if optional_context not in context_levels:
                results[prefix+optional_context] = "None"
        version_path = ""
        for provided_context in context_levels[1:]:
            version_path += f"/{provided_context}s/" + choices[prefix+provided_context]
        version_path += f"/tasks/{task}/"
        if prefix == "review":
            version_path += ".snapshot/"
        subversion_path = version_path + choices[prefix+"version"] + f"/work/{VFXPipelinePanelBasic.get_context_as_string(choices, prefix)}_{choices[prefix+'task']}/scripts"
        results[prefix+"version"] = LogicEX.attempt_resolve_path(lambda : shows_root + choices[prefix+"show"] + version_path)
        results[prefix+"subversion"] = LogicEX.attempt_resolve_path(lambda : shows_root + choices[prefix+"show"] + LogicEX.folder_keyword_replacement(subversion_path))
        return results
    
    def get_path_to_latest_subversion(choices : Dict[Any,Any]) -> str:
        return LogicEX.UI_itera_full(VFXPipelinePanelBasic.get_locations_of_user_choices(choices)["subversion"], LogicEX.get_subversion_regex())[-1]

    def get_path_to_selected_subversion(choices : Dict[Any,Any]) -> str:
        return LogicEX.folder_keyword_replacement(LogicEX.join(VFXPipelinePanelBasic.get_locations_of_user_choices(choices)["subversion"],choices["subversion"]))

    def get_path_to_selected_version(choices : Dict[Any,Any]) -> str:
        locations = VFXPipelinePanelBasic.get_locations_of_user_choices(choices)
        return LogicEX.join(locations["version"], choices["version"])
        
    def get_latest_version_number(choices : Dict[Any,Any]) -> str:
        locations = VFXPipelinePanelBasic.get_locations_of_user_choices(choices)
        workspace_path = Path(LogicEX.folder_keyword_replacement(locations["subversion"]))
        return task_set_up.get_latest_script_number(workspace_path)

    def get_next_version_number(choices : Dict[Any,Any]) -> str:
        """Return an empty string if no next version could be interpreted."""
        locations = VFXPipelinePanelBasic.get_locations_of_user_choices(choices)
        workspace_path = Path(LogicEX.folder_keyword_replacement(locations["subversion"]))
        return task_set_up.get_next_script_number(workspace_path)

    def open_nuke_script(self, path_to_script) -> None:
        nuke_utils.make_tmp_nuke_script_then_open(path_to_script)

    def get_context_as_string(choices : Dict[Any,Any], prefix : str = "") -> str:
        levels = [prefix+l for l in task_set_up.get_task_definition(choices[prefix+"task"]).context_levels]
        return LogicEX.from_dict_to_string(choices,levels,"_")