import nuke, os, glob

def load_gizmos(node_menu, dir_of_gizmo_dirs):
    gizmo_dirs = os.listdir(dir_of_gizmo_dirs)

    # todo: maybe use 
    # for root, dirs, files in os.walk( to get gizmos on the top level/sub levels)
    for gizmo_dir in gizmo_dirs:
        full_dir_name = os.path.join(dir_of_gizmo_dirs, gizmo_dir)
        gizmos = glob.glob( os.path.join(full_dir_name, '*.gizmo'))

        for gizmo in gizmos:
            gizmo_name, _ = os.path.splitext(os.path.basename(gizmo))
            node_menu.addCommand(f"{gizmo_dir}/{gizmo_name}", f"nuke.createNode('{gizmo_name}')", icon=f'{os.path.join(full_dir_name, gizmo_name)}.png')
            nuke.pluginAddPath(full_dir_name)

if __name__ == '__main__':
    load_gizmos(node_menu, dir_of_gizmo_dirs)