from GUI import KnobStem, Panel, PanelContent, TabStem
import nuke
import nuke_utils
import os
from pathlib import Path
import re
import tempfile
from typing import Dict, Any, List

class ReporterEX():
    report = []
    def add(message : str):
        ReporterEX.report.append(message)
    def tell() -> str:
        message = ""
        for line in ReporterEX.report:
            message += line + "\n"
        return message
    def popup():
        nuke.message(ReporterEX.tell())
    def reset():
        ReporterEX.report = []

class LogicEX():
    start = 1
    coordinates = [0,0]
    gap = 150
    count = 1
    csv_path = ""
    output_root = ""
    path_to_science = ""
    script_start_frame = 1

    def reset_node_layout():
        LogicEX.count = 1
        coordinates = [0,0]

    def run(inputs : List[str], context : Dict[str,Any], render):
        to_refer_to = inputs[0]
        LogicEX.reset_node_layout()
        nuke_utils.delete_all()
        nuke.frame(LogicEX.script_start_frame)

        nuke_utils.make_node("ContactSheet","Contact_Sheet")
        nuke.toNode("Contact_Sheet").setXYpos(LogicEX.coordinates[0]+LogicEX.gap//2,LogicEX.coordinates[1]*LogicEX.gap+int(LogicEX.gap*1.5))
        nuke.toNode("Contact_Sheet").knobs()["columns"].setValue(2)
        nuke.toNode("Contact_Sheet").knobs()["rows"].setValue(2)
        nuke.toNode("Contact_Sheet").knobs()["roworder"].setValue("TopBottom")
        nuke.toNode("Contact_Sheet").knobs()["colorder"].setValue("LeftRight")
        nuke.toNode("Contact_Sheet").knobs()["center"].setValue(True)
        nuke.root().knobs()["fps"].setValue(24)

        for to_add in inputs:
            LogicEX.add_text(to_add)
            nuke.toNode(to_add + "_text").knobs()["message"].setValue(context[to_add + "_text_content"])
            if context[to_add + "_exists"]:
                for instruction in context[to_add + "_instructions"]:
                    instruction(to_add, context[to_add])
            else:
                ReporterEX.add(context["context"] + " is missing this input: " + to_add)
                LogicEX.add_fake_black_box(to_add, to_refer_to) 
            LogicEX.count+=1

        width, height = 1024,1024
        nuke.root().knobs()["last_frame"].setValue(len(os.listdir(context[to_refer_to])))
        nuke.toNode("Contact_Sheet").knobs()["width"].setValue(width)
        nuke.toNode("Contact_Sheet").knobs()["height"].setValue(height)
        
        nuke.nodePaste(str(Path(__file__).parent / "templates/quad_sheet/quad_sheet_text_node_raw_NR.txt"))
        nuke.toNode("Contact_Sheet_Text").setInput(0,nuke.toNode("Contact_Sheet"))
        LogicEX.apply_default_text_settings("Contact_Sheet_Text")
        nuke_utils.make_node("Viewer","Viewer")
        nuke.toNode("Viewer").setInput(0,nuke.toNode("Contact_Sheet_Text"))
        LogicEX.make_writer(context)
        LogicEX.save_as(context)
        if render:
            LogicEX.render()
        LogicEX.save_as(context)
        ReporterEX.add(context["context"] + " was made.\n")
        LogicEX.count = 1

    def add_image_sequence(name : str, path_to_image_sequence : str):
        shot_length = len(os.listdir(path_to_image_sequence))
        file_format = "." + os.listdir(path_to_image_sequence)[0].split(".")[-1]
        pound_signs = "#" * len(os.listdir(path_to_image_sequence)[0].split(".")[-2])
        file_name_of_first_frame = sorted(os.listdir(path_to_image_sequence))[0]
        file_name_of_first_frame_without_frame_number = file_name_of_first_frame[:-10]
        first_frame = str(int(sorted(os.listdir(path_to_image_sequence))[0].split(".")[-2]))
        last_frame = str(int(sorted(os.listdir(path_to_image_sequence))[-1].split(".")[-2]))

        ending = pound_signs + file_format + " "
        shot_end = LogicEX.start-1+shot_length
        read_node_name = name
        text_node_name = read_node_name + "_text"
        first_frame_hashed = str(path_to_image_sequence) + "/" + (file_name_of_first_frame_without_frame_number + ending + first_frame + "-" + last_frame)
        nuke_utils.make_node("Read",read_node_name)
        nuke.toNode(read_node_name).knobs()["file"].fromUserText(first_frame_hashed)
        nuke.toNode(read_node_name).setXYpos(LogicEX.coordinates[0]+LogicEX.count*LogicEX.gap,LogicEX.coordinates[1])
        nuke.toNode(read_node_name).knobs()["first"].setValue(int(first_frame))
        nuke.toNode(read_node_name).knobs()["last"].setValue(int(last_frame))
        nuke.toNode(read_node_name).knobs()["origfirst"].setValue(int(first_frame))
        nuke.toNode(read_node_name).knobs()["origlast"].setValue(int(last_frame))
        nuke.toNode(read_node_name).knobs()["colorspace"].setValue("Output - sRGB")
        nuke.toNode(read_node_name).knobs()["on_error"].setValue("black")
        if file_format == ".png":
            nuke.toNode(read_node_name).knobs()["colorspace"].setValue("ACES - ACEScct")
        
        nuke.root().knobs()["first_frame"].setValue(LogicEX.script_start_frame)
        nuke.toNode(read_node_name).knobs()["frame_mode"].setValue("start at")
        nuke.toNode(read_node_name).knobs()["frame"].setValue(str(LogicEX.script_start_frame))
        nuke.toNode(text_node_name).setInput(0,nuke.toNode(read_node_name))

    def add_video(name : str, path_to_video : str):
        read_node_name = name
        text_node_name = name + "_" + "text"
        nuke_utils.make_node("Read",read_node_name)
        nuke.toNode(read_node_name).knobs()["file"].fromUserText(path_to_video)
        nuke.toNode(read_node_name).setXYpos(LogicEX.coordinates[0]+LogicEX.count*LogicEX.gap,LogicEX.coordinates[1])
        nuke.toNode(read_node_name).knobs()["colorspace"].setValue("Output - sRGB")
        nuke.toNode(text_node_name).setInput(0,nuke.toNode(read_node_name))
        nuke.root().knobs()["first_frame"].setValue(LogicEX.script_start_frame)
        nuke.toNode(read_node_name).knobs()["frame_mode"].setValue("start at")
        nuke.toNode(read_node_name).knobs()["frame"].setValue(str(LogicEX.script_start_frame))

    def apply_default_text_settings(text_node_name):
        nuke.toNode(text_node_name).knobs()["enable_shadows"].setValue(True)
        nuke.toNode(text_node_name).knobs()["enable_shadows"].setValue(True)
        nuke.toNode(text_node_name).knobs()["shadow_opacity"].setValue(1)
        nuke.toNode(text_node_name).knobs()["shadow_distance"].setValue(0)
        nuke.toNode(text_node_name).knobs()["shadow_size"].setValue(5)

    def add_text(name):
        read_node_name = name
        text_node_name = name + "_" + "text"
        nuke_utils.make_node("Text2",text_node_name)
        nuke.toNode(text_node_name).knobs()["message"].setValue(name.replace("_"," "))
        nuke.toNode(text_node_name).setInput(0,nuke.toNode(read_node_name))
        nuke.toNode(text_node_name).knobs()["box"].setR(1024)
        nuke.toNode(text_node_name).knobs()["box"].setT(1024)
        nuke.toNode(text_node_name).knobs()["global_font_scale"].setValue(1)
        nuke.toNode(text_node_name).knobs()["yjustify"].setValue("bottom")
        nuke.toNode(text_node_name).knobs()["xjustify"].setValue("left")
        nuke.toNode(text_node_name).setXYpos(LogicEX.coordinates[0]+LogicEX.count*LogicEX.gap,LogicEX.coordinates[1]*LogicEX.gap+LogicEX.gap)
        LogicEX.apply_default_text_settings(text_node_name)
        nuke.toNode("Contact_Sheet").setInput(LogicEX.count-1,nuke.toNode(text_node_name))

    def save_as(context : Dict[str,Any]):
        location = os.path.join(LogicEX.output_root,context["context"]) 
        location_as_path = Path(location)
        for folder in [location_as_path.parent.parent.parent, location_as_path.parent.parent, location_as_path.parent, location_as_path]:
            LogicEX.make(folder)
        nuke.scriptSaveAs(filename=location + "/" + context["context"] + ".nk", overwrite = True)

    def run_all(style_name : str):
        inputs = QuadSheetStyleLookup.get_style(style_name).inputs
        to_process = LogicEX.get_contexts_from_csv(LogicEX.csv_path)
        render = True
        if nuke.QuadPanel.Render.value() == "No":
            render = False
        if not to_process:
            nuke.message("That CSV file supplied has no shot contexts that could be interpreted, please check the file and try again!")
        for context in to_process:
            LogicEX.run(inputs, context, render)

    def make_writer(context : Dict[str,Any]):
        nuke.nodePaste(str(Path(__file__).parent / "templates/quad_sheet/quad_sheet_write_node_raw.txt"))
        nuke.toNode("Writer").setXYpos(LogicEX.coordinates[0]+LogicEX.gap//2,LogicEX.coordinates[1]*LogicEX.gap+int(LogicEX.gap*3.5))
        nuke.toNode("Writer").setInput(0,nuke.toNode("Contact_Sheet_Text"))
        write_destination = LogicEX.get_write_destination(context)
        nuke.toNode("Writer").knobs()["file"].setValue(write_destination)
        nuke.toNode("Writer").knobs()["mov64_audiofile"].setValue(context["audio"])
        nuke.toNode("Writer").knobs()["first"].setValue(int(nuke.root().knobs()["first_frame"].value()))
        nuke.toNode("Writer").knobs()["last"].setValue(int(nuke.root().knobs()["last_frame"].value()))

    def get_write_destination(context : Dict[str,Any]):
        return str(Path(LogicEX.output_root) / str(context["context"] + "/" + context["context"] + ".mov"))

    def render():
        start = str(int(nuke.root().knobs()["first_frame"].value()))
        end = str(int(nuke.root().knobs()["last_frame"].value()))
        os.system(os.environ["NUKE_EXE_PATH"] + f" -X Writer {nuke.scriptName()} {start}-{end}")

    def tell_which_ones_are_missing_inputs():
        for context in LogicEX.get_contexts_from_csv(LogicEX.csv_path):
            LogicEX.run(context, False)
        file = open(tempfile.gettempdir() + "/nukeReport.txt", "w")
        for line in ReporterEX.report:
            file.write(ReporterEX.report)
        file.close()

    def run_all_skip_if_video_exists():
        for context in LogicEX.get_contexts_from_csv(LogicEX.csv_path):
            if os.path.exists(LogicEX.get_write_destination(context)):
                continue
            LogicEX.run(context)

    def parse_context(context : str, target_version = "LATEST"):
        show = context.split("_")[0]
        episode = context.split("_")[1]
        part = context.split("_")[2]
        shot = context.split("_")[3]
        language = context.split("_")[4]
        character = context.split("_")[5]
        variant = context.split("_")[6]
        charvar = character + "_" + variant
        root_path = LogicEX.get_root_path(context)
        latest_vubb_version = LogicEX.get_path_to_latest_slapcomp(root_path)
        if target_version != "LATEST":
            latest_vubb_version = target_version
        slapcomp_path = None
        neural_render_path = None
        dataset_path = None
        if latest_vubb_version is not None:    
            slapcomp_path = root_path + "/output/VUBB/" + latest_vubb_version + "/slapcomp/"
            slapcomp_path += os.listdir(slapcomp_path)[0]
            neural_render_path = root_path + "/output/VUBB/" + latest_vubb_version + "/neural_render"
            dataset_path = root_path + "/output/VUBB/" + latest_vubb_version + "/dataset"
        else:
            latest_vubb_version = ""
        reference_path = f"/Volumes/workspace/shows/{show}/internal/PT_Refs/{part}/{context}.mov"
        ground_truth_path = root_path + "/PROXYJPG/proxy"
        face_on_path = LogicEX.get_path_to_latest_faceon_comp(str(Path(root_path).parent) + "/faceon_comp/")
        audio_path = root_path + "/AUDIO/audio/" + os.listdir(root_path + "/AUDIO/audio/")[0]
        science_NR_path = str(Path(LogicEX.path_to_science)) + f"/{show}_{episode}_{part}_{shot}/languages/{language}/variants/{charvar}/VUBB/neural_render"
        if not os.path.exists(science_NR_path) or not os.listdir(science_NR_path):
            science_NR_path = None
        
        return {
            "show" : show,
            "episode" : episode,
            "part" : part,
            "shot" : shot,
            "character" : character,
            "language" : language,
            "variant" : variant,
            "charvar" : character + "_" + variant,
            "context" : context,
            "root_path" : root_path,
            "Ground_Truth" : ground_truth_path,
            "Ground_Truth_exists" : os.path.exists(ground_truth_path),
            "Ground_Truth_instructions" : [LogicEX.add_image_sequence],
            "Ground_Truth_text_content" : "Original Ref",
            "Slapcomp" : slapcomp_path,
            "Slapcomp_exists" : slapcomp_path is not None and os.path.exists(slapcomp_path),
            "Slapcomp_text_content" : "PT Slapcomp " + latest_vubb_version,
            "Slapcomp_instructions" : [LogicEX.add_video],
            "NeuralRender" : neural_render_path,
            "NeuralRender_exists" : neural_render_path is not None and os.path.exists(neural_render_path),
            "NeuralRender_text_content" : "Prod NR " + latest_vubb_version,
            "NeuralRender_instructions" : [LogicEX.add_image_sequence],
            "Reference" : reference_path,
            "Reference_exists" : os.path.exists(reference_path),
            "Reference_text_content" : "PT Ref",
            "Reference_instructions" : [LogicEX.add_video],
            "FaceOn" : face_on_path,
            "FaceOn_exists" : face_on_path is not None and os.path.exists(face_on_path),
            "FaceOn_text_content" : "FaceOn",
            "FaceOn_instructions" :  [LogicEX.add_video],
            "ScienceNR" : science_NR_path,
            "ScienceNR_exists" : science_NR_path is not None and os.path.exists(science_NR_path),
            "ScienceNR_text_content" : "Science NR",
            "ScienceNR_instructions" : [LogicEX.add_image_sequence],
            "Dataset" : dataset_path,
            "Dataset_exists" : dataset_path is not None and os.path.exists(dataset_path),
            "Dataset_text_content" : "Original Ref",
            "Dataset_instructions": [LogicEX.add_image_sequence, LogicEX.add_dataset_crop],
            "audio" : audio_path,
            }

    def get_root_path(context : str):
        show = context.split("_")[0]
        episode = context.split("_")[1]
        part = context.split("_")[2]
        shot = context.split("_")[3]
        language = context.split("_")[4]
        character = context.split("_")[5]
        variant = context.split("_")[6]
        charvar = character + "_" + variant
        return f"/Volumes/workspace/shows/{show}/episodes/{episode}/parts/{part}/shots/{shot}/languages/{language}/variants/{charvar}/tasks/performance_transfer"

    def get_all_slapcomp_versions(vubb_dir : str) -> List[Any]:
        return sorted([version for version in os.listdir(vubb_dir) if os.path.isdir(vubb_dir + version) and "slapcomp" in os.listdir(vubb_dir + version)])

    def get_path_to_latest_slapcomp(root_path : str):
        vubb_dir = root_path + "/output/VUBB/"
        try:
            return LogicEX.get_all_slapcomp_versions(vubb_dir)[-1]
        except Exception as EX:
            print("No slapcomp exists for " + root_path)
            return None 

    def is_this_a_shot_context(string : str):
        return re.match("[a-z]{4}[0-9]{2}_ep[0-9]{2}_pt[0-9]{2}_[0-9]{4}.*", string) is not None

    def read_csv_file(csv_path : str):
        # format of csv file is unexpected so did this manually
        file = open(csv_path)
        contents = file.read()
        file.close()
        results = []
        for row in contents.split("\n"):
            for column in row.split(","):
                if LogicEX.is_this_a_shot_context(column) and column not in results:
                    results.append(column)
        return results

    def get_contexts_from_csv(csv_path : str) -> List[Dict[str,Any]]:
        to_do = LogicEX.read_csv_file(csv_path)
        return [LogicEX.parse_context(context) for context in to_do]

    def get_path_to_latest_faceon_comp(root_path : str):
        try:
            all_versions = sorted([os.path.join(root_path, version) for version in os.listdir(root_path)])
            versions_with_outputs = [os.path.join(version, "output") for version in all_versions if "output" in os.listdir(version)]
            versions_with_floating_faces = [os.path.join(version, "FLOATING_FACE") for version in versions_with_outputs if "FLOATING_FACE" in os.listdir(version)]
            versions_with_reviews = [os.path.join(version, "review") for version in versions_with_floating_faces if "review" in os.listdir(version)]
            versions_with_videos = [os.path.join(version, os.listdir(version)[0]) for version in versions_with_reviews if len(os.listdir(version)) > 0]
            if not versions_with_videos:
                return None
            return versions_with_videos[-1]
        except Exception as EX:
            return None # no valid face on exists

    def make(folder : str):
        if not os.path.exists(folder):
            os.mkdir(folder)

    def run_via_csv(csv_path : str, output_root : str):
        ReporterEX.reset()
        LogicEX.csv_path = csv_path
        LogicEX.output_root = output_root
        LogicEX.run_all(nuke.QuadPanel.Style.value())
        ReporterEX.popup()
        ReporterEX.reset()

    def add_fake_black_box(to_add, reference_node):
        """Text is misaligned when set on no input.
        Can use a different input and set gamma to zero to get black background."""
        nuke_utils.unselect_all()
        text_node_name = to_add + "_text"
        gamma_node_name = to_add + "_Gamma"
        nuke_utils.make_node("Gamma",gamma_node_name)
        nuke.toNode(text_node_name).setInput(0,nuke.toNode(gamma_node_name))
        nuke.toNode(gamma_node_name).setInput(0,nuke.toNode(reference_node))
        nuke.toNode(gamma_node_name).knobs()["value"].setValue(0)
        nuke_utils.unselect_all()
        nuke.toNode(gamma_node_name).setXYpos(nuke.toNode(text_node_name).xpos(), nuke.toNode(gamma_node_name).ypos())

    def add_dataset_crop(name: str, path_to_image_sequence : str):
        nuke_utils.make_node("Crop",f"Crop_{name}")
        nuke.toNode(f"Crop_{name}").setXYpos(LogicEX.coordinates[0]+LogicEX.count*LogicEX.gap,LogicEX.coordinates[1]-LogicEX.count*-1)
        nuke.toNode(f"Crop_{name}").setInput(0,nuke.toNode(name))
        nuke.toNode(f"Crop_{name}").knobs()["box"].setValue([0,0,1024,1024])
        nuke.toNode(f"Crop_{name}").knobs()["reformat"].setValue(True)
        nuke_utils.make_node("Switch",f"Switch_{name}")
        nuke.toNode(f"Switch_{name}").setInput(0,nuke.toNode(f"Crop_{name}"))
        nuke.toNode(f"Switch_{name}").setXYpos(LogicEX.coordinates[0]+LogicEX.count*LogicEX.gap,LogicEX.coordinates[1]-LogicEX.gap*-3)
        nuke.toNode(f"{name}_text").setInput(0,nuke.toNode(f"Switch_{name}"))

    def get_single_context_versions(context : str) -> str:
        try:
            root_path = LogicEX.get_root_path(context)
            if not os.path.exists(root_path):
                return []
            return [version.split("/")[-1] for version in LogicEX.get_all_slapcomp_versions(root_path + "/output/VUBB/")]
        except Exception:
            return [] # context is incorrect / does not exist

    def present_single_context_versions(context : str) -> List[Any]:
        return ["LATEST"] + LogicEX.get_single_context_versions(context)

    def convert_yes_no_to_bool(string : str):
        return "yes" in string.lower() 

class QuadSheetStyleLookup():
    def get_style(name):
        return QuadSheetStyleLookup.get_all_styles()[name]
    def get_all_styles():
        return {
            "Neural Render" : QuadSheetStyleLookup.Style(name="Neural Render", inputs=["Dataset", "Reference", "NeuralRender", "ScienceNR"]),
            "Full Frame" : QuadSheetStyleLookup.Style(name="Full Frame", inputs=["Ground_Truth", "Reference", "Slapcomp", "FaceOn"]),
        }
    def get_all_style_names():
        return list(QuadSheetStyleLookup.get_all_styles().keys())
    class Style():
        def __init__(self, name, inputs):
            self.name = name
            self.inputs = inputs

class QuadPanel(Panel):
    version = "1.1"

    def __init__(self):
        Panel.set_up(self, PanelContent(name = "Quad Split View Maker", title_list=[
            KnobStem("WorkspaceTitle", "Text", "", lambda: 0,0,{"value" : "<font size='7' color='#d33834'>Quad Split Review Maker</font>"})],
                tab_list=[TabStem(name="Version " + QuadPanel.version,
                    knob_list=[
                        KnobStem("Style","Enumeration","Select the Style of Quad Sheet to Make:", lambda : 0, 1, {"constructor" : QuadSheetStyleLookup.get_all_style_names()}),
                        KnobStem("Render","Enumeration","Render a Video Output for each context?:", lambda : 0, 1, {"constructor" : ["Yes","No"]}),
                        KnobStem("OpenCSV","File","Select the CSV File to process:", lambda : self.openCSV(),1, {}),
                        KnobStem("OutputDir","File","Select a directory in which to save results:", lambda : self.openCSV() or self.singleContext(), 1, {"value" : tempfile.gettempdir()}),
                        KnobStem("ScienceDir","String","Select the root directory of the Science Slapcomps:", 
                            lambda : setattr(LogicEX, "path_to_science", self.ScienceDir.getValue()), 1, {"force_set" : "/Volumes/workspace/shows/ufof01/investigations/231213_fox_adfa_new_model_result"}),
                        KnobStem("Execute","PyScript","Process CSV File",lambda : LogicEX.run_via_csv(self.OpenCSV.getValue(),self.OutputDir.getValue()), 2, {"enabled":False}),
                        KnobStem("JustOneContext","String","Input just one context to process:",lambda : self.singleContext(), 1, {}),
                        KnobStem("VersionControl","Enumeration","Process just one context using this vubb version", lambda : 0, 1,{"constructor" : ["Select Version:"], "enabled" : False}),
                        KnobStem("ExecuteJustOneContext","PyScript","Process just one context",lambda : LogicEX.run(
                            QuadSheetStyleLookup.get_style(self.Style.value()).inputs,
                            LogicEX.parse_context(self.JustOneContext.getValue(),
                            self.VersionControl.value()),
                            LogicEX.convert_yes_no_to_bool(self.Render.value()),), 1, {"enabled":False}),
                    ])]))
        LogicEX.path_to_science = self.content.knob_stem_lookup["ScienceDir"].optionals["force_set"]
        setattr(nuke, "QuadPanel", self)

    def knobChanged(self, knob : nuke.Knob) -> None:
        getattr(self, "update_" + knob.name())()

    def openCSV(self):
        if os.path.exists(self.OpenCSV.getValue()) and self.OpenCSV.getValue()[-4:] == ".csv" and os.path.exists(self.OutputDir.getValue()):
                self.Execute.setEnabled(True)
        else:
            self.Execute.setEnabled(False)
    
    def singleContext(self):
        if len(self.JustOneContext.getValue()) > 0 and os.path.exists(self.OutputDir.getValue()):
            for knob in [self.ExecuteJustOneContext, self.VersionControl]: 
                knob.setEnabled(True)
            LogicEX.output_root = self.OutputDir.getValue()
            self.VersionControl.setValues(LogicEX.present_single_context_versions(self.JustOneContext.getValue()))
        else:
            for knob in [self.ExecuteJustOneContext, self.VersionControl]: 
                knob.setEnabled(False)