import nuke
import json
from typing import Optional
from pathlib import Path
import nuke_utils
from FlwlsVFXPipelinePanel import LogicEX


#local imports
from task_set_up import TaskType

NOTES_POPUP_FIELD_LABEL = "Notes for publish"

def notes_popup(generic_notes: str) -> Optional[str]:
    
    popup_panel = nuke.Panel("Add Notes to your publish")
    popup_panel.addMultilineTextInput(NOTES_POPUP_FIELD_LABEL, generic_notes)
    
    re = popup_panel.show()

    if re == 0:
        raise ValueError("Publish process canceled")
    notes_to_publish = popup_panel.value(NOTES_POPUP_FIELD_LABEL)
    
    return notes_to_publish

def nr_cleanup_notes(script_path: Path, workspace_version: str) -> str:
    '''Gets the PT version from the metadata.json file. Only if working in NR Cleanup workspace.'''

    metadata_path = script_path.parents[3] / "metadata.json"

    pt_sg_version_number = ""
    if metadata_path.exists():
        with open(metadata_path) as f:
            json_meta = json.load(f)
            pt_sg_version_number = json_meta['inputs']['VUBB.neural_render']
    
    generic_notes = f"pt_version {pt_sg_version_number} and workspace_version {workspace_version}."
    
    return generic_notes

def default_notes_for_task(task_type: str, script_path: Path, workspace_version: str) -> str:

    if task_type == TaskType.VFX_NR_CLEANUP.value:
        return nr_cleanup_notes(script_path, workspace_version)
    
    return ""

def review_panel_popup(task_type: str, workspace_version: str) -> Optional[Path]:
   
    script_path = Path(nuke.scriptName())
    generic_notes = default_notes_for_task(task_type, script_path, workspace_version)
    notes_to_publish = notes_popup(generic_notes)

    if notes_to_publish == "":
        notes_to_publish = generic_notes
    
    manage_sticky_notes(notes_to_publish)

    notes_location_stem = script_path.parents[3] / "output" / "notes_to_publish" 
    LogicEX.remake(notes_location_stem)
    notes_location = script_path.parents[3] / "output" / "notes_to_publish" / f"{script_path.stem}_notes.txt"

    note_file = open(notes_location, "w")
    note_file.write(notes_to_publish)
    note_file.close()

    return notes_location

def manage_sticky_notes(latest_note : str):
    keyword = "PublishStickyNote"
    existing_sticky_notes = nuke_utils.get_all_nodes_that_contain_substring_in_name(keyword)
    if nuke.selectedNodes():
        selected_node = nuke.selectedNodes()[0]
    else:
        selected_node = nuke_utils.get_any_write_node()
    top_left_anchor = [selected_node.knobs()["xpos"].getValue(), selected_node.knobs()["ypos"].getValue()]
    if existing_sticky_notes:
        latest = existing_sticky_notes[-1]
        top_left_anchor = [latest.knobs()["xpos"].getValue(), latest.knobs()["ypos"].getValue()+ 50]
    else:
        top_left_anchor[1] += 100
    new_sticky_note = nuke_utils.make_node("StickyNote", keyword)
    nuke_utils.put_node_here(new_sticky_note.name(), top_left_anchor[0], top_left_anchor[1])
    new_content = nuke_utils.get_current_user() + " " + nuke_utils.get_current_date() + "\n" + latest_note
    new_sticky_note.knobs()["label"].setValue(new_content)
