import nuke

# Define offsets and spacing as constants
X_OFFSET = 0  # Additional offset for horizontal positioning
Y_OFFSET = 0  # Additional offset for vertical positioning
VIEWER_SPACING = 100  # Horizontal spacing between Viewer nodes
APPROX_VIEWER_HEIGHT = 100  # Approximate Viewer node height for alignment

def run():
    """
    Align all Viewer nodes in Nuke horizontally at the bottom of the Node Graph.
    """
    # Fetch all Viewer nodes in the script
    viewer_nodes = [node for node in nuke.allNodes() if node.Class() == "Viewer"]

    if not viewer_nodes:
        nuke.message("No Viewer found in the script!")
        return

    # Sort Viewer nodes alphabetically by name
    viewer_nodes.sort(key=lambda viewer_node: viewer_node['name'].value())

    # Determine the current view's center and zoom level
    current_center = nuke.center()  # Center of the current view
    zoom_level = nuke.zoom()  # Current zoom level
    print(f"Zoom level: {zoom_level:.2f}")

    # Calculate positioning
    center_x, center_y = current_center[0], current_center[1]
    start_x = center_x - (len(viewer_nodes) - 1) * VIEWER_SPACING // 2 + X_OFFSET
    adjusted_y = center_y + (APPROX_VIEWER_HEIGHT / zoom_level) + Y_OFFSET

    # Align Viewer nodes
    for i, viewer in enumerate(viewer_nodes):
        new_x = int(start_x + i * VIEWER_SPACING)
        new_y = int(adjusted_y)
        viewer.setXpos(new_x)
        viewer.setYpos(new_y)

    print("Viewers successfully aligned!")
run()
