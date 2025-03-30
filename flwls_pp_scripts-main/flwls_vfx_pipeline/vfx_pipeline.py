import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import re
import shutil
import os

@dataclass(frozen=True)
class Context():
    '''Usual context keys you'd expect are:
    "task", "show", "episode", "part", "shot", "version"
    and
    "language", "variant"
    '''
    dict: dict

    @classmethod
    def from_dict(cls, dict: Dict) -> "Context":
        return Context(dict= dict)

def get_context_from_inputs_folder(path: str):
    '''Uses the 'inputs' folder schema to extract context
    e.g.
    /Volumes/workspace/shows/pulp00/tasks/vfx_nr_cleanup/inputs/v001/languages/fra/shots/ep01_pt02_0240/PRECOMP/jules_main
    should return
    Context(dict={'task': 'vfx_nr_cleanup', 'show': 'pulp00', 'version': 1, 'shot': 240, 'episode': 1, 'part': 2, 'language': 'fra', 'variant': 'jules_main'})
    and
    /Volumes/workspace/shows/pulp00/tasks/vfx_occlusion/inputs/v002/shots/ep01_pt01_0300
    should return
    /Volumes/workspace/shows/pulp00/tasks/vfx_occlusion/inputs/v002/shots/ep01_pt01_0300
    '''

    path = Path(path)
    try:
        context_dict = {}
        context_dict['workspace_root'] = Path('/Volumes/workspace')
        context_dict['task'] = _get_subfolder_name(filepath=path, key='tasks')
        if context_dict['task'] in ('vfx_occlusion', 'vfx_inpaint'):
            context_dict['level'] = 'Shot'
        elif context_dict['task'] == 'vfx_nr_cleanup':
            context_dict['level'] = 'ShotLanguageVariant'
        context_dict['show'] = _get_subfolder_name(filepath=path, key='shows')
        context_dict['version'] = int(_get_subfolder_name(filepath=path, key='inputs')[1:])
        context_dict['shot'] = int(_get_subfolder_name(filepath=path, key='shots')[10:])
        context_dict['episode'] = int(_get_subfolder_name(filepath=path, key='shots')[2:4])
        context_dict['part'] = int(_get_subfolder_name(filepath=path, key='shots')[7:9])
        context_dict['language'] = _get_subfolder_name(filepath=path, key='languages')
        context_dict['variant'] = _get_subfolder_name(filepath=path, key='PRECOMP')

        return Context(dict=context_dict)
    except TypeError as e:
        raise TypeError(f'Error when extracting context from filepath. Make sure that the "input_shot_knob" is filled properly')

def get_context_from_script_name(script_name: str):
    '''
    Assuming filenames are named as in _get_filename_suffix_from_context()
    arguments:
    @script_name = str of the script name only

    TODO: Very similar functionality exists in publish_vfx_task.py Maybe there are better ways to get the context
    '''

    try:
        script_name_parts = script_name.split('_')
        context_dict = {}
        context_dict['workspace_root'] = Path('/Volumes/workspace')
        if "nr" in script_name_parts:
            if "cleanup" in script_name_parts:
                context_dict['task'] = "vfx_nr_cleanup"
        elif "inpaint" in script_name_parts:
            context_dict['task'] = "vfx_inpaint"
        elif "occlusion" in script_name_parts:
            context_dict['task'] = "vfx_occlusion"
        if context_dict['task'] in ('vfx_occlusion', 'vfx_inpaint'):
            context_dict['level'] = 'Shot'
        elif context_dict['task'] == 'vfx_nr_cleanup':
            context_dict['level'] = 'ShotLanguageVariant'        
        context_dict['show'] = script_name_parts[0]
        context_dict['episode'] = int(script_name_parts[1][2:4])
        context_dict['part'] = int(script_name_parts[2][2:4])
        context_dict['shot'] = int(script_name_parts[3])
        if context_dict['level'] == 'ShotLanguageVariant':
            context_dict['language'] = script_name_parts[4]
            context_dict['variant'] = f"{script_name_parts[5]}_{script_name_parts[6]}"
            
        return Context(dict=context_dict)
    except TypeError as e:
        raise TypeError(f'{e}\nError when extracting context from script name. Does the script name contain all the context')


def _format_version_number_to_string(version_number: int) -> str:
    '''given an int returns 'v001', 'v002'...
    '''
    return f'v{version_number:03d}'

def _allowed_characters():
    '''
    Only other non-alphanumeric characters we allow. E.g. in filenames
    '''
    return "_-"

def find_illegal_characters(text_to_check: str) -> bool:
    '''
    Returns any characters that are not alphanumeric and not in _allowed_characters()
    '''
    discovered_illegal_characters_set = {char for char in text_to_check if not char.isalnum() and char not in _allowed_characters()}
    return discovered_illegal_characters_set

def _get_inputs_folder_from_context(context:Context) -> Path:
    '''Given a Context returns a path to the shot (ShotLanguage) level in the 'inputs' folder
    '''
    cntx = context.dict
    inputs_path = Path(cntx['workspace_root'])
    inputs_path = inputs_path / 'shows' / cntx['show'] / 'tasks' / cntx['task'] / 'inputs' / f"v{cntx['version']:03d}"
    episode_part_shot = f"ep{cntx['episode']:02d}_pt{cntx['part']:02d}_{cntx['shot']:04d}"
    if cntx['level'] == 'Shot':
        inputs_path = inputs_path / 'shots' / episode_part_shot
    elif cntx['level'] == 'ShotLanguageVariant':
        inputs_path = inputs_path / 'languages' / cntx['language'] / 'shots' / episode_part_shot
    else:
        raise ValueError('Problem with context-level')
    return inputs_path

def _get_subfolder_name(filepath: Path, key: str) -> str:
    for i, part in enumerate(filepath.parts):
        if part == key and i < len(filepath.parts) - 1:
            return filepath.parts[i + 1]
    return None

def _create_work_folder_structure(context: Context):
    '''
    Making the folder called "work" if it doesn't exist yet
    TODO: (AK) add other folders
    '''

    task_path = _get_task_path(context=context)
    work_path = task_path / 'work'
    if not work_path.is_dir():
        work_path.mkdir(parents=True)

def _get_task_path(context: Context) -> Path:
    '''
    NOTE: renaming the vfx_occlusion and vfx_inpaint tasks is to match
    Jesse M's publishing schemas
    '''
    cntx = context.dict
    shot_path = cntx['workspace_root'] / 'shows' / cntx['show'] / 'episodes' / f"ep{cntx['episode']:02d}" / 'parts' / f"pt{cntx['part']:02d}" / 'shots' / f"{cntx['shot']:04d}" 
    task_path = None
    if cntx['level'] == 'Shot':
        task = None
        if cntx['task'] == 'vfx_inpaint':
            task = 'vfx_inpainting'
        elif cntx['task'] == 'vfx_occlusion':
            task = 'vfx_occlusions'
        if task:
            task_path = shot_path / 'tasks' / task 
    elif cntx['level'] == 'ShotLanguageVariant':
        task_path = shot_path / 'languages' / cntx['language'] / 'variants' / cntx['variant'] / 'tasks' / cntx['task']

    if not task_path:
        raise ValueError("task_path must not be None")
    return task_path

def _get_task_template_nuke_script(context: Context)-> Path:
    '''
    Get the task template .nk file from repo
    '''
    script_path = Path(__file__)
    templates_folder = script_path.parent / 'templates'
    
    task = context.dict['task']
    task_template_path = list(templates_folder.glob(f'**/{task}*'))[0]
    return task_template_path

def _copy_task_template_to_task_folder(context: Context) -> Path():
    '''
    Copies a vfx task specifc template from this repo's templates folder
    to the task folder.
    Returns: path to the copied file
    '''
    destination_filepath = _get_task_nuke_script_destination_path(context=context)
    template_path = _get_task_template_nuke_script(context=context)
    shutil.copy(src=template_path.as_posix(), dst=destination_filepath.as_posix())
    return destination_filepath

def _copy_task_template_to_specific_destination(context: Context, destination_path_with_filename: Path) -> Path():
    '''
    Copies a vfx task specifc template from this repo's templates folder
    to where you tell it. You need to include the final filename too.
    Returns: path to the copied file
    '''
    template_path = _get_task_template_nuke_script(context=context)
    shutil.copy(src=template_path.as_posix(), dst=destination_path_with_filename.as_posix())
    return destination_path_with_filename

def _get_task_nuke_script_destination_path(context:Context) -> Path:
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    filename_suffix = _get_filename_suffix_from_context(context=context)
    latest_version = _get_latest_version_of_file_in_folder(file_name=filename_suffix, folder_path=work_folder)
    version = _version_up(latest_version)
    destination_filepath = work_folder / f'{filename_suffix}_{version}.nk'
    return destination_filepath

def get_subtask_nuke_script_destination_path(context:Context, subtask_name: str) -> Path:
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    subtask_suffix = _get_filename_suffix_from_context(context=context) + "_" + subtask_name
    subtask_folder = work_folder / subtask_suffix
    latest_version = _get_latest_version_of_file_in_folder(file_name=subtask_suffix, folder_path=subtask_folder)
    version = _version_up(latest_version)
    destination_filepath = subtask_folder / f'{subtask_suffix}_{version}.nk'
    return destination_filepath

def get_all_existing_task_nuke_scripts(context: Context) -> List:
    ''' Returns all Nuke scripts in the folder that match the pipeline naming convention
    '''
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    directory = '/path/to/directory'  # Replace with the actual directory path
    pattern = r'v(\d+)'
    # Get all files in the directory ending with ".nk"
    
    nuke_scripts = [f for f in os.listdir(work_folder) if f.endswith('.nk')]

    # Sort files based on version number
    sorted_nuke_scripts = sorted(nuke_scripts, key=lambda x: int(re.search(pattern, x).group(1)), reverse=True)

    return sorted_nuke_scripts

def get_work_directory(context: Context):
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    return work_folder

def _get_filename_suffix_from_context(context: Context) -> str:
    cntx = context.dict
    filename = f"{cntx['show']}_ep{cntx['episode']:02d}_pt{cntx['part']:02d}_{cntx['shot']:04d}"
    if cntx['level'] == 'Shot':
        filename = f"{filename}_{cntx['task']}"
    elif cntx['level'] == 'ShotLanguageVariant':
        filename = f"{filename}_{cntx['language']}_{cntx['variant']}_{cntx['task']}"
    return filename

def _get_latest_version_of_file_in_folder(file_name:str, folder_path: Path) -> str:
    '''
    Find the latest version of the file_name in a given folder_path assuming that
    the version number is of the form "_v%03d". If none are found returns v000
    '''
    filename_pattern = f'*{file_name}_v*'
    files = list(folder_path.glob(filename_pattern))
    files = [file for file in files if file.is_file()]
    if len(files) == 0:
        return 'v000'
    else:
        files.sort(reverse=True)
        latest_file_name = files[0].name
        version_number_pattern = r"v\d{3}"
        match = re.search(pattern=version_number_pattern, string=latest_file_name)
        return match.group()

def _version_up(version: str) -> str:
    '''
    Given a version as a string in the format "v%03d", returns then next one up
    '''
    version_up = int(version[1:])+1
    return _format_version_number_to_string(version_number=version_up)

def _symlink_task_inputs(context: Context):
    '''
    Makes a link to the shot or shotlanguage level assets in 'tasks' folder
    keeping the version number of aggregation.
    '''
    version = _format_version_number_to_string(context.dict['version'])
    task_path = _get_task_path(context=context)
    aggregation_inputs_folder = _get_inputs_folder_from_context(context=context)
    task_in_folder = task_path / 'in'
    if not task_in_folder.is_dir():
        task_in_folder.mkdir(parents=True)
    task_in_folder_version = task_in_folder / version
    if task_in_folder_version.is_symlink():
        task_in_folder_version.unlink()
    elif task_in_folder_version.is_file() or task_in_folder_version.is_dir():
        new_name = task_in_folder_version.parent / f'{version}_backup'
        task_in_folder_version.rename(new_name)
    task_in_folder_version.symlink_to(aggregation_inputs_folder)


def set_up_shot(context: Context) -> Path():
    '''
    Creates the 'work' folder
    Symlinks 'in' files from 'inputs' folder
    Copies task specific Nuke template

    Returns: Path to the Nuke script
    '''
    _symlink_task_inputs(context=context)
    _create_work_folder_structure(context=context)
    return _copy_task_template_to_task_folder(context=context)

def get_all_existing_task_nuke_scripts(context: Context) -> List:
    ''' Returns all Nuke scripts in the folder that match the pipeline naming convention
    '''
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    pattern = r'v(\d+)'
    # Get all files in the directory ending with ".nk"
    
    nuke_scripts = [f for f in os.listdir(work_folder) if f.endswith('.nk')]

    # Sort files based on version number
    sorted_nuke_scripts = sorted(nuke_scripts, key=lambda x: int(re.search(pattern, x).group(1)), reverse=True)

    return sorted_nuke_scripts

def get_work_directory(context: Context):
    task_path = _get_task_path(context=context)
    work_folder = task_path / "work"
    return work_folder

if __name__=="__main__":
    
    '''
    Three examples tasks to demonstrate how they can be set up
    '''

    in_folder_path = "/Volumes/workspace/shows/pulp00/tasks/vfx_nr_cleanup/inputs/v002/languages/fra/shots/ep01_pt01_0300/PRECOMP/jules_main"
    context = get_context_from_inputs_folder(path=in_folder_path)
    print('===================')
    print(f'{context.dict["task"]}')
    print(f'going to set up shot{context.dict["shot"]}')
    print(in_folder_path)
    print(set_up_shot(context=context))

    in_folder_path = "/Volumes/workspace/shows/pulp00/tasks/vfx_inpaint/inputs/v002/shots/ep01_pt01_0300"
    context = get_context_from_inputs_folder(path=in_folder_path)
    print('===================')
    print(f'{context.dict["task"]}')
    print(f'going to set up shot{context.dict["shot"]}')
    print(in_folder_path)
    print(set_up_shot(context=context))

    in_folder_path = "/Volumes/workspace/shows/pulp00/tasks/vfx_occlusion/inputs/v002/shots/ep01_pt01_0300"
    context = get_context_from_inputs_folder(path=in_folder_path)
    print('===================')
    print(f'{context.dict["task"]}')
    print(f'going to set up shot{context.dict["shot"]}')
    print(in_folder_path)
    print(set_up_shot(context=context))