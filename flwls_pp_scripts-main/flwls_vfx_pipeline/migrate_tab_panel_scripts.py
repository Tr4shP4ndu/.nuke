from pathlib import Path
import nuke
import nuke_utils
import migrate_nuke_script_to_target_workspace
import task_set_up
import json


def _populate_target_workspace_enumeration_knob(source_nuke_script_path: Path) -> list:
    
    try:
        task_directory = source_nuke_script_path.parents[4]
        available_versions = [file.name for file in task_directory.glob('v[0-9][0-9][0-9]')]
        if not available_versions:
            return ["No available workspaces"]    
        return sorted(available_versions, reverse=True)
    
    except:
        return ["No available workspaces"]

def _get_nuke_script_path() -> str:
    source_nuke_script_path = nuke.root().name()
    return source_nuke_script_path

def _get_source_workspace_version(source_nuke_script_path: Path) -> str:
    filename = source_nuke_script_path.stem
    filename_parts = filename.split('_')
    ws_version = filename_parts[-2]
    ws_number = ws_version.split('ws')[-1]
    return str(ws_number)

def _get_context_from_script_name(nuke_script_path: str) -> str:
    task_definition = task_set_up.get_task_based_on_script_location(nuke_script_path)
    filename = Path(nuke_script_path).stem
    return filename[:filename.find(task_definition.task_type.name)]


def _set_knob_defaults_migration(self):
    '''
    SET KNOB DEFAULTS MIGRATION TAB
    '''
    source_nuke_script_path = _get_nuke_script_path()
    target_version_knob_values = (_populate_target_workspace_enumeration_knob(source_nuke_script_path=Path(source_nuke_script_path)))
    self.TargetWorkspaceEnumerationKnob.setValues(target_version_knob_values)
    self.TargetWorkspaceEnumerationKnob.setValue(target_version_knob_values[0])
    try:
        source_pt_version = _get_PT_SG_version_from_workpace_metadata_json(source_nuke_script_path)
    except Exception as EX:
        source_pt_version = "Undefined" # above fails when path can't find version number
    if self.TargetWorkspaceEnumerationKnob.value() == "No available workspaces":
        current_workspace_indicator_message = ("<font size='4' color='#d33834'>No workspace available")
        self.MigrateToTargetWorkspaceKnob.setEnabled(False)
    else:
        source_version_number = _get_source_workspace_version(source_nuke_script_path=Path(source_nuke_script_path))
        latest_available_workspace = self.TargetWorkspaceEnumerationKnob.values()
        latest_available_workspace = sorted(latest_available_workspace, reverse=True)

        if latest_available_workspace[0] == str(f"v{source_version_number}"):
            current_workspace_indicator_message = str(f"<font size='4' color=green>You are working in workspace v{source_version_number}{source_pt_version}</span>")
        else:
            current_workspace_indicator_message = str(f"<font size='4' color='#d33834'>You are working in workspace v{source_version_number}{source_pt_version}</span>")
        self.MigrateToTargetWorkspaceKnob.setEnabled(True)

    self.CurrentWorkspaceIndicator.setValue(current_workspace_indicator_message)

def _run_migrate_nuke_script(self): 
        nuke.scriptSave()
        source_nuke_script_path = _get_nuke_script_path()
        target_workspace_version = self.TargetWorkspaceEnumerationKnob.value()
        migrated_script = migrate_nuke_script_to_target_workspace.migrate_nuke_script_to_target_workspace(source_nuke_script_path = source_nuke_script_path, target_workspace_version = target_workspace_version)
        workspace_path = task_set_up.traverse_from_script_folder_to_workspace_path(migrated_script)
        task_definition = task_set_up.get_task_based_on_script_location(migrated_script)
        context = _get_context_from_script_name(migrated_script)
        headless_migrated_script = task_set_up.write_headless_script(
            context=context,
            workspace_path=workspace_path,
            nuke_script=migrated_script,
            task_definition = task_definition)
        nuke_utils.run_headless_script(nuke_script_location=migrated_script, python_script_location=headless_migrated_script)
        nuke.scriptOpen(migrated_script)

def _get_PT_SG_version_from_workpace_metadata_json(source_nuke_script_path: str) -> str:
    '''Gets the PT version from the metadata.json file. Only if working in NR Cleanup workspace.'''
    if source_nuke_script_path == "Root": return ""

    source_nuke_script_path = Path(source_nuke_script_path)

    if (source_nuke_script_path.parents[4]).name == "vfx_nr_cleanup":
        metadata_path = f"{Path(source_nuke_script_path.parents[3])}/metadata.json"

        if Path(metadata_path).exists:
            with open(metadata_path) as f:
                json_meta = json.load(f)
                pt_sg_version_number = json_meta['inputs']['VUBB.neural_render']

            meta_pt_sg_version_number = f". Performance transfer {pt_sg_version_number}."
            return meta_pt_sg_version_number

    else:
        return ""

def get_PT_SG_version_only(source_nuke_script_path: str) -> str:
    metadata_path = f"{Path(source_nuke_script_path.parents[3])}/metadata.json"
    result = "?"
    if Path(metadata_path).exists:
            with open(metadata_path) as f:
                json_meta = json.load(f)
                result = json_meta['inputs']['VUBB.neural_render']
    return result




