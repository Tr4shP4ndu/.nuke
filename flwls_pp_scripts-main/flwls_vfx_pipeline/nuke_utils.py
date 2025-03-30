import nuke
import logging
import os
from pathlib import Path
import re
import tempfile
import time
from threading import Thread
from typing import Any, Callable, Dict, Set, Tuple, List
from datetime import datetime

def delete_all():
    for node in nuke.allNodes():
        nuke.delete(node)
def unselect_all():
    for node in nuke.allNodes():
        node.setSelected(False)
def make_node(Type : str, name: str):
    result = nuke.createNode(Type, inpanel=False)
    result.setName(name)
    unselect_all()
    return result
def make_read_from_write(Type : str, name : str, parent_node : nuke.Node, folderpath : str, start_frame : int):
    with nuke.root():
        parent_node_position = get_node_position(parent_node)
        offset = [-75,75]
        read_node = make_node(Type, name)
        if len(os.listdir(folderpath)) > 1:
            add_image_sequence_to_this_node(read_node, folderpath)
        else:
            single_element = os.path.join(folderpath, os.listdir(folderpath)[0])
            read_node.knobs()["file"].setValue(single_element)
        read_node.knobs()["frame_mode"].setValue("start_at")
        read_node.knobs()["frame"].setValue(str(start_frame))
        put_node_here(read_node.knobs()["name"].value(), parent_node_position[0]+offset[0], parent_node_position[1]+offset[1])
        read_node_new_name = parent_node.knobs()["filename_flwls"].value()
        if read_node_new_name == "":
            read_node_new_name = parent_node.knobs()["datatype_flwls"].value()
        read_node.knobs()["name"].setValue(read_node_new_name)
def delete_node(name:str):
    nuke.delete(nuke.toNode(name))
def put_node_here(node_name : str, x : int, y : int):
    nuke.toNode(node_name).setXYpos(int(x),int(y))
def get_node_position(node : nuke.Node) -> Tuple[int,int]:
    return [node.xpos(), node.ypos()]
def add_image_sequence_to_this_node(node : nuke.Node, path_to_image_sequence : str):
        shot_length = len(os.listdir(path_to_image_sequence))
        file_format = "." + os.listdir(path_to_image_sequence)[0].split(".")[-1]
        file_name_of_first_frame = sorted(os.listdir(path_to_image_sequence))[0]
        file_name_of_first_frame_without_frame_number = file_name_of_first_frame[:-10]
        first_frame = 0
        last_frame = 0
        frame_as_string = ""
        try:
            frame_as_string = sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2]
            first_frame = str(int(sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2]))
            last_frame = str(int(sorted(os.listdir(path_to_image_sequence))[-1].split(".")[-2]))
        except ValueError:
            frame_as_string = sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2].split("_")[-1]
            first_frame = str(int(sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2].split("_")[-1]))
            last_frame = str(int(sorted(os.listdir(path_to_image_sequence))[-1].split(".")[-2].split("_")[-1]))
        pound_signs = "#" * len(frame_as_string)
        ending = pound_signs + file_format + " "
        shot_end = shot_length
        first_frame_hashed = str(path_to_image_sequence) + "/" + (file_name_of_first_frame_without_frame_number + ending + first_frame + "-" + last_frame)
        node.knobs()["file"].fromUserText(first_frame_hashed)
        node.knobs()["first"].setValue(int(first_frame))
        node.knobs()["last"].setValue(int(last_frame))
        node.knobs()["origfirst"].setValue(int(first_frame))
        node.knobs()["origlast"].setValue(int(last_frame))
        node.knobs()["on_error"].setValue("black")
def is_this_a_video(path : str):
    return path.split(".")[-1] in ["mov","mp4"]
def add_video_to_this_node(node : nuke.Node, path_to_video : str):
    node.knobs()["file"].fromUserText(path_to_video)
def make_tmp_nuke_script() -> None:
    if nuke.root().name() == "Root":
        filepath = tempfile.gettempdir() + "/temp_nuke_script_" + os.environ["USER"]+ ".nk"
        nuke.scriptSaveAs(filename=filepath, overwrite= 1)
def make_tmp_nuke_script_then_open(script_path : str) -> None:
    make_tmp_nuke_script()
    nuke.scriptOpen(script_path)
def run_headless_script(nuke_script_location : str, python_script_location : str) -> None:
    os.system(os.environ["NUKE_EXE_PATH"] + f" -t {python_script_location} {nuke_script_location}")
def nuke_user_path_from_dir(frames_dir: Path, regex : re.Pattern) -> str:
    frame_nums = []
    matched_name = None
    for frame_path in frames_dir.iterdir():
        frame_file_match = regex.search(frame_path.name)
        if frame_file_match is None:
            continue

        file_name, delimiter, frame_num, file_ext = frame_file_match.groups()
        frame_nums.append(frame_num)

        if matched_name is None:
            matched_name = file_name
        if file_name != matched_name:
            continue

    if matched_name is None:
        raise Exception("No sequence found in directory")

    nuke_frame_padding = "#" * len(frame_nums[0])
    return (
        f"{file_name}{delimiter}{nuke_frame_padding}"
        f"{file_ext} {min(frame_nums)}-{max(frame_nums)}"
    )
def open(file : str) -> None:
    nuke.scriptOpen(file)
def save(file : str) -> None:
    nuke.scriptSaveAs(filename=file, overwrite=True)
def run_these_tasks_with_progress_bar(tasks : List[Callable]) -> List[str]:
    def how_much_left(done_tasks, number_of_tasks):
        return int(done_tasks*100/number_of_tasks)
    results = ["No tasks run yet."]
    number_of_tasks = len(tasks)
    if not number_of_tasks:
        return results
    done_tasks = 0
    progress_node = nuke.ProgressTask(f"Tasks: {number_of_tasks}")
    progress_node.setProgress(0)
    for task in tasks:
        results.append(task())
        done_tasks +=1
        progress_node.setProgress(how_much_left(done_tasks,number_of_tasks))
    return results
def run_these_tasks_parallel_with_progress_bar(tasks: List[Callable]) -> List[str]:
    number_of_tasks = len(tasks)
    if not number_of_tasks:
        return results
    finished_tasks = {}
    progress_node = nuke.ProgressTask(f"Tasks: {number_of_tasks}")
    progress_node.setProgress(0)
    waiting = "Waiting"
    def do_task(task):
        finished_tasks[str(task)] = waiting
        finished_tasks[str(task)] = task()
    results = ["No tasks run yet."]
    threads = [Thread(target=do_task, args=(task,)) for task in tasks]
    for thread in threads:
        thread.start()
    while waiting in finished_tasks.values():
        time.sleep(1)
        number_of_finished_tasks = len([task for task in finished_tasks.values() if task != waiting])
        progress_node.setProgress(int(number_of_finished_tasks*100/number_of_tasks))
    return list(finished_tasks.values())
def format_text(open : str, content: str, close : str) -> str:
    return open + content + close
def get_coloured_text(content : str, colour : str):
    return format_text("<font color = '{}'>".format(colour),content, "</font>")
def print_to_console(message : str) -> None:
    """print() statements in nuke don't show in console, use logging."""
    logging.getLogger().handlers.clear()
    logger_handler = logging.StreamHandler()
    logger_handler.setFormatter(logging.Formatter(str(message)))
    logging.getLogger().addHandler(logger_handler)
    logging.getLogger().error(" ")
def copy_camera_animation(copy_from_node_name : str, copy_to_node_name : str):
    original_camera = nuke.toNode(copy_from_node_name)
    new_camera = nuke.toNode(copy_to_node_name)
    new_camera.knob("read_from_file").setValue(False)
    for knob_name in [knob for knob in original_camera.knobs() if original_camera.knobs()[knob].isAnimated() and "copyAnimations" in dir(original_camera.knobs()[knob])]:
        new_camera.knobs()[knob_name].setAnimated(True)
        new_camera.knobs()[knob_name].copyAnimations(original_camera.knobs()[knob_name].animations())
def add_backdrop_next_to_node(target_node : str, node_name: str, message_text : str, offset : Tuple[int], colour: int = 0):
    node = make_node("BackdropNode", node_name)
    node.knobs()["tile_color"].setValue(colour)
    node.knobs()["label"].setValue(message_text)
    existing_location = get_node_position(nuke.toNode(target_node))
    target_location = [existing_location[x] + offset[x] for x in [0,1]]
    put_node_here(node.name(), target_location[0], target_location[1])
    node.knobs()["z_order"].setValue(2)
    node.knobs()["bdwidth"].setValue(150)
def convert_nuke_frame_range_to_string(ranges : List[List[int]]) -> str:
    if not ranges:
        return "None"
    results_as_string = ""
    for r in ranges:
        if len(r) == 1:
            results_as_string+=(f"{r[0]},")
        else:
            results_as_string+=(f"{r[0]}-{r[-1]},")
    return results_as_string[:-1]
def get_frames_based_on_input(folder : str) -> List[int]:
    return [int(re.search(r"[0-9]{6}", file).group(0)) for file in sorted(os.listdir(folder))]
def get_nuke_frame_ranges_based_on_input(frames: List[int]) -> List[List[int]]:
    if not frames:
        return []
    counter = 0
    current_range = []
    ranges = []
    current = 0
    while counter < len(frames):
        if frames[counter] == current+1:
            current_range.append(frames[counter])
        else:
            if current_range:
                ranges.append(current_range)
            current_range = [frames[counter]]
        current = frames[counter]
        counter +=1
    ranges.append(current_range)
    return ranges
def get_project_framerange() -> nuke.FrameRange:
    all_frames = [int(nuke.root().knobs()[key].value()) for key in ["first_frame", "last_frame"]]
    return nuke.FrameRange(all_frames[0], all_frames[-1], 1)
def get_missing_frames_based_on_file_input(image_sequence_folder_path : str) -> List[int]:
    r = get_frames_based_on_input(image_sequence_folder_path)
    all_frames = get_project_framerange()
    return [frame for frame in all_frames if frame not in r]
def load_camera_from_abc(node_name : str, filepath : str):
    camera = nuke.toNode(node_name)
    camera.knob("frame_rate").setValue(nuke.root().knobs()['fps'].value())
    camera.knob("use_frame_rate").setValue(True)
    camera.knob("read_from_file").setValue(True)
    camera.knob("file").fromUserText(filepath)
def get_current_nuke_version():
    return nuke.NUKE_VERSION_STRING
def get_all_nodes_that_contain_substring_in_name(substring : str) -> List[nuke.Node]:
    return [node for node in nuke.allNodes() if substring in node.name()]
def get_current_date() -> str:
    return datetime.today().strftime('%Y-%m-%d')
def get_current_user():
    return os.environ["USER"]
def get_any_write_node():
    return [node for node in nuke.allNodes() if node.Class() == "Write"][0]