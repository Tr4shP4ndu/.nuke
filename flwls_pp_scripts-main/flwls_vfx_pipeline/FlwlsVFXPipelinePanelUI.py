
import os

from flwls_vfx_pipeline import publish_vfx_workspace
from FlwlsVFXPipelinePanel import VFXPipelinePanelBasic, LogicEX
from GUI import KnobStem, TabStem, PanelContent, Panel
import migrate_tab_panel_scripts
from internal_publish import InternalPubEX
from playlist_review import PlaylistReviewEX
from typing import Any, Callable, List, Dict
from pathlib import Path
import task_set_up
import nuke
import nuke_utils


class VFXPipelinePanel(Panel):
    def __init__(self):
        Panel.set_up(self, PanelContent(name = "Flwls VFX Pipeline Panel", title_list=[KnobStem("WorkspaceTitle","Text","",lambda : 0,0, {"value" : "<font size='7' color='#d33834'>Flawless VFX</font>"})],
        tab_list=[
        TabStem(name="Open Script",
            knob_list=[
            # to add an example KnobStem:
            # KnobStem(name="", the_type="", label="",update="",linebreaks=0,optionals={})
            KnobStem("WorkspaceSubTitle","Text","",lambda : 0,1, {"value" : "<font size='5'>Context Picker</font>"}),
            KnobStem("task","Enumeration","Task",lambda: self.cascade_update("task"), 0, {"constructor" : ["Select Task:"] + LogicEX.get_released_task_types(), "enabled" : True, "force_set" : "vfx_nr_cleanup"}),
            KnobStem("show","Enumeration","Show",lambda: self.cascade_update("show"), 0, {"constructor" : ["Select Show:"], "enabled" : True, "visible" : True}),
            KnobStem("episode","Enumeration","Episode",lambda: self.cascade_update("episode"), 0, {"constructor" : ["Select Episode:"], "enabled" : False, "visible" : False}),
            KnobStem("part","Enumeration","Part",lambda: self.cascade_update("part"), 0, {"constructor" : ["Select Part:"], "enabled" : False, "visible" : False}),
            KnobStem("shot","Enumeration","Shot",lambda: self.cascade_update("shot"), 0, {"constructor" : ["Select Shot"], "enabled" : False, "visible" : False}),
            KnobStem("language","Enumeration","Language",lambda: self.cascade_update("language"), 0, {"constructor" : ["Select Language:"],"enabled":False, "visible" : False}),
            KnobStem("variant","Enumeration","Variant",lambda: self.cascade_update("variant"), 0, {"constructor" : ["Select Variant:"], "enabled" : False, "visible" : False}),
            KnobStem("version","Enumeration","Version", lambda: self.cascade_update("version"), 1, {"constructor" : ["Select Version:"], "enabled" : False, "visible" : False}),
            KnobStem("openLatestScriptButton","PyScript","Find and Open Latest Script for this Context", lambda: self.open_nuke_script(self.get_path_to_latest_subversion()), 1, { "enabled":False, "visible" : False}),
            KnobStem("makeNewScriptButton","PyScript","Make New Script for this Context", self.version_up_script, 1, { "enabled":False, "visible" : False}),
            KnobStem("subversion","Enumeration","Script", lambda: self.cascade_update("subversion"), 1, {"constructor" : ["Select Script:"], "enabled" : False, "visible" : False}),
            KnobStem("openSelectedScriptButton","PyScript","Open Selected Script", lambda : self.open_nuke_script(self.get_path_to_selected_subversion()), 1, { "enabled":False, "visible" : False})]),
        TabStem(name="Migrate",
            knob_list=[
            KnobStem("MigrateSubTitle","Text","",lambda : 0,1, {"value" : "<font size='5'>Migrate Script</font>"}),
            KnobStem("CurrentWorkspaceIndicator","Text","",lambda : 0,1, {"value" : ""}),
            KnobStem("TargetWorkspaceEnumerationKnob","Enumeration","Target Workspace", lambda: 0, 0, {"constructor" : migrate_tab_panel_scripts._populate_target_workspace_enumeration_knob(Path(migrate_tab_panel_scripts._get_nuke_script_path())), "enabled" : True, "visible" : True}),
            KnobStem("MigrateToTargetWorkspaceKnob","PyScript","Migrate script to target workspace", lambda : migrate_tab_panel_scripts._run_migrate_nuke_script(self), 0, { "enabled":False, "visible" : True}),
            KnobStem("RefreshPanelKnob","PyScript","Refresh", lambda : migrate_tab_panel_scripts._set_knob_defaults_migration(self), 0, { "enabled":True, "visible" : True})]),
        TabStem(name="Publish",
            knob_list=[
            KnobStem("PublishTabSubTitle","Text","",lambda : 0,1, {"value" : "<font size='5'>Publish Element</font>"}),
            KnobStem("PublishElementKnob","PyScript","Publish Read Node and Version Up", lambda : publish_vfx_workspace.publish_node() or self.version_up_current_script(), 1, { "enabled":True, "visible" : True}),
            KnobStem("SyncKnob","PyScript","Sync Latest Render to S3", lambda : publish_vfx_workspace.sync_latest_render_to_s3(), 1, { "enabled": os.path.exists("/usr/local/bin/create_workspace_cache"), "visible" : True}),
            KnobStem("PublishOnlyKnob","PyScript","Publish Latest Render", lambda : publish_vfx_workspace.publish_latest_render_gui(), 1, { "enabled": True, "visible" : True}),
        ]),
        TabStem(name="Internal Publish",
            knob_list=[
            KnobStem("InternalPublishSubTitle","Text","",lambda : 0,1, {"value" : "Internally Publish all content user has rendered using Write_Flwls nodes."}),
            KnobStem("InternalPublishRefresh","PyScript","Refresh", lambda : InternalPubEX.refresh(), 0, {"label" : "Refresh"}),] + InternalPubEX.offer_user_intpub_options(),
            ),
        TabStem(name="Retrieve Internal Publish",
            knob_list=[
            KnobStem("RetrieveIntPubText1","Text","",lambda : 0,1, {"value" : "Retrieve an existing Internal Publish and add it to the current script."}),
            KnobStem("RetrieveIntPubEnum1","Enumeration","Data Type:", lambda : InternalPubEX.update_datatype_select_knob(), 0, {"constructor" : ["Select Data Type:"] + InternalPubEX.get_existing_datatype_publishes()}),
            KnobStem("RetrieveIntPubEnum2","Enumeration","Version:", lambda : self.knobs()["RetrieveIntPubButton1"].setEnabled(True), 1, {"constructor" : ["Select Version:"], "enabled" : False}),
            KnobStem("RetrieveIntPubButton1","PyScript","Retrieve", lambda : InternalPubEX.retrieve_user_selected_internal_publish_inbuilt(), 0, {"label" : "Retrieve This Internal Publish", "enabled" : False}),
            ],),
        TabStem(name="Shotgrid Playlist Review Tool",
            knob_list=[
            KnobStem("ShotgridReviewText1","Text","",lambda : 0,0, {"value" : "<font size='5' color=#30e81f> Create a Review out of a Shotgrid Playlist</font>"}),
            KnobStem("ShotgridReviewText2","Text","",lambda : 0,1, {"value" : "<font size='2' color=#30e81f> Version: 0.1</font>"}),
            KnobStem("ShotgridReviewText3","Text","",lambda : 0,0, {"value" : "<font size='3' color=#30e81f>\tSave and Version Up (Tick) or Do Nothing (Untick) after loading Playlist:</font>"}),
            KnobStem("ShotgridReviewSaveOrNot","Boolean","",lambda : 0,0, {"default" : [True]}),
            KnobStem("ShotgridReviewCSVSelect","File","<font size='3' color=#30e81f> Select CSV File:</font>",lambda : PlaylistReviewEX.set_load_from_exr_knob(self),0, {}),
            KnobStem("ShotgridReviewLoadFromCSV","PyScript","Load from CSV", lambda : PlaylistReviewEX.load_from_csv_via_pannel(self) or
                PlaylistReviewEX.create_all_entries(self.knobs()["ShotgridReviewSaveOrNot"].getValue()), 0, {"enabled" : False}),
            KnobStem("WorkspaceSubTitle","Text","",lambda : 0,1, {"value" : "<font size='3' color=#30e81f> Review a Single Context via Context Picker:</font>"}),
            KnobStem("reviewtask","Enumeration","Task",lambda: self.cascade_update("task", "review"), 0, {"constructor" : ["Select Task:"] + LogicEX.get_released_task_types(override="review"), "enabled" : True, "force_set" : "vfx_nr_cleanup"}),
            KnobStem("reviewshow","Enumeration","Show",lambda: self.cascade_update("show", "review"), 0, {"constructor" : ["Select Show:"], "enabled" : True, "visible" : True}),
            KnobStem("reviewepisode","Enumeration","Episode",lambda: self.cascade_update("episode", "review"), 0, {"constructor" : ["Select Episode:"], "enabled" : False, "visible" : False}),
            KnobStem("reviewpart","Enumeration","Part",lambda: self.cascade_update("part", "review"), 0, {"constructor" : ["Select Part:"], "enabled" : False, "visible" : False}),
            KnobStem("reviewshot","Enumeration","Shot",lambda: self.cascade_update("shot", "review"), 0, {"constructor" : ["Select Shot"], "enabled" : False, "visible" : False}),
            KnobStem("reviewlanguage","Enumeration","Language",lambda: self.cascade_update("language", "review") or self.knobs()["reviewversion"].setLabel("Select Snapshot"), 0, {"constructor" : ["Select Language:"],"enabled":False, "visible" : False}),
            KnobStem("reviewvariant","Enumeration","Variant",lambda: self.cascade_update("variant", "review") or self.knobs()["reviewversion"].setLabel("Select Snapshot"), 0, {"constructor" : ["Select Variant:"], "enabled" : False, "visible" : False}),
            KnobStem("reviewversion","Enumeration","Version", lambda: self.cascade_update("version", "review") or self.knobs()["reviewsubversion"].setVisible(False) or self.knobs()["ShotgridReviewFromContextPicker"].setVisible(True),
                1, {"constructor" : ["Select Snapshot:"], "enabled" : False, "visible" : False}),
            KnobStem("reviewsubversion","Enumeration","Script", lambda: 0, 0, {"constructor" : ["Select Script:"], "enabled" : False, "visible" : False}),
            KnobStem("ShotgridReviewFromContextPicker","PyScript","Load from Context Picker", lambda : PlaylistReviewEX.load_from_context_picker(self) or
                PlaylistReviewEX.create_all_entries(self.knobs()["ShotgridReviewSaveOrNot"].getValue()), 1, {"enabled" : True, "visible" : False}),
            KnobStem("ShotgridReviewText4","Text","",lambda : 0,0, {"value" : "<font size='5' color=#30e81f> Create a Review using a Playlist URL / ID</font>"}),
            KnobStem("ShotgridReviewText5","Text","",lambda : 0,1, {"value" : f"<font size='4' color=#30e81f>{self.get_shotgrid_info_string()}</font>"}),
            KnobStem("ShotgridReviewURL","EvalString","URL",lambda : PlaylistReviewEX.set_load_from_url_knob(self),0, {"value" : "",}),
            KnobStem("ShotgridReviewLoadFromURL","PyScript","Load from URL", lambda : PlaylistReviewEX.load_from_url(self), 0, {"enabled" : False}),
            ],),    
            ]))
        
        migrate_tab_panel_scripts._set_knob_defaults_migration(self)

        if self.content.knob_stem_lookup["task"].has_option("force_set"):
            self.cascade_update("task")
            self.cascade_update("task","review")

        setattr(nuke, "VFXPipelinePanelBasic", self)

    def get_shotgrid_info_string(self):
        result = "This will trigger a job execution on aws. Once it succeeds the script will be saved as a new version here:"
        result += f" /Volumes/workspace/shows/SHOWNAME/tasks/review/{nuke_utils.get_current_date()}"
        result += " (The name of the show will depend on the playlist)"
        return result

    def get_option_names(self) -> List[Any]:
        return VFXPipelinePanelBasic.get_option_names()

    def get_user_choices(self, prefix="")-> Dict[Any, Any]:
        return dict([[prefix+choice, getattr(self, prefix+choice).value()] for choice in self.get_option_names()])

    def get_locations_of_user_choices(self, prefix="") -> Dict[Any, Any]:
        return VFXPipelinePanelBasic.get_locations_of_user_choices(self.get_user_choices(prefix), prefix)
    
    def get_path_to_latest_subversion(self) -> str:
        return VFXPipelinePanelBasic.get_path_to_latest_subversion(self.get_user_choices())

    def get_path_to_selected_subversion(self) -> str:
        return VFXPipelinePanelBasic.get_path_to_selected_subversion(self.get_user_choices())

    def get_path_to_selected_version(self) -> str:
        return VFXPipelinePanelBasic.get_path_to_selected_version(self.get_user_choices())
        
    def get_latest_version_number(self) -> str:
        workspace_path = Path(LogicEX.folder_keyword_replacement(self.get_locations_of_user_choices()["subversion"]))
        return task_set_up.get_latest_script_number(workspace_path)

    def get_next_version_number(self) -> str:
        """Return an empty string if no next version could be interpreted."""
        return VFXPipelinePanelBasic.get_next_version_number(self.get_user_choices())

    def update_next_script_button_text(self) -> None:
        if not self.makeNewScriptButton.visible():
            return
        default = "Make New Script for this Context"
        self.makeNewScriptButton.setLabel(default)
        result = self.get_next_version_number()
        if result != "v001":
            self.makeNewScriptButton.setLabel(default + f" ({result})")

    def update_latest_script_button_text(self) -> None:
        if not self.openLatestScriptButton.visible():
            return
        default = "Find and Open Latest Script for this Context"
        self.openLatestScriptButton.setLabel(default)
        result = self.get_latest_version_number()
        if result != "v000":
            self.openLatestScriptButton.setLabel(default + f" ({result})")

    def only_one_choice_exists(self, values) -> bool:
        return len(values) == 2 and values[1] != "NONE"

    def cascade_update(self, target : str, prefix = "") -> None:
        """When one is changed, update it and next one in chain, then disable those after."""
        self.make_work_path_if_required()
        choices = self.get_user_choices(prefix)
        task = choices[prefix+"task"]
        locations = self.get_locations_of_user_choices(prefix)
        
        values_by_button = {
            prefix+"task" : [ "Select Task:"] + LogicEX.get_released_task_types(prefix),
            prefix+"show" : ["Select Show:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"show"], LogicEX.get_show_regex()),
            prefix+"episode" : ["Select Episode:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"episode"], LogicEX.get_episode_regex()),
            prefix+"part" : ["Select Part:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"part"], LogicEX.get_part_regex()),
            prefix+"shot" : ["Select Shot:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"shot"], LogicEX.get_shot_regex()),
            prefix+"language" : ["Select Language:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"language"], LogicEX.get_language_regex()),
            prefix+"variant" : ["Select Variant:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"variant"], LogicEX.get_variant_regex()),
            prefix+"version" : ["Select Version:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"version"], LogicEX.get_version_regex()),
            prefix+"subversion" : ["Select Script:"] + LogicEX.UI_itera_file_names_only(locations[prefix+"subversion"], LogicEX.get_subversion_regex()),}

        to_update = { 
                prefix+"task" : lambda : self.knobs()[prefix+"task"].setValues(values_by_button[prefix+"task"]),
                prefix+"show" : lambda : self.knobs()[prefix+"show"].setValues(values_by_button[prefix+"show"]),
                prefix+"episode" : lambda : self.knobs()[prefix+"episode"].setValues(values_by_button[prefix+"episode"]),
                prefix+"part" : lambda : self.knobs()[prefix+"part"].setValues(values_by_button[prefix+"part"]),
                prefix+"shot" : lambda : self.knobs()[prefix+"shot"].setValues(values_by_button[prefix+"shot"]),
                prefix+"language" : lambda : self.knobs()[prefix+"language"].setValues(values_by_button[prefix+"language"]),
                prefix+"variant" : lambda : self.knobs()[prefix+"variant"].setValues(values_by_button[prefix+"variant"]),
                prefix+"version" : lambda : self.knobs()[prefix+"version"].setValues(values_by_button[prefix+"version"]),
                prefix+"subversion" : lambda : self.knobs()[prefix+"subversion"].setValues(values_by_button[prefix+"subversion"]),
                }
        
        to_update[prefix+target]()

        for choice in [c for c in to_update.keys()]:
            if choice in locations.keys():
                if locations[choice] == "None":
                    getattr(self, choice).setEnabled(False)
                    getattr(self, choice).setVisible(False)
                    choices.pop(choice)
                    to_update.pop(choice)

        start = list(choices.keys()).index(prefix+target)
        for cascade_target in list(choices.keys())[start+1:start+2]:
            to_update[cascade_target]()
            getattr(self, cascade_target).setEnabled(True)
            getattr(self, cascade_target).setVisible(True)   
            if self.only_one_choice_exists(values_by_button[cascade_target]):
                getattr(self, cascade_target).setValue(values_by_button[cascade_target][1])
                self.cascade_update(cascade_target.replace(prefix, ""), prefix)
                return
            else:
                getattr(self, cascade_target).setValue("Select " + cascade_target[0].upper() + cascade_target[1:] + ":")  
        for disable_target in list(to_update.keys())[start+2:]:
                getattr(self, disable_target).setEnabled(False)
                getattr(self, disable_target).setVisible(False)

        for function in [self.makeNewScriptButton.setEnabled, self.makeNewScriptButton.setVisible]:
            function(LogicEX.folder_exists(self.get_path_to_selected_version()))
        for function in [self.openLatestScriptButton.setEnabled, self.openLatestScriptButton.setVisible]:
            function(LogicEX.folder_exists(self.get_path_to_latest_subversion()))
        for function in [self.openSelectedScriptButton.setEnabled, self.openSelectedScriptButton.setVisible]:
            function(LogicEX.folder_exists(self.get_path_to_selected_subversion()))
        for function in [self.update_latest_script_button_text, self.update_next_script_button_text]:
            function()

    def make_work_path_if_required(self) -> None:
        version_path = self.get_path_to_selected_version()
        work_path = LogicEX.join(version_path, "work")
        work_path_context = LogicEX.join(work_path, self.get_context_as_string("") + "_" + self.get_user_choices()["task"])
        work_path_scripts = LogicEX.join(work_path_context, "scripts")
        if LogicEX.folder_exists(version_path):
            for folder in [work_path, work_path_context, work_path_scripts]:
                LogicEX.make(folder)

    def open_nuke_script(self, path_to_script) -> None:
        nuke_utils.make_tmp_nuke_script_then_open(path_to_script)

    def get_context_as_string(self, prefix) -> str:
        choices = self.get_user_choices(prefix)
        levels = [prefix+l for l in task_set_up.get_task_definition(choices[prefix+"task"]).context_levels]
        return LogicEX.from_dict_to_string(choices,levels,"_")
     
    def version_up_script(self) -> None:
        choices = self.get_user_choices()
        script_folder = LogicEX.folder_keyword_replacement(self.get_locations_of_user_choices()["subversion"])
        context = self.get_context_as_string(prefix="")
        version = choices["version"]
        task = choices["task"]
        task_definition = task_set_up.get_task_definition(task)
        script_destination = Path(__file__).parent / f"{task_definition.path_to_template}"
        task_set_up.version_up_script(
                context, 
                version,
                script_folder, 
                script_destination,
                task)

    def version_up_current_script(self) -> None:
        """Version up already open script."""
        choices = LogicEX.get_context_based_on_current_path()
        script_folder = Path(nuke.root()['name'].value()).parent
        context = LogicEX.from_dict_to_string(choices,task_set_up.get_task_definition(choices["task"]).context_levels,"_")
        next_version = task_set_up.get_next_script_dest(script_folder, context, choices["version"], choices["task"])
        nuke_utils.save(next_version)

    def knobChanged(self, knob) -> None:
        getattr(self, "update_" + knob.name())()
