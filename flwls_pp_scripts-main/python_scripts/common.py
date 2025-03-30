# logic that can be shared among any gizmos / scripts that power gizmos

from dataclasses import dataclass
from functools import partial
import nuke
from typing import Any, Dict, List, Callable

@dataclass
class CallbackAction():
    """Triggered when the user changes something in the gizmo menu."""
    condition : Callable
    action : Callable

@dataclass
class CallbackActionTree():
    """List of Callback Actions to run when handling changes to gizmo menu."""
    action_tree : List[CallbackAction]
    def run(self):
        [action.action() for action in self.action_tree if action.condition()]

@dataclass
class NodeToMake():
        the_type : str = ""
        name : str = ""
        position : List = lambda : []

@dataclass
class NodeLink():
    target : str
    src : str
    slot : int

class GizNodeEX():
    """Gizmo Node Logic"""
    def delete_all_nodes(gizmo : nuke.Node):
        with gizmo:
            for node in nuke.allNodes():
                nuke.delete(node)

    def find_this_subnode(gizmo : nuke.Node, node_name : str):
        return [node for node in gizmo.nodes() if node.name() == node_name][0]

    def link(gizmo : nuke.Node, node_link : NodeLink) -> None:
        with gizmo:
            nuke.toNode(node_link.target).setInput(node_link.slot, nuke.toNode(node_link.src))

    def make_these_nodes_agnostic(gizmo : nuke.Node, nodes_to_make : List[NodeToMake], node_links : List[NodeLink]) -> None:
        with gizmo:
            for node_to_make in nodes_to_make:
                current_node = nuke.createNode(node_to_make.the_type, inpanel=False)
                current_node.setName(node_to_make.name)
                if node_to_make.position():
                    current_node.knobs()["xpos"].setValue(node_to_make.position()[0])
                    current_node.knobs()["ypos"].setValue(node_to_make.position()[1])
            for link in node_links:
                GizNodeEX.link(gizmo, link)
    
    def copy_paste_these_nodes_out_of_gizmo(gizmo : nuke.Node, node_names_to_copy : List[str]):
        with gizmo:
            for node in nuke.allNodes():
                node.knobs()["selected"].setValue(node.knobs()["name"].value() in node_names_to_copy)
            nuke.nodeCopy("%clipboard%")
        nuke.nodePaste("%clipboard%")

@dataclass
class GizmoAction():
    """For actions such as filling or hiding knobs belonging to nodes inside a gizmo."""
    action : Callable


class GizmoActionLookup():
    def get_action(name : str) -> GizmoAction:
        action_lookup = {
            "invisible" : lambda pointer_to_knob, knob_name, value : getattr(pointer_to_knob().knobs()[knob_name], value)(nuke.INVISIBLE),
            "disable" : lambda pointer_to_knob, knob_name, value : getattr(pointer_to_knob().knobs()[knob_name], value)(nuke.DISABLED),
            "recursive" : lambda pointer_to_knob, knob_name, value : getattr(pointer_to_knob().knobs()[knob_name], value)(nuke.KNOB_CHANGED_RECURSIVE),
            "autofill_multi" : lambda pointer_to_knob, knob_name, value : pointer_to_knob().knobs()[knob_name].setValues(value),
            "autofill_single" : lambda pointer_to_knob, knob_name, value : pointer_to_knob().knobs()[knob_name].setValue(value),
            "toggle_vis" : lambda pointer_to_knob, knob_name, value : [pointer_to_knob().knobs()[knob_name].setVisible(not pointer_to_knob().knobs()[knob_name].visible()) for counter in range(0, value)],
        }
        return GizmoAction(action=action_lookup[name])
    def compile_action_list(name : str, pointer_to_knob : Callable, knob_names_to_args : List[Any]) -> List[GizmoAction]:
        return [GizmoAction(action=
            partial(GizmoActionLookup.get_action(name).action,
            pointer_to_knob,
            pair[0],
            pair[1]))
            for pair in knob_names_to_args if pair]
