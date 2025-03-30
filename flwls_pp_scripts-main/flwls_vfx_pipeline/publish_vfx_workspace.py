from functools import partial
import json
import os
import logging
import nuke
from pathlib import Path
import re
import shutil
from typing import Dict, Optional, Union
from urllib.request import Request, urlopen
import ssl
from threading import Thread

# internal imports
import FlwlsVFXPipelinePanel
from FlwlsVFXPipelinePanel import LogicEX
import task_set_up
import nuke_utils

import sys
sys.path.append(os.path.dirname(__file__))
import publish_review_panel


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# console handler
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

logger.addHandler(ch)


VERSION_REGEX = re.compile("v\d+")

def publish_headless(filepath : Path):
    """Publishing entrypoint for headless nuke."""
    nuke_utils.print_to_console(copy_and_publish_render(filepath, False))

def publish_node():
    """Publishing entrypoint from FlwlsVFXPipelinePanel."""
    if not nuke.selectedNodes or nuke.selectedNode().Class() != "Read":
        nuke.message("Please select a Read node to publish.")
        return
    filepath = Path(nuke.selectedNode().knob("file").value())
    result = copy_and_publish_render(filepath, True)
    message = "Monitor job using TrueSync notifications.\n\n" +  str(filepath) + "\n\n" + str(result)
    nuke_utils.print_to_console(str(result))
    nuke.message(message)

def prelim_check():
    all_write_nodes = [node for node in nuke.allNodes() if node.Class() == "Write"]
    for node in all_write_nodes:
        path = node.knobs()["file"].evaluate()
        if path is None or not os.path.exists(os.path.dirname(path)) or not os.listdir(os.path.dirname(path)):
            nuke.message(f"The write node {node.knobs()['name'].value()} has not been rendered yet.")
            return False
    return True

def sync_latest_render_to_s3():
    if not prelim_check():
        return
    write_node = nuke_utils.get_any_write_node()
    render_element_filepath = Path(write_node.knob("file").evaluate())
    copy_render(render_element_filepath, True, True)
    context = LogicEX.get_context_based_on_current_path()
    workspace_version = get_workspace_version_from_filename(render_element_filepath)
    review_notes_path = publish_review_panel.review_panel_popup(context["task"], workspace_version)
    task_level = task_set_up.get_task_definition(context["task"]).task_level.value.replace("feature","variant") # script expects variant not feature
    sync_command = sync_command = f"/usr/local/bin/create_workspace_cache -p send -t {task_level} "
    for level, name in {"show" : "-s", "episode" : "-e", "part" : "--part", "shot" : "--shot", "language" : "--lang", "variant" : "--variants", "task" : "--task"}.items():
        if level in context.keys():
            sync_command += f"{name} {context[level]} "
    sync_command += f"--output {workspace_version}"
    Thread(target=os.system, args=(sync_command,)).start()
    nuke.message("Started sync job. Check the console for more information.")
    
def copy_render(render_element_filepath: Path, using_GUI = False, using_symlink = False) -> None:
    context = LogicEX.get_context_based_on_current_path()
    task_definition = task_set_up.get_task_definition(context["task"])
    render_element = task_definition.publish_datatype

    render_version_folder = get_render_version_folder_from_render_path(render_element_filepath)
    output_folder = get_output_folder_from_render_version_folder(
        render_version_folder=render_version_folder,
        render_element=render_element
    )
    copy_render_version_folder_contents_to_outputs_folder(render_version_folder, output_folder, using_GUI, using_symlink)

def copy_and_publish_render(render_element_filepath: Path, using_GUI = False) -> Optional[Dict[str, str]]:
    copy_render(render_element_filepath, using_GUI)
    workspace_version = get_workspace_version_from_filename(render_element_filepath)
    render_version_folder = get_render_version_folder_from_render_path(render_element_filepath)
    context = LogicEX.get_context_based_on_current_path()
    task_definition = task_set_up.get_task_definition(context["task"])
    render_element = task_definition.publish_datatype
    output_folder = get_output_folder_from_render_version_folder(
        render_version_folder=render_version_folder,
        render_element=render_element
    )
    review_mov_path = get_review_mov_path(output_folder=output_folder)
    review_exr_path = get_review_exr_path(output_folder=output_folder)
    review_notes_path = publish_review_panel.review_panel_popup(context["task"], workspace_version)

    return publish(
        publish_type=render_element,
        context=context,
        task=task_definition,
        workspace_version=workspace_version,
        relative_review_path=review_mov_path,
        exr_review_path=review_exr_path,
        notes_review_path=review_notes_path,
        add_to_playlist=True
    )

def publish_latest_render_gui():
    results = publish_latest_render()
    nuke.message(str(results))

def publish_latest_render() -> Dict[str, str]:
    write_node = nuke_utils.get_any_write_node()
    render_element_filepath = Path(write_node.knob("file").evaluate())
    render_version_folder = get_render_version_folder_from_render_path(render_element_filepath)
    context = LogicEX.get_context_based_on_current_path()
    task_definition = task_set_up.get_task_definition(context["task"])
    render_element = task_definition.publish_datatype
    workspace_version = get_workspace_version_from_filename(render_element_filepath)
    output_folder = get_output_folder_from_render_version_folder(
        render_version_folder=render_version_folder,
        render_element=render_element
    )
    review_mov_path = get_review_mov_path(output_folder=output_folder)
    review_exr_path = get_review_exr_path(output_folder=output_folder)
    review_notes_folder = output_folder.parent / "notes_to_publish"

    review_notes_path = review_notes_folder / LogicEX.itera(review_notes_folder)[0]
    if not os.path.exists(review_notes_path):
        review_notes_path = publish_review_panel.review_panel_popup(context["task"], workspace_version)
    
    return publish(
        publish_type=render_element,
        context=context,
        task=task_definition,
        workspace_version=workspace_version,
        relative_review_path=review_mov_path,
        exr_review_path=review_exr_path,
        notes_review_path=review_notes_path,
        add_to_playlist=True
    )

def publish(
    publish_type: task_set_up.TaskType,
    context: Dict[str,str],
    task : task_set_up.TaskDefinition,
    workspace_version: str,
    relative_review_path: Path,
    exr_review_path: Optional[Path],
    notes_review_path: Optional[Path],
    add_to_playlist: Optional[bool]
) -> Optional[Dict[str, str]]:
    url = f"{os.environ['TRUESYNC_SERVER_API_ENDPOINT']}/pipeline/job"

    context_values_as_string = LogicEX.from_dict_to_string(context, [k for k in context.keys() if k not in ["show","task","version"]], "/")

    job_command = [
        context["task"],
        "publish-workspace",
        context["show"],
        task.task_level.value,
        context_values_as_string,
        workspace_version,
        str(relative_review_path),
    ]

    if exr_review_path is not None:
        job_command.extend(["--review-frames", str(exr_review_path)])

    user = os.environ.get("USER")
    if user is not None:
        job_command.extend(["--sg-user", f"{user}@flawlessai.com"])
    
    if notes_review_path is not None:
        job_command.extend(["--notes", str(notes_review_path)])

    if add_to_playlist:
        job_command.extend(["--add-to-playlist"])                      
    payload = {
        "job_name": "compositing_nuke_job",
        "payload": job_command
    }

    payload = json.dumps(payload).encode("utf-8")

    req = Request(
        url=url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
        },
    )
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    res = urlopen(req, context=ssl_ctx)

    if res.status < 200 or res.status >= 300:
        raise RuntimeError(
            f"Failed to send request. {res.status}: {res.reason} - {res.msg} - {res.read()}"
        )

    return json.loads(res.read())

def copy_render_version_folder_contents_to_outputs_folder(render_version_folder: Path, output_folder: Path, gui : bool, using_symlink : bool):
    LogicEX.remake(output_folder)
    instructions = []
    copy_function = LogicEX.hard_copy if not using_symlink else LogicEX.copy_with_mono_symlinks
    for input_subfolder in LogicEX.itera(render_version_folder):
        output_subfolder = LogicEX.join(output_folder, Path(input_subfolder).name)
        LogicEX.make(output_subfolder)
        [instructions.append(partial(copy_function, source, output_subfolder)) for source in LogicEX.itera(input_subfolder)] 
    if gui:
        nuke_utils.run_these_tasks_with_progress_bar(instructions)
    else:
        [inst() for inst in instructions]


def get_output_folder_from_render_version_folder(render_version_folder: Path, render_element: str) -> Path:
    output_folder = render_version_folder.parents[3] / "output" / render_element
    return output_folder


def get_render_version_folder_from_render_path(render_filepath: Path) -> Path:
    render_folder = render_filepath.parents[1]
    if VERSION_REGEX.search(render_folder.name) is None:
        raise ValueError(f"No version number in render folder path: {render_folder}")
    return render_folder


def get_workspace_version_from_filename(render_element_filename: str) -> str:
    render_version_folder = get_render_version_folder_from_render_path(render_element_filename)
    workspace_version = render_version_folder.parts[-5]
    if VERSION_REGEX.search(workspace_version) is None:
        raise ValueError(f"'{workspace_version}' is not in the valid version format")
    return workspace_version


def get_review_mov_path(output_folder: Path) -> Path:
    mov_folder = output_folder / "review_mov"
    if not mov_folder.is_dir():
        raise ValueError(f"No review mov folder in {output_folder}")
    mov_files = list(mov_folder.glob("**/*.mov"))
    if len(mov_files) == 0:
        raise ValueError(f"No review .mov file in {mov_folder}")
    mov_files.sort()
    mov_path = mov_files[0]
    mov_parts = mov_path.parts[-4:]
    return Path(*mov_parts)


def get_review_exr_path(output_folder: Path) -> Optional[Path]:
    exr_folder = output_folder / "review_exr" 
    if not exr_folder.is_dir():
        raise ValueError(f"No EXR review file in folder {output_folder}")
    exr_files = list(exr_folder.glob("*.exr"))
    if len(exr_files) == 0:
        logger.debug("No EXRs found in directory. Publishing without them.")
        return None
    first_file = exr_files[0].name.split(".")[0]
    for item in exr_files:
        if first_file in item.name:
            continue
        else:
            raise ValueError(f"Exrs found in this directory do not belong to the same sequence: Found: {item.name} Needs to match: {first_file}" )
            
    return exr_folder


