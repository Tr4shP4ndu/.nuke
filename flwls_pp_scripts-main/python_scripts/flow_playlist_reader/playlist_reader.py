import csv
import os
import nuke
import nuke_utils
from pathlib import Path
import re
from typing import Any, Callable, List, Dict

import callback_handler
from common import NodeToMake, NodeLink, GizNodeEX
import FlwlsVFXPipelinePanel

def read_csv(path_to_csv : str) -> Dict[Any, Any]:
    file = open(path_to_csv,"r")
    reader = csv.DictReader(file)
    raw_results = []
    for row in reader:
        raw_results.append(row["Path to Frames"])
    file.close()
    return raw_results

def read_script(path_to_script : str) -> List[str]:
    file = open(path_to_script, "r")
    contents = file.readlines()
    file.close()
    return [line.replace("\n", "") for line in contents]

def parse_csv(path_to_csv : str) -> Dict[Any, Any]:
    raw_results = read_csv(path_to_csv)
    parsed_results = {}
    for path_to_frames in raw_results:
        current_context = FlwlsVFXPipelinePanel.LogicEX.get_context_based_on_this_path(path_to_frames)
        current_name = FlwlsVFXPipelinePanel.LogicEX.from_dict_to_string(current_context, ["show","episode","part","shot","language","variant"], "_")
        exr_path = path_to_frames
        path_to_script = FlwlsVFXPipelinePanel.LogicEX.folder_keyword_replacement(os.path.dirname(exr_path) + "/script/$FINDFIRSTFOLDER$")
        script_data = read_script(path_to_script)
        path_to_plate = os.path.dirname([line for line in script_data if "input/PLATE/plate/" in line][0].replace("file ","").replace(" ",""))
        path_to_precomp = os.path.dirname([line for line in script_data if "/input/PRECOMP/precomp/" in line][0].replace("file ","").replace(" ",""))
        current_node = {
                "name" : current_name,
                "context" : current_context,
                "reviewexr_path" : exr_path,
                "plate_path" : path_to_plate,
                "precomp_path" : path_to_precomp,
                "script_path" : path_to_script,
                }
        parsed_results[current_name] = current_node
    return parsed_results

def get_inputs_to_accept():
    return ["PLATE","REVIEWEXR","PRECOMP"]

def convert_shot_name_to_switch_node(shot_name : str) -> str:
    return f"SWITCH_{shot_name}"

def convert_shot_name_and_input_to_read_node(shot_name : str, to_make : str) -> str:
    return f"READ_{to_make}_{shot_name}"

def get_gizmo_sub_definition(shot_name : str, top_left_corner : List[int], spacing : List[int]):
    nodes_to_make = [NodeToMake("Switch", convert_shot_name_to_switch_node(shot_name))]
    links_to_make = []
    inputs_to_accept = get_inputs_to_accept()
    [[  nodes_to_make.append(
            NodeToMake("Read", 
            convert_shot_name_and_input_to_read_node(shot_name, to_make),
            lambda to_make = to_make: [top_left_corner[0] + (inputs_to_accept.index(to_make) * spacing[0]), top_left_corner[1]])),
        links_to_make.append(NodeLink(convert_shot_name_to_switch_node(shot_name),convert_shot_name_and_input_to_read_node(shot_name, to_make), inputs_to_accept.index(to_make))),
    ] for to_make in inputs_to_accept]
    return nodes_to_make, links_to_make

def get_regex(folder : str) -> re.Pattern:
    extension = "." + os.listdir(folder)[0].split(".")[-1]
    division = [c for c in os.listdir(folder)[0] if not c.isalnum()]
    name = ".*"
    return re.compile("^(?P<name>{})(?P<delim>{})(?P<num>.*)(?P<ext>{})$".format(name, division, extension))

def run(gizmo : nuke.Node, path_to_csv : str):
    shots = parse_csv(path_to_csv)
    GizNodeEX.delete_all_nodes(gizmo)
    all_nodes_to_make = [NodeToMake("Output", "OUTPUT")]
    all_links_to_make = []
    top_left_corner = [0,0]
    spacing = [100,100]
    counter = 0
    for shot in shots.values():
        node_data = get_gizmo_sub_definition(shot["name"], [top_left_corner[0], top_left_corner[1] + (counter * spacing[1])], spacing)
        all_nodes_to_make += node_data[0]
        all_links_to_make += node_data[1]
        counter+=1
    GizNodeEX.make_these_nodes_agnostic(gizmo, all_nodes_to_make, all_links_to_make)
    for shot in shots.values():
        for node in [node for node in all_nodes_to_make if "READ" in node.name and shot["name"] in node.name]:
            input_name = node.name.split("_")[1].lower() + "_path"
            GizNodeEX.find_this_subnode(gizmo, node.name).knobs()['file'].fromUserText(
                os.path.join(shot[input_name], nuke_utils.nuke_user_path_from_dir(Path(shot[input_name]),get_regex(shot[input_name]))))
    GizNodeEX.link(gizmo, NodeLink("OUTPUT",f"SWITCH_{list(shots.values())[0]['name']}", 0))
    GizNodeEX.copy_paste_these_nodes_out_of_gizmo(gizmo, [node.name for node in all_nodes_to_make if "READ" in node.name])

def update(gizmo : nuke.Node):
    shot_name = gizmo.knobs()["SwapContext"].value()
    input_name = gizmo.knobs()["SwapInput"].value()

    use_this_switch =  convert_shot_name_to_switch_node(shot_name)
    use_this_index = get_inputs_to_accept().index(input_name)

    GizNodeEX.find_this_subnode(gizmo, use_this_switch).knobs()["which"].setValue(use_this_index)
    GizNodeEX.link(gizmo, NodeLink("OUTPUT",use_this_switch, 0))

    GizNodeEX.find_this_subnode(gizmo, "OUTPUT").knobs()

def has_setup_been_done(gizmo : nuke.Node):
    with gizmo:
        return len(nuke.allNodes()) > 1