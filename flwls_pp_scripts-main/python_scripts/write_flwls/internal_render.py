import nuke
import nukescripts
from dataclasses import dataclass
from functools import partial
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Callable

from common import NodeToMake, NodeLink, GizmoActionLookup, GizmoAction, GizNodeEX
import task_set_up
import FlwlsVFXPipelinePanel


@dataclass
class InternalRenderDataType():
    name : str
    gizmo : nuke.Node
    nodes_to_make : List[NodeToMake] = lambda : [] 
    node_links: List[NodeLink] = lambda : []
    write_node_name : str = ""
    file_types : List[str] = lambda : []
    active_tab_names : List[str] = lambda : []
    colour: str = "513a00ff"
    actions: List[GizmoAction] = lambda : []
    do_auto_actions : bool = True
    overrides : Dict[Any,Any] = lambda : {}
    store_in_render_folder : bool = False
    consider_sparseness : bool = False
    render_one_item_per_frame : bool = True
    @staticmethod
    def get_latest_internal_render(filepath : str) -> str:
        return [folder for folder in FlwlsVFXPipelinePanel.LogicEX.itera(filepath) if os.listdir(folder)][-1]
    @staticmethod
    def get_next_version(path: Path) -> str:
        if not (os.path.exists(path) and os.path.isdir(path)):
            return "v001"
        return task_set_up.convert_int_to_version(task_set_up.convert_version_to_int(InternalRenderDataType.get_existing_internal_publishes(path)[-1])+1)
    def get_latest_version(path: Path) -> str:
        if not (os.path.exists(path) and os.path.isdir(path)):
            return "v001"
        if not InternalRenderDataType.get_existing_internal_publishes(path):
            return "v001"
        result_as_int = task_set_up.convert_version_to_int(InternalRenderDataType.get_existing_internal_publishes(path)[-1])
        if result_as_int == 0:
            return "v001"
        return task_set_up.convert_int_to_version(task_set_up.convert_version_to_int(InternalRenderDataType.get_existing_internal_publishes(path)[-1]))    
    @staticmethod
    def get_existing_internal_publishes(path : str) -> List[str]:
        if not os.path.exists(path) or not os.listdir(path):
            return ["v000"]
        version_regex = re.compile(FlwlsVFXPipelinePanel.LogicEX.get_version_regex())
        return [ver for ver in sorted(os.listdir(path)) if version_regex.match(ver) is not None]
    def run(self):
        self.reset_nodes()
        self.make_nodes()
        self.auto_tab_toggle()
        if self.do_auto_actions:
            self.prepare_auto_actions()
        self.do_actions()
    def reset_nodes(self):
        for node in nuke.allNodes():
            nuke.delete(node)
    def make_nodes(self):
        GizNodeEX.make_these_nodes_agnostic(self.gizmo, self.nodes_to_make, self.node_links)
    def do_actions(self):
        for action in self.actions:
            action.action()
    def access_write_node(self):
        return InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name)
    def call_before_logic(self):
        node = InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name)
        exec(node.knobs()["beforeRender"].value())
    def remove_before_and_after_logic(self):
        node = InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name)
        node.knob("beforeRender").setValue("")
        node.knob("afterRender").setValue("")
    def prepare_auto_actions(self):
        [self.actions.insert(0, action) for action in
            GizmoActionLookup.compile_action_list("invisible", lambda : self.gizmo, [[node_name, "clearFlag"] for node_name in ["openFolder","filetype_flwls", "datatype_flwls", "filename_flwls","info_printout",]]) +\
            GizmoActionLookup.compile_action_list("autofill_multi", lambda : self.gizmo, [["filetype_flwls",self.file_types]]) +\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : self.gizmo, [
                ["filename_flwls", {**{"custom_name" : self.name}, **self.overrides}["custom_name"]],
                ["info_printout", InternalRenderDataType.get_info_printout(
                {**{"custom_name" : self.name}, **self.overrides}["custom_name"], {**{"filetype" : self.file_types[0]}, **self.overrides}["filetype"])]]) +\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name), [
                ["create_directories", True] if "create_directories" in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs() else [],
                ])]
        if self.gizmo.knobs()["disable_execution"] != "1":
            [self.actions.insert(0, action) for action in
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name), [
                ["beforeRender" , self.resolve_beforeRenderKnobContent()],
                ["afterRender" , self.resolve_afterRenderKnobContent()],
                ])]
        [self.actions.append(action) for action in GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name), [
            ["file", self.gizmo.knobs()["filePath"].value()] if "file" in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs() else [],
            ["file_type", self.gizmo.knobs()["filetype_flwls"].value()] if "file_type" in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs()
            and self.gizmo.knobs()["filetype_flwls"].value() in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs()["file_type"].values() else [],
            ["colorspace", 6] if "colorspace" in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs() and self.name != "REVIEW_MOV" else [],
            ["colorspace", 115] if "colorspace" in InternalRenderDataType.find_this_node(self.gizmo, self.write_node_name).knobs() and self.name == "REVIEW_MOV" else [],
            ])]
        self.actions.append(GizmoAction(action=lambda : self.gizmo.knobs()["openFolder"].setVisible(True)))
        self.gizmo["tile_color"].setValue(int(self.colour, 16))
        if "renderdialog" in dir(nukescripts):
            nukescripts.renderdialog._gRenderDialogState.saveValue("frame_range", "global")
            if self.consider_sparseness:
                nukescripts.renderdialog._gRenderDialogState.saveValue("frame_range", "custom")
                nukescripts.renderdialog._gRenderDialogState.saveValue("frame_range_string", InternalRenderDataType.get_only_real_frames())
    def resolve_before_and_after(self):
        return """from internal_render import *; result = str(InternalRenderDataType.resolve_future_filepath('{}','{}')); """.format({**{"custom_name" : self.name}, **self.overrides}["custom_name"],{**{"filetype" : self.file_types[0]}, **self.overrides}["filetype"]) +\
                    """printout = InternalRenderDataType.get_info_printout('{}','{}'); """.format({**{"custom_name" : self.name}, **self.overrides}["custom_name"],{**{"filetype" : self.file_types[0]}, **self.overrides}["filetype"]) +\
                    """[node for node in current_gizmo_pointer.nodes() if node.name() == "{}"]""".format(self.write_node_name) + """[0].knobs()["file"].setValue(result); current_gizmo_pointer.knobs()['info_printout'].setValue(printout);""" +\
                    """[FlwlsVFXPipelinePanel.LogicEX.make(str(x)) for x in [Path(result).parent.parent.parent.parent, Path(result).parent.parent.parent, Path(result).parent.parent]];"""
    def resolve_beforeRenderKnobContent(self):
        return self.resolve_before_and_after() +\
            "current_gizmo_pointer.knobs()['renderHistory'].setValue(current_gizmo_pointer.knobs()['filePath'].value()); "
    def resolve_afterRenderKnobContent(self):
        result = self.resolve_before_and_after() + "current_gizmo_pointer.knobs()['openFolder'].setEnabled(True);" +\
        "current_gizmo_pointer.knobs()['readfromwrite_flwls'].setEnabled(True);"
        if not self.store_in_render_folder:
            return result
        return result + "InternalRenderDataType.move_to_render_folder();"
    def auto_tab_toggle(self):
        with self.gizmo:
            for knob_name in nuke.thisNode().knobs():
                this_knob = nuke.thisNode().knob(knob_name)
                if "tab" in this_knob.name():
                    this_knob.setFlag(nuke.INVISIBLE)
                    if this_knob.name() in self.active_tab_names:
                        this_knob.clearFlag(nuke.INVISIBLE)          
    @staticmethod
    def how_many_items_would_this_render(render_one_item_per_frame : bool):
        if not render_one_item_per_frame:
            return 1
        return len(InternalRenderDataType.get_only_real_frames().split(","))
    @staticmethod
    def get_only_real_frames():
        try:
            real_frames = [int(re.findall("[0-9]{6}", frame)[-1]) for frame in FlwlsVFXPipelinePanel.LogicEX.itera(task_set_up.traverse_from_script_folder_to_workspace_headless().parent.parent / "input/VUBB/neural_render")]
            return "".join([str(frame) + "," for frame in real_frames])[:-1]
        except Exception as EX:
            return f"{int(nuke.toNode('root').knobs()['first_frame'].value())}-{int(nuke.toNode('root').knobs()['last_frame'].value())}"
    @staticmethod
    def move_to_render_folder():
        datatype_name = current_gizmo_pointer.knobs()["datatype_flwls"].value().lower()
        version = re.findall("[v][0-9]{3}", nuke.root().name())[-1]
        destination_parent = task_set_up.traverse_from_script_folder_to_workspace_headless() / "renders" / version
        for folder in [destination_parent.parent, destination_parent]:
            FlwlsVFXPipelinePanel.LogicEX.make(str(folder))
        destination_folder = destination_parent / datatype_name
        context = FlwlsVFXPipelinePanel.LogicEX.get_context_based_on_current_path()
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)
        FlwlsVFXPipelinePanel.LogicEX.make(str(destination_folder))
        source_folder = str(Path(current_gizmo_pointer.knobs()["filePath"].value()).parent.parent)
        for file in FlwlsVFXPipelinePanel.LogicEX.itera(InternalRenderDataType.get_latest_internal_render(source_folder)):
            future_file_name = FlwlsVFXPipelinePanel.LogicEX.from_dict_to_string({**context, **{"version" : context["version"].replace("v","ws")}}, context.keys(), "_") + "_" + version + "."
            frames = re.findall("[0-9]{6}", file)
            extension = "." + file.split(".")[-1]
            if frames:
                future_file_name += frames[0] + extension
            else:
                future_file_name += extension[1:]
            file_destination = FlwlsVFXPipelinePanel.LogicEX.join(str(destination_folder), future_file_name)
            shutil.copy(file, file_destination)
    @staticmethod
    def cleanse_custom_name(custom_name : str) -> str:
        """As users can type in any custom name, make sure it is a possible folder name."""
        if current_gizmo_pointer is not None:
            custom_name = current_gizmo_pointer.knobs()["filename_flwls"].value()
            if len(custom_name) == 0:
                custom_name = current_gizmo_pointer.knobs()["datatype_flwls"].value()
        return "".join(c for c in custom_name if c.isalnum() or c == "_")
    @staticmethod
    def resolve_file_ending(ending : str) -> str:
        if ending.lower() in ["png","exr","jpg","jpeg","targa","tiff"]:
            return f".%06d.{ending}"
        return f".{ending}"
    @staticmethod
    def resolve_future_filepath(custom_name : str, ending : str) -> str:
        custom_name = InternalRenderDataType.cleanse_custom_name(custom_name)
        internal_render_target = task_set_up.traverse_from_script_folder_to_workspace_headless() / "internal_renders"
        target = internal_render_target / custom_name
        filename = custom_name + InternalRenderDataType.resolve_file_ending(ending)
        if "renderdialog" not in dir(nukescripts):
            version_target = target / InternalRenderDataType.get_latest_version(target)
            if os.path.exists(version_target):
                render_one_item_per_frame = filename.split(".")[-2] == "%06d"
                number_of_expected_items = InternalRenderDataType.how_many_items_would_this_render(render_one_item_per_frame)
                number_of_actual_items_in_last_render = len(os.listdir(version_target))
                if number_of_actual_items_in_last_render == number_of_expected_items:
                    version_target = target / InternalRenderDataType.get_next_version(target) 
        else:
            version_target = target / InternalRenderDataType.get_next_version(target)
        current_gizmo_pointer.knobs()["folderPath"].setValue(str(version_target.parent))
        current_gizmo_pointer.knobs()["filePath"].setValue(str(version_target / filename))
        return version_target / filename
    @staticmethod
    def find_this_node(gizmo, node_name) -> nuke.Node:
        return GizNodeEX.find_this_subnode(gizmo, node_name)
    @staticmethod
    def get_info_printout(custom_name : str, ending : str) -> str:
        """Get info about where a render will go."""
        filepath = "..." + str(InternalRenderDataType.resolve_future_filepath(custom_name, ending))[-50:]
        version = task_set_up.convert_version_to_int(re.findall("[v][0-9]{3}", filepath)[-1])
        version = task_set_up.convert_int_to_version(version)
        return f"Filepath: {filepath}\nVersion: {version}\n"
    @staticmethod
    def stash_custom_name():
        if current_gizmo_pointer is None:
            return
        current_gizmo_pointer.knobs()["filename_flwls_hidden"].setValue(current_gizmo_pointer.knobs()["filename_flwls"].value())
    @staticmethod
    def pop_custom_name():
        if current_gizmo_pointer is None:
            return
        current_gizmo_pointer.knobs()["filename_flwls"].setValue(current_gizmo_pointer.knobs()["filename_flwls_hidden"].value())
        current_gizmo_pointer.knobs()["filename_flwls_hidden"].setValue("")

# during a nuke callback (for example, afterRender), nuke.toNode always resolves to None, use this instead
current_gizmo_pointer = None

def get_internal_render_data_type(name: str, gizmo : nuke.Node, overrides : Dict[Any,Any] = {}) -> InternalRenderDataType:
    lookup = {
        "SELECT" : InternalRenderDataType(
            name = "SELECT",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_GEO")],
            node_links = [],
            write_node_name = "",
            file_types = [""],
            colour = "",
            active_tab_names = [],
            overrides = {},
            do_auto_actions = False,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                    ["WriteGroupBegin", "setFlag"],["filetype_flwls" , "setFlag"],["filename_flwls", "setFlag"], ["execute_write_flwls", "setFlag"], ["readfromwrite_flwls", "setFlag"]]),),
        "PREPGEO" : InternalRenderDataType(
            name = "PREPGEO",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_GEO"), NodeToMake("WriteGeo","geo"), NodeToMake("Output","OUTPUT_GEO")],
            node_links = [NodeLink("geo","INPUT_GEO", 0),NodeLink("geo","OUTPUT_GEO", 0)],
            write_node_name = "geo",
            file_types = ["abc","fbx", "obj"],
            colour = "db881bff",
            active_tab_names = ["write_geo_tab"],
            overrides = overrides,
            render_one_item_per_frame = False,
            actions = 
                GizmoActionLookup.compile_action_list("recursive", lambda : InternalRenderDataType.find_this_node(gizmo, "geo"), [["file_type", "setFlag"]]) +\
                GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "geo"), [
                    ["file_type", 0],
                    ["file_type", {**{"filetype" : "abc"}, **overrides}["filetype"]]])+\
                GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                    ["WriteGroupBegin", "clearFlag"], ["readfromwrite_flwls", "setFlag"]] +\
                    [[knob_name, "clearFlag"] if {**{"filetype" : "abc"}, **overrides}["filetype"] == "abc" else [knob_name, "setFlag"] for knob_name in \
                        ["abc_options", "writeGeometries_1", "writePointClouds_1", "writeCameras_1", "writeAxes_1", "storageFormat"]] +\
                    [[knob_name, "clearFlag"] if {**{"filetype" : "abc"}, **overrides}["filetype"] == "fbx" else [knob_name, "setFlag"] for knob_name in \
                        ["fbx_options", "compatibility_version", "writeGeometries_2", "writeCameras_2", "writeLights_1", "writeAxes_2", "writePointClouds_2", "asciiFileFormat", "animateMeshVertices"]]
                    )),
        "COPYCAT" : InternalRenderDataType(
            name = "COPYCAT",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_COPYCAT"), NodeToMake("Input","INPUT_GROUNDTRUTH"), NodeToMake("CopyCat","copycat"), NodeToMake("Output","OUTPUT_1")],
            node_links = [NodeLink("copycat", "INPUT_COPYCAT", 0),NodeLink("copycat", "INPUT_GROUNDTRUTH",1)],
            write_node_name = "copycat",
            file_types = ["cat"],
            colour = "db911bff",
            active_tab_names = ["copycat_tab","progress_tab"],
            overrides = overrides,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "setFlag"]]) +\
            GizmoActionLookup.compile_action_list("toggle_vis", lambda : gizmo, [
                ["Write_Flwls", 2]]) +\
            GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                [node, "setFlag"] for node in ["label", "note_font", "note_font_size", "note_font_color", "hide_input", "cached", "disable", "dope_sheet", "bookmark",
                "postage_stamp", "postage_stamp_frame", "lifetimeStart", "lifetimeEnd", "useLifetime", "lock_connections", "exportWrite"]])+\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "copycat"), [
                ["dataDirectory",str(InternalRenderDataType.resolve_future_filepath({**{"custom_name" : "COPYCAT"}, **overrides}["custom_name"],"").parent)]
                ])
            ,),
        "SMARTVECTOR" : InternalRenderDataType(
            name = "SMARTVECTOR",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_SMARTVECTOR"), NodeToMake("Input", "INPUT_MATTE"), NodeToMake("SmartVector", "smartvector"), NodeToMake("Write", "Write"), NodeToMake("Output", "output1")],
            node_links = [NodeLink("smartvector", "INPUT_MATTE", 1),NodeLink("smartvector", "INPUT_SMARTVECTOR", 0), NodeLink("Write", "smartvector",0), NodeLink("output1", "Write",1)],
            write_node_name = "Write",
            file_types = ["exr"],
            colour = "1bdb3bff",
            active_tab_names = ["write_tab", "smartvector_tab"],
            overrides = overrides,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "setFlag"]]) +\
            GizmoActionLookup.compile_action_list("toggle_vis", lambda : gizmo, [
                ["Write_Flwls", 2]]) +\
            GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                [node, "setFlag"] for node in ["label", "note_font", "note_font_size", "note_font_color", "hide_input", "cached", "disable", "dope_sheet", "bookmark",
                "postage_stamp", "postage_stamp_frame", "lifetimeStart", "lifetimeEnd", "useLifetime", "lock_connections", "exportWrite"]]) +\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "Write"), [
                ["channels", "all"]])) 
                ,
        "PREPCOMP" : InternalRenderDataType(
            name = "PREPCOMP",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_PREPCOMP"),NodeToMake("Write","Write"),NodeToMake("Output","output1")],
            node_links = [NodeLink("Write","INPUT_PREPCOMP", 0)],
            write_node_name = "Write",
            file_types = ["exr", "jpeg", "png", "cin", "dpx", "mov", "hdr", "targa", "tiff"],
            colour = "db1b1bff",
            active_tab_names = ["write_tab"],
            overrides = overrides,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "clearFlag"]])+\
                GizmoActionLookup.compile_action_list("disable", lambda : gizmo, [
                ["readfromwrite_flwls", "setFlag"],])+\
                GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "Write"), [
                ["channels", "all"]])),
        "FLOATING_FACE" : InternalRenderDataType(
            name = "FLOATING_FACE",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_FLOATING_FACE"), NodeToMake("Write","Write"), NodeToMake("Output","OUTPUT_1")],
            node_links = [NodeLink("Write","INPUT_FLOATING_FACE", 0)],
            write_node_name = "Write",
            file_types = ["exr"],
            colour = "1bc2dbff",
            active_tab_names = ["write_tab"],
            overrides = overrides,
            store_in_render_folder = True,
            consider_sparseness = True,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "clearFlag"]]) +\
                GizmoActionLookup.compile_action_list("disable", lambda : gizmo, [["readfromwrite_flwls", "setFlag"],])+\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "Write"), [
                ["channels", "rgba"]]),),
        "REVIEW_EXR" : InternalRenderDataType(
            name = "REVIEW_EXR",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_REVIEW_EXR"), NodeToMake("Write","Write"), NodeToMake("Output","OUTPUT_1")],
            node_links = [NodeLink("Write","INPUT_REVIEW_EXR", 0)],
            write_node_name = "Write",
            file_types = ["exr"],
            colour = "2e1bdbff",
            active_tab_names = ["write_tab"],
            overrides = overrides,
            store_in_render_folder = True,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "clearFlag"]]) +\
                GizmoActionLookup.compile_action_list("disable", lambda : gizmo, [["readfromwrite_flwls", "setFlag"],])+\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "Write"), [
                ["channels", "rgba"]]),),
        "REVIEW_MOV" : InternalRenderDataType(
            name = "REVIEW_MOV",
            gizmo = gizmo,
            nodes_to_make = [NodeToMake("Input", "INPUT_REVIEW_MOV"), NodeToMake("Write","Write"), NodeToMake("Output","OUTPUT_1")],
            node_links = [NodeLink("Write","INPUT_REVIEW_MOV",0)],
            write_node_name = "Write",
            file_types = ["mov"],
            colour = "c71bdbff",
            active_tab_names = ["write_tab"],
            overrides = overrides,
            store_in_render_folder = True,
            render_one_item_per_frame = False,
            actions = GizmoActionLookup.compile_action_list("invisible", lambda : gizmo, [
                ["WriteGroupBegin", "clearFlag"],["readfromwrite_flwls", "clearFlag"]]) +\
                GizmoActionLookup.compile_action_list("disable", lambda : gizmo, [["readfromwrite_flwls", "setFlag"],])+\
            GizmoActionLookup.compile_action_list("autofill_single", lambda : InternalRenderDataType.find_this_node(gizmo, "Write"), [
                ["file_type", "mov"]])
                ,
        ),
        
    }
    return lookup[name]