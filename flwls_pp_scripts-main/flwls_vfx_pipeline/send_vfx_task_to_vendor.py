import copy
import csv
import shutil
from typing import Dict, List
from vfx_pipeline import Context, _get_filename_suffix_from_context, _get_task_path, _symlink_task_inputs, _format_version_number_to_string, _get_latest_version_of_file_in_folder, _version_up
from pathlib import Path

def get_list_of_contexts_from_csv(csv_path: Path) -> List[Context]:
    '''
    Searches for column called "ShotLanguageVariant Name"
    Assumes vfx_nr_cleanup task for now!!!
    returns all ShotLanguageVariants in the csv, does not check for status or tags (for now)
    '''
    
    shotlanguagevariants = []
    with csv_path.open('r') as file:
        for line in csv.DictReader(file):
            shotlanguagevariant_name = line["ShotLanguageVariant Name"]
            shotlanguagevariant_data = shotlanguagevariant_name.split('_')
            
            context_dict = {}
            context_dict['workspace_root'] = Path('/Volumes/workspace')
            context_dict['task'] = "vfx_nr_cleanup"
            context_dict['level'] = 'ShotLanguageVariant'        

            context_dict['show'] = shotlanguagevariant_data[0]
            context_dict['episode'] = int(shotlanguagevariant_data[1][2:4])
            context_dict['part'] = int(shotlanguagevariant_data[2][2:4])
            context_dict['shot'] = int(shotlanguagevariant_data[3])
            if context_dict['level'] == 'ShotLanguageVariant':
                context_dict['language'] = shotlanguagevariant_data[4]
                context_dict['variant'] = f"{shotlanguagevariant_data[5]}_{shotlanguagevariant_data[6]}"

            shotlanguagevariants.append(Context(context_dict))

    return shotlanguagevariants

def _add_in_version_to_contexts(context: Context, version_nr: int) -> List[Context]:
    '''
    There's definitely a better way for this, but just something quickly 
    /Volumes/workspace/shows/elsp01/tasks/vfx_nr_cleanup/inputs/v322/languages/zho/shots
    '''
    context_with_versions = copy.deepcopy(context)

    context_with_versions.dict['version'] = version_nr
    
    return context_with_versions

def _create_to_vendor_folder(task_path: Path) -> Path:
    to_vendor_folder = task_path / "to_vendor"
    to_vendor_folder.mkdir(parents=True, exist_ok=True)
    return to_vendor_folder

def prepare_to_vendor_folder(context:Context) -> Path:
    task_path = _get_task_path(context=context)
    return _create_to_vendor_folder(task_path=task_path)

def copy_audio_to_vendor_folder(context:Context, vendor_folder: Path):
    '''
    copies latest published audio from /Volumes/pipeline
    '''
    context = context.dict
    audio_path = Path("/Volumes") / "pipeline" / "shows" / context["show"] / "publish" / "episode" / f'ep{context["episode"]:02}' / "part" / f'pt{context["part"]:02}' / "shot" / f'{context["shot"]:04}' / "language" / context["language"] / "AUDIO"
    audio_versions = list(audio_path.iterdir())
    audio_versions.sort(reverse=True)
    latest_audio_version = audio_versions[0]
    latest_audio_version = latest_audio_version / "audio"
    audio_dst_path = vendor_folder / "audio"
    if audio_dst_path.is_symlink():
        audio_dst_path.unlink()
    elif audio_dst_path.is_file() or audio_dst_path.is_dir():
        new_name = audio_dst_path.parent / f'{audio_dst_path.name}_backup'
        audio_dst_path.rename(new_name)
    audio_dst_path.symlink_to(latest_audio_version)

def copy_denoise_plate_to_vendor_folder(context:Context, vendor_folder: Path):
    '''
    Get's the denoise plate from the 'in' folder and makes a link.
    '''
    denoised_plate_src_folder = _get_task_path(context) / "in" / _format_version_number_to_string(context.dict['version']) / "DENOISED" / "plate"
    denoised_plate_dst_folder = vendor_folder / "denoised_plate"
    if denoised_plate_dst_folder.is_symlink():
        denoised_plate_dst_folder.unlink()
    elif denoised_plate_dst_folder.is_file() or denoised_plate_dst_folder.is_dir():
        new_name = denoised_plate_dst_folder.parent / f'{denoised_plate_dst_folder.name}_backup'
        denoised_plate_dst_folder.rename(new_name)
    denoised_plate_dst_folder.symlink_to(denoised_plate_src_folder)

def copy_neural_render_to_vendor_folder(context:Context, vendor_folder:Path):
    '''
    finds the latest neural render from performance_transfer .snapshot folder
    e.g. /Volumes/workspace/shows/elsp01/episodes/ep01/parts/pt05/shots/0070/languages/zho/variants/actor_main/tasks/performance_transfer/.snapshot/v005/Output/neural_render
    '''
    cntx = context.dict
    neural_render_dst_path = vendor_folder / "neural_render"
    neural_render_src_path = Path('/Volumes/workspace/shows') / cntx['show'] / "episodes" / f"ep{cntx['episode']:02}" / "parts" / f"pt{cntx['part']:02}" / "shots" / f"{cntx['shot']:04}" / "languages" / f"{cntx['language']}" / "variants" / f"{cntx['variant']}" / "tasks" / "performance_transfer" / ".snapshot"
    nr_versions = list(neural_render_src_path.iterdir())
    nr_versions.sort(reverse=True)
    latest_nr_version = nr_versions[0]
    latest_nr_version = latest_nr_version / "Output" / "neural_render"

    if neural_render_dst_path.is_symlink():
        neural_render_dst_path.unlink()
    elif neural_render_dst_path.is_file() or neural_render_dst_path.is_dir():
        new_name = neural_render_dst_path.parent / f'{neural_render_dst_path.name}_backup'
        neural_render_dst_path.rename(new_name)
    neural_render_dst_path.symlink_to(latest_nr_version)

def copy_plate_to_vendor_folder(context:Context, vendor_folder:Path):
    '''
    finds the latest neural render from performance_transfer .snapshot folder
    e.g. /Volumes/workspace/shows/elsp01/episodes/ep01/parts/pt05/shots/0070/languages/zho/variants/actor_main/tasks/performance_transfer/.snapshot/v005/Output/neural_render
    '''
    cntx = context.dict
    plate_dst_path = vendor_folder / "plate"
    plate_src_path = Path('/Volumes/workspace/shows') / cntx['show'] / "episodes" / f"ep{cntx['episode']:02}" / "parts" / f"pt{cntx['part']:02}" / "shots" / f"{cntx['shot']:04}" / "languages" / f"{cntx['language']}" / "variants" / f"{cntx['variant']}" / "tasks" / "precomp" / "PLATE" / "plate"

    if plate_dst_path.is_symlink():
        plate_dst_path.unlink()
    elif plate_dst_path.is_file() or plate_dst_path.is_dir():
        new_name = plate_dst_path.parent / f'{plate_dst_path.name}_backup'
        plate_dst_path.rename(new_name)
    plate_dst_path.symlink_to(plate_src_path)

def copy_nuke_template_to_vendor_folder(context:Context, vendor_folder:Path) -> Path:
    '''
    Copies a vendor nuke script to_vendor folder. Version up if one already there.
    '''
    to_vendor_scripts_folder = vendor_folder / 'scripts'
    to_vendor_scripts_folder.mkdir(exist_ok=True, parents=True)
    filename_suffix = _get_filename_suffix_from_context(context)
    latest_version = _get_latest_version_of_file_in_folder(file_name=filename_suffix, folder_path=to_vendor_scripts_folder)
    version = _version_up(latest_version)
    destination_filepath = to_vendor_scripts_folder / f'{filename_suffix}_{version}.nk'
    
    this_python_script_path = Path(__file__)
    templates_folder = this_python_script_path.parent / 'templates'
    template_path = list(templates_folder.glob(f'**/nrcleanup_to_vendor*'))[0]
    shutil.copy(src=template_path.as_posix(), dst=destination_filepath.as_posix())
    return destination_filepath


def prepare_shot_to_send_to_vendor(csv_path: Path, inputs_version_nr: int):
    contexts_list = get_list_of_contexts_from_csv(csv_path=csv_path)
    for context in contexts_list:
        vendor_folder = prepare_to_vendor_folder(context=context)
        
        context = _add_in_version_to_contexts(context=context, version_nr=inputs_version_nr)
        _symlink_task_inputs(context=context)
        copy_audio_to_vendor_folder(context=context, vendor_folder=vendor_folder)
        copy_denoise_plate_to_vendor_folder(context=context, vendor_folder=vendor_folder)
        copy_neural_render_to_vendor_folder(context=context, vendor_folder=vendor_folder)
        copy_plate_to_vendor_folder(context=context, vendor_folder=vendor_folder)
        saved_nuke_template = copy_nuke_template_to_vendor_folder(context=context, vendor_folder=vendor_folder)
        print(saved_nuke_template)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Path to the csv exported from shotgrid. Looking for the 'ShotLanguageVariant Name' column")
    parser.add_argument("inputs_version", help="number of the aggregation version", type=int)
    args = parser.parse_args()

    prepare_shot_to_send_to_vendor(
        csv_path=Path(args.csv_path),
        inputs_version_nr=args.inputs_version
    )
