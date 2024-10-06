import nuke
import os

def load_gizmos_toolsets(root_path, menu, extensions, icons_dir):
    for root, dirs, files in os.walk(root_path):
        dirs.sort()
        files.sort()

        relative_path = os.path.relpath(root, root_path)
        sub_menu = menu

        if relative_path != ".":
            sub_menu = menu.addMenu(relative_path.replace(os.sep, '/'))

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]

                icon_path = os.path.join(icons_dir, f"{file_name}.png")
                icon = icon_path if os.path.exists(icon_path) else None

                try:
                    if file.endswith('.gizmo'):
                        # Normalize the file path for Nuke
                        normalized_path = os.path.normpath(file_path)
                        print(f"Loading Gizmo: {file_name} from {normalized_path}")
                        sub_menu.addCommand(file_name, f"nuke.createNode('{file_name}')", icon=icon)
                    elif file.endswith('.nk'):
                        # Normalize the file path for Nuke
                        normalized_path = os.path.normpath(file_path)
                        print(f"Loading Node Graph: {file_name} from {normalized_path}")
                        sub_menu.addCommand(file_name, f"nuke.nodePaste('{normalized_path}')", icon=icon)
                except Exception as e:
                    print(f"Failed to create node '{file_name}': {e}")

if __name__ == '__main__':
    load_gizmos_toolsets(root_path, menu, extensions, icons_dir)
