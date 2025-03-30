'''
This module describes implements the functions that nodes in templates can use via callbacks
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
    nuke.scriptSaveToTemp(script_backup_path.as_posix())

# exec("""\nfrom datetime import datetime\nimport nuke\nfrom pathlib import Path\nimport re\nfrom typing import Optional\n\ndef _nuke_current_script_name() -> Path:\n    return Path(nuke.scriptName())\n\ndef _find_version(file_name: str) -> Optional[str]:\n    match = re.search(r'_v\\d+', file_name)\n    if match:\n        return match.group()\n    else:\n        return None\n\ndef _get_version_from_nuke_script_name(script_name: Path) -> str:\n    version = _find_version(script_name.stem)\n    if version == None:\n        raise ValueError("Couldn't find version number in current Nuke script name")\n    else:\n        version = version[1:]\n    return version\n\ndef _get_render_version_folder(script_name: Path) -> Path:\n    version = _get_version_from_nuke_script_name(script_name)\n    render_version_folder = script_name.parents[1] / "renders" / version\n    return render_version_folder\n\ndef _get_script_backup_path(script_name: Path) -> Path:\n    current_time = datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S") + "UTC"\n    script_backup_folder = _get_render_version_folder(script_name) / 'script'\n    script_backup_folder.mkdir(exist_ok=True, parents=True)\n    return script_backup_folder / f"{script_name.stem}_backup_{current_time}.nk"\n\ndef save_backup_nuke_script():\n    script_backup_path = _get_script_backup_path(_nuke_current_script_name())\n    nuke.scriptSaveToTemp(script_backup_path.as_posix())\n\nsave_backup_nuke_script()\n""")