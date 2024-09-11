import nuke
import nukescripts
import os
from pathlib import Path

# Constants
tp_tools_menu = 'FC_Tools'  # Name of the top menu that will be added to Nuke
gizmos_directory = os.path.join(os.path.dirname(__file__), 'gizmos')  # Directory where Gizmos are stored
resources_directory = os.path.join(os.path.dirname(__file__), 'resources')  # Directory where resources (icons) are stored
icons_dir = os.path.join(resources_directory, 'icons')  # Directory for Gizmo icons

# Add FC_Tools to the top menu bar in Nuke
tp_top_menu = nuke.menu('Nuke').addMenu(tp_tools_menu)

# Add FC_Tools to the node menu in Nuke (with an icon)
tp_node_menu = nuke.menu('Nodes').addMenu(tp_tools_menu, icon='tp_logo.png')


def add_gizmos_from_dir(directory, menu):
    """
    Recursively traverses a directory structure, creating corresponding Nuke submenus
    and adding .gizmo files as nodes in the correct hierarchy.
    """
    for entry in os.scandir(directory):  # Use os.scandir for slightly better performance and readability
        full_path = entry.path
        
        # If the entry is a directory, create a submenu and recurse into it
        if entry.is_dir():
            sub_menu = menu.addMenu(entry.name, icon=os.path.join(icons_dir, f'{entry.name}.png'))  # Add submenu
            add_gizmos_from_dir(full_path, sub_menu)  # Recursive call for subdirectories
        
        # If the entry is a .gizmo file, add it as a command in the current menu
        if entry.is_file() and entry.name.endswith('.gizmo'):
            gizmo_name, _ = os.path.splitext(entry.name)
            icon_path = os.path.join(directory, f'{gizmo_name}.png')  # Optional icon for the gizmo
            command = f"nuke.createNode('{gizmo_name}')"  # Command to create the gizmo node in Nuke
            menu.addCommand(gizmo_name, command, icon=icon_path)  # Add gizmo to the menu
            nuke.pluginAddPath(directory)  # Ensure the directory is added to Nuke's plugin path


# Initialize the process by adding gizmos from the specified directory to the menu
add_gizmos_from_dir(gizmos_directory, tp_node_menu)


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
