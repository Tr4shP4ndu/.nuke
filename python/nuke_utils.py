import nuke
import logging
import os
from pathlib import Path
import re
import tempfile
import time
from threading import Thread
from typing import Any, Callable, Dict, List

def delete_all():
    for node in nuke.allNodes():
        nuke.delete(node)
def unselect_all():
    for node in nuke.allNodes():
        node.setSelected(False)
def make_node(Type : str, name: str):
    result = nuke.createNode(Type)
    result.setName(name)
    unselect_all()
    return result
def delete_node(name:str):
    nuke.delete(nuke.toNode(name))
def put_node_here(node_name : str, x : int, y : int):
    nuke.toNode(node_name).setXYpos(x,y)
def add_image_sequence_to_this_node(node : nuke.Node, path_to_image_sequence : str):
        shot_length = len(os.listdir(path_to_image_sequence))
        file_format = "." + os.listdir(path_to_image_sequence)[0].split(".")[-1]
        pound_signs = "#" * len(os.listdir(path_to_image_sequence)[0].split(".")[-2])
        file_name_of_first_frame = sorted(os.listdir(path_to_image_sequence))[0]
        file_name_of_first_frame_without_frame_number = file_name_of_first_frame[:-10]
        first_frame = str(int(sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2]))
        last_frame = str(int(sorted(os.listdir(path_to_image_sequence))[-1].split(".")[-2]))
        ending = pound_signs + file_format + " "
        shot_end = shot_length
        first_frame_hashed = str(path_to_image_sequence) + "/" + (file_name_of_first_frame_without_frame_number + ending + first_frame + "-" + last_frame)
        node.knobs()["file"].fromUserText(first_frame_hashed)
        node.knobs()["first"].setValue(int(first_frame))
        node.knobs()["last"].setValue(int(last_frame))
        node.knobs()["origfirst"].setValue(int(first_frame))
        node.knobs()["origlast"].setValue(int(last_frame))
        node.knobs()["colorspace"].setValue("Output - sRGB")
        node.knobs()["on_error"].setValue("black")
        if file_format == ".png":
            node.knobs()["colorspace"].setValue("ACES - ACEScct")
        node.knobs()["frame_mode"].setValue("start at")
        node.knobs()["frame"].setValue("1")
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