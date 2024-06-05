import nuke
import nukescripts

def gizmoToGroup(sel):
    '''
    Main function to replace a gizmo with a corresponding group.
    '''
    for gizmo in sel:
        if gizmo.Class().endswith("Gizmo"):
            # Save the name of the gizmo
            selName = gizmo.name()
            
            # Get all inputs of the gizmo
            selInputs = [gizmo.input(i) for i in range(gizmo.inputs())]
            
            # Make group from gizmo
            g = gizmo.makeGroup()
            
            # Get coordinates
            x, y = gizmo.xpos(), gizmo.ypos()
            
            # Delete the gizmo
            nuke.delete(gizmo)
            
            # Rename the group
            g["name"].setValue(selName)
            
            # Reposition the group
            g.setXpos(x)
            g.setYpos(y)
            
            # Set all inputs back
            for i, input_node in enumerate(selInputs):
                g.setInput(i, input_node)
        else:
            nuke.message(f"{gizmo.name()} is not a gizmo. Please select a gizmo.")

def replaceGizmoWithGroup():
    '''
    Replace the selected gizmos with the corresponding groups.
    '''
    sel = nuke.selectedNodes()
    if not sel:
        nuke.message("Please select at least one gizmo.")
        return
    
    for node in sel:
        if "Gizmo" in node.Class():
            node.setSelected(True)
            gizmoToGroup([node])
        else:
            node.setSelected(False)
