from common import CallbackAction, CallbackActionTree
import os
import sys
sys.path.append(os.path.dirname(__file__))
import nuke
import nuke_utils
from functools import partial
import FlwlsVFXPipelinePanel
import internal_render
from typing import Any, Callable, Dict
from pathlib import Path


def callback_handler(args : Dict[Any,Any]):
    if args["node"] is None or args["knob"] is None:
        return
    node_name = args["node"].name()
    knob_name = args["knob"].name()
    knob_value = args["knob"].value()
    if "Write_Flwls" in node_name:
        internal_render.current_gizmo_pointer = args["node"]
    action_tree = CallbackActionTree(action_tree=[
        CallbackAction(condition=lambda : knob_name == "datatype_flwls" and args["knob"].value() == "SELECT", action = lambda : [partial(args["node"].knobs()[knob_name].setFlag, nuke.INVISIBLE)() for knob_name in ["openFolder","filename_flwls", "filetype_flwls", "info_printout",]]),
        CallbackAction(condition=lambda : knob_name == "datatype_flwls", action = lambda : partial(
            internal_render.get_internal_render_data_type, knob_value, args["node"])().run()),
        CallbackAction(condition=lambda : knob_name == "filename_flwls" or knob_name == "filetype_flwls", action = lambda: partial(
            internal_render.get_internal_render_data_type, args["node"].knobs()["datatype_flwls"].value(), args["node"],
            {"custom_name" : args["node"].knobs()["filename_flwls"].value(),
            "filetype" : args["node"].knobs()["filetype_flwls"].value()})().run()),
        CallbackAction(condition=lambda : True, action = lambda : partial(args["node"].knobs()["openFolder"].setEnabled, False)()),
        CallbackAction(condition=lambda : os.path.exists(Path(internal_render.current_gizmo_pointer.knobs()["folderPath"].value()).parent), action = lambda : partial(args["node"].knobs()["openFolder"].setEnabled, True)()),
        CallbackAction(condition=lambda : knob_name == "openFolder", action = lambda : 
            os.system('xdg-open "%s"' % str(Path(args["node"].knobs()["folderPath"].value()).parent)
        ))
        ])
    action_tree.run()
    