from common import CallbackAction, CallbackActionTree
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[0]))
sys.path.append(str(Path(__file__).parents[2] / "flwls_vfx_pipeline"))
import nuke
import nuke_utils
from functools import partial
import internal_render
from typing import Any, Callable, Dict
import threading
import traceback


def callback_handler(args : Dict[Any,Any]):
    try:
        callback_logic(args)
    except Exception as EX:
        print(f"Flwls_Write Callback failed, skipping. (Original Error:\n{traceback.format_exc()})")

def callback_logic(args : Dict[Any, Any]):
    if args["node"] is None or args["knob"] is None:
        return
    node_name = args["node"].name()
    knob_name = args["knob"].name()
    knob_value = args["knob"].value()
    if "Write_Flwls" in node_name:
        internal_render.current_gizmo_pointer = args["node"]
    action_tree = CallbackActionTree(action_tree=[
        CallbackAction(condition=lambda : knob_name == "datatype_flwls" and args["knob"].value() == "SELECT", action = lambda : [partial(args["node"].knobs()[knob_name].setFlag, nuke.INVISIBLE)() for knob_name in ["openFolder","filename_flwls", "filetype_flwls", "info_printout",]]),
        CallbackAction(condition=lambda : knob_name == "datatype_flwls" or knob_name == "refresh", action = lambda : internal_render.InternalRenderDataType.stash_custom_name() or partial(
            internal_render.get_internal_render_data_type, args["node"].knobs()["datatype_flwls"].value(), args["node"])().run() or internal_render.InternalRenderDataType.pop_custom_name()),
        CallbackAction(condition=lambda : knob_name == "filename_flwls" or knob_name == "filetype_flwls", action = lambda: partial(
            internal_render.get_internal_render_data_type, args["node"].knobs()["datatype_flwls"].value(), args["node"],
            {"custom_name" : args["node"].knobs()["filename_flwls"].value(),
            "filetype" : args["node"].knobs()["filetype_flwls"].value()})().run()),
        CallbackAction(condition=lambda : True, action = lambda : partial(args["node"].knobs()["openFolder"].setEnabled, False)()),
        CallbackAction(condition=lambda : os.path.exists(Path(internal_render.current_gizmo_pointer.knobs()["folderPath"].value()).parent), action = lambda : partial(args["node"].knobs()["openFolder"].setEnabled, True)()),
        CallbackAction(condition=lambda : knob_name == "openFolder", action = lambda : 
            os.system('xdg-open "%s"' % str(Path(args["node"].knobs()["folderPath"].value()).parent))),
        CallbackAction(condition=lambda : knob_name == "readfromwrite_flwls", action = lambda : nuke_utils.make_read_from_write(
                                        "Read", 
                                        "read_from_write",
                                        internal_render.current_gizmo_pointer,
                                        str(Path(args["node"].knobs()["renderHistory"].value()).parent), 
                                        str(int(nuke.root().knobs()["first_frame"].value())))),
        CallbackAction(condition=lambda : knob_name == knob_name == "refresh", action = lambda :
            internal_render.current_gizmo_pointer.knobs()['readfromwrite_flwls'].setEnabled(len(os.listdir(nuke.toNode("Write_Flwls").knobs()["folderPath"].value()))>0))
        ])
    action_tree.run()