'''
Imports
'''

import shutil
from pathlib import Path
import re

'''
Constants
'''
NUKE_EXTENSION = '.nk'
SCRIPT_VERSION_PREFIX = 'v'
WORKSPACE_VERSION_PREFIX = 'ws'
SCRIPTS_DIR_NAME = 'scripts'
WORK_DIR_NAME = 'work'
BASEVERSION = '001'


def migrate_nuke_script_to_target_workspace(source_nuke_script_path:str, target_workspace_version:str) -> str:

    '''
When working inside a Flawless VFX workspace, a user can use the 'migrate_nuke_script_to_target_workspace' function, to migrate 
their nuke script from a source workspace, to a target workspace (within the same context). 

The function takes two arguments:
        script_to_migrate_path
            A str of the Nuke Script path, that the user intends to migrate.

        target_workspace_version
            The target workspace version, the user would like to migrate their script into. 

    Both arguments are str type, as this is all Nuke can deal with. The Function also returns a str of the filepath of the migrated script back to nuke.
    This script doesn't have to be used in tandem with Nuke itself. 
    '''

    source_nuke_script_path = Path(source_nuke_script_path)

    source_workspace_directory = source_nuke_script_path.parents[1]

    task_context = _get_task_context(current_working_directory=source_workspace_directory)

    target_workspace_directory = _get_target_workspace_work_folder_path(source_nuke_script_path = source_nuke_script_path,
                                                                                      task_context=task_context, 
                                                                                      target_workspace_version = target_workspace_version)

    
    if  Path.exists(target_workspace_directory):
        
        target_script_version_number = _get_latest_version_number_for_context_in_target_workspace(target_workspace_directory = target_workspace_directory, 
                                                                                    task_context = task_context)        
    else:
        target_workspace_directory.mkdir(parents=True, exist_ok=True)
        target_script_version_number = BASEVERSION


    migrated_script_path = _copy_script_into_target_directory(target_workspace_directory = target_workspace_directory, 
                                                                            source_nuke_script_path = source_nuke_script_path, 
                                                                            target_workspace_version = target_workspace_version, 
                                                                            task_context = task_context,
                                                                            target_script_version_number = target_script_version_number)
    
    
    return str(migrated_script_path)

def _copy_script_into_target_directory(target_workspace_directory: Path, source_nuke_script_path: Path, target_workspace_version: str, task_context: str, target_script_version_number: str):

    workspace_version_prefix = target_workspace_version.replace(SCRIPT_VERSION_PREFIX, WORKSPACE_VERSION_PREFIX)
    migrated_script_name = f'{task_context}_{workspace_version_prefix}_{SCRIPT_VERSION_PREFIX}{target_script_version_number}{NUKE_EXTENSION}'
    migrated_script_path_in_target_dir = Path(target_workspace_directory, migrated_script_name)
    shutil.copy2(source_nuke_script_path, migrated_script_path_in_target_dir)
    return migrated_script_path_in_target_dir

def _get_latest_version_number_for_context_in_target_workspace(target_workspace_directory: Path, task_context: str) -> str:
    
    nuke_file_names = [file.name for file in target_workspace_directory.glob(f'*{NUKE_EXTENSION}') ]

    nr_cleanup_nuke_scripts = [f for f in nuke_file_names if f.startswith(task_context)]
    version_numbers = [int(re.findall(r'\d+', f)[-1]) for f in nr_cleanup_nuke_scripts]
    highest_version_number = max(version_numbers) if version_numbers else 0

    new_version_number = str(highest_version_number + 1).zfill(3)

    return new_version_number

def _get_task_context(current_working_directory: Path) -> str:

    '''
    Task context appears as following:
    show00_ep_pt_shot_lang_varient_task
    or
    pulp00_ep01_pt02_0070_fra_jules_main_vfx_nr_cleanup
    Gets context from the grandparent DIR of the source nuke script
    '''

    task_context = Path(current_working_directory)
    return task_context.name

def _get_target_workspace_work_folder_path(source_nuke_script_path: Path, task_context: str, target_workspace_version: str) -> Path:

    task_directory = source_nuke_script_path.parents[4]
    migrated_script_dir = Path(task_directory, target_workspace_version, WORK_DIR_NAME, task_context, SCRIPTS_DIR_NAME)

    return migrated_script_dir

if __name__=="__main__":

    nuke_script_path = ''
    target_workspace_version = ''
    migrated_script = migrate_nuke_script_to_target_workspace(source_nuke_script_path = nuke_script_path, 
                       target_workspace_version = target_workspace_version)
    print(migrated_script)