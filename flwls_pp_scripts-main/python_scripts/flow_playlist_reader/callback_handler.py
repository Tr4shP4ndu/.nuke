import os
from functools import partial
import sys
sys.path.append(os.path.dirname(__file__))
from typing import Any, Callable, Dict
import nuke

from common import CallbackAction, CallbackActionTree
import playlist_reader

def callback_handler(args : Dict[Any,Any]):
    if args["node"] is None or args["knob"] is None:
        return
    node_name = args["node"].name()
    knob_name = args["knob"].name()
    knob_value = args["knob"].value()
    path_to_csv = args["node"].knobs()["CSVInput"].getValue()
    is_valid_csv = os.path.exists(path_to_csv) \
        and "." in path_to_csv \
        and path_to_csv.split(".")[-1] == "csv" 
    action_tree = CallbackActionTree(action_tree = [
        CallbackAction(condition = lambda : not is_valid_csv, action=lambda : partial(args["node"].knobs()["LoadCSV"].setEnabled, False)()),
        CallbackAction(condition = lambda: not playlist_reader.has_setup_been_done(args["node"]), action = lambda : [x() for x in [
            partial(args["node"].knobs()["SwapContext"].setVisible, False),
            partial(args["node"].knobs()["SwapInput"].setVisible, False),
        ]]),
        CallbackAction(condition = lambda : is_valid_csv, action=lambda : partial(args["node"].knobs()["LoadCSV"].setEnabled, True)()),
        CallbackAction(condition = lambda : is_valid_csv and knob_name == "LoadCSV", action=lambda : partial(playlist_reader.run, gizmo = args["node"], path_to_csv = path_to_csv)()),
        CallbackAction(condition = lambda : playlist_reader.has_setup_been_done(args["node"]), action = lambda : [x() for x in [
            partial(args["node"].knobs()["SwapContext"].setVisible, True),
            partial(args["node"].knobs()["SwapInput"].setVisible, True),
        ]]),
        CallbackAction(condition = 
                        lambda : playlist_reader.has_setup_been_done(args["node"])
                        and len(args["node"].knobs()["SwapContext"].values()) < 2, action = lambda : [x() for x in [
            partial(args["node"].knobs()["SwapContext"].setValues, [x for x in playlist_reader.parse_csv(path_to_csv).keys()]),
            partial(args["node"].knobs()["SwapInput"].setValues, playlist_reader.get_inputs_to_accept()),]]),
        CallbackAction(condition = 
                        lambda : playlist_reader.has_setup_been_done(args["node"])
                        and len(args["node"].knobs()["SwapContext"].values()) > 1
                        and knob_name == "SwapContext"
                        and knob_value in [x for x in playlist_reader.parse_csv(path_to_csv).keys()],
                        action = lambda : partial(playlist_reader.update, args["node"])()),
        CallbackAction(condition = 
                        lambda : playlist_reader.has_setup_been_done(args["node"])
                        and len(args["node"].knobs()["SwapInput"].values()) > 1
                        and knob_name == "SwapInput"
                        and knob_value in playlist_reader.get_inputs_to_accept(),
                        action = lambda : partial(playlist_reader.update, args["node"])())
        ])
    action_tree.run()

