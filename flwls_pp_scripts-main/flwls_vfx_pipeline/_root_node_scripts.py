'''
This module contains Python scripts for to be used in callbacks in nuke root
When copying these into the callbacks convert them to oneliners
'''


'''
onScriptLoad
Fills task input Read nodes
'''

from pathlib import Path
import re
import nuke

denoise_plate = nuke.toNode('DNS_PLATE')

def _get_context_from_script_name(script_name: str):
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
        return context_dict
    except TypeError as e:
        raise TypeError(f'{e}\nError when extracting context from script name. Does the script name contain all the context')

def _get_task_path(context: dict) -> Path:
    cntx = context
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

def _latest_in_version(task_path: Path):
    in_path = task_path / 'in'
    folders = [f for f in in_path.glob('v[0-9][0-9][0-9]') if f.is_dir()]
    folders.sort(reverse=True)
    return folders[0]

def _get_sequence_path_in_fromUserText_format(sequence_folder: Path, extension: str):
    filepaths = list(sequence_folder.glob(f'*{extension}'))
    filepaths.sort()
    start_frame_path = filepaths[0]
    first_frame_number = int(re.search(r'\.([0-9]{6})', start_frame_path.stem).group(1))
    start_frame_name = re.sub(r'\.([0-9]{6})', '.######', start_frame_path.name)
    return f'{start_frame_path.parent / start_frame_name} {first_frame_number}-{first_frame_number + len(filepaths) - 1}'

def _get_variant_from_scriptname():
    return "_".join(Path(nuke.scriptName()).stem.split('_')[5:7])

if denoise_plate:
    if denoise_plate.knob('file').value() == "":
        script_name = Path(nuke.root().name()).stem
        context = _get_context_from_script_name(script_name)
        task_path = _get_task_path(context)
        denoise_plate_folder = _latest_in_version(task_path) / 'DENOISED' / 'plate'
        denoise_plate_seq = _get_sequence_path_in_fromUserText_format(sequence_folder=denoise_plate_folder, extension='exr')
        denoise_plate.knob('file').fromUserText(denoise_plate_seq)
        denoise_plate['frame'].setValue('1')
        denoise_plate['frame_mode'].setValue('start_at')
        nuke.root().knob('first_frame').setValue(denoise_plate.firstFrame())
        nuke.root().knob('last_frame').setValue(denoise_plate.lastFrame())
        nuke.root().knob('lock_range').setValue(True)
        nuke.root().knob('fps').setValue(denoise_plate.metadata("input/frame_rate"))
        nuke.root().knob('format').setValue(denoise_plate.knob('format').value())

precompNodeName = 'PRECOMP'
precompExists = bool([n for n in nuke.allNodes() if n.name() == precompNodeName])
if not precompExists:
    pass
else:
    precomp_plate = nuke.toNode('PRECOMP')
    if precomp_plate.knob('file').value() == "":
        script_name = Path(nuke.root().name()).stem
        context = _get_context_from_script_name(script_name)
        task_path = _get_task_path(context)
        precomp_plate_folder = _latest_in_version(task_path) / 'PRECOMP' / _get_variant_from_scriptname() / 'PRECOMP' / 'precomp'
        precomp_plate_seq = _get_sequence_path_in_fromUserText_format(sequence_folder=precomp_plate_folder, extension='exr')
        precomp_plate.knob('file').fromUserText(precomp_plate_seq)
        precomp_plate['frame'].setValue('1')
        precomp_plate['frame_mode'].setValue('start_at')




'''
onScriptLoad
Fills task input Read nodes
ONELINER
'''

exec("""\n'''\nThis module contains Python scripts for to be used in callbacks in nuke root\nWhen copying these into the callbacks convert them to oneliners\n'''\n\n\n'''\nonScriptLoad\nFills task input Read nodes\n'''\n\nfrom pathlib import Path\nimport re\nimport nuke\n\ndenoise_plate = nuke.toNode('DNS_PLATE')\n\ndef _get_context_from_script_name(script_name: str):\n    try:\n        script_name_parts = script_name.split('_')\n        context_dict = {}\n        context_dict['workspace_root'] = Path('/Volumes/workspace')\n        if "nr" in script_name_parts:\n            if "cleanup" in script_name_parts:\n                context_dict['task'] = "vfx_nr_cleanup"\n        elif "inpaint" in script_name_parts:\n            context_dict['task'] = "vfx_inpaint"\n        elif "occlusion" in script_name_parts:\n            context_dict['task'] = "vfx_occlusion"\n        if context_dict['task'] in ('vfx_occlusion', 'vfx_inpaint'):\n            context_dict['level'] = 'Shot'\n        elif context_dict['task'] == 'vfx_nr_cleanup':\n            context_dict['level'] = 'ShotLanguageVariant'\n        context_dict['show'] = script_name_parts[0]\n        context_dict['episode'] = int(script_name_parts[1][2:4])\n        context_dict['part'] = int(script_name_parts[2][2:4])\n        context_dict['shot'] = int(script_name_parts[3])\n        if context_dict['level'] == 'ShotLanguageVariant':\n            context_dict['language'] = script_name_parts[4]\n            context_dict['variant'] = f"{script_name_parts[5]}_{script_name_parts[6]}"\n        return context_dict\n    except TypeError as e:\n        raise TypeError(f'{e}\\nError when extracting context from script name. Does the script name contain all the context')\n\ndef _get_task_path(context: dict) -> Path:\n    cntx = context\n    shot_path = cntx['workspace_root'] / 'shows' / cntx['show'] / 'episodes' / f"ep{cntx['episode']:02d}" / 'parts' / f"pt{cntx['part']:02d}" / 'shots' / f"{cntx['shot']:04d}"\n    task_path = None\n    if cntx['level'] == 'Shot':\n        task = None\n        if cntx['task'] == 'vfx_inpaint':\n            task = 'vfx_inpainting'\n        elif cntx['task'] == 'vfx_occlusion':\n            task = 'vfx_occlusions'\n        if task:\n            task_path = shot_path / 'tasks' / task\n    elif cntx['level'] == 'ShotLanguageVariant':\n        task_path = shot_path / 'languages' / cntx['language'] / 'variants' / cntx['variant'] / 'tasks' / cntx['task']\n\n    if not task_path:\n        raise ValueError("task_path must not be None")\n    return task_path\n\ndef _latest_in_version(task_path: Path):\n    in_path = task_path / 'in'\n    folders = [f for f in in_path.glob('v[0-9][0-9][0-9]') if f.is_dir()]\n    folders.sort(reverse=True)\n    return folders[0]\n\ndef _get_sequence_path_in_fromUserText_format(sequence_folder: Path, extension: str):\n    filepaths = list(sequence_folder.glob(f'*{extension}'))\n    filepaths.sort()\n    start_frame_path = filepaths[0]\n    first_frame_number = int(re.search(r'\\.([0-9]{6})', start_frame_path.stem).group(1))\n    start_frame_name = re.sub(r'\\.([0-9]{6})', '.######', start_frame_path.name)\n    return f'{start_frame_path.parent / start_frame_name} {first_frame_number}-{first_frame_number + len(filepaths) - 1}'\n\ndef _get_variant_from_scriptname():\n    return "_".join(Path(nuke.scriptName()).stem.split('_')[5:7])\n\nif denoise_plate:\n    if denoise_plate.knob('file').value() == "":\n        script_name = Path(nuke.root().name()).stem\n        context = _get_context_from_script_name(script_name)\n        task_path = _get_task_path(context)\n        denoise_plate_folder = _latest_in_version(task_path) / 'DENOISED' / 'plate'\n        denoise_plate_seq = _get_sequence_path_in_fromUserText_format(sequence_folder=denoise_plate_folder, extension='exr')\n        denoise_plate.knob('file').fromUserText(denoise_plate_seq)\n        denoise_plate['frame'].setValue('1')\n        denoise_plate['frame_mode'].setValue('start_at')\n        nuke.root().knob('first_frame').setValue(denoise_plate.firstFrame())\n        nuke.root().knob('last_frame').setValue(denoise_plate.lastFrame())\n        nuke.root().knob('lock_range').setValue(True)\n        nuke.root().knob('fps').setValue(denoise_plate.metadata("input/frame_rate"))\n        nuke.root().knob('format').setValue(denoise_plate.knob('format').value())\n\nprecompNodeName = 'PRECOMP'\nprecompExists = bool([n for n in nuke.allNodes() if n.name() == precompNodeName])\nif not precompExists:\n    pass\nelse:\n    precomp_plate = nuke.toNode('PRECOMP')\n    if precomp_plate.knob('file').value() == "":\n        script_name = Path(nuke.root().name()).stem\n        context = _get_context_from_script_name(script_name)\n        task_path = _get_task_path(context)\n        precomp_plate_folder = _latest_in_version(task_path) / 'PRECOMP' / _get_variant_from_scriptname() / 'PRECOMP' / 'precomp'\n        precomp_plate_seq = _get_sequence_path_in_fromUserText_format(sequence_folder=precomp_plate_folder, extension='exr')\n        precomp_plate.knob('file').fromUserText(precomp_plate_seq)\n        precomp_plate['frame'].setValue('1')\n        precomp_plate['frame_mode'].setValue('start_at')\n\n\n\n\n\n'''\nonScriptLoad\nFills task input Read nodes\nONELINER\n'''\n""")