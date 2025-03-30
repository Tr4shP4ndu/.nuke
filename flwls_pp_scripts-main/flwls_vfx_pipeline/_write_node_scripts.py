'''
This module contains Python scripts for to be used in callbacks in Write nodes
When copying these into the callbacks convert them to oneliners
'''


'''
beforeRender for main .exr render for VFX task
Creates the top level folder for the render
Takes a snapshot of nuke script and saves it into script folder
'''

from datetime import datetime
from pathlib import Path
import re

script_path = Path(nuke.scriptName())
script_dir = script_path.parent
script_name = script_path.stem
script_name_without_version = re.sub(f'_v\d+', '', script_name)
version = nukescripts.version_get(script_path.as_posix(),'v')

render_dir = script_dir / f"{script_name_without_version}_renders" / f"{''.join(version)}"

try:
    render_dir.mkdir(parents=True, exist_ok=False)
except FileExistsError:
    if nuke.ask(f"{render_dir} already exists. Overwrite?"):
        pass
    else:
        raise FileExistsError(f"Stopping to avoid overwriting render: {render_dir}. Try saving the script with a higher version number first.")
script_snapshot_path = render_dir / 'script'
script_snapshot_path.mkdir(exist_ok=True)
current_time = datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S") + "UTC"
script_snapshot_path = script_snapshot_path / f"{script_name}_snapshot_{current_time}.nk"
nuke.scriptSaveToTemp(script_snapshot_path.as_posix())

'''
beforeRender for main .exr render for VFX task
Creates the top level folder for the render
Takes a snapshot of nuke script and saves it into script folder
oneliner converted
'''
exec("""\nfrom datetime import datetime\nfrom pathlib import Path\nimport re\n\nscript_path = Path(nuke.scriptName())\nscript_dir = script_path.parent\nscript_name = script_path.stem\nscript_name_without_version = re.sub(f'_v\\d+', '', script_name)\nversion = nukescripts.version_get(script_path.as_posix(),'v')\n\nrender_dir = script_dir / f"{script_name_without_version}_renders" / f"{''.join(version)}"\n\ntry:\n    render_dir.mkdir(parents=True, exist_ok=False)\nexcept FileExistsError:\n    if nuke.ask(f"{render_dir} already exists. Overwrite?"):\n        pass\n    else:\n        raise FileExistsError(f"Stopping to avoid overwriting render: {render_dir}. Try saving the script with a higher version number first.")\nscript_snapshot_path = render_dir / 'script'\nscript_snapshot_path.mkdir(exist_ok=True)\ncurrent_time = datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S") + "UTC"\nscript_snapshot_path = script_snapshot_path / f"{script_name}_snapshot_{current_time}.nk"\nnuke.scriptSaveToTemp(script_snapshot_path.as_posix())\n""")


'''
onCreate for main .mov render for VFX task
'''

from pathlib import Path
import re
import nuke
import os

def build_lang_context(script_name):
    split_name = os.path.basename(script_name).split("_")

    context = {}

    context["show"] = split_name[0]
    context["episode"] = split_name[1]
    context["part"] = split_name[2]
    context["shot"] = split_name[3]
    context["language"] = split_name[4]

    return context

def get_highest_folder_name(directory):
    folder_names = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    if not folder_names:
        return None
    highest_folder = max(folder_names, key=lambda x: int(x[1:]))
    return highest_folder

context = build_lang_context((nuke.root().name()))

audio_tree = str(Path("/Volumes") / "pipeline" / "shows" / context["show"] / "publish" / "episode" / context["episode"] / "part" / context["part"] / "shot" / context["shot"] / "language" / context["language"] / "AUDIO")
audio_file_tree = str(Path(audio_tree) / get_highest_folder_name(audio_tree) / "audio")
audio_file = os.listdir(audio_file_tree)
latest_shot_lang_audio = str(Path(audio_file_tree) / audio_file[0])

nuke.thisNode().knob("mov64_audiofile").setValue(latest_shot_lang_audio)


'''
One liner converted.
'''                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
exec("""\nfrom pathlib import Path\nimport re\nimport nuke\nimport os\n\ndef build_lang_context(script_name):\n    split_name = os.path.basename(script_name).split("_")\n\n    context = {}\n\n    context["show"] = split_name[0]\n    context["episode"] = split_name[1]\n    context["part"] = split_name[2]\n    context["shot"] = split_name[3]\n    context["language"] = split_name[4]\n\n    return context\n\ndef get_highest_folder_name(directory):\n    folder_names = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]\n    if not folder_names:\n        return None\n    highest_folder = max(folder_names, key=lambda x: int(x[1:]))\n    return highest_folder\n\ncontext = build_lang_context((nuke.root().name()))\n\naudio_tree = str(Path("/Volumes") / "pipeline" / "shows" / context["show"] / "publish" / "episode" / context["episode"] / "part" / context["part"] / "shot" / context["shot"] / "language" / context["language"] / "AUDIO")\naudio_file_tree = str(Path(audio_tree) / get_highest_folder_name(audio_tree) / "audio")\naudio_file = os.listdir(audio_file_tree)\nlatest_shot_lang_audio = str(Path(audio_file_tree) / audio_file[0])\n\nnuke.thisNode().knob("mov64_audiofile").setValue(latest_shot_lang_audio)\n""")



'''
Write node in contextual workspace_v001
'''

from datetime import datetime
import nuke
from pathlib import Path
import re
from typing import Optional

def _nuke_current_script_name() -> Path:
    return Path(nuke.scriptName())

def _find_version(file_name: str) -> Optional[str]:
    match = re.search(r'_v\d+', file_name)
    if match:
        return match.group()
    else:
        return None

def _get_version_from_nuke_script_name(script_name: Path) -> str:
    version = _find_version(script_name.stem)
    if version == None:
        raise ValueError("Couldn't find version number in current Nuke script name")
    else:
        version = version[1:]
    return version

def _get_render_version_folder(script_name: Path) -> Path:
    version = _get_version_from_nuke_script_name(script_name)
    render_version_folder = script_name.parents[1] / "renders" / version
    return render_version_folder

def _get_script_backup_path(script_name: Path) -> Path:
    current_time = datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S") + "UTC"
    script_backup_folder = _get_render_version_folder(script_name) / 'script'
    script_backup_folder.mkdir(exist_ok=True, parents=True)
    return script_backup_folder / f"{script_name.stem}_backup_{current_time}.nk"

def save_backup_nuke_script():
    script_backup_path = _get_script_backup_path(_nuke_current_script_name())
    if not script_backup_folder.is_file():
        nuke.scriptSaveToTemp(script_backup_path.as_posix())

# exec("""\nfrom datetime import datetime\nimport nuke\nfrom pathlib import Path\nimport re\nfrom typing import Optional\n\ndef _nuke_current_script_name() -> Path:\n    return Path(nuke.scriptName())\n\ndef _find_version(file_name: str) -> Optional[str]:\n    match = re.search(r'_v\\d+', file_name)\n    if match:\n        return match.group()\n    else:\n        return None\n\ndef _get_version_from_nuke_script_name(script_name: Path) -> str:\n    version = _find_version(script_name.stem)\n    if version == None:\n        raise ValueError("Couldn't find version number in current Nuke script name")\n    else:\n        version = version[1:]\n    return version\n\ndef _get_render_version_folder(script_name: Path) -> Path:\n    version = _get_version_from_nuke_script_name(script_name)\n    render_version_folder = script_name.parents[1] / "renders" / version\n    return render_version_folder\n\ndef _get_script_backup_path(script_name: Path) -> Path:\n    current_time = datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S") + "UTC"\n    script_backup_folder = _get_render_version_folder(script_name) / 'script'\n    script_backup_folder.mkdir(exist_ok=True, parents=True)\n    return script_backup_folder / f"{script_name.stem}_backup_{current_time}.nk"\n\ndef save_backup_nuke_script():\n    script_backup_path = _get_script_backup_path(_nuke_current_script_name())\n    nuke.scriptSaveToTemp(script_backup_path.as_posix())\n\nsave_backup_nuke_script()\n""")
