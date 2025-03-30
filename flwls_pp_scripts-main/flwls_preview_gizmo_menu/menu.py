import os
import nuke
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "flwls_vfx_pipeline"))
import load_gizmos_toolsets

nuke.pluginAddPath('./icons')
preview_directory = "/Volumes/shared/vfx/flwls_preview_tools_menu"
preview_menu = nuke.menu('Nodes').addMenu('flwls_preview_tools', icon='flawless-gm.png')
preview_menu.addCommand(name='Preview Tools Dir', command=f'nuke.message("The Flawless Gizmo Preview directory is located here: {preview_directory}")')
load_gizmos_toolsets.load_gizmos_toolsets(preview_directory, preview_menu, ['.gizmo', '.nk'])
