"""
Nuke - Flawless Menu overrides
"""
# Project specific imports
import nuke
import nukescripts
import os
#import sys
from pathlib import Path
nuke.pluginAddPath('flwls_vfx_pipeline')
import flwls_vfx_pipeline
import quad_panel
import shot_review_import_ui
import load_gizmos_toolsets
# Constants
FLAWLESS_PP_MENU = 'Flawless'

# Add Flawless pp top menu 
FLAWLESS_PP_TOP_MENU = nuke.menu('Nuke').addMenu(FLAWLESS_PP_MENU)

# Add Flawless pp node menu 
FLAWLESS_PP_NODE_MENU = nuke.menu('Nodes').addMenu(FLAWLESS_PP_MENU, icon='flawless-pp.png')


# Add flawless Nodes
gizmos_directory = os.path.join (os.path.dirname(__file__), 'gizmos')
toolsets_directory = os.path.join (os.path.dirname(__file__), 'toolsets')
load_gizmos_toolsets.load_gizmos_toolsets(gizmos_directory, FLAWLESS_PP_NODE_MENU, ['.gizmo'])
load_gizmos_toolsets.load_gizmos_toolsets(toolsets_directory, FLAWLESS_PP_NODE_MENU, ['.nk'])

# Add FlawlessVFXPipeline
# TODO: (AK) this should happen in a separate menu.py


paneMenu = nuke.menu('Pane')
paneMenu.addCommand("Flwls VFX Pipeline Panel",lambda: flwls_vfx_pipeline.FlwlsVFXPipelinePanelUI.VFXPipelinePanel().addToPane())
nukescripts.registerPanel('VFXPipelinePanelBasic', lambda : flwls_vfx_pipeline.FlwlsVFXPipelinePanel.VFXPipelinePanel().addToPane())

paneMenu.addCommand('QuadPanel', lambda: quad_panel.QuadPanel().addToPane())
nukescripts.registerPanel('QuadPanel', lambda : quad_panel.QuadPanel().addToPane())

# Add flawless pp COMMANDS (top menu)
# Please import in the line to speed up loading time
# Please keep submenu items in alphabetical order :-D
# TODO: (AK) this should happen in a separate menu.py

# Shortcut to VFX Pipeline Panel
FLAWLESS_PP_TOP_MENU.addCommand(
    "VFX Pipeline Panel",
    lambda: setattr(nuke, "VFXPipelinePanelBasic", 
    flwls_vfx_pipeline.FlwlsVFXPipelinePanelUI.VFXPipelinePanel()) or nuke.VFXPipelinePanelBasic.addToPane(),
    index=0  # Add this menu item at the top
)

FLAWLESS_PP_TOP_MENU.addCommand( "Shot Review Import Panel", 
    shot_review_import_ui.add_panel,
    index=1 # 2nd menu item  
)


# SET READS/WRITES COLORSPACE TO ACES-2065-1
FLAWLESS_PP_TOP_MENU.addCommand("Set Selected Nodes Colorspace/ACES-2065-1",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('ACES - ACES2065-1') for node in nuke.selectedNodes('Read')]")

# SET READS/WRITES COLORSPACE TO ACES-CC
FLAWLESS_PP_TOP_MENU.addCommand("Set Selected Nodes Colorspace/ACES-CC",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('color_timing') for node in nuke.selectedNodes('Read')]")

# SET READS/WRITES COLORSPACE TO ACES-CCT
FLAWLESS_PP_TOP_MENU.addCommand("Set Selected Nodes Colorspace/ACES-CCT",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('ACES - ACEScct') for node in nuke.selectedNodes('Read')]")

# SET READS/WRITES COLORSPACE TO ACES-Output-sRGB
FLAWLESS_PP_TOP_MENU.addCommand("Set Selected Nodes Colorspace/Output-sRGB",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('Output - sRGB') for node in nuke.selectedNodes('Read')]")



# Sends selected write node comp to batch render
FLAWLESS_PP_TOP_MENU.addCommand("Send to batch queue",
                                "import python_scripts.local_render_to_batch; python_scripts.local_render_to_batch.main()")


# Override Nuke's Alt+Shift+S to version up only the script in the current folder and not any folder names above as well
def flwls_script_save_new_version():
    root_name = nuke.toNode("root").name()
    (prefix, old_version) = nukescripts.version_get(root_name, "v")
    
    script_name = Path(root_name).name
    script_dir = Path(root_name).parent
    new_script_name = nukescripts.version_set(script_name, prefix, int(old_version), int(old_version)+1 )
    
    new_root_name = script_dir / new_script_name
    nuke.scriptSaveAs(str(new_root_name))

nuke.menu("Nuke").menu("File").removeItem("Save New Comp Version")
FLAWLESS_PP_TOP_MENU.addCommand('Flwls Save New Version', 'flwls_script_save_new_version()', 'alt+shift+s')

