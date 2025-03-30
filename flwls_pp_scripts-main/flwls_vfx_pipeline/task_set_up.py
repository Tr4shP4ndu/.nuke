from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union
from dataclasses import dataclass
import nuke
import nuke_utils
import shutil
import tempfile
import inspect
import re
import os


class TaskType(Enum):
    VFX_OCCLUSION = "vfx_occlusion"
    VFX_INPAINT = "vfx_inpaint"
    VFX_NR_CLEANUP = "vfx_nr_cleanup"
    OBJECT_REPLACEMENT = "object_replacement"
    VENDOR_NR_CLEANUP = "vfx_vendor"

class TaskLevel(Enum):
    SHOT = "shot"
    SHOT_LANGUAGE = "shot_language"
    SHOT_FEATURE = "shot_feature"
    SHOT_LANGUAGE_FEATURE = "shot_language_feature"

@dataclass(frozen=True)
class ShotLanguageVariantContext:
    STR_REGEX = re.compile(
        "^([a-z]{4}[0-9]{2})_([a-z]{2}[0-9]{2})_([a-z]{2}[0-9]{2})_([0-9]{4})_([a-z]+)_([a-z]+_[a-z]+).*"
    )
    context_type = TaskLevel.SHOT_LANGUAGE_FEATURE.value

    '''Usual context keys you'd expect are:
    "show", "episode", "part", "shot"
    "language", "variant"
    '''
    show: str
    episode: str
    part: str
    shot: str
    language: str
    variant: str

    @property
    def context_values(self) -> str:
        return "/".join([
            self.episode,
            self.part,
            self.shot,
            self.language,
            self.variant
        ])

    @classmethod
    def from_dict(cls, context_values: Dict) -> "ShotLanguageVariantContext":
        return ShotLanguageVariantContext(**context_values)
    
    @classmethod
    def from_str(cls, context_values: str) -> "ShotLanguageVariantContext":
        matches = ShotLanguageVariantContext.STR_REGEX.match(context_values)
        if not matches:
            raise Exception(f"Provided context {context_values} is not a valid ShotLanguageVariant context")
        return ShotLanguageVariantContext(*matches.groups())

@dataclass(frozen=True)
class ShotLanguageContext:
    STR_REGEX = re.compile(
        "^([a-z]{4}[0-9]{2})_([a-z]{2}[0-9]{2})_([a-z]{2}[0-9]{2})_([0-9]{4})_([a-z]+).*"
    )
    context_type = TaskLevel.SHOT_LANGUAGE.value

    '''Usual context keys you'd expect are:
    "show", "episode", "part", "shot"
    "language"
    '''
    show: str
    episode: str
    part: str
    shot: str
    language: str

    @property
    def context_values(self) -> str:
        return "/".join([
            self.episode,
            self.part,
            self.shot,
            self.language
        ])

    @classmethod
    def from_dict(cls, context_values: Dict) -> "ShotLanguageContext":
        return ShotLanguageContext(**context_values)

    @classmethod
    def from_str(cls, context_values: str) -> "ShotLanguageContext":
        matches = ShotLanguageContext.STR_REGEX.match(context_values)
        if not matches:
            raise Exception(
                f"Provided context {context_values} is not a valid ShotLanguage context"
            )
        return ShotLanguageContext(*matches.groups())

@dataclass
class TaskInput():
    data_type: str
    element: str
    node_name: str
    input_knob: str = "file"
    is_frames: bool = True
    optional : bool = False
    is_camera : bool = False

@dataclass
class TaskLogic():
    """Task-specific logic to append to headless script and run."""
    logic : Callable
    args : List[Any]
    condition : Callable

@dataclass(frozen=True)
class TaskDefinition():
    task_type : str
    task_level : str
    context_levels : List[str]
    requirements : List[TaskInput]
    path_to_template : str
    publish_datatype : str
    task_logic : List[TaskLogic] = lambda: []


def get_task_definition(task_name : str) -> TaskDefinition:
    results = {
        "13.1v2" : {
        TaskType.VFX_NR_CLEANUP.value : TaskDefinition(
            task_type=TaskType.VFX_NR_CLEANUP,
            task_level=TaskLevel.SHOT_LANGUAGE_FEATURE,
            context_levels=["show","episode","part","shot","language","variant"],
            requirements=[TaskInput(data_type = "PRECOMP", element = "precomp", node_name = "PRECOMP"),
            TaskInput(data_type = "PLATE", element = "plate", node_name = "PLATE"),
            TaskInput(data_type = "DENOISED", element = "plate", node_name = "DENOISE_PLATE"),
            TaskInput(data_type = "AUDIO", element = "audio", node_name = "WRITE_REVIEW_MOV", input_knob="mov64_audiofile", is_frames=False),
            TaskInput(data_type = "OCCLUSIONS", element = "occlusions", node_name = "OCCLUSION", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="track/head_interpolated.abc", node_name = "FOSD_HEAD", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/head_interpolated.abc", node_name = "PT_HEAD", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="track/camera_reversed.abc", node_name = "CAMERA_FILE", is_camera=True, optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/teeth_top.abc", node_name = "TEETH_TOP", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/teeth_bottom.abc", node_name = "TEETH_BOTTOM", optional=True),],
            path_to_template="templates/vfx_nr_cleanup_nuke13.nk",
            publish_datatype="FLOATING_FACE",
            task_logic = [
                TaskLogic(logic = nuke_utils.copy_camera_animation, condition = lambda : True, args = ["'CAMERA_FILE'","'CAMERA'"]),
            ],
            ),
        TaskType.OBJECT_REPLACEMENT.value : TaskDefinition(
            task_type=TaskType.OBJECT_REPLACEMENT,
            task_level=TaskLevel.SHOT_LANGUAGE, 
            context_levels=["show","episode","part","shot","language"],
            requirements=[TaskInput(data_type = "PLATE", element = "plate", node_name ="PLATE"),
            TaskInput(data_type = "DENOISED", element = "plate", node_name = "DENOISE_PLATE", optional=True),],
            path_to_template="templates/vfx_object_replacement_v001.nk",
            publish_datatype="OBJ_REPLACE",
            task_logic = [],),
        TaskType.VFX_OCCLUSION.value : TaskDefinition(
            task_type=TaskType.VFX_OCCLUSION,
            task_level=TaskLevel.SHOT,
            context_levels=["show","episode","part","shot"],
            requirements=[TaskInput(data_type = "DENOISED", element = "plate", node_name = "DENOISE_PLATE", optional=True),],
            path_to_template="templates/vfx_occlusion_v005.nk",
            publish_datatype="OCCLUSIONS",
            task_logic = [],),
        TaskType.VENDOR_NR_CLEANUP.value : TaskDefinition(
            task_type = TaskType.VENDOR_NR_CLEANUP,
            task_level=TaskLevel.SHOT_LANGUAGE_FEATURE,
            context_levels = ["show","episode","part","shot","language","variant"],
            requirements = None,
            path_to_template = None,
            publish_datatype = None,
        ),
    },
        "15.0v4" : {
        TaskType.VFX_NR_CLEANUP.value : TaskDefinition(
            task_type=TaskType.VFX_NR_CLEANUP,
            task_level=TaskLevel.SHOT_LANGUAGE_FEATURE,
            context_levels=["show","episode","part","shot","language","variant"],
            requirements=[TaskInput(data_type = "PRECOMP", element = "precomp", node_name = "PRECOMP"),
            TaskInput(data_type = "PLATE", element = "plate", node_name = "PLATE"),
            TaskInput(data_type = "DENOISED", element = "plate", node_name = "DENOISE_PLATE"),
            TaskInput(data_type = "AUDIO", element = "audio", node_name = "WRITE_REVIEW_MOV", input_knob="mov64_audiofile", is_frames=False),
            TaskInput(data_type = "OCCLUSIONS", element = "occlusions", node_name = "OCCLUSION", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="track/head_interpolated.abc", node_name = "FOSD_HEAD", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/head_interpolated.abc", node_name = "PT_HEAD", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="track/camera_reversed.abc", node_name = "CAMERA_FILE", is_camera=True, optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/teeth_top.abc", node_name = "TEETH_TOP", optional=True),
            TaskInput(data_type = "RECONSTRUCTED_MESH", element="pt/teeth_bottom.abc", node_name = "TEETH_BOTTOM", optional=True),],
            path_to_template="templates/vfx_nr_cleanup_nuke15.nk",
            publish_datatype="FLOATING_FACE",
            task_logic = [
                TaskLogic(logic = nuke_utils.copy_camera_animation, condition = lambda : True, args = ["'CAMERA_FILE'","'CAMERA'"]),
            ],
            ),
        }
    }
    nuke_version = nuke_utils.get_current_nuke_version()
    if nuke_version not in results.keys():
        raise Exception(f"There are no tasks that support this version of nuke: {nuke_version}")
    if task_name not in results[nuke_version].keys():
        raise Exception(f"{task_name} is not supported in this version of nuke: {nuke_version}")
    return results[nuke_version][task_name]

    
def set_node_input(task_input: TaskInput, input_path: Path):
    node = nuke.toNode(task_input.node_name)
    if task_input.is_frames:
        node[task_input.input_knob].fromUserText(str(input_path))
    else:
        node[task_input.input_knob].setValue(str(input_path))
    for knob in ["first","last"]:
        value = node.knobs()[knob].value()
        if value == 0:
            value = 1
        node.knobs()[knob].setValue(value)
    node.knobs()["on_error"].setValue("black")

def get_latest_version_as_int(path : Path) -> int:
    """Gets the latest version as an integer, zero if none exist in target path."""
    existing_versions = get_existing_scripts(path)
    as_digits = sorted([convert_version_to_int(v) for v in existing_versions])
    if not as_digits:
        return 0
    return as_digits[-1]

def convert_version_to_int(version : str):
    return int(version[1:])

def get_latest_script_number(path : Path) -> str:
    latest = get_latest_version_as_int(path)
    return convert_int_to_version(latest)

def get_existing_scripts(path : Path) -> List[str]:
    """Get sorted list of existing versions in target path."""
    if not os.path.exists(path):
        return []
    existing_scripts = sorted(file for file in os.listdir(path) if len(file) > 4 and file[-3:] == ".nk" and file[0] != ".")
    return sorted([ver[-6:-3] for ver in existing_scripts if ver[-6:-3].isnumeric()])

def get_next_script_number(path : Path) -> str:
    """Gets latest +1."""
    latest = get_latest_version_as_int(path)
    return convert_int_to_version(latest+1)

def get_next_script_dest(path : Path, context: str, version: str, task : str) -> str:
    """Get the absolute path to the next script that needs to be made in order to version up."""
    file_name = context + "_" + task + "_ws" + version[1:] + "_" + str(get_next_script_number(path)) + ".nk"
    return str(path / file_name)

def convert_int_to_version(version : int) -> str:
    """Convert int to v001"""
    return "v{0:03d}".format(version)

def apply_global_settings():
    """
    Apply Root settings, some of which depend on an input being loaded successfully (e.g. denoise plate dictates
    the fps and format of the script.)
    """
    nuke.Root().knobs()["frame"].setValue(1)
    nuke.Root().knobs()["format"].setValue(nuke.toNode("DENOISE_PLATE").knobs()["format"].value())
    nuke.Root().knobs()["fps"].setValue(nuke.toNode("DENOISE_PLATE").metadata()["input/frame_rate"])
    nuke.Root().knobs()["first_frame"].setValue(nuke.toNode("DENOISE_PLATE").knobs()["first"].value())
    nuke.Root().knobs()["last_frame"].setValue(nuke.toNode("DENOISE_PLATE").knobs()["last"].value())

def get_task_input_path(task_input: TaskInput, workspace_inputs: Path, optional : bool):
    input_dir = workspace_inputs / task_input.data_type / task_input.element
    if os.path.isfile(input_dir):
        return input_dir
    if optional and not os.path.exists(input_dir):
        return None
    if not optional and not os.path.exists(input_dir):
        raise Exception(f"Required input {task_input.data_type} not found here: {input_path}")
    if task_input.is_frames:
        input_path = input_dir / nuke_utils.nuke_user_path_from_dir(input_dir, re.compile(r"^(?P<name>\w+)(?P<delim>_|\.)(?P<num>\d+)(?P<ext>\.exr)$"))
    else:
        input_path = input_dir / next(input_dir.iterdir()).name
    return input_path

def put_in_try_catch_block(content : str, optional : bool):
    result = "\ntry:\n\t" + content + "\nexcept Exception as EX:\n\t"
    to_add = "pass\n" if optional else "raise Exception('Required input is missing.')\n\n"
    result+=to_add
    return result

def write_headless_script(context : str, workspace_path : str, nuke_script : str, task_definition : TaskDefinition) -> str:
    base_script = inspect.getsource(nuke_utils) + "\n\n"
    base_script += f"nuke.scriptOpen('{nuke_script}')\n"
    workspace_inputs = workspace_path / "input"
    for task_input in task_definition.requirements:
        input_path = str(get_task_input_path(task_input, workspace_inputs, task_input.optional))
        if task_input.is_frames:
            if not task_input.is_camera:
                base_script += put_in_try_catch_block(f"nuke.toNode('{task_input.node_name}').knobs()['{task_input.input_knob}'].fromUserText('{input_path}')", task_input.optional)
        else:
            base_script += put_in_try_catch_block(f"nuke.toNode('{task_input.node_name}').knobs()['{task_input.input_knob}'].setValue('{input_path}')", task_input.optional)
    base_script += inspect.getsource(apply_global_settings)
    base_script += "\n\napply_global_settings()\n\n"
    # cameras must be loaded after other inputs, and after global settings are set, but before task logic runs
    for task_input in task_definition.requirements:
        input_path = str(get_task_input_path(task_input, workspace_inputs, task_input.optional))
        if task_input.is_camera:
            base_script += put_in_try_catch_block(f"load_camera_from_abc('{task_input.node_name}', '{input_path}')\n", task_input.optional)

    for task_logic in task_definition.task_logic:
        if task_logic.condition():
            base_script += task_logic.logic.__name__ + "("
            for arg in task_logic.args:
                base_script += f"{arg},"
            base_script += ")\n\n"
    base_script += f"nuke.scriptSaveAs(filename='{nuke_script}',overwrite=1)\n"
    base_script += "nuke.scriptExit()\n"
    filepath = tempfile.gettempdir() + "/temp_python_script_" + os.environ["USER"]+ f"_{context}.py"
    with open(filepath, "w") as file:
        file.write(base_script)
    return filepath

def traverse_from_script_folder_to_workspace_path(script_folder : str) -> Path:
    if os.path.isdir(script_folder):
        return  Path(script_folder).parent.parent.parent
    return  Path(script_folder).parent.parent.parent.parent

def get_task_based_on_script_location(script_location : str) -> str:
    return get_task_definition(script_location[script_location.find("tasks/") + len("tasks/"):].split("/")[0])

def traverse_from_script_folder_to_workspace_headless() -> Path:
    result = Path(nuke.root().name()).parent.parent
    if not os.path.exists(result):
        message = "This script has not been saved in the workspace correctly. Cannot find the workspace folder."
        nuke.message(message)
        raise Exception(message)
    return result

def version_up_script(context: str, version : str, script_folder : str, source : Path, task : str) -> None:
    """Version up to the next script."""
    workspace_path = traverse_from_script_folder_to_workspace_path(script_folder)
    destination = get_next_script_dest(Path(script_folder), context,version,task)
    shutil.copy(source, destination)
    nuke_utils.make_tmp_nuke_script()
    python_script_location = write_headless_script(
        context,
        workspace_path,
        destination,
        get_task_definition(task))
    nuke_utils.run_headless_script(destination, python_script_location)
    nuke_utils.open(destination)
