import nuke
import nukescripts
import os
import glob
import sys
from pathlib import Path
nuke.pluginAddPath('PyroPython')
import load_pyrobox

# Constants
TP_MENU_NAME = 'TP_PyroBox'
CURRENT_DIR = os.path.dirname(__file__)
PYROBOX_DIR = os.path.join(CURRENT_DIR, 'PyroBox_Tools')
RESOURCES_DIR = os.path.join(CURRENT_DIR, 'Resources')
tp_top_menu = nuke.menu('Nuke').addMenu(TP_MENU_NAME)
tp_node_menu = nuke.menu('Nodes').addMenu(TP_MENU_NAME, icon=os.path.join(RESOURCES_DIR, 'tp_logo.png'))
load_pyrobox.load_gizmos_toolsets(PYROBOX_DIR, tp_node_menu, ['.gizmo', '.nk'], os.path.join(CURRENT_DIR, 'PyroBox_Tools_Icons'))


def get_username():
    """
    Attempts to retrieve the system username. Handles different systems gracefully.
    
    Returns:
        str: The username of the current system user.
    """
    try:
        import pwd
        username = pwd.getpwuid(os.getuid())[4] if pwd.getpwuid(os.getuid())[4] else pwd.getpwuid(os.getuid())[0]
    except:
        username = os.getenv("USERNAME")
    return username


# Add a "Hello" command that greets the user in the top menu
tp_top_menu.addCommand("Hallo Fellow Gremlin",
                       "nuke.message(f'Hello {get_username()}')")


# Define commands to set colorspaces for selected nodes
tp_top_menu.addCommand("Set Selected Nodes Colorspace to ACES-CC",
                       "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('color_timing') for node in nuke.selectedNodes('Read')]")

tp_top_menu.addCommand("Set Selected Nodes Colorspace to ACES-CCT",
                       "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('ACES - ACEScct') for node in nuke.selectedNodes('Read')]")

tp_top_menu.addCommand("Set Selected Nodes Colorspace to Output-sRGB",
                       "nuke.root()['colorManagement'].setValue('OCIO'); [node['colorspace'].setValue('Output - sRGB') for node in nuke.selectedNodes('Read')]")


def script_save_new_version():
    """
    Custom "Save New Version" functionality that increments the version number of the script
    without affecting folder names.
    """
    root_name = nuke.toNode("root").name()  # Get the root node name
    (prefix, old_version) = nukescripts.version_get(root_name, "v")  # Extract version from the root node
    
    # Set new version number
    script_name = Path(root_name).name
    script_dir = Path(root_name).parent
    new_script_name = nukescripts.version_set(script_name, prefix, int(old_version), int(old_version) + 1)
    
    # Save the script with the new version
    new_root_name = script_dir / new_script_name
    nuke.scriptSaveAs(str(new_root_name))


# Override the default "Save New Comp Version" and add a custom "Save New Version" with a keyboard shortcut
nuke.menu("Nuke").menu("File").removeItem("Save New Comp Version")  # Remove the default behavior
tp_top_menu.addCommand('Save New Version', 'script_save_new_version()', 'alt+shift+s')  # Add the new custom version command
