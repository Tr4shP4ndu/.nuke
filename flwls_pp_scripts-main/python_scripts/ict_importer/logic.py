"""This module contains the logic to, given a path to a folder of fitting parameters for a shot, produces the following:
Alembic Head
Alembic Teeth Top
Alembic Teeth Bottom
Alembic Facetracker Camera"""

#region imports
from functionality import *
import random
#endregion

class LogicEX():
    def run():
        try:
            ReporterEX.start_timer("export alembics")
            LogicEX.start_session()
            ReporterEX.end_timer("export alembics")
            print(ReporterEX.tell_time("export alembics", "\nIt took $REPLACE$ seconds to export the files as alembics.\n"))
            LogicEX.end_session_debug()
        except Exception as EX:
            LogicEX.ReporterEX.raise_exception_and_quit(traceback.format_exc())
    
    def start_session():
        FileImporterEX.set_up()
        LogicEX.InputEX.run()
        LogicEX.hack_workspace()
        PlateEX.set_shot_fps()
        FileImporterEX.get_all_params()
        ICTEX.import_and_attach_blendshapes()
        LogicEX.run_teeth_replacement()
        PlateEX.set_shot_length()
        AnimationEX.run()
        CameraEX.run()
        LogicEX.export()
        LogicEX.save_elsewhere()
    
    def hack_workspace():
        def fake_access(key):
            result =  {
            SOURCE_PARAMS : LogicEX.InputEX.input_raw["PT"],
            AUDIO_GENERATED_DD : LogicEX.InputEX.input_raw["PT"],
            FULLPLATE : LogicEX.InputEX.input_raw["PLATE"],
            PROXYPLATE : LogicEX.InputEX.input_raw["PLATE"],
            TEETHTOP : os.path.join(os.path.dirname(__file__),"DEFAULT/TeethTop_LP.obj"),
            TEETHBOTTOM : os.path.join(os.path.dirname(__file__),"DEFAULT/TeethBottom_LP.obj"),
        }

            if os.path.isdir(LogicEX.InputEX.input_raw["TEETH"]): # custom teeth directory
                result[TEETHTOP] = os.path.join(LogicEX.InputEX.input_raw["TEETH"],"TeethTop_LP.obj")
                result[TEETHBOTTOM] = os.path.join(LogicEX.InputEX.input_raw["TEETH"],"TeethBottom_LP.obj")
            elif LogicEX.InputEX.input_raw["TEETH"] == "FLAT":
                result[TEETHTOP] : os.path.join(os.path.dirname(__file__),"FLAT/TeethTop_LP.obj")
                result[TEETHBOTTOM] : os.path.join(os.path.dirname(__file__),"FLAT/TeethBottom_LP.obj")
            return result[key]
        setattr(FileImporterEX, "access", fake_access)

    def export():
        output = LogicEX.InputEX.input_raw["OUTPUT"]
        name = LogicEX.InputEX.input_raw["NAME"]
        targets = LogicEX.decide_export_names(output)
        FileExporterEX.export_scene(location=output,file_names=targets)

        if LogicEX.InputEX.arg("TONGUE"):
            LogicEX.export_tongues(LogicEX.InputEX.input_raw["OUTPUT"])
        LogicEX.ReporterEX.success_message(LogicEX.ReporterEX.what_was_actually_exported(LogicEX.extra_targets(output, targets)))
        LogicEX.export_reversed()
        shutil.rmtree(LogicEX.InputEX.input_raw["PT"])
        
    def decide_export_names(output):
        location = output
        tag = LogicEX.InputEX.input_raw["NAME"]
        if tag != "":
            tag += "_"
        file_names = {
            "head_output" : os.path.join(location, tag+"Head.abc"),
            "camera_output" : os.path.join(location, tag+"Camera.abc"),
            "camera_data_output" : os.path.join(location, tag+"CameraData.csv"),
            "teeth_output_top" : os.path.join(location, tag+"TeethTop.abc"),
            "teeth_output_bottom" : os.path.join(location, tag+"TeethBottom.abc"),
        }
        return file_names
        
    def end_session():
        bpy.ops.wm.quit_blender()

    def run_teeth_replacement():
        if LogicEX.InputEX.input_raw["RESETTEETHLOC"] == "TRUE":
            TeethEX.teeth_z_offset_bottom = 0
            TeethEX.teeth_z_offset_top = 0
        bpy.data.objects["Head"].hide_select = False
        TeethEX.chinpin = 969
        TeethEX.add_teeth()
        TeethEX.add_teeth_bone()
        TeethEX.parent_bone()
        
    def end_session_debug():
        if LogicEX.InputEX.input_raw["DEBUG"] == "True":
            bpy.ops.wm.save_as_mainfile(filepath=tempfile.tempdir+ "/" + FileImporterEX.decide_user() + "_alembic_export_debug.blend")
            print(LogicEX.ReporterEX.get_debug_message())
    
    def save_elsewhere():
        "Save to temp directory to avoid overwriting base.blend if user opens"
        FileImporterEX.make_folder_if_not(FileImporterEX.local_paths[TEMPUSER] + "ICTToolSaves/")
        FileImporterEX.make_folder_if_not(FileImporterEX.local_paths[TEMPUSER] + "ICTToolSaves/")
        bpy.ops.wm.save_as_mainfile(filepath=FileImporterEX.local_paths[TEMPUSER] + "ICTToolSaves/temp.blend")

    def get_tongue_names():
        return {
            "Tongue_rest.abc" : "Basis",
            "Tongue_ae.abc" : "AE",
            "Tongue_ee.abc" : "EE",
            "Tongue_ih.abc" : "Ih",
            "Tongue_oh.abc" : "Oh",
            "Tongue_woo.abc" : "W_OO",
            "Tongue_th.abc" : "Th",
            "Tongue_sz.abc" : "Sz",
            "Tongue_tldn.abc" : "T_L_D_N",
        }
    
    def export_tongues(output_path):
        tongue_data = LogicEX.get_tongue_names()
        BlenderEX.unselect_all_select_only_object_x("Tongue")

        start = START
        end = BlenderEX.get_frame_range()[1]

        for tongue_name in tongue_data.keys():
            output =  os.path.join(output_path, tongue_name)
            shape_key = tongue_data[tongue_name]
            for shape_key_name in tongue_data.values():
                bpy.data.shape_keys["Key"].key_blocks[shape_key_name].value = 0
            if shape_key != "Basis":
                bpy.data.shape_keys["Key"].key_blocks[shape_key].value = 1
            bpy.ops.wm.alembic_export(filepath=output,selected=True,start=start,end=end,xsamples=1)

    def extra_targets(output, targets):
        """Add extra export targets that don't exist in the PT scene - for end message"""
        tongues = LogicEX.get_tongue_names()
        for tongue in tongues.keys():
            targets[tongues[tongue]] = os.path.join(output, tongue)
        return targets

    def export_reversed():
        """Redo all the exports as if the head were in the centre of the world."""
        LogicEX.run_reversal()
        output = Path(LogicEX.InputEX.input_raw["OUTPUT"]) / "reversed"
        FileImporterEX.make_folder_if_not(output)
        name = LogicEX.InputEX.input_raw["NAME"] + "_reversed"
        targets = LogicEX.decide_export_names(output)
        FileExporterEX.export_scene(location=output,file_names=targets)
        if LogicEX.InputEX.arg("TONGUE"):
            LogicEX.export_tongues(output)
        LogicEX.ReporterEX.success_message(LogicEX.ReporterEX.what_was_actually_exported(LogicEX.extra_targets(output, targets)))
        LogicEX.undo_reversal()
    
    def run_reversal():
        """Edit the scene to put the head in the centre of the world with no transforms.
        The camera does all the moving."""

        # make assets we need selectable
        bpy.data.objects["Head"].hide_select = False
        bpy.data.objects["FaceTrackerCam"].hide_select = False

        # make static and reversed head
        BlenderEX.unique_copy_rename_move("Head","Static Head","Reversed")
        BlenderEX.unique_copy_rename_move("Head","Reversed Head","Reversed")
        bpy.data.actions["HeadAction"].copy()
        bpy.data.actions["HeadAction"].copy()

        bpy.data.actions["HeadAction.001"].name = "StaticHeadAction"
        bpy.data.actions["HeadAction.002"].name = "ReversedHeadAction"
        bpy.data.objects["Static Head"].animation_data.action = bpy.data.actions["StaticHeadAction"]
        bpy.data.objects["Reversed Head"].animation_data.action = bpy.data.actions["ReversedHeadAction"]

        # remove keyframes from static head and place at 0,0,0
        BlenderEX.unselect_all_select_only_object_x("Static Head")
        bpy.context.screen.areas[0].type = "GRAPH_EDITOR"
        bpy.ops.graph.select_all(BlenderEX.context_override("GRAPH_EDITOR"),action=SELECT)
        bpy.ops.graph.delete(BlenderEX.context_override("GRAPH_EDITOR"))
        bpy.context.screen.areas[0].type = "VIEW_3D"
        bpy.ops.object.location_clear(BlenderEX.context_override("VIEW_3D"))
        bpy.ops.object.rotation_clear(BlenderEX.context_override("VIEW_3D"))

        BlenderEX.unselect_all_select_only_object_x("Reversed Head")
        bpy.context.screen.areas[0].type = "GRAPH_EDITOR"
        bpy.context.screen.areas[0].spaces[0].pivot_point = "CURSOR"
        bpy.ops.graph.select_all(BlenderEX.context_override("GRAPH_EDITOR"),action=SELECT)
        bpy.ops.transform.resize(BlenderEX.context_override("GRAPH_EDITOR"), value=(1, -1, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.context.screen.areas[0].type = "VIEW_3D"
        bpy.data.objects["Reversed Head"].rotation_mode = "XYZ"

        # make moving camera
        BlenderEX.unselect_all_select_only_object_x("FaceTrackerCam")
        bpy.ops.object.duplicate_move(BlenderEX.context_override("VIEW_3D"),OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_axis_ortho":'X', "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.data.objects["FaceTrackerCam.001"].name = "MovingCamera"
        bpy.ops.object.location_clear(BlenderEX.context_override("VIEW_3D"))
        bpy.ops.object.rotation_clear(BlenderEX.context_override("VIEW_3D"))
        BlenderEX.move_object_x_to_collection_y("MovingCamera", "Reversed")


        # make empty that follows reversed head
        bpy.ops.view3d.snap_cursor_to_center(BlenderEX.context_override("VIEW_3D"))
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.data.objects["Empty"].name = "Reversed Empty"
        bpy.data.objects["Reversed Empty"].constraints.new(type="COPY_ROTATION")
        bpy.data.objects["Reversed Empty"].constraints["Copy Rotation"].target = bpy.data.objects["Reversed Head"]
        BlenderEX.move_object_x_to_collection_y("Reversed Empty","Reversed")

        # add constraints to camera
        bpy.data.objects["MovingCamera"].constraints.new(type="COPY_TRANSFORMS")
        bpy.data.objects["MovingCamera"].constraints["Copy Transforms"].target = bpy.data.objects["FaceTrackerCam"]
        bpy.data.objects["MovingCamera"].constraints.new(type="COPY_LOCATION")
        bpy.data.objects["MovingCamera"].constraints["Copy Location"].target = bpy.data.objects["Reversed Head"]
        bpy.data.objects["MovingCamera"].constraints["Copy Location"].use_offset = True
        bpy.data.objects["MovingCamera"].constraints.new(type="CHILD_OF")
        bpy.data.objects["MovingCamera"].constraints["Child Of"].target = bpy.data.objects["Reversed Empty"]
        BlenderEX.unselect_all_select_only_object_x("MovingCamera")
        bpy.data.objects["MovingCamera"].constraints["Child Of"].inverse_matrix = mathutils.Matrix.Identity(4)


        # make original head copy the static head for export

        bpy.data.objects["Head"].constraints.new(type="COPY_TRANSFORMS")
        bpy.data.objects["Head"].constraints["Copy Transforms"].target = bpy.data.objects["Static Head"]
        bpy.data.objects["FaceTrackerCam"].name = "FakeCam"
        bpy.data.objects["MovingCamera"].name = "FaceTrackerCam"

    def undo_reversal():
        while len(bpy.data.objects["Head"].constraints) > 0:
            bpy.data.objects["Head"].constraints.remove(bpy.data.objects["Head"].constraints[0])
        bpy.data.objects["FaceTrackerCam"].name = "MovingCamera"
        bpy.data.objects["FakeCam"].name = "FaceTrackerCam"


    class ReporterEX():
        buffer = "\n\n\n*****\n\n\n" # formatting buffer, otherwise it's hard to read messages amongst blender spam output
        debug_vars = {
            "fps_init": "bpy.data.scenes[Scene].render.fps",
            "fps_base" : "bpy.data.scenes[Scene].render.fps_base",
            "final_fps" : "bpy.data.scenes[Scene].render.fps",
        }

        def success_message(targets):
            if not targets:
                message = "Nothing has been exported by the script."
            else:
                message = LogicEX.ReporterEX.buffer + "The following have been exported successfully:\n"
                for x in targets:
                    message += x + "\n"
            print(message)
        
        def what_was_actually_exported(targets):
            return [x for x in sorted(list(targets.values())) if os.path.exists(x)]

        def raise_exception_and_quit(message):
            LogicEX.end_session()
            print(LogicEX.ReporterEX.buffer +  " Alembic Export Failed.\n " + message + LogicEX.ReporterEX.buffer)
            exit(-1)

        def get_debug_message():
            message = "\nDebug Info:\n"
            for var in LogicEX.ReporterEX.debug_vars.keys():
                message += "\n" + var + ": " + str(eval(LogicEX.ReporterEX.debug_vars[var])) + "\n"
            return message

    class InputEX():
        required_inputs = ["PT","PLATE","OUTPUT"]

        optional_inputs = ["NAME","TEETH","DEBUG","RESETTEETHLOC","TONGUE"]
        input_raw = {}
        def run():
            LogicEX.InputEX.accept_inputs()
            LogicEX.InputEX.check_inputs()
            LogicEX.InputEX.transform_fitting_parameters()
        def accept_inputs():
            args = sys.argv[8:]
            for x in [x.split("=") for x in args if "=" in x]:
                LogicEX.InputEX.input_raw[x[0]] = x[1]
        def check_inputs():
            for x in LogicEX.InputEX.required_inputs:
                if x not in LogicEX.InputEX.input_raw.keys():
                    LogicEX.ReporterEX.raise_exception_and_quit(x + " has not been specified in the runtime arguments.")
            for x in LogicEX.InputEX.optional_inputs:
                if x not in LogicEX.InputEX.input_raw.keys():
                    LogicEX.InputEX.input_raw[x] = ""
            if os.path.isdir(LogicEX.InputEX.input_raw["OUTPUT"]) is False:
                LogicEX.ReporterEX.raise_exception_and_quit(LogicEX.InputEX.input_raw["OUTPUT"] + " does not exist.")
        def transform_fitting_parameters():
            """Given X folder of fitting parameters, write them to the temp folder and rename them to follow 001001 convention."""
            random_hash = str(hex(random.randint(1,9999)))[2:]
            target_parent = FileImporterEX.local_paths[TEMPUSER]+"3DEXPORT/"
            target = target_parent + random_hash + "/"
            for folder in [target_parent, target]:
                if not os.path.exists(folder):
                    os.mkdir(folder)
            for counter, fp in enumerate(sorted(os.listdir(LogicEX.InputEX.input_raw["PT"]))):
                full_source_path = os.path.join(LogicEX.InputEX.input_raw["PT"],fp)
                frame = int(fp[-11:-5])
                full_target_path = target + "{0:06d}.json".format(frame+PLATESTART-START)
                shutil.copy(full_source_path,full_target_path)
            LogicEX.InputEX.input_raw["PT"] = target
        def need_to_transform():
            """If the name of a fitting parameter is longer than 6 characters, it should be transformed.
            Example: 001001.json = fine
            ep01_pt01_0300_jules_main_v002.000000.json = copy, paste, rename to 001001"""
            file_name = FileImporterEX.get_file_name_from_full_path(
                FileImporterEX.get_single_file_path(LogicEX.InputEX.input_raw["PT"]).split(".")[0])
            return len(file_name) > 6
        def arg(arg):
            return LogicEX.InputEX.input_raw[arg].lower() == "true"

LogicEX.run()
