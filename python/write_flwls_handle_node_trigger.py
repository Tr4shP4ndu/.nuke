import nuke
import os
import re
import logging
from typing import Any, Dict, List, Callable
from pathlib import Path
from write_flwls_data import DATA

def update_write_geo_knobchanged(write_flwls_knobs: dict, filtered_geo_knobs: dict) -> None:
    filetype_ranges = {
        "ABC": ["abc_options", "fbx_options"],
        "FBX": ["fbx_options", "create_directories_separator"]
    }

    filetype_value = write_flwls_knobs["filetype_flwls"][1]
    
    geo_specific_knobs = {}
    geo_knobs_found = False
    for knob_name, (knob, value, knob_type) in filtered_geo_knobs.items():
        if knob_name == 'abc_options':
            geo_knobs_found = True
        elif knob_name == 'create_directories_separator':
            geo_knobs_found = False
            continue
        if geo_knobs_found:
            geo_specific_knobs[knob_name] = (knob, value, knob_type)

    for knob_name, (knob, _, _) in geo_specific_knobs.items():
        knob.setFlag(nuke.INVISIBLE)

    affected_range = filetype_ranges.get(filetype_value, [])
    write_geo_specific_knobs_filtered = {}
    knobs_found = False
    for knob_name, (knob, value, knob_type) in geo_specific_knobs.items():
        if knob_name == affected_range[0]:
            knobs_found = True
        if knobs_found:
            if knob_name == affected_range[1]:
                break
            write_geo_specific_knobs_filtered[knob_name] = (knob, value, knob_type)
            knob.clearFlag(nuke.INVISIBLE)

def update_write_knobchanged(write_flwls_knobs: dict, filtered_write_knobs: dict) -> None:
    filetype_ranges = {
        "CIN": ["cin_options", "dpx_options"],
        "DPX": ["dpx_options", "exr_options"],
        "EXR": ["exr_options", "jpeg_options"],
        "JPEG": ["jpeg_options", "mov_options"],
        "MOV": ["mov_options", "mxf_options"],
        "MXF": ["mxf_options", "png_options"],
        "PNG": ["png_options", "sgi_options"],
        "SGI": ["sgi_options", "targa_options"],
        "TARGA": ["targa_options", "tiff_options"],
        "TIFF": ["tiff_options", "yuv_options"],
        "YUV": ["yuv_options", "create_directories"],
        "ABC": ["abc_options", "fbx_options"],
        "FBX": ["fbx_options", "create_directories_separator"],
    }
    filetype_value = write_flwls_knobs["filetype_flwls"][1]
    
    write_specific_knobs = {}
    is_between_cin_and_exr = False
    for knob_name, (knob, value, knob_type) in filtered_write_knobs.items():
        if knob_name == 'cin_options':
            is_between_cin_and_exr = True
        elif knob_name == 'create_directories_separator':
            is_between_cin_and_exr = False
            continue
        if is_between_cin_and_exr:
            write_specific_knobs[knob_name] = (knob, value, knob_type)

    for knob_name, (knob, _, _) in write_specific_knobs.items():
        knob.setFlag(nuke.INVISIBLE)

    affected_range = filetype_ranges.get(filetype_value, [])
    write_specific_knobs_filtered = {}
    knobs_found = False
    for knob_name, (knob, value, knob_type) in write_specific_knobs.items():
        if knob_name == affected_range[0]:
            knobs_found = True
        if knobs_found:
            if knob_name == affected_range[1]:
                break
            write_specific_knobs_filtered[knob_name] = (knob, value, knob_type)
            knob.clearFlag(nuke.INVISIBLE)

def format_text(base_text, settings):
    """
    Format text with optional styling settings.
    """
    colour_lookup = {"yellow" : "eba834",  "white" : "228B22"}

    result = base_text
    if settings["bold"]:
        result = f"<b>{result }</b>"
    if settings["center"]:
        result = f"<center>{result}"
    if settings["use_colour"]:
        result = f"""<font color='#{colour_lookup [settings["colour"]]}'>{result}</font>"""
    return result
    
def update_write_flwls_text_knobs(write_flwls_knobs: dict, path_info: dict) -> None:
    """
    Update the text knobs for write nodes based on the selected datatype.
    """
    if write_flwls_knobs["datatype_flwls"][1] == "SELECT":
        for to_change in ["Datatype", "Filetype", "Version", "Filename", "Scriptname"]:
            write_flwls_knobs[to_change.lower() + "_text_flwls"][0].setValue(format_text(to_change + ":"), {"bold" : True, "center" : True, "use_colour" : True, "colour" : "white"},format_text("Please choose a datatype"), {"bold" : True, "center" : True, "use_colour" : True, "colour" : "yellow"})
    else:
        for to_change in ["Datatype", "Filetype", "Version", "Filename", "Scriptname"]:
            write_flwls_knobs[to_change.lower() + "_text_flwls"][0].setValue(format_text(to_change + ":"), {"bold" : True, "center" : True, "use_colour" : True, "colour" : "white"},format_text(write_flwls_knobs[to_change.lower() + "_flwls"][1]), {"bold" : True, "center" : True, "use_colour" : True, "colour" : "yellow"})

def update_file_paths(write_flwls_knobs: dict, path_info: dict, constructed_filepath: str) -> None:
    if write_flwls_knobs["datatype_flwls"][1] == "SELECT":
        write_flwls_knobs["filepath_flwls"][0].setValue("Please choose a datatype")
    else:
        mapping = DATA.get(write_flwls_knobs["datatype_flwls"][1])
        filetype_knob_values = write_flwls_knobs["filetype_flwls"][1]
        if mapping:
            write_flwls_knobs["filepath_flwls"][0].setValue(constructed_filepath)
            name_nodes = mapping.get("name_node")
            if isinstance(name_nodes, list):
                for name_node in name_nodes:
                    target_write_node = nuke.toNode(name_node)
                    if target_write_node:
                        if name_node == "copycat":
                            target_write_node["dataDirectory"].setValue(constructed_filepath)
                        elif name_node == "Write":
                            target_write_node["file"].setValue(constructed_filepath)
                            target_write_node["create_directories"].setValue(1.0)
                            target_write_node["file_type"].setValue(filetype_knob_values.lower())
                            target_write_node["create_directories"].setValue(True)
                        else:
                            target_write_node["file"].setValue(constructed_filepath)
                            target_write_node["create_directories"].setValue(1.0)
                            target_write_node["file_type"].setValue(filetype_knob_values.lower())
                            target_write_node["create_directories"].setValue(True)
            else:
                target_write_node = nuke.toNode(name_nodes)
                if target_write_node:
                    if name_nodes == "copycat":
                        target_write_node["dataDirectory"].setValue(constructed_filepath)
                    elif name_nodes == "Write":
                        target_write_node["file"].setValue(constructed_filepath)
                        target_write_node["create_directories"].setValue(1.0)
                        target_write_node["file_type"].setValue(filetype_knob_values.lower())
                        target_write_node["create_directories"].setValue(True)
                    else:
                        if name_nodes == "geo":
                            target_write_node["file"].setValue(constructed_filepath)
                            target_write_node["file_type"].setValue(filetype_knob_values.lower())
                            return
                        else:
                            target_write_node["file"].setValue(constructed_filepath)
                            target_write_node["file_type"].setValue(filetype_knob_values.lower())
                            target_write_node["create_directories"].setValue(True)


def get_latest_version(write_flwls_knobs: dict, path_info: dict) -> str:
    folder_path = os.path.join(path_info["task_folder"], write_flwls_knobs["datatype_flwls"][1].lower(), write_flwls_knobs["filename_flwls"][1])
    
    if not os.path.exists(folder_path):
        return "v001"
    
    versions = []
    for item in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, item)):
            match = re.match(r'v(\d{3})$', item)
            if match:
                versions.append(int(match.group(1)))
    
    latest_version = max(versions, default=0) + 1
    return f"v{latest_version:03d}"

def construct_filepath(write_flwls_knobs: dict, path_info: dict) -> str:
    """
    Construction of the file path to each Datatype user selects plus detection of version.
    """
    DATA_datatypes = get_datatype_knob_DATA(write_flwls_knobs)
    DATA_digits = DATA_datatypes.get("digits", "")

    #latest_version = get_latest_version(write_flws_knobs_info, path_info)
    #write_flws_knobs_info["version_flwls"][0].setValue(latest_version)
    #version_knob_values = []
    #version_knob_values.append(latest_version)
    #write_flws_knobs_info["version_flwls"][0].setValues(version_knob_values)
    version_knob = write_flwls_knobs["version_flwls"][1]

    path_formats = {
        "default": f"{path_info['task_folder']}/{write_flwls_knobs['datatype_flwls'][1].lower()}/{write_flwls_knobs['filename_flwls'][1]}/{version_knob}/{path_info['script_name']}_{write_flwls_knobs['datatype_flwls'][1].lower()}_{write_flwls_knobs['filename_flwls'][1]}_{version_knob}{DATA_digits}.{write_flwls_knobs['filetype_flwls'][1].lower()}",
        "nr_cleanup": f"{path_info['task_folder']}/renders/{path_info['script_version']}/{write_flwls_knobs['datatype_flwls'][1].lower()}/{path_info['script_name']}{DATA_digits}.{write_flwls_knobs['filetype_flwls'][1].lower()}",
        "copycat": f"{path_info['task_folder']}/{write_flwls_knobs['datatype_flwls'][1].lower()}/{write_flwls_knobs['filename_flwls'][1]}/{version_knob}",
        "mov_special": f"{path_info['task_folder']}/renders/{path_info['script_version']}/{write_flwls_knobs['datatype_flwls'][1].lower()}/{path_info['script_name']}.{write_flwls_knobs['filetype_flwls'][1].lower()}",
        "prepgeo": f"{path_info['task_folder']}/{write_flwls_knobs['datatype_flwls'][1].lower()}/{write_flwls_knobs['filename_flwls'][1]}/{version_knob}/{path_info['script_name']}_{write_flwls_knobs['datatype_flwls'][1].lower()}_{write_flwls_knobs['filename_flwls'][1]}_{version_knob}.{write_flwls_knobs['filetype_flwls'][1].lower()}"
    }

    if write_flwls_knobs['datatype_flwls'][1] in ["FLOATING_FACE", "REVIEW_EXR"]:
        constructed_filepath = path_formats["nr_cleanup"]
    elif write_flwls_knobs['datatype_flwls'][1] == "REVIEW_MOV":
        constructed_filepath = path_formats["mov_special"]
    elif write_flwls_knobs['datatype_flwls'][1] == "COPYCAT":
        constructed_filepath = path_formats["copycat"]
    elif write_flwls_knobs['datatype_flwls'][1] == "PREPGEO":
        constructed_filepath = path_formats["prepgeo"]
    elif write_flwls_knobs['datatype_flwls'][1] == "SELECT":
        constructed_filepath = "Please choose Datatype>Filetype>Version"
    else:
        constructed_filepath = path_formats["default"]
    return constructed_filepath
    
def update_filetype_knob(write_flwls_knobs: dict) -> None:
    DATA_datatypes = get_datatype_knob_DATA(write_flwls_knobs)
    write_flwls_knobs["filetype_flwls"][0].setValues(DATA_datatypes.get("filetypes"))

def update_gizmo_tabs(write_flwls_knobs: dict) -> None:
    DATA_datatypes = get_datatype_knob_DATA(write_flwls_knobs)
    node_data = DATA_datatypes
    if node_data:
        action_type, knobs_to_update = node_data.get("actions", ["invisible", []])

        all_tabs = DATA["WRITE_FLWLS_TABS"]["all_tabs"]
        for tab in all_tabs:
            write_flwls_knobs[tab][0].setFlag(nuke.INVISIBLE)

        for knob in knobs_to_update:
            if action_type == "visible":
                write_flwls_knobs[knob][0].clearFlag(nuke.INVISIBLE)

def create_delete_nodes(write_flws_knobs_info: dict) -> None:
    """
    Creates necessary nodes and deletes unused ones based on the selected datatype.
    """
    try:
        for node in nuke.allNodes():
            nuke.delete(node)
        
        if write_flws_knobs_info["datatype_flwls"][1] == "SELECT":
            return
        
        mapping = DATA.get(write_flws_knobs_info["datatype_flwls"][1])
        if mapping:
            write_nodes = mapping.get("write_node")
            name_nodes = mapping.get("name_node")
            input_names = mapping.get("input_names")
            if not isinstance(write_nodes, list):
                write_nodes = [write_nodes]
            if not isinstance(name_nodes, list):
                name_nodes = [name_nodes]
            if not isinstance(input_names, list):
                input_names = [input_names]

            output = nuke.createNode("Output", inpanel=False)
            for write_node, name_node, input_name in zip(write_nodes, name_nodes, input_names):
                existing_nodes = [node for node in nuke.allNodes() if node.name() == name_node]
                if not existing_nodes:
                    if write_node == "SmartVector":
                        target_smartvector_node = nuke.createNode("SmartVector", inpanel=False)
                        target_smartvector_node.setName("smartvector")
                        target_node = nuke.createNode("Write", inpanel=False)
                        target_node.setName("Write")
                        source_input_node = nuke.createNode("Input", inpanel=False)
                        source_input_node.setName("INPUT_SMARTVECTOR")
                        matte_input_node = nuke.createNode("Input", inpanel=False)
                        matte_input_node.setName("MATTE")
                        target_smartvector_node.setInput(0, source_input_node)
                        target_smartvector_node.setInput(1, matte_input_node)
                        output.setInput(0, target_node)
                    elif write_node == "CopyCat":
                        target_node = nuke.createNode(write_node, inpanel=False)
                        target_node.setName(name_node)
                        input_copycat_node = nuke.createNode("Input", inpanel=False)
                        input_copycat_node.setName("INPUT_COPYCAT")
                        target_node.setInput(0, input_copycat_node)
                        output.setInput(0, target_node)
                        if "GROUNDTRUTH" in input_names:
                            gt_input_node = nuke.createNode("Input", inpanel=False)
                            gt_input_node.setName("GROUNDTRUTH")
                            target_node.setInput(1, gt_input_node)
                    else:
                        target_node = nuke.createNode(write_node, inpanel=False)
                        target_node.setName(name_node)
                        input_node = nuke.createNode("Input", inpanel=False)
                        input_node.setName(input_name)
                        target_node.setInput(0, input_node)
                        output.setInput(0, target_node)
    except Exception as e:
        logging.error("Error in create_or_delete_nodes:", exc_info=True)

def change_gizmo_color(knobs_info: dict) -> None:
    """
    Changes the color of the gizmo based on the selected datatype.
    """
    node_data = DATA.get(knobs_info["datatype_flwls"][1])
    if node_data:
        color = node_data.get("color")
        gizmo_node = nuke.thisNode()
        gizmo_node["tile_color"].setValue(int(color, 16))

def get_datatype_knob_DATA(write_flws_knobs_info: dict) -> None:
    """
    Get information about the selected datatype.
    """
    DATA_datatypes = DATA.get(write_flws_knobs_info["datatype_flwls"][1], None)
    return DATA_datatypes

def get_script_info() -> dict:
    """
    Get information about the script.
    """
    script_filepath = Path(nuke.root().name())
    path_info = {
        "script_filepath": script_filepath,
        "task_folder": script_filepath.parent.absolute(),
        "script_name": script_filepath.stem,
        "script_version": re.search(r'v(\d{3})', script_filepath.name).group() if re.search(r'v(\d{3})', script_filepath.name) else ''
    }
    # Dict script_filepath: script_filepath, task_folder, script_name, script_version --> script_info["script_filepath"]
    return path_info

def tab_knobs(write_flwls_knobs: Dict, tab_name: str, break_condition: str):
    filtered_knobs = {}
    found_tab = False
    for knob_name, (knob, value, knob_type) in write_flwls_knobs.items():
        if knob_name == tab_name:
            found_tab = True
        if found_tab and knob_name != tab_name:
            if knob_name == break_condition:
                break
            filtered_knobs[knob_name] = (knob, value, knob_type)
    return filtered_knobs

def write_flwls_node_knobs(write_flwls_node: nuke.Node) -> dict:
    """
    Get information about write node knobs.
    """
    write_flwls_knobs = {}
    for knob_name, knob in write_flwls_node.knobs().items():
        write_flwls_knobs[knob_name] = (knob, knob.value(), type(knob))

    knob_callbacks = nuke.thisKnob().name()
    geo_knobs_from_tab = tab_knobs(write_flwls_knobs, "write_geo_tab", "copycat_tab")
    write_knobs_from_tab = tab_knobs(write_flwls_knobs, "write_tab", "write_geo_tab")

    # Dict Node: knob[0], value[1] & class[2] --> write_flwls_knobs["datatype_flwls"][0].setValue("Custom")
    return write_flwls_knobs, knob_callbacks, geo_knobs_from_tab, write_knobs_from_tab

def handle_node_trigger(write_flwls_node: nuke.Node) -> None:
    """
    Handle node trigger events.
    """
    if write_flwls_node is not None:
        write_flwls_knobs, knob_callbacks, geo_knobs_from_tab, write_knobs_from_tab = write_flwls_node_knobs(write_flwls_node) 
        path_info = get_script_info()
        update_write_flwls_text_knobs(write_flwls_knobs, path_info)

        if knob_callbacks in ["datatype_flwls"]:
            try:
                update_filetype_knob(write_flwls_knobs)
                change_gizmo_color(write_flwls_knobs)
                create_delete_nodes(write_flwls_knobs) 
                update_gizmo_tabs(write_flwls_knobs) 
            except Exception as e:
                logging.error("Error:", exc_info=True)

        if knob_callbacks in ["filetype_flwls", "version_flwls", "filename_flwls"]:
            try:
                constructed_filepath = construct_filepath(write_flwls_knobs, path_info)
                update_file_paths(write_flwls_knobs, path_info, constructed_filepath)
                if write_flwls_knobs["datatype_flwls"][1] == "SELECT":
                    return
                elif write_flwls_knobs["datatype_flwls"][1] in ["PREPCOMP", "FLOATING_FACE", "REVIEW_EXR", "REVIEW_MOV", "SMARTVECTOR"] and knob_callbacks in ["filetype_flwls", "version_flwls", "filename_flwls"]:
                    update_write_knobchanged(write_flwls_knobs, write_knobs_from_tab)
                elif write_flwls_knobs["datatype_flwls"][1] == "PREPGEO" and knob_callbacks in ["filetype_flwls", "version_flwls", "filename_flwls"]:
                    update_write_geo_knobchanged(write_flwls_knobs, geo_knobs_from_tab)
            except Exception as e:
                logging.error("Error:", exc_info=True)