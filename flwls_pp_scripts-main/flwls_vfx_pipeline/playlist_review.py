from FlwlsVFXPipelinePanel import *
import csv
from datetime import datetime
from functools import partial
import subprocess

class PlaylistReviewEX():
    loaded_csv_data = None
    entry_size = [1000,250]
    current_anchor = [0,0] # top left of backdrop
    subanchor = [100,100] # offset from top left of backdrop
    y_axis_gap_between_entries = 50 
    node_keyword = "_PlaylistReviewEX" # all node names made for review contain this
    bg_colours = {"red" : 2566914303, "orange" : 2571501823, "yellow" : 2574975231, "green" : 1368981759, "blue" : 9935359, "indigo" : 587241983, "violet" : 2566948351 }
    current_colour_index = -1
    
    def top_left_anchor():
        return [-1000,-100]

    def has_user_selected_valid_csv(VFXPPInstance : nuke.Node):
        path = VFXPPInstance.knobs()["ShotgridReviewCSVSelect"].getValue()
        return os.path.exists(path) and path.split(".")[-1] == "csv"
    
    def set_load_from_exr_knob(VFXPPInstance : nuke.Node):
        usable = PlaylistReviewEX.has_user_selected_valid_csv(VFXPPInstance)
        VFXPPInstance.knobs()["ShotgridReviewLoadFromCSV"].setEnabled(usable)
    
    def set_load_from_url_knob(VFXPPInstance : nuke.Node):
        usable = VFXPPInstance.knobs()["ShotgridReviewURL"].getValue() != ""
        VFXPPInstance.knobs()["ShotgridReviewLoadFromURL"].setEnabled(usable)

    def load_from_url(VFXPPInstance : nuke.Node):
        playlist_id = VFXPPInstance.knobs()["ShotgridReviewURL"].getValue().split("/")[-1]
        endpoint = os.environ["TRUESYNC_SERVER_API_ENDPOINT"]
        command = """curl -X POST -H 'Content-Type: application/json' $ENDPOINT$/pipeline/job -d '{"job_name": "compositing_nuke_job", "payload": ["shotgrid_playlist_review", "$ID$"]}' """
        command = command.replace("$ENDPOINT$", endpoint).replace("$ID$", playlist_id)
        message = subprocess.getoutput(command)
        message = message[message.find("{"):]
        nuke.message(message)
        print(message)

    def load_from_csv_via_pannel(VFXPPInstance : nuke.Node):
        path_to_csv = VFXPPInstance.knobs()["ShotgridReviewCSVSelect"].getValue()
        if not PlaylistReviewEX.has_user_selected_valid_csv(VFXPPInstance):
            raise Exception(f"{path_to_csv} is an invalid CSV filepath.")
        PlaylistReviewEX.loaded_csv_data = PlaylistReviewEX.load_csv_directly(path_to_csv)

    def load_from_context_picker(VFXPPInstance : nuke.Node):
        path_to_workspace = VFXPPInstance.get_locations_of_user_choices("review")["reviewversion"] + nuke.VFXPipelinePanelBasic.get_user_choices("review")["reviewversion"]
        results = { 0 : {
            "workspace" : path_to_workspace,
            "name" : VFXPPInstance.get_context_as_string("review") + "_" + path_to_workspace.split("/")[-1],
            "show" : path_to_workspace.split("/")[4],
        }}
        PlaylistReviewEX.loaded_csv_data = results

    def load_csv_directly(path_to_csv : str) -> Dict[str,str]:
        results = {}
        with open(path_to_csv) as file:
            reader = csv.DictReader(file)
            for row_number, row in enumerate(reader):
                results[row_number] = {}
                for key in row.keys():
                    results[row_number][key] = row[key]
                results[row_number]["workspace"] = PlaylistReviewEX.navigate_to_workspace(results[row_number])
                results[row_number]["name"] = results[row_number]["Link"] + "_" + results[row_number]["Version Name"]
                results[row_number]["show"] = results[row_number]["Link"].split("_")[0]
        return results

    def navigate_to_workspace(data : Dict[str, str]) -> str:
        raw_context = data["Link"]
        parsed_context = LogicEX.convert_string_to_context_agnostic(raw_context, "_")
        task_folder_name = data["Task"].lower()
        if task_folder_name == "vendor_nr_cleanup":
            task_folder_name = "vfx_vendor"
        return parsed_context["workspace"] + "/tasks/" + task_folder_name + "/.snapshot/" + data["Version Name"]

    def create_all_entries(version_up : bool):
        PlaylistReviewEX.delete_all_entries()
        PlaylistReviewEX.current_anchor = PlaylistReviewEX.top_left_anchor()
        to_run = [partial(PlaylistReviewEX.create_this_entry, entry, count) for count, entry in enumerate(PlaylistReviewEX.loaded_csv_data.values())]
        nuke_utils.run_these_tasks_with_progress_bar(to_run)
        if not version_up:
            return
        if not list(PlaylistReviewEX.loaded_csv_data.values()):
            return
        workspace_directory = PlaylistReviewEX.get_review_workspace(PlaylistReviewEX.loaded_csv_data[0]["show"])
        PlaylistReviewEX.sync_materials(workspace_directory)
        PlaylistReviewEX.save(workspace_directory)

    def tick_up_anchor():
        PlaylistReviewEX.current_anchor[1] += PlaylistReviewEX.entry_size[1]

    def delete_all_entries():
        for node in nuke.allNodes():
            nuke_utils.delete_node(node.name())
    
    def get_next_colour() -> int:
        PlaylistReviewEX.current_colour_index +=1
        if PlaylistReviewEX.current_colour_index >= len(PlaylistReviewEX.bg_colours.values()):
            PlaylistReviewEX.current_colour_index = 0
        return list(PlaylistReviewEX.bg_colours.values())[PlaylistReviewEX.current_colour_index]

    def create_this_entry(entry : Dict[str,str], count : int):
        backdrop_node = PlaylistReviewEX.create_backdrop_for_this_entry(entry)
        bd_spacing = [backdrop_node.knobs()["bdwidth"].getValue() / 10, 0]
        bd_anchor = [backdrop_node.knobs()["xpos"].getValue() + bd_spacing[0], 
            PlaylistReviewEX.y_axis_gap_between_entries * count +\
            backdrop_node.knobs()["ypos"].getValue() + backdrop_node.knobs()["bdheight"].getValue() / 2]
        nuke_utils.put_node_here(backdrop_node.name(), bd_anchor[0], bd_anchor[1])
        current_subanchor = [bd_anchor[0] + PlaylistReviewEX.subanchor[0], bd_anchor[1] + PlaylistReviewEX.subanchor[1]]
        for [key, value] in PlaylistReviewEX.get_whitelist_of_all_possible_reviewable_items().items():
            path_to_content = LogicEX.join(entry["workspace"], value)
            if not LogicEX.folder_exists(path_to_content):
                continue
            current_read_node_name = entry["name"] + "_" + key + PlaylistReviewEX.node_keyword
            current_read_node = nuke_utils.make_node("Read",current_read_node_name)
            nuke_utils.put_node_here(current_read_node_name, current_subanchor[0], current_subanchor[1])
            current_subanchor[0] += bd_spacing[0] 
            if len(os.listdir(path_to_content)) == 1 and nuke_utils.is_this_a_video(LogicEX.itera(path_to_content)[0]):
                nuke_utils.add_video_to_this_node(current_read_node, LogicEX.itera(path_to_content)[0])
            else:
                nuke_utils.add_image_sequence_to_this_node(current_read_node, path_to_content)
            current_read_node.knobs()["label"].setValue(key)
            current_read_node.knobs()["note_font_size"].setValue(15)
            current_read_node.knobs()["note_font_color"].setValue(0)
            current_read_node.knobs()["autolabel"].setValue("nuke.thisNode().knob(\"label\").value()")
    
    def create_backdrop_for_this_entry(entry : Dict[str,str]) -> nuke.Node:
        backdrop_node_name = entry["name"] + "_backdrop" + PlaylistReviewEX.node_keyword
        backdrop_node = nuke_utils.make_node("BackdropNode", entry["name"] + "_backdrop" + PlaylistReviewEX.node_keyword)
        nuke_utils.put_node_here(backdrop_node_name, PlaylistReviewEX.current_anchor[0], PlaylistReviewEX.current_anchor[1])
        backdrop_node.knobs()["bdwidth"].setValue(PlaylistReviewEX.entry_size[0])
        backdrop_node.knobs()["bdheight"].setValue(PlaylistReviewEX.entry_size[1])
        backdrop_node.knobs()["label"].setValue(entry["name"])
        backdrop_node.knobs()["tile_color"].setValue(PlaylistReviewEX.get_next_colour())
        backdrop_node.knobs()["note_font_size"].setValue(40)
        backdrop_node.knobs()["note_font_color"].setValue(0)
        PlaylistReviewEX.tick_up_anchor()
        return backdrop_node
    
    def get_whitelist_of_all_possible_reviewable_items() -> Dict[str,str]:
        # This is task-agnostic so expect some of these to not be available - skip those that don't exist
        return {
            "PLATE" : "input/PLATE/plate",
            "DENOISED" : "input/DENOISED/plate",
            "PRECOMP" : "input/PRECOMP/precomp",
            "FLOATING_FACE" : "output/FLOATING_FACE/floating_face",
            "FLOATING_FACE_REVIEW_EXR" : "output/FLOATING_FACE/review_exr",
            "FLOATING_FACE_REVIEW_MOV" : "output/FLOATING_FACE/review",
            "NR_CLEANUP" : "output/NR_CLEANUP/nr_cleanup",
            "VENDOR_REBOX" : "output/VendorRebox/vendor_rebox",
            "OBJ_REPLACE" : "output/OBJ_REPLACE/obj_replace",
            "OCCLUSIONS" : "output/OCCLUSIONS/occlusions",
             }
    
    def get_review_workspace(show_name : str):
        result = LogicEX.get_shows_root() + show_name + f"/tasks/review/{datetime.today().strftime('%Y-%m-%d')}"
        existing_versions = LogicEX.UI_itera_file_names_only(result, LogicEX.get_version_regex())
        if existing_versions == ["NONE"]:
            latest_version_as_int = 0
        else:
            latest_version_as_int = task_set_up.convert_version_to_int(existing_versions[-1])
        current_version_as_int = latest_version_as_int + 1
        current_version = task_set_up.convert_int_to_version(current_version_as_int)
        result = LogicEX.join(result, current_version)
        LogicEX.make(result)
        return result
    
    def save(workspace_path : str):
        path_to_folder = LogicEX.join(workspace_path, "REVIEW_SCRIPT")
        LogicEX.make(path_to_folder)
        nuke_utils.save(LogicEX.join(path_to_folder, PlaylistReviewEX.get_playlist_name() + ".nk"))

    def get_playlist_name():
        if "playlist_name" in PlaylistReviewEX.loaded_csv_data[0].keys():
            return "".join([c for c in PlaylistReviewEX.loaded_csv_data[0]["playlist_name"] if c.isalnum()])
        return "playlist"

    def sync_materials(workspace_path : str):
        """Save symlinks to all the content needed by all read nodes so it can be synced to S3."""
        path_to_folder = LogicEX.join(workspace_path, "SYNC_MATERIALS")
        LogicEX.make(path_to_folder)
        for entry in PlaylistReviewEX.loaded_csv_data.values():
            entry_name = entry["name"]
            entry_folder = LogicEX.join(path_to_folder, entry_name)
            LogicEX.make(entry_folder)
            for read_node in [node for node in nuke.allNodes() if\
                    entry_name in node.knobs()["name"].value()\
                    and node.Class() == "Read"\
                    and os.path.exists(os.path.dirname(node.knobs()["file"].evaluate()))]:
                node_name = read_node.knobs()["name"].value().replace(PlaylistReviewEX.node_keyword, "")
                node_source_folder = os.path.dirname(read_node.knobs()["file"].evaluate())
                node_target_folder = LogicEX.join(entry_folder, node_name)
                LogicEX.make(node_target_folder)
                to_do = [partial(LogicEX.copy_with_mono_symlinks, file, node_target_folder) for file in LogicEX.itera(node_source_folder)]
                nuke_utils.run_these_tasks_with_progress_bar(to_do)
                node_source_folder = os.path.dirname(read_node.knobs()["file"].evaluate())
                current_node_path_ending = read_node.knobs()["file"].getValue().split("/")[-1]
                new_node_path = LogicEX.join(node_target_folder, current_node_path_ending)
                read_node.knobs()["file"].setValue(new_node_path)