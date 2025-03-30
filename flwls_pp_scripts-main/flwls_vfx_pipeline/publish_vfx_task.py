import json
from vfx_pipeline import Context, _get_task_path, _get_subfolder_name
from pathlib import Path
import shutil
import subprocess

def publish_vfx_task(render_path: Path):
    '''
    checks publish is valid (we'll add this later)
    uses Jesse M's tool to set-up workspace and create 'output' folder - DONE
    moves the task output exr render from render_path to output folder - DONE
    executes publishing
    reports job starting (maybe) 
    also moves ancilliary files to output folder for safekeeping, such as Nuke script and preview_mov - DONE
    creates symlinks in the original 'work' folder in render_path - DONE
    '''
    context = _get_context_from_render_path(path=render_path)
    _create_publish_workspace(context=context)
    publish_path = _get_publish_path(_get_task_path(context=context))
    _move_render_to_publish_directory(context=context, render_path=render_path, publish_path=publish_path)
    _symlink_publish_back_to_render_directory(render_path=render_path, publish_path=publish_path)
    _execute_publish(publish_path=publish_path)

def _get_context_from_render_path(path: Path):
    '''
    TODO: Very similar functionality exists in vfx_pipeline.py Maybe there are better ways to get the context
    '''
    exr_path = Path(path) / 'exr'
    try:
        render_name_parts = list(exr_path.iterdir())
        render_name_parts = render_name_parts[0].name
        render_name_parts = render_name_parts.split('_')
        context_dict = {}
        context_dict['workspace_root'] = Path('/Volumes/workspace')
        if "nr" in render_name_parts:
            if "cleanup" in render_name_parts:
                context_dict['task'] = "vfx_nr_cleanup"
        elif "inpaint" in render_name_parts:
            context_dict['task'] = "vfx_inpaint"
        elif "occlusion" in render_name_parts:
            context_dict['task'] = "vfx_occlusion"
        if context_dict['task'] in ('vfx_occlusion', 'vfx_inpaint'):
            context_dict['level'] = 'Shot'
        elif context_dict['task'] == 'vfx_nr_cleanup':
            context_dict['level'] = 'ShotLanguageVariant'        
        context_dict['show'] = render_name_parts[0]
        context_dict['episode'] = int(render_name_parts[1][2:4])
        context_dict['part'] = int(render_name_parts[2][2:4])
        context_dict['shot'] = int(render_name_parts[3])
        if context_dict['level'] == 'ShotLanguageVariant':
            context_dict['language'] = render_name_parts[4]
            context_dict['variant'] = f"{render_name_parts[5]}_{render_name_parts[6]}"
            
        return Context(dict=context_dict)
    except TypeError as e:
        raise TypeError(f'Error when extracting context from filepath. Make sure that the exr renders exist')


def _create_publish_workspace(context:Context) -> Path:
    '''
    Uses Jesse M's tool in his virtual environment to create the output folder and data_map.json
    Returns path to the data_map.json as dict
    note task names are modded to match Jesse M ones
    '''
    cntx = context.dict
    task = None
    command = "source /opt/truesync/flwls-prepare-workspace/bin/activate; workspace-create"
    shot_context = f"ep{cntx['episode']:02d}/pt{cntx['part']:02d}/{cntx['shot']:04d}"
    if cntx['level'] == 'Shot':
        if cntx['task'] == 'vfx_inpaint':
            task = 'vfx_inpainting'
        elif cntx['task'] == 'vfx_occlusion':
            task = 'vfx_occlusions'
        command = f"{command} {cntx['show']} {task} {shot_context}"
    elif cntx['level'] == 'ShotLanguageVariant':
        if cntx['task'] == 'vfx_nr_cleanup':
            task = 'vfx_nr_cleanup'
            command = f"{command} {cntx['show']} {task} {shot_context}/{cntx['language']}/{cntx['variant']}"
    if task:
      subprocess.run(command, shell=True)
    else:
        raise ValueError("Couldn't set task in context when attempting to create publish workspace")
    
def _execute_publish(publish_path:Path):
    '''
    Uses Jesse M's tool in his virtual environment to execute the actual publish
    Picks the latest DATA_MAP .json and uses that.
    '''
    
    task = publish_path.parents[2].name
    data_maps = list(publish_path.parents[1].joinpath("DATA_MAP").glob("**/data_map.json"))
    data_maps.sort(reverse=True)
    if len(data_maps) > 0:
        command = f"source /opt/truesync/flwls-prepare-workspace/bin/activate; workspace-publish {task} {data_maps[0]}"
        subprocess.run(command, shell=True)
    else:
        raise ValueError("Couldn't find a data_map.json for publishing {publish_path}")


def _get_publish_path(task_path:Path) -> Path:
    task = task_path.name
    data_type = None
    if task == 'vfx_occlusions':
        data_type = 'OCCLUSIONS'
    elif task == 'vfx_inpainting':
        data_type = 'INPAINTING' ### THIS ONE IS BUGGY AT THE MOMENT!!!! It makes OCCLUSION folder instead, I've notified Jesse M
    elif  task == 'vfx_nr_cleanup':
        data_type = 'NR_CLEANUP'

    data_map_folder = task_path / 'output' / 'DATA_MAP'
    latest_version_folder = _latest_version_folder(data_map_folder)
    data_map_json_file = latest_version_folder / "data_map" / "data_map.json"
    with open(data_map_json_file, 'r') as f:
        data = json.load(f)
    return Path(data[data_type])
    


def _latest_version_folder(folder_path: Path):
    '''
    find a folder in the form v001, v002, v003.. and pick the latest
    '''
    folders = [f for f in folder_path.glob('v[0-9][0-9][0-9]') if f.is_dir()]
    folders.sort(reverse=True)
    return folders[0]

def _move_render_to_publish_directory(context:Context, render_path:Path, publish_path:Path):
    '''
    Takes files and subfolders from the render directory and moves them to the publish directory
    '''

    for src_path in render_path.iterdir():
        if src_path.name == "exr":
                if context.dict['task'] == 'vfx_occlusion':
                    dst_path = publish_path / 'occlusions'
                if context.dict['task'] == 'vfx_inpaint':
                    dst_path = publish_path / 'inpainting'
                if context.dict['task'] == 'vfx_nr_cleanup':
                    dst_path = publish_path / 'nr_cleanup'
        else:
            dst_path = publish_path / src_path.name

        # Move the item to the destination folder
        shutil.move(str(src_path), str(dst_path))

def _symlink_publish_back_to_render_directory(render_path=Path, publish_path=Path):
    '''
    For each folder in publish path, makes a directory in render_path and symlinks the contents
    '''

    for src_path in publish_path.iterdir():
        if src_path.is_dir():
            if src_path.name in ('occlusions', 'inpainting', 'nr_cleanup'):
                dst_folder_path = render_path / 'exr'
            else:
                dst_folder_path = render_path / src_path.name
            dst_folder_path.mkdir()
            for src_file in src_path.iterdir():
                dst_symlink = dst_folder_path / src_file.name
                dst_symlink.symlink_to(src_file)


if __name__=="__main__":
    
    render_path = Path('/Volumes/workspace/shows/pulp00/episodes/ep01/parts/pt01/shots/0300/tasks/vfx_inpainting/work/pulp00_ep01_pt01_0300_vfx_inpaint_renders/v012/')
    print(_get_context_from_render_path(render_path))
    # publish_vfx_task(render_path=render_path)