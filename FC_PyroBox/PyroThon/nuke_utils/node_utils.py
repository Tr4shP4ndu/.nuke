from __future__ import annotations
import os
import re
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Union

import nuke

# Local imports
from PyroPython.nuke_utils.node_update import nodeUpdate
from PyroPython.nuke_utils.typedefs import (
    MetadataReturnType,
    NukeKnobVal,
)


__all__ = [
    "find_node_by_name",
    "get_node_knob_value",
    "set_node_knob_value",
    "set_node_knob_value_keyframe",
    "set_node_knob_animated",
    "set_node_filepath",
    "get_node_frame_count",
    "get_node_metadata",
    "execute_node_knob",
    "select_node",
    "deselect_node",
    "deselect_all_nodes",
    "duplicate_nodes",
    "connect_two_nodes",
]


def find_node_by_name(name: str) -> Optional[Node]:  # type: ignore # noqa
    """Find a node in a Nuke script using its name

    Args:
        name: The name of the node to search for

    Returns:
        An object of type `Node` if a node with the specified name is found, `None` otherwise
    """

    return nuke.toNode(name)


def get_node_knob_value(node: Node, knob_name: str) -> NukeKnobVal:  # type: ignore # noqa
    """Get the value of a node's knob given the knob's name

    Args:
        node: The Node object that has the knob
        knob_name: The name of the knob

    Returns:
        The knob's value which could be a `str`, `int`, `float` or `bool` object

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    return node.knob(knob_name).value()


def set_node_knob_value(node: Node, knob_name: str, new_value: NukeKnobVal) -> bool:  # type: ignore # noqa
    """Update the value of a node's knob given the knob's name

    Args:
        node: The Node object that has the knob
        knob_name: The name of the knob
        new_value: The new value (`str`, `int`, `float` or `bool`) that will be used to update the knob

    Returns:
        boolean: `True` if the knob's value has been updated, `False` otherwise

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    return node.knob(knob_name).setValue(new_value)


def set_node_knob_value_keyframe(node: Node, knob_name: str, new_value: NukeKnobVal, frame: int, index: int = 0) -> bool:  # type: ignore # noqa
    """Update the value of a node's knob given the knob's name at a specific
    frame, setting a keyframe on that frame. The knob has to be animated for
    a keyframe to be added. Otherwise, the value will be updated for all
    frames

    Args:
        node: The Node object that has the knob
        knob_name: The name of the knob
        new_value: The new value (str, int, float or bool) that will be used to update the knob
        frame: The frame number
        index: (Optional) If the knob has multiple fields, the index specifies which field will be updated

    Returns:
        boolean: `True` if the knob's value has been updated, `False` otherwise

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    return node.knob(knob_name).setValueAt(new_value, frame, index)


def set_node_knob_animated(node: Node, knob_name: str) -> bool:  # type: ignore # noqa
    """Set a node's knob to be animated

    Args:
        node: The Node object that has the knob
        knob_name: The name of the knob

    Returns:
        boolean: `True` if the knob's value has been updated, `False` otherwise

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    return node.knob(knob_name).setAnimated()


def set_node_filepath(node: Node, filepath: Union[Path, str]) -> None:  # type: ignore # noqa
    """Specialised function that works on nodes that have a "file" knob
    (e.g. Read and Write nodes)

    Args:
        node: The Node object that has the knob
        filepath: The filepath that will be used to set the file knob's value

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    node.knob("file").fromUserText(str(filepath))


def setup_read_node(
    node: Node,
    filepath: Union[Path, str],
    frame_start: int,
    frame_end: int,
    start_at: Optional[int] = None,
) -> None:  # type: ignore # noqa
    if not node:
        return

    set_node_filepath(node, filepath)
    __set_read_node_start_and_end(node, frame_start, frame_end, start_at)


def get_node_frame_count(node: Node) -> int:  # type: ignore # noqa
    """Get the frame count of the specified node

    Args:
        node: The node object to query

    Returns:
        int: The number of frames in the specified node

    Raises:
        RuntimeError: When node is not a valid node
    """

    return node.frameRange().frames()


def get_node_metadata(
    node: Node, key: Optional[str]  # type: ignore # noqa
) -> Optional[MetadataReturnType]:
    """Get the metadata dictionary of a node or the value of a specific metadata key

    Args:
        node: The node object to query
        key: (Optional) A specific key to check for

    Returns:
        MetadataReturnType | None

    Raises:
        RuntimeError: When node is not a valid node
    """

    return node.metadata() if not key else node.metadata().get(key)


def execute_node_knob(node: Node, knob_name: str) -> None:  # type: ignore # noqa
    # TODO (AS): Check if the execute method returns a boolean
    """Execute a node's knob (e.g. a button that does something when clicked)

    Args:
        node: The Node object that has the knob
        knob_name: The name of the knob

    Returns:
        boolean: `True` if the knob's value has been updated, `False` otherwise

    Raises:
        AttributeError: When the node is not a valid node or if it doesn't have a knob with the specified name
    """

    node.knob(knob_name).execute()


def select_node(node: Node):  # type: ignore # noqa
    node.setSelected(True)


def deselect_node(node: Node):  # type: ignore # noqa
    node.setSelected(False)


def deselect_all_nodes() -> List[Node]:  # type: ignore # noqa
    """Deselects all currently selected nodes and returns a list with the nodes
    that have been deselected"""

    nodes = nuke.selectedNodes()

    for node in nodes:
        deselect_node(node)

    return nodes


def duplicate_nodes(
    nodes: List[Node],  # type: ignore # noqa
    x_offset: int = 100,
    y_offset: int = 0,
) -> List[Node]:  # type: ignore # noqa
    deselect_all_nodes()

    for node in nodes:
        select_node(node)

    # NOTE (AS): Nuke can't duplicate or copy nodes to system clipboard in headless
    # mode. This is the only reliable way I found of duplicating nodes
    clipboard = (
        Path(tempfile.gettempdir()) / f"clipboard_{time.strftime('%y%m%d_%H%M%s')}"
    )

    nuke.nodeCopy(str(clipboard))

    deselect_all_nodes()

    nuke.nodePaste(str(clipboard))

    os.remove(clipboard)

    duplicate_nodes = nuke.selectedNodes()

    for node in duplicate_nodes:
        node.setXpos(node.xpos() + x_offset)
        node.setYpos(node.ypos() + y_offset)

    return duplicate_nodes


def connect_two_nodes(sending_node: Node, receiving_node: Node, input: int = 0):  # type: ignore # noqa
    receiving_node.connectInput(input, sending_node)


def __set_read_node_start_and_end(node: Node, frame_start: int, frame_end: int, start_at: Optional[int] = None) -> None:  # type: ignore # noqa
    set_node_knob_value(node, "frame_mode", "start at")
    set_node_knob_value(
        node, "frame", f"{start_at if start_at is not None else frame_start}"
    )
    set_node_knob_value(node, "first", frame_start)
    set_node_knob_value(node, "origfirst", frame_start)
    set_node_knob_value(node, "last", frame_end)
    set_node_knob_value(node, "origlast", frame_end)


def delete_node(node: Node):
    nuke.delete(node)


def get_node_position(node: nuke.Node) -> Tuple[int, int]:
    return [node.xpos(), node.ypos()]


def put_node_here(node: Node, x: int, y: int):
    node.setXYpos(x, y)


def put_backdrop_next_to_node(
    target_node: Node,
    message_text: str,
    offset: Tuple[int],
    colour: int = 0,
    z_order: int = 2,
    bdwidth: int = 150,
) -> Node:
    node = nuke.createNode("BackdropNode")
    node.knobs()["name"].setValue(target_node.knobs()["name"].value() + "_BACKDROP")
    node.knobs()["tile_color"].setValue(colour)
    node.knobs()["label"].setValue(message_text)
    existing_location = get_node_position(target_node)
    target_location = [existing_location[x] + offset[x] for x in [0, 1]]
    put_node_here(node, target_location[0], target_location[1])
    node.knobs()["z_order"].setValue(z_order)
    node.knobs()["bdwidth"].setValue(bdwidth)
    deselect_all_nodes()
    return node


def get_frames_based_on_input(folder: str) -> List[int]:
    return [
        int(re.search(r"[0-9]{6}", file).group(0))
        for file in sorted(os.listdir(folder))
    ]


def get_nuke_frame_ranges_based_on_input(frames: List[int]) -> List[List[int]]:
    if not frames:
        return []
    counter = 0
    current_range = []
    ranges = []
    current = 0
    while counter < len(frames):
        if frames[counter] == current + 1:
            current_range.append(frames[counter])
        else:
            if current_range:
                ranges.append(current_range)
            current_range = [frames[counter]]
        current = frames[counter]
        counter += 1
    ranges.append(current_range)
    return ranges


def get_project_framerange() -> nuke.FrameRange:
    all_frames = [
        int(nuke.root().knobs()[key].value()) for key in ["first_frame", "last_frame"]
    ]
    return nuke.FrameRange(all_frames[0], all_frames[-1], 1)


def get_missing_frames_based_on_file_input(
    image_sequence_folder_path: str,
) -> List[int]:
    r = get_frames_based_on_input(image_sequence_folder_path)
    all_frames = get_project_framerange()
    return [frame for frame in all_frames if frame not in r]


def convert_nuke_frame_range_to_string(ranges: List[List[int]]) -> str:
    if not ranges:
        return "None"
    results_as_string = ""
    for r in ranges:
        if len(r) == 1:
            results_as_string += f"{r[0]},"
        else:
            results_as_string += f"{r[0]}-{r[-1]},"
    return results_as_string[:-1]


def update_script_with_these_modifications(updates : List[node_update]) -> None:
    for update in updates:
        set_node_knob_value(find_node_by_name(update.node_name),update.knob_name,update.value)
