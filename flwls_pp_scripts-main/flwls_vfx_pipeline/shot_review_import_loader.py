"""Node graph setup functions"""

import nuke

import os

from typing import Tuple, List, Optional

from glob import glob

import filesystem_parser

NOTE_FONT_SIZE = 42
BD_WIDTH = 803.0
BD_HEIGHT = 463.0
NODE_RED = 4278190335

def setup_read(file_path: Optional[str] = None, start_frame: int = 1, end_frame: int = 1) -> nuke.Node:
    """Generic read node creation"""
    node = nuke.createNode("Read")
    node.knobs()
    if file_path:
        node.knob("file").setValue(file_path)
        node.knob("first").setValue(start_frame)
        node.knob("last").setValue(end_frame)
    else:
        node.knob("tile_color").setValue(NODE_RED)
    return node


def frame_pad(name_split: str) -> Tuple[str, int]:
    """Convert numbered frame to padded frame"""
    name_split = name_split.split("_")
    frame_substring, ext = os.path.splitext(name_split[-1])

    frame_substring = frame_substring.split(".")

    frame_number = frame_substring[-1]
    frame_pad = "#" * len(frame_number)
    prepadding = "_".join(name_split[:-1])

    prepadding += "_"
    if len(frame_substring) > 1:
        prepadding += ".".join(frame_substring[:-1])
        frame_padded = f"{prepadding}.{frame_pad}{ext}"
    else:
        frame_padded = f"{prepadding}{frame_pad}{ext}"

    if len(frame_number) is 0:
        frame_number = 1
    return frame_padded, int(frame_number)


def place_backdrop(pos: List[int], variant: str, language: str, shot: str, part: str) -> None:
    """Adds the block background"""
    if variant == "all":
        variant = ""
    backdrop_node = nuke.createNode("BackdropNode")
    backdrop_node.knob("label").setValue(f"{part} {shot} {language.upper()} {variant}")
    backdrop_node.knob("note_font_size").setValue(NOTE_FONT_SIZE)
    backdrop_node.knob("bdwidth").setValue(BD_WIDTH)
    backdrop_node.knob("bdheight").setValue(BD_HEIGHT)

    backdrop_node.knob("ypos").setValue(pos[0] + BD_HEIGHT)
    backdrop_node.knob("xpos").setValue(pos[1])

    pos[0] += BD_HEIGHT


def create_read_node(file_paths: str) -> nuke.Node:
    """Adds a read node from a filepath list"""
    highest_version = file_paths[0]
    first_frame = file_paths[-1]

    name_padded, end_frame = frame_pad(os.path.basename(highest_version))
    _, start_frame = frame_pad(os.path.basename(first_frame)) 

    directory = os.path.dirname(highest_version)
    nuke_path = os.path.join(directory, name_padded)
    return setup_read(nuke_path, start_frame, end_frame)

def place_vfx_comp(shot: str, variant: str, language: str, part: str = "pt05", episode: str = "ep01", show: str = "lidl01") -> nuke.Node:
    """Add the vfx comp element"""
    file_paths = glob(
        f"/Volumes/workspace/shows/{show}/episodes/{episode}/parts/{part}/shots/{shot}/languages/{language}/variants/{variant}/tasks/vfx_nr_cleanup/*/output/FLOATING_FACE/review_exr/{show}_{episode}_{part}_{shot}_{language}_{variant}_vfx_nr_cleanup_ws*_v*.*.exr"
    )
    file_paths.sort(reverse=1)
    if file_paths:
        return create_read_node(file_paths)
    return setup_read(None)


def place_plate(shot: str, language: str, part: str = "pt05", episode: str = "ep01", show: str = "lidl01") -> nuke.Node:
    """Add the shot plate element"""
    file_paths = glob(
        f"/Volumes/workspace/shows/{show}/episodes/{episode}/parts/{part}/shots/{shot}/languages/{language}/tasks/face_merge/*/input/PLATE/plate/{show}_{episode}_{part}_{shot}_*_PLATE_plate_*.exr"
    )
    file_paths.sort(reverse=1)
    if file_paths:
        return create_read_node(file_paths)
    return setup_read(None)


def get_faceon(shot: str, variant:str, language: str, part: str = "pt05", episode: str = "ep01", show: str = "lidl01") -> nuke.Node:
    """Add the face on element"""
    file_paths = glob(
        f"/Volumes/workspace/shows/{show}/episodes/{episode}/parts/{part}/shots/{shot}/languages/{language}/variants/{variant}/tasks/faceon_comp/v*/output/FLOATING_FACE/review/{show}_{episode}_{part}_{shot}_{language}_{variant}_faceon_comp.mov"
    )
    if file_paths:
        file_paths.sort(reverse=1)
        file_paths = file_paths[0]
    return setup_read(file_paths)


def add_time_offset(node: nuke.Node, offset_amount: int) -> nuke.Node:
    """Retimes plates to current comp framerange"""
    offset_node = nuke.createNode("TimeOffset")
    offset_node.knob("time_offset").setValue(offset_amount)
    offset_node.knob("ypos").setValue(
        node.knob("ypos").value() + 120)
    offset_node.knob("xpos").setValue(node.knob("xpos").value())
    offset_node.setInput(0, node)
    offset_node.knob("selected").setValue(True)
    return offset_node


def add_label(node: nuke.Node, text: str) -> nuke.Node:
    """Adds a label above a nuke node"""
    label = nuke.createNode("StickyNote")
    label.knob("label").setValue(text)
    label.knob("ypos").setValue(node.knob("ypos").value() - 40)
    label.knob("xpos").setValue(node.knob("xpos").value())
    label.knob("note_font").setValue("DejaVu Sans Bold")
    return label


def determine_initial_position(node_selection: List[nuke.Node]) -> List[int]:
    """Set the initial position to start building"""
    current_location = [0, 0]
    for node in node_selection:
        if node.Class() == "BackdropNode":
            if node.knob("ypos").value() > current_location[0]:
                current_location[0] = node.knob("ypos").value()
                current_location[1] = node.knob("xpos").value()

    return current_location


def place_language_variant(current_location: List[int], comp_frame_offset: int, shot: str, language: str, variant: str, part: str, episode: str, show: str):
    start_frame = end_frame = None
    nodes_per_language = []
    plate_node = place_plate(shot, language, part, episode, show)
    if plate_node:
        plate_node.knob("selected").setValue(True)
        plate_node.knob("ypos").setValue(current_location[0] + 640)
        plate_node.knob("xpos").setValue(current_location[1] + 40)
        label = add_label(plate_node, "Plate")

        offset_node = add_time_offset(plate_node, comp_frame_offset)
        nodes_per_language.extend([plate_node, offset_node, label])

        start_frame = plate_node.knob("first").value()
        end_frame = plate_node.knob("last").value()

        faceon_node = get_faceon(shot, variant, language, part, episode, show)
        if faceon_node:
            faceon_node.knob("selected").setValue(True)
            faceon_node.knob("ypos").setValue(current_location[0] + 640)
            faceon_node.knob("xpos").setValue(current_location[1] + 280)
            if start_frame and end_frame:
                faceon_node.knob("first").setValue(start_frame)
                faceon_node.knob("last").setValue(end_frame)

            label = add_label(faceon_node, "FaceOn")
            offset_node = add_time_offset(faceon_node, comp_frame_offset)
            nodes_per_language.extend([faceon_node, offset_node, label])

        vfxcomp_node = place_vfx_comp(shot, variant, language, part, episode, show)
        if vfxcomp_node:
            vfxcomp_node.knob("selected").setValue(True)
            vfxcomp_node.knob("ypos").setValue(current_location[0] + 640)
            vfxcomp_node.knob("xpos").setValue(current_location[1] + 480)

            if start_frame and end_frame:
                vfxcomp_node.knob("first").setValue(start_frame)
                vfxcomp_node.knob("last").setValue(end_frame)

            label = add_label(vfxcomp_node, "VFXComp")
            offset_node = add_time_offset(vfxcomp_node, comp_frame_offset)
            nodes_per_language.extend([vfxcomp_node, offset_node, label])

        place_backdrop(current_location, variant, language, shot, part)

    for node in nodes_per_language:
        node.knob("selected").setValue(False)

def review_shot(shot: str, part: str, episode: str, show: str, language: str, variant: str) -> None:
    """Builds an element comparison block for a shot"""
    original_sel = nuke.selectedNodes()
    for node in original_sel:
        node.knob("selected").setValue(False)

    comp_frame_offset = 1000
    current_location = determine_initial_position(original_sel)
    languages = filesystem_parser.get_languages(show, episode, part, shot)

    variants = {}
    if language != "all":
        languages = [language]
    for build_language in languages:
        variants[build_language] = []
        for build_variant in filesystem_parser.get_variants(show, episode, part, shot, build_language):
            if variant == "all" or build_variant == variant:
                variants[build_language].append(build_variant)

    for language, build_variants in variants.items():
        for variant in build_variants:
            place_language_variant(current_location, comp_frame_offset, shot, language, variant, part, episode, show)
    if not variants:
        place_language_variant(current_location, comp_frame_offset, shot, language, "all", part, episode, show)

    for node in original_sel:
        node.knob("selected").setValue(True)

