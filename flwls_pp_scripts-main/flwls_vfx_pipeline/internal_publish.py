import os
import nuke
import nuke_utils
import FlwlsVFXPipelinePanel
from GUI import KnobStem
import json
from pathlib import Path
import re
import task_set_up
import migrate_tab_panel_scripts
from typing import Any, Dict, List


class InternalPubEX():
    """Handles writing and reading files for internal publishes."""
    target_write_node_base_name = "Write_Flwls"
    target_read_node_base_name = "Read_Flwls"
    knob_base_name = "intpub"
    node_padding = 350

    def get_list_of_flwls_write_nodes() -> List[nuke.Node]:
        return [node for node in nuke.allNodes() if node.name()[:len(InternalPubEX.target_write_node_base_name)] == InternalPubEX.target_write_node_base_name
        and "folderPath" in [knob for knob in node.knobs()]
        and os.path.exists(node.knobs()["folderPath"].value())
        and os.path.exists(InternalPubEX.try_to_get_absolute_dir(node.knobs()["folderPath"].value()))
        and os.listdir(InternalPubEX.try_to_get_absolute_dir(node.knobs()["folderPath"].value()))
        and [folder for folder in FlwlsVFXPipelinePanel.LogicEX.itera(node.knobs()["folderPath"].value()) if os.listdir(folder)]
        ]

    def get_list_of_flwls_read_nodes() -> List[nuke.Node]:
        return [node for node in nuke.allNodes() if node.name()[:len(InternalPubEX.target_read_node_base_name)] == InternalPubEX.target_read_node_base_name]

    def try_to_get_current_context() -> Dict[Any,Any]:
        try:
            return FlwlsVFXPipelinePanel.LogicEX.get_context_based_on_current_path()
        except Exception as EX:
            return False # script hasn't been saved / isn't in valid pipeline location

    def get_latest_internal_render(filepath : str) -> str:
        return [folder for folder in FlwlsVFXPipelinePanel.LogicEX.itera(filepath) if os.listdir(folder)][-1]

    def offer_user_intpub_options() -> List[KnobStem]:
        context = InternalPubEX.try_to_get_current_context()
        if not context:
            return [KnobStem("SnapshotText","Text","",lambda : 0,0, {"value" : "Current script has not been saved in a valid VFX task workspace location."})] 
        results = []
        for node in InternalPubEX.get_list_of_flwls_write_nodes():
            datatype = node.knobs()["datatype_flwls"].value()
            filepath = InternalPubEX.try_to_get_absolute_dir(node.knobs()["folderPath"].value())
            latest = InternalPubEX.get_latest_internal_render(filepath)
            datatype_dir = InternalPubEX.resolve_path_to_internal_datatype_dir(datatype)
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Text1","Text","", lambda : 0, 0, {"value" : nuke_utils.get_coloured_text("Node Name: ", "#d33834") + node.name()}))
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Text2","Text", "", lambda : 0,0, {"value" :  nuke_utils.get_coloured_text("Datatype: ", "#d33834") + datatype}))
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Text3","Text", "", lambda : 0,0, {"value" :  nuke_utils.get_coloured_text("Source: ...", "#d33834") + latest[-50:]}))
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Text4","Text","",lambda : 0,0, {"value" : nuke_utils.get_coloured_text("Next Snapshot Version: ", "#d33834") + InternalPubEX.get_next_version(datatype_dir)}))
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Button1","PyScript","Internally Publish This Node", lambda : InternalPubEX.run_internal_publish_via_knob(),1, {"label" : "Internal Publish"}))
            results.append(KnobStem(node.name() + InternalPubEX.knob_base_name + "Text5","Text", "", lambda : 0,0, {"value" :  "-"*50}))
        if not results:
            message = "The Flwls_Write nodes need to have their datatypes set, and have been rendered."
            results.append(KnobStem(InternalPubEX.knob_base_name + "Text1","Text",message, lambda : 0, 1, {}))
        results.insert(0, KnobStem("SnapShotAllButton","PyScript","Internally Publish All Nodes", lambda : InternalPubEX.internal_publish_all(),0, {"label" : "Internally Publish All Nodes"}))
        return results

    def refresh() -> None:
        setattr(nuke, "VFXPipelinePanelBasic", FlwlsVFXPipelinePanel.VFXPipelinePanelBasic())
        nuke.tabClose()
        nuke.VFXPipelinePanelBasic.addToPane()
        InternalPubEX.toggle_knob_visibility("Open Script", 3)
        InternalPubEX.toggle_knob_visibility("Internal Publish", 2)

    def toggle_knob_visibility(knob_name : str, count : int) ->None:
        for x in range(0, count):
            nuke.VFXPipelinePanelBasic.knobs()[knob_name].setVisible(not nuke.VFXPipelinePanelBasic.knobs()[knob_name].visible())

    def resolve_path_to_internal_pub_dir() -> str:
        if not InternalPubEX.try_to_get_current_context():
            return ""
        workspace_folder = task_set_up.traverse_from_script_folder_to_workspace_path(nuke.root().name()).parent / "internal_publishes"
        return workspace_folder
    
    def resolve_path_to_internal_datatype_dir(datatype : str) -> Path:
        if InternalPubEX.resolve_path_to_internal_pub_dir() == "":
            return ""
        result =  InternalPubEX.resolve_path_to_internal_pub_dir() / datatype
        return result

    def resolve_path_to_selected_datatype_and_version_dir() -> Path:
        datatype = nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum1"].value()
        version = nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum2"].value().split(" ")[0]
        return InternalPubEX.resolve_path_to_internal_datatype_dir(datatype) / version / datatype

    def get_next_version(path: Path) -> str:
        if not (os.path.exists(path) and os.path.isdir(path)):
            return "v001"
        return task_set_up.convert_int_to_version(task_set_up.convert_version_to_int(InternalPubEX.get_existing_internal_publishes(path)[-1])+1)

    def get_existing_internal_publishes(path : str) -> List[str]:
        if not os.path.exists(path) or not os.listdir(path):
            return ["v000"]
        version_regex = re.compile(FlwlsVFXPipelinePanel.LogicEX.get_version_regex())
        return [ver for ver in sorted(os.listdir(path)) if version_regex.match(ver) is not None]

    def get_full_info_for_existing_internal_publishes(path : str) ->List[str]:
        version_regex = re.compile(FlwlsVFXPipelinePanel.LogicEX.get_version_regex())
        def get(ver):
            return InternalPubEX.read_metadata(path / f"{ver}/metadata/metadata.json")
        return [ver + f" (Workspace Version : {get(ver)['workspace_version']}           PT Version: {get(ver)['pt_version']})"
            for ver in sorted(os.listdir(path)) 
            if version_regex.match(ver) is not None]

    def try_to_get_absolute_dir(filepath : str):
        if os.path.isdir(filepath):
            return filepath
        return str(Path(filepath).parent)

    def run_internal_publish_via_knob() -> None:
        """Called directly from knob and gets node name from nuke.thisKnob"""
        node_name = nuke.thisKnob().name()[:nuke.thisKnob().name().index(InternalPubEX.knob_base_name)]
        InternalPubEX.internal_publish_by_name(node_name)
    
    def internal_publish_by_name(node_name):
        """Can be called outside node using knob name for access."""
        node = nuke.toNode(node_name)
        datatype = node.knobs()["datatype_flwls"].value()
        filepath =  InternalPubEX.try_to_get_absolute_dir(node.knobs()["folderPath"].value())
        latest = InternalPubEX.get_latest_internal_render(filepath)
        internal_pub_dir = str(InternalPubEX.resolve_path_to_internal_pub_dir())
        if not os.path.exists(os.path.dirname(internal_pub_dir)):
            return
        datatype_dir = str(InternalPubEX.resolve_path_to_internal_datatype_dir(datatype))
        version = InternalPubEX.get_next_version(datatype_dir)
        destination_folder = f"{datatype_dir}/{version}"
        content_destination_folder = f"{destination_folder}/{datatype}"
        nuke_script_destination_folder = f"{destination_folder}/nuke_script"
        metadata_folder = f"{destination_folder}/metadata"
        for folder in [internal_pub_dir, datatype_dir, destination_folder,content_destination_folder,nuke_script_destination_folder, metadata_folder]:
            FlwlsVFXPipelinePanel.LogicEX.make(folder)
        for file in FlwlsVFXPipelinePanel.LogicEX.itera(latest):
            file_name = FlwlsVFXPipelinePanel.LogicEX.get_full_name(file)
            destination = FlwlsVFXPipelinePanel.LogicEX.join(content_destination_folder, file_name)
            os.system(f"ln {file} {destination}")
        nuke.scriptSave()
        os.system(f"ln {nuke.root().name()} {nuke_script_destination_folder}/{os.path.basename(nuke.root().name())}")
        metadata = {"workspace_version" : "v" + str(migrate_tab_panel_scripts._get_source_workspace_version(Path(nuke.root().name()))),
        "pt_version" : migrate_tab_panel_scripts.get_PT_SG_version_only(Path(nuke.root().name()))}
        InternalPubEX.save_metadata(metadata, f"{metadata_folder}/metadata.json")
        InternalPubEX.refresh()
    
    def save_metadata(data, location):
        file = open(location, "w")
        json.dump(data, file)
        file.close()

    def read_metadata(location):
        file = open(location, "r")
        results = json.loads(file.read())
        file.close()
        return results

    def internal_publish_all() -> None:
        for node in InternalPubEX.get_list_of_flwls_write_nodes():
            InternalPubEX.internal_publish_by_name(node.name())

    def get_existing_datatype_publishes() -> List[str]:
        if not os.path.exists(InternalPubEX.resolve_path_to_internal_pub_dir()):
            return []
        return sorted([FlwlsVFXPipelinePanel.LogicEX.get_full_name(data) for data in FlwlsVFXPipelinePanel.LogicEX.itera(InternalPubEX.resolve_path_to_internal_pub_dir())
            if os.listdir(data)
        ])
    
    def update_datatype_select_knob() -> None:
        to_update = ["RetrieveIntPubEnum2", "RetrieveIntPubButton1", ]
        for knob in to_update:
            nuke.VFXPipelinePanelBasic.knobs()[knob].setEnabled(False)
        datatype_selection = nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum1"].value()
        path = InternalPubEX.resolve_path_to_internal_datatype_dir(datatype_selection)
        versions = InternalPubEX.get_full_info_for_existing_internal_publishes(path)
        if versions == ["v000"]: # no existing versions
            return
        nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum2"].setValues(versions)
        nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum2"].setValue(versions[-1])
        nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubEnum2"].setEnabled(True)
        nuke.VFXPipelinePanelBasic.knobs()["RetrieveIntPubButton1"].setEnabled(True)

    def retrieve_user_selected_internal_publish_inbuilt() -> None:
        """Add an in-built read node for this internal publish."""
        path_to_data = InternalPubEX.resolve_path_to_selected_datatype_and_version_dir()
        is_image = InternalPubEX.type_of_data(path_to_data, [".png",".exr",".jpg",".jpeg"])
        is_file_sequence = len(os.listdir(path_to_data)) > 1
        is_video = InternalPubEX.type_of_data(path_to_data, [".mov"])
        is_geometry = InternalPubEX.type_of_data(path_to_data, [".fbx",".abc",".obj"])
        node_name = InternalPubEX.get_name_of_next_flwls_read_node()
        if is_image and is_file_sequence:
            read_node = InternalPubEX.make_new_flwls_read_node("Read")
            nuke_utils.add_image_sequence_to_this_node(read_node, str(path_to_data))
        if is_image and not is_file_sequence:
            read_node = InternalPubEX.make_new_flwls_read_node("Read")
            read_node.fromUserText(FlwlsVFXPipelinePanel.LogicEX.itera(path_to_data)[0])
        if is_video:
            read_node = InternalPubEX.make_new_flwls_read_node("Read")
            read_node.fromUserText(FlwlsVFXPipelinePanel.LogicEX.itera(path_to_data)[0])
            read_node.knobs()["colorspace"].setValue("Output - sRGB")
            nuke.root().knobs()["first_frame"].setValue("1")
            read_node.knobs()["frame_mode"].setValue("start at")
            read_node.knobs()["frame"].setValue("1")
        if is_geometry:
            read_node = InternalPubEX.make_new_flwls_read_node("ReadGeo")
            read_node.fromUserText(FlwlsVFXPipelinePanel.LogicEX.itera(path_to_data)[0])
    
    def get_name_of_next_flwls_read_node() -> str:
        existing_flwls_read_node_names = [node.name() for node in InternalPubEX.get_list_of_flwls_read_nodes()] 
        if not existing_flwls_read_node_names:
            return InternalPubEX.target_read_node_base_name
        else:
            target = 1
            while True:
                result = f"{InternalPubEX.target_read_node_base_name}{target}"
                target+=1
                if result not in existing_flwls_read_node_names:
                    break
            return result

    def make_new_flwls_read_node(node_type : str) -> nuke.Node:
        next_name = InternalPubEX.get_name_of_next_flwls_read_node()
        next_position = InternalPubEX.get_position_of_next_flwls_read_node()
        result = nuke_utils.make_node(node_type, next_name)
        nuke_utils.put_node_here(next_name, next_position[0],next_position[1])
        return result
    
    def get_position_of_next_flwls_read_node() -> List[int]:
        existing_flwls_read_node_names = [node.name() for node in InternalPubEX.get_list_of_flwls_read_nodes()] 
        other_node_names = [node.name() for node in nuke.allNodes() if node.name() not in existing_flwls_read_node_names]
        if not existing_flwls_read_node_names and not other_node_names:
            return [0,0]
        if not existing_flwls_read_node_names and other_node_names:
            anchor = [nuke.toNode(other_node_names[0]).xpos(), nuke.toNode(other_node_names[0]).ypos()]
            return [anchor[0] + (InternalPubEX.node_padding * (len(existing_flwls_read_node_names))), anchor[1] - InternalPubEX.node_padding]
        if existing_flwls_read_node_names:
            anchor = [nuke.toNode(existing_flwls_read_node_names[-1]).xpos(), nuke.toNode(existing_flwls_read_node_names[-1]).ypos()]
            return [anchor[0] + (InternalPubEX.node_padding * (len(existing_flwls_read_node_names))), anchor[1]]
        return [0,0]
    
    def type_of_data(folder : str, types : List[str]) -> bool:
        return Path(os.listdir(folder)[0]).suffix in types

