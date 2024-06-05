import nuke
import nukescripts
import os
import glob
from pathlib import Path


# Constants
FC_TOOLS_MENU = 'FC_Tools'

# Add FC_Tools pp top menu 
FC_TOOLS_TOP_MENU = nuke.menu('Nuke').addMenu(FC_TOOLS_MENU)

# Add FC_Tools pp node menu 
FC_TOOLS_NODE_MENU = nuke.menu('Nodes').addMenu(FC_TOOLS_MENU, icon='flawless-pp.png')


# Add Gizmo Nodes and Icons
gizmos_directory = os.path.join (os.path.dirname(__file__), 'gizmos')
resources_directory = os.path.join (os.path.dirname(__file__), 'resources')
gizmo_dirs = os.listdir(gizmos_directory)
icons_dir = os.path.join(resources_directory, 'icons')

for gizmo_dir in gizmo_dirs:
    full_dir_name = os.path.join(gizmos_directory, gizmo_dir)
    folder_icon_path = os.path.join(icons_dir, f'{gizmo_dir}.png')
    gizmos = glob.glob( os.path.join(full_dir_name, '*.gizmo'))

    for gizmo in gizmos:
        gizmo_name, _ = os.path.splitext(os.path.basename(gizmo))
        FC_TOOLS_NODE_MENU.addCommand(f"{gizmo_dir}/{gizmo_name}", f"nuke.createNode('{gizmo_name}')", icon=f'{os.path.join(full_dir_name, gizmo_name)}.png')
        nuke.pluginAddPath(full_dir_name)


#Hello Message
def get_username():
    try:
        import pwd
        if pwd.getpwuid(os.getuid())[4]:
            username= pwd.getpwuid(os.getuid())[4]
        else:
            username= pwd.getpwuid(os.getuid())[0]
    except:
        username= os.getenv("USERNAME")
    return username

FC_TOOLS_TOP_MENU.addCommand("Hallo Fellow Gremlin",
                              "nuke.message(f'Hello {get_username()}')")


# SET READS/WRITES COLORSPACE TO ACES-CC
FC_TOOLS_TOP_MENU.addCommand("Set Selected Nodes Colorspace to ACES-CC",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('color_timing') for node in nuke.selectedNodes('Read')]")


# SET READS/WRITES COLORSPACE TO ACES-CCT
FC_TOOLS_TOP_MENU.addCommand("Set Selected Nodes Colorspace to ACES-CCT",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('ACES - ACEScct') for node in nuke.selectedNodes('Read')]")


# SET READS/WRITES COLORSPACE TO ACES-Output-sRGB
FC_TOOLS_TOP_MENU.addCommand("Set Selected Nodes Colorspace to Output-sRGB",
                              "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('Output - sRGB') for node in nuke.selectedNodes('Read')]")


# Override Nuke's Alt+Shift+S to version up only the script in the current folder and not any folder names above as well
def script_save_new_version():
    root_name = nuke.toNode("root").name()
    (prefix, old_version) = nukescripts.version_get(root_name, "v")
    
    script_name = Path(root_name).name
    script_dir = Path(root_name).parent
    new_script_name = nukescripts.version_set(script_name, prefix, int(old_version), int(old_version)+1 )
    
    new_root_name = script_dir / new_script_name
    nuke.scriptSaveAs(str(new_root_name))

nuke.menu("Nuke").menu("File").removeItem("Save New Comp Version")
FC_TOOLS_TOP_MENU.addCommand('Save New Version', 'script_save_new_version()', 'alt+shift+s')