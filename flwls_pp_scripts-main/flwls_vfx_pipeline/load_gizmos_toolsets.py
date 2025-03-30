import nuke
import os

def load_gizmos_toolsets(root_path, menu, extensions):
    """
    Recursively loads files into submenus based on folder structure.
    
    Args:
    root_path (str): The main folder where the search starts.
    menu (nuke.Menu): The parent menu to add submenus and commands.
    extensions (list): List of file extensions to include.
    """
    for root, dirs, files in os.walk(root_path):
        dirs.sort()
        files.sort()
        
        relative_path = os.path.relpath(root, root_path)
        sub_menu = menu

        # Create submenu for subfolders
        if relative_path != ".":
            sub_menu = menu.addMenu(relative_path.replace(os.sep, '/'))

        # Add files to the submenu
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_path_norm = os.path.normpath(file_path)
                file_name = os.path.splitext(file)[0]
                
                # Add gizmo and .nk files to the menu
                if file.endswith('.gizmo'):
                    sub_menu.addCommand(file_name, lambda fp=file_path_norm: nuke.createNode(fp))
                elif file.endswith('.nk'):
                    sub_menu.addCommand(file_name, lambda fp=file_path_norm: nuke.nodePaste(fp))

if __name__ == '__main__':
    load_gizmos_toolsets(root_path, menu, extensions)
