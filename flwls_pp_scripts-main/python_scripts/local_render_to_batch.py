import nuke
import re
import json
import ssl
import os
import tempfile
import uuid
import urllib.request
from datetime import datetime
from http import HTTPStatus
from http.client import HTTPResponse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import random
import traceback
from write_flwls import internal_render
random.seed(datetime.now())


NUKE_LOCATION = os.environ.get('NUKE_EXE_PATH')

LOCAL_USERNAME = os.environ.get("USER")
TRUESYNC_ENDPOINT = os.environ.get('TRUESYNC_SERVER_API_ENDPOINT')
FFS_ENDPOINT = os.environ.get('FFS_API_ENDPOINT')
SCRATCH_SAVE_ROOT = tempfile.gettempdir()
SHOT_NAME_REGEX = re.compile(r"(?P<file_ext>[\._](%0\d+d|#+).[a-z]{3}$)")
CONTEXT_REGEX = re.compile(r"shows/(?P<shows>\w+)(/episodes/(?P<episode>ep\d{2}))?(/parts/(?P<part>pt\d{2}))?(/shots/(?P<shot>\d{4}))?(/languages/(?P<languages>[a-z]{3}))?(/variants/(?P<variants>\w+_main))?")
MONITOR_ENDPOINT = os.environ.get('JOB_MONITORING_SERVICE_HOSTNAME')
PREP_RENDER_SCRIPT_TEMPLATE = """
import nuke
import sys
import os

inScript = sys.argv[1]
nuke.scriptOpen(inScript)
nuke.toNode('{write_node_name}').knob("beforeRender").setValue('')
nuke.toNode('{write_node_name}').knob("file").setValue('{full_path}')
nuke.root().knob('colorManagement').setValue('OCIO')
nuke.root().knob('OCIO_config').setValue("aces_1.2")
nuke.scriptSave(inScript)

"""

def get_write_path(write_node_name: str) -> Path :
    """
    Short function here that will find the write node path, fill out any variables that it may have coded into it 
    via tcl commands, and then make the directory for it to render to. It returns the write path
    """

    write_path=nuke.toNode(f'{write_node_name}').knob('file').value()
    base_file_name = nuke.toNode(f'{write_node_name}').knob('file').evaluate().split("/")[-1].split(".")[0]

    write_regex_results = SHOT_NAME_REGEX.search(write_path)
    
    if write_regex_results is None:
        return Path(write_path)

    write_ext = write_regex_results.groupdict()
    evaluate_info = nuke.toNode(f'{write_node_name}').knob('label').evaluate()
    nuke.toNode(f'{write_node_name}').knob('label').setValue('[value file]')
    new_path = Path(evaluate_info).parent / str(base_file_name + write_ext["file_ext"])
    
    return new_path


def prep_nuke_script_for_render(write_node_name: str, render_script) -> None:

    """
    Uses the above PREP_RENDER_SCRIPT_TEMPLATE to create a python script. That script is then ran in terminal, opening up nuke,
    changing the write node output path, and then saves the script so that the file will render out to the correct location. 
    """
    new_path = get_write_path(write_node_name)
    
    write_node_modify = f'{SCRATCH_SAVE_ROOT}/prep_nuke_render_script{str(uuid.uuid4())}.py'
    prep_render_script = PREP_RENDER_SCRIPT_TEMPLATE.format(
        write_node_name=write_node_name, full_path=str(new_path)
    )

    with open(write_node_modify, "a+") as prep_render_script_file:
        prep_render_script_file.write(prep_render_script)
    command = f"{NUKE_LOCATION} -t {write_node_modify} {render_script}"
    os.system(command)
    os.unlink(write_node_modify)


def make_render_snapshot() -> Path:
    """makes a snapshot of the current script and stores it in a folder labeled .render_scripts.
    This is being done in case the user submits a render and then changes some things before the render posts
    which may cause errors down the line. 

    Function is returning a string (script_snapshot_path)
    """
    script_path = Path(nuke.scriptName())
    time_addition = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(script_path.name).stem
    script_snapshot_path = script_path.parent / f".{filename}_render_snapshot_{time_addition}.nk"

    nuke.scriptSaveToTemp(str(script_snapshot_path))
    return script_snapshot_path


def make_render_snapshot_multithreaded() -> Path:
    """Snapshot which allows two scripts to be made at the same time without a data race.
    """
    script_path = Path(nuke.scriptName())
    random_hash = hex(random.randint(1,999999))
    filename = Path(script_path.name).stem
    script_snapshot_path = script_path.parent / f".{filename}_render_snapshot_{random_hash}.nk"

    nuke.scriptSaveToTemp(str(script_snapshot_path))
    return script_snapshot_path

def get_user_input() -> List[int]:
    """Gets data of frame ranges from the selected write node and presents that information to the user 
    as an int in a popup window. If that is the desired frame range than selecting okay will return that stock value, 
    however if that is not the intended value and they want to render a shorter range, whatever int based value that 
    is put into that pop up will be returned.
    """

    first_frame = int(nuke.root().knob("first_frame").value())
    last_frame = int(nuke.root().knob("last_frame").value())
    frame_range = f"{int(first_frame)}-{int(last_frame)}"
    frame_range_as_int = last_frame-first_frame

    ret = nuke.getFramesAndViews('get frame range', frame_range)
    if ret is None:
        raise Exception("Process Canceled")

    the_range = ret[0]

    if frame_range_as_int <= 1:
        return the_range, 1 # can't split one frame into a batch

    for node in nuke.selectedNodes():
        knob_name = "filetype_flwls" if "filetype_flwls" in [knob for knob in node.knobs()] else "file_type"
        if knob_name in node.knobs() and node.knobs()[knob_name].value() in ["mov", ".mp4"]:
            return the_range, 1 # not currently supporting splitting a video into subset renders

    ret = nuke.getInput(f'Split into X chunks. (Min: 1, Max: {frame_range_as_int+1})', "1")
    
    if ret is None:
        raise Exception("Process Canceled")
    
    if not ret[0].isnumeric():
        raise Exception("Must be a valid integer")

    chunks = int(ret[0])

    if chunks > frame_range_as_int+1:
        chunks = frame_range_as_int+1
    if chunks < 1:
        chunks = 1
    
    return the_range, chunks


def create_urllib_request(method: str, end_point: str, ssl_included: Optional[bool] = False, json_payload: Optional[dict] = None) -> HTTPResponse:
    if json_payload is not None:
        json_payload = json.dumps(json_payload).encode("utf-8")

    headers = {}
    if method == "POST":
        headers = {"Content-Type": "application/json"}

    request = urllib.request.Request(
        end_point,
        data=json_payload,
        method=method,
        headers=headers
    )

    ssl_context = None
    if ssl_included:
        ssl_context = ssl._create_unverified_context()
    
    return urllib.request.urlopen(request, context=ssl_context)


def query_show_service(show_name) -> bool:
    try:
        response = create_urllib_request("GET", f"{FFS_ENDPOINT}/get/show/{show_name}", True)
        return response.status == HTTPStatus.OK

    except:
        return False


def check_shot_context() -> dict:
    saved_script = Path(nuke.scriptName())
    context_match = CONTEXT_REGEX.search(str(saved_script.parent))
    
    extracted_context = {}
    if context_match is not None:
        extracted_context = context_match.groupdict()

    show_name = extracted_context.get("shows") or ""
    episode = extracted_context.get("episode") or ""
    part = extracted_context.get("part") or ""
    shot = extracted_context.get("shot") or ""
    language = extracted_context.get("languages") or ""
    variant = extracted_context.get("variants") or ""
    context_level = "shot" 
    if language != "":
        context_level += "_language"
    if variant != "":
        context_level += "_feature"
        
    p = nuke.Panel("Context Checking")
    p.addSingleLineInput("Show", show_name)
    p.addSingleLineInput("Episode", episode)
    p.addSingleLineInput("Part", part)
    p.addSingleLineInput("Shot", shot)
    p.addSingleLineInput("Language", language)
    p.addSingleLineInput("Variant", variant)
    p.addSingleLineInput("Context Level", context_level)
    
    ret = p.show()

    if ret == False:
        raise Exception("Process Canceled")

    show_name = p.value("Show")
    episode = p.value("Episode")
    part = p.value("Part")
    shot = p.value("Shot")
    language = p.value("Language")
    variant = p.value("Variant")
    context_level = p.value("Context Level")

    while query_show_service(show_name) != True:
        show_name = nuke.getInput("Please enter a valid, in production show", show_name)
        if show_name is None:
            raise Exception("Process Canceled")

    context_values = episode + "/" + part + "/" + shot
    if language != "":
        context_values += "/" + language
    if variant != "":
        context_values += "/" + variant

    return {
        "show": show_name,
        "episode": episode,
        "part": part,
        "shot": shot,
        "language": language,
        "variant": variant,
        "context_level" : context_level,
        "context_values" : context_values,
    }


def post_job_monitor_request(shot_context : Dict[str, str]) -> str:
    date_created = datetime.now()
    id_to_regester = str(uuid.uuid4())
    monitor_command = {
        "context": shot_context,
        "jobType": "general_render_script",
        "jobId":id_to_regester,
        "createdAt":date_created.isoformat(),
        "computations": [],
        "user": LOCAL_USERNAME
    }

    try:
        response = create_urllib_request("POST", f"{MONITOR_ENDPOINT}/api/jobs/register-job", False, monitor_command)
        return id_to_regester
    except:
        return None


def post_render_request(write_node: str, render_script: str,  frame_range: str, shot_context : Dict[str, str], show_post_message : bool) -> str:
    """After all variables have been determined this function will post the job to the 
    compositing_nuke_job batch queue as a "general" job
    This function will also post to the job monitor

    Items in the monitor_command and where they come from
    job_id= batch_queue posted job id
    job_type=what kind of job its posting
    context= nothing (Special job since it sits outside of the pipeline but can find context if needed)
    time_created=current time when created
    computations=nothing (Followed test job, not sure if this is needed)
    """
    for key in shot_context.keys():
        if shot_context[key] == "":
            shot_context[key] = "NONE" # CLI can't accept an argument that's an empty string
    job_command = [
        "general_render_script",
        shot_context["show"],
        shot_context["context_level"],
        shot_context["context_values"],
        write_node,
        str(render_script),
        frame_range,
    ]
    
    payload = {
        "job_name": "compositing_nuke_job",
        "payload": job_command
    }
    response = create_urllib_request("POST", f"{TRUESYNC_ENDPOINT}/pipeline/job", True, payload)
    json_response = json.load(response)

    if not response.status == HTTPStatus.ACCEPTED:
        raise Exception("Failed to send job to batch render, please contact a TD and provide a ticket for further assistance.")
    
    message = "Job successfully submitted, your Job Id is " + str(json_response["jobId"]) + " and you can watch the job on the job monitor."

    if show_post_message:
        nuke.message(message)
    
    return message


def post_render_requests_split(write_node: str, frame_range : str, chunks : int, shot_context : Dict[str,str], mode):
    lowest, highest = int(frame_range.split("-")[0]), int(frame_range.split("-")[1])
    split_size = (highest - lowest) // chunks
    all_frames_to_render = [f for f in range(lowest, highest+1)]
    post_message = f"Your render job was split into {chunks} different jobs approximately {split_size if split_size > 0 else 1} {'frames' if split_size > 1 else 'frame'} in size each:\n\n"
    while all_frames_to_render:
        current_frames_to_render = []
        for f in range(0, split_size+1):
            if all_frames_to_render:
                current_frames_to_render.append(all_frames_to_render.pop(0))
        if mode == "Write":
            render_script = make_render_snapshot_multithreaded()
            prep_nuke_script_for_render(write_node, render_script)
        else:
            render_script = nuke.root().name()
        if len(current_frames_to_render) == 0:
            subset = str(current_frames_to_render[0])
        else:
            subset = f"{current_frames_to_render[0]}-{current_frames_to_render[-1]}"
        post_message += post_render_request(write_node, render_script, subset, shot_context, False) + "\n\n"
    nuke.message(post_message)

def ensure_read_node_colourspace_matches_script_setting():
    for node in [n for n in nuke.allNodes() if n.Class() == "Read"]:
        node.knobs()["colorspace"].setValue(nuke.root().knobs()["workingSpaceLUT"].value())

def main():
    try:
        if TRUESYNC_ENDPOINT is None:
            raise Exception("No Endpoint enviroment variable found")
        if MONITOR_ENDPOINT is None:
            raise Exception("No Endpoint for the job monitor found")
        
        node_selection = nuke.selectedNodes()

        incorrect_selection = "Please select one valid 'Write' node"

        if len(node_selection) != 1:
            raise Exception(incorrect_selection)
        
        if not (node_selection[0].Class() == "Write" or "Write_Flwls" in node_selection[0].name()):
            raise Exception(incorrect_selection)
        
        mode = "Write_Flwls" if "Write_Flwls" in node_selection[0].name() else "Write"

        node_name = node_selection[0].name()
        user_input = get_user_input()
        frame_range = user_input[0]
        chunks = user_input[1]
        shot_context = check_shot_context()
        if mode == "Write":
            render_script = make_render_snapshot()
            prep_nuke_script_for_render(node_selection[0].name(), render_script)
        if mode == "Write_Flwls":
            ensure_read_node_colourspace_matches_script_setting()
            render_script = nuke.root().name()
            internal_render.current_gizmo_pointer = node_selection[0]
            nuke.selectedNodes()[0].knobs()["refresh"].execute()
            internal_render.current_gizmo_pointer.knobs()["disable_execution"] = "1"
            datatype = internal_render.get_internal_render_data_type(
                internal_render.current_gizmo_pointer.knobs()["datatype_flwls"].value(),
                internal_render.current_gizmo_pointer)
            datatype.call_before_logic()
            datatype.remove_before_and_after_logic()
            nuke.scriptSave()
        if chunks == 1:
            post_render_request(node_selection[0].name(), render_script, frame_range,shot_context,True)
        else:
            post_render_requests_split(node_selection[0].name(), frame_range, chunks,shot_context, mode)
    except Exception as err:
        nuke.message(traceback.format_exc())
