import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent/"flwls_vfx_pipeline"))
import nuke_utils
import nuke
import nukescripts
import subprocess
import glob
import time
import re
import shutil
from typing import Callable, List

def generate_ict_cam_geo(plate_dir: str, fosd_fp_dir : str, pt_fp_dir : str, output_dir : str, user_teeth_option: str, custom_teeth_dir: str, import_tongue: bool): 
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for folder_name in ["plate_dir", "fosd_fp_dir", "pt_fp_dir", "output_dir"]:
        if eval(folder_name) != "":
            if not os.path.exists(eval(folder_name)):
                nuke.message(f"{eval(folder_name)} is not a valid path for {folder_name}")
                return

    if user_teeth_option == ("CUSTOM"):
        user_teeth_option = custom_teeth_dir
    skip_tongue = str(bool(import_tongue))
    
    tasks_to_do = {
        fosd_fp_dir : lambda : subprocess.getoutput(f"python {locate_ict_importer_dir()}/launcher.py PT={fosd_fp_dir} PLATE={plate_dir} TEETH={user_teeth_option} TONGUE={skip_tongue} OUTPUT={output_dir} NAME=fosd"),
        pt_fp_dir : lambda : subprocess.getoutput(f"python {locate_ict_importer_dir()}/launcher.py PT={pt_fp_dir} PLATE={plate_dir} TEETH={user_teeth_option} TONGUE={skip_tongue} OUTPUT={output_dir} NAME=pt")
    }

    results = nuke_utils.run_these_tasks_with_progress_bar([tasks_to_do[task] for task in tasks_to_do.keys() if os.path.exists(task)])
    if not os.listdir(output_dir):
        nuke.message("Failed to produce outputs due to the following issue:\n" + results[-1])
    
    gather_user_input_to_for_alembic_import(output_dir=output_dir, plate_directory=plate_dir, user_teeth_option=user_teeth_option)

def gather_user_input_to_for_alembic_import(output_dir: str, plate_directory: str, user_teeth_option: str):

    output_dir = str(os.path.join(output_dir,"reversed"))

    imported_nodes = []
    exported_abc_files = []

    exported_files = os.listdir(output_dir)

    for file in exported_files:
        if file.endswith(".abc"):
            exported_abc_files.append(file)


    try:
        path_parts = plate_directory.split(os.path.sep)
        input_workspace = path_parts.index('input')
        workspace_version = path_parts[input_workspace - 1]
    except:
        workspace_version = "not found"


    for abc in exported_abc_files:
        
        label, _ = os.path.splitext(os.path.basename(abc))
        label = f"{label} Wksp {workspace_version}"
        
        if "Camera" not in abc:
            import_type = "geo"
        else:
            import_type = "cam"

        if "Teeth" in abc and user_teeth_option == "NONE": #skips teeth import if user selects NONE for teeth option
            pass
        
        else:
            imported_node = import_alembic(file_pattern=abc, label=label, import_type=import_type, alembic_dir=output_dir, nuke_message_on_error=1)
            imported_nodes = imported_nodes + imported_node
       
    _layout_nodes(imported_nodes = imported_nodes, workspace_version = workspace_version)
    return
    
def _layout_nodes(imported_nodes: list, workspace_version: str) -> None:
    nuke.selectAll()
    nuke.invertSelection()
    ict_importer_gizmo = nuke.thisNode()
    ict_importer_gizmo.setSelected(True)
    nuke.nodeCopy("%clipboard%")
    ict_importer_gizmo.setSelected(False)
    copied_ict_importer_gizmo = nuke.nodePaste("%clipboard%")
    copied_ict_importer_gizmo.setSelected(False)
    imported_nodes.append(ict_importer_gizmo)

    for node in imported_nodes:
        node.autoplace()
        node.setSelected(True)

    backdrop = nukescripts.autobackdrop.autoBackdrop()
    backdrop.knob('tile_color').setValue(0x555555ff)
    backdrop.knob('note_font_size').setValue(20)

    backdrop_height = backdrop.knob('bdheight').value()
    backdrop.knob('bdheight').setValue(backdrop_height + 40)
  
    backdrop.knob('label').setValue(f"ICT Imports - Input workspace {workspace_version}")

    imported_nodes.append(backdrop)

    for node in imported_nodes: #incoming nodes are left selected (nuke default for adding nodes)
        node.setSelected(True)

def locate_ict_importer_dir() -> str: 
    return str(Path(__file__).parent / "ict_importer")

def _create_versioned_alembic_out_dir_in_workspace(indir: str): 

    if indir == "": # IF NO workspace DIR IS FOUND, THE NUKE SCRIPT IS USED 
        nuke_script_path = nuke.root().name() #GETS NUKE SCRIPT PATH

        if os.path.exists(nuke_script_path):
            indir = os.path.dirname(os.path.dirname(nuke_script_path)) #ASSUMING USER HAS SCRIPTS OR WORK FOLDER, THE INTERNAL PUBLISH IS PUT ALONGSIDE THESE
        else:
            ict_importer_gizmo = nuke.thisNode()
            out_dir = ict_importer_gizmo['alembic_out_dir'].value()
            return out_dir

    # OUTPUT STRUCTURE
    new_folder = "INTERNAL_PUBLISH"
    ict_geo_folder = "ict_imports"

    # CREATES OUTPUT STRUCTURE
    param_out = os.path.join(indir, new_folder, ict_geo_folder)
    
    # DEFINE BASE VERSION NUMBER
    base_version = "v001"

    # DEFINE VERION NUMBER PATTERN (LIMITED TO 999 VERSIONS)
    folder_pattern = "v{:03d}"

    folders = []
    # COMPILES LIST OF DIRECTORIES IN OUTPUT workspace 
    if os.path.exists(param_out):
        folders = [f for f in os.listdir(param_out) if os.path.isdir(os.path.join(param_out, f))]

    if len(folders) == 0: # CHECKS IF USER HAS GENERATED ANY VERSIONS

        # IF NO DIRS EXIST, V001 IS CREATED 
        base_folder_path = os.path.join(param_out, base_version)
        param_out_path = base_folder_path
    
    else:

        # GETS LATEST VERSION NUMBER INSIDE SCRIPT 
        version_numbers = [int(folder[1:]) for folder in folders if folder.startswith("v") and folder[1:].isdigit()]
        latest_version = max(version_numbers) if version_numbers else 0

        last_out = os.path.join(str(param_out), str(folder_pattern.format(latest_version))) # CREATES FULL PATH TO LATEST OUTPUT FOLDER 
        latest_contents = os.listdir(last_out) # CHECKS IF FILES HAVE BEEN EXPORTED INTO LATEST OUTPUT FOLDER

        # IF FILES EXIST IN LATEST OUTPUT FOLDER, A NEW FOLDER IS CREATED WITH A HIGHER VERSION NUMBER
        if len(latest_contents) > 0: 
            new_version = latest_version + 1
            new_folder_name = folder_pattern.format(new_version)
            param_out_path = os.path.join(param_out, new_folder_name)
       
       # IF NO EXPORTS EXIST IN LATEST FOLDER, THEN THIS FOLDER IS USED FOR PREFILL DATA
        else:
            new_version = latest_version
            new_folder_name = folder_pattern.format(new_version)
            param_out_path = os.path.join(param_out, new_folder_name)

    return param_out_path # RETUNS OUTPUT DIR TO PANEL

def import_alembic(file_pattern: str, label: str, import_type: str, alembic_dir: str, nuke_message_on_error: bool): 

    frame_rate = nuke.root().knob('fps').value() #gathers frame rate from nuke script #unselect all nodes

    geo_node_path = Path(locate_ict_importer_dir()) / "prefilled_readgeo_for_alembic_import.nk" # IMPORTS PREFILLED GEO node FROM PP SCRIPTS

    matching_files = glob.glob(os.path.join(alembic_dir, file_pattern)) # USES GLOB TO SEARCH FOR FILE PATTERN

    if len(matching_files) > 0: # DOES THE FILE PATTERN EXIST IN OUTPUT
        
        file_path = matching_files[0]  # EXTRANCTS PATH FROM LIST (ONLY EVER 1 IN LIST)

        # CREATED NUKE CAMERA node AND PUPULATES IT WITH SPECIFIED FILE IN OUTPUT DIR 
        if import_type == "cam":
            camera_node = nuke.nodes.Camera2(file=file_path)
            camera_node.knob('read_from_file').setValue(True)
            camera_node.knob('read_from_file_link').setValue(True)
            camera_node.knob('frame_rate').setValue(frame_rate)
            camera_node.knob('label').setValue(label)
            imported_node = camera_node

        # IMPORTS GEO node AND POPULATES IT WITH SPECIFIED FILE IN OUTPUT DIR
        if import_type == "geo":
            nuke.nodePaste(geo_node_path.as_posix())
            readgeo_node = nuke.selectedNode()
            readgeo_node.knob('frame_rate').setValue(frame_rate)
            readgeo_node.knob('file').setValue(file_path)
            readgeo_node.knob('label').setValue(label)
            imported_node = readgeo_node
        
    else: # DELIVERS THE USER AN ERROR IF THE SPECIFIED OUTPUT DOESN'T EXIST IN THEIR OUTPUT DIR 
        if nuke_message_on_error:
            nuke.message(f"Failed importing {label} from \n{alembic_dir}")
            return

    nodes_list = [imported_node]

    return nodes_list

def _locate_directory_above_script(directory_name: str): 
    
    # FINDS CURRENT NUKE SCRIPT SAVE LOCATION
    try:
        script_location = nuke.root().name()
        working_script_parent_folder = os.path.dirname(script_location)
        working_script_parent_path = os.path.abspath(working_script_parent_folder)
        
        # SUB FUNCTION NAVIGATES UP TREES AND RETURNS THE PATH TO THE TARGET DIR
        def find_folder_in_directory_tree(folder_path, target_dirs):
            path = Path(folder_path).resolve()

            while path != Path('/'):
                for target_dir in target_dirs:
                    target_folder = path / target_dir
                    if target_folder.is_dir():
                        return target_folder

                path = path.parent
            return None
    except:
        return None

    # CALLS SUB FUNCTION TO SEARCH FOR TARGET DIR
    result = find_folder_in_directory_tree(working_script_parent_path, directory_name) #WORKING SCRIPT PATH FUNCTIONS AS A STARTING POINT
    if result:
        return result
    else:
        result = ""
        return result

def create_loading_bar(duration: int, loading_bar_message: str): 
    progress_node = nuke.ProgressTask("Loading")

    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        current_time = time.time() - start_time
        progress = current_time / duration * 100
        progress_node.setProgress(int(progress))
        progress_node.setMessage(loading_bar_message)
        time.sleep(0.1)

    progress_node.setProgress(100)
    progress_node.setMessage("Complete")

def latest_in_version(parent_directory: str):
    #nuke.message("latest_in_version")
    try:
        folders = [f for f in parent_directory.glob('v[0-9][0-9][0-9]') if f.is_dir()]
        folders.sort(reverse=True)
        return folders[0]
    except:
        return "None"

def return_folder_name(workspace: Path):
    parent = str(Path(workspace) / (latest_in_version(workspace)) / "FITTING_PARAMS")
    chars = os.listdir(parent)
    return str(chars[0])

def prefill_dependencies(node: str):
    
    node.knob('custom_teeth_path').setEnabled(False)

    indir = ["input"]
    folder_path = _locate_directory_above_script(indir)

    try:
        plate_prefill = (str(Path(folder_path) / "PLATE" / "plate"))
    except:
        plate_prefill = ""

    if os.path.exists(plate_prefill):
        node['plate_path'].setValue(plate_prefill)

    try:
        fosd_prefill = str(Path(folder_path) / "FITTING_PARAMS" / "fitting_params" ) 
    except:
        fosd_prefill = ""

    if os.path.exists(fosd_prefill):
        node['fosd_path'].setValue(fosd_prefill)

    try:
        pt_prefill = str(Path(folder_path) / "VUBB" / "fitting_params" ) 
    except:
        pt_prefill = ""
    if os.path.exists(pt_prefill):
        node['pt_path'].setValue(pt_prefill)

    try:
        alembic_out = _create_versioned_alembic_out_dir_in_workspace(str(folder_path))
        node['alembic_out_dir'].setValue(alembic_out)
    except:
        pass

