import nuke
import os

def load_gizmos_toolsets(root_path = str, menu = nuke.Menu, extensions = list):
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
                file_path = os.path.join(root, file).replace(os.sep, '/')
                file_name = os.path.splitext(file)[0]
                ext = os.path.splitext(file)[1]  # Extract the extension
                # Define the action based on file extension
                action = (lambda fp=file_path, e=ext: nuke.createNode(fp) if e == '.gizmo' else nuke.nodePaste(fp))
                sub_menu.addCommand(file_name, action)

if __name__ == '__main__':
    load_gizmos_toolsets(root_path, menu, extensions)
