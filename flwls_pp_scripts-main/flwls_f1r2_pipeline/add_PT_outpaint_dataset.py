import os
from pathlib import Path
from re import A

import nuke

#----------------------------------------------------------------------#
#
# Validate the nuke scene
#
#----------------------------------------------------------------------#

"""
Check the name of the FaceBuilder
Check the knobs of the FaceBuilder
Check the Facebuilder Cam

Check the name of the FaceTracker
Check the knobs of the FaceTracker
Check the FaceTracker Cam
"""

def rename_node(node, newname):
    node.setName(newname)

def get_nodes_by_type(nodetype):
    return nuke.allNodes(nodetype)

def find_node(node_name):
    node = nuke.toNode(node_name)
    if node is None:
        raise ValueError(f"node not found: [{node_name}]")
    return node

def find_and_rename(nodetype, name, rename =False):
    nodes = get_nodes_by_type(nodetype)
    if not nodes:
       raise ValueError(f'No {nodetype} node found in the scene')
    if len(nodes) > 1:
        raise ValueError(f'More than one {nodetype} node found in the scene')

    if rename and nodes[0].name() != name:
        rename_node(nodes[0], name)

    return nodes[0]

def check_knob_value(node, knob, expected):
    actual = node.knob(knob).value()
    if isinstance(actual, str):
        actual = actual.strip()

    if actual != expected:
        raise ValueError(f"{node.name()}.{knob}: expected: [{expected}], actual: [{actual}]")

#-----------------------------------------------------------------------------#

def find_and_rename_facebuilder():
    return find_and_rename("FaceBuilder2", "FACEBUILDER")

def find_and_rename_facetracker():
    return find_and_rename("FaceTracker", "FACETRACKER")

def check_facebuilder_knobs(face_builder):
    for act, exp in (("topology", "high poly"),
                     ("selected_uv_set", "maxface"),
                     ("focal_length_mode", "fixed focal length"),
                     ("render_mode", "textured")):
        check_knob_value(face_builder, act, exp)

    check_true = ("geo_ears", "geo_eyes", "geo_jaw", "geo_mouth",
                  "geo_neckupper", "geo_nose", "geo_scalp", "geo_upperface",
                  "non_neutral_expressions",)
    for knob in check_true:
        check_knob_value(face_builder, knob, True)

    check_false = ("geo_necklower", "output_transformed_geo",)
    for knob in check_false:
        check_knob_value(face_builder, knob, False)

def check_facetracker_knobs(facetracker):
    for act, exp in (("focal_length_mode", "fixed focal length"),
                     ("render_mode", "unchanged")):
        check_knob_value(facetracker, act, exp)

    check_knob_value(facetracker, "output_transformed_geo", False)

def find_and_rename_cam(parent, newname, rename =True):
    cams = get_nodes_by_type('Camera')
    for cam in cams:
        knob = cam.knob('translate')
        if knob.hasExpression():
            nodename = knob.toScript().split()[0].split('.')[0][1:]
            if nodename == parent.name():
                if rename:
                    rename_node(cam, newname)
                return cam
    raise ValueError(f'Failed to rename {parent.name()} cam')

def get_exclude_fotd_frames():
    # Access the "ExcludeFrames_flwls" node
    node = nuke.toNode('ExcludeFrames_flwls')
    if not node:
        raise ValueError('No ExcludeFrames_flwls node found')

    # Fill in the frameRange
    first_frame = nuke.root().firstFrame()
    last_frame = nuke.root().lastFrame()

    exclude_frames = []

    exclude_from_training_knob = node['excluded_trainig']
    for frame in range(first_frame, last_frame+1):
        value = bool(exclude_from_training_knob.valueAt(frame))
        if value:
            exclude_frames.append(str(frame))

    # print for fun
    return ','.join(exclude_frames)

def create_exclude_node(name, exclude_frames):
    node = nuke.toNode(name)
    if not node:
        node = nuke.createNode('Dot')
        node.setName(name)
        knob = nuke.nuke.Text_Knob('frames', 'Frames')
        node.addKnob(knob)
    else:
        knob = node.knob('frames')

    if exclude_frames:
        knob.setValue(exclude_frames)

    return node

def create_exclude_nodes():
    # Exclude frames
    exclude_fotd = get_exclude_fotd_frames()
    for i in ('EXCLUDE_FOTD_STANDARD', 'EXCLUDE_FOTD_OUTPAINTING'):
        create_exclude_node(i, exclude_fotd)

def get_nodes_from_fotd_script(publish_type, experiment):
    facebuilder = find_and_rename_facebuilder()
    #check_facebuilder_knobs(facebuilder)
    facebuilder_cam = find_and_rename_cam(facebuilder, "FACEBUILDER_CAM")

    facetracker = find_and_rename_facetracker()
    #check_facetracker_knobs(facetracker)
    facetracker_cam = find_and_rename_cam(facetracker, "FACETRACKER_CAM")

    #create_exclude_nodes(publish_type, experiment)

    return (facetracker, facetracker_cam)

def scene_setup(render_template):
    # Import a nuke script [FOTDRENDERTMPL]
    

    nuke.nodePaste(render_template)



    nuke.toNode('FACETRACKER_CAM_INPUT').setInput(0,nuke.toNode('CAMERA_TO_DATASET_GENERATION'))
    nuke.toNode('FACETRACKER_INPUT').setInput(0, nuke.toNode('GEO_TO_DATASET_GENERATION'))
    nuke.toNode('PLATE_INPUT').setInput(0, nuke.toNode('PLATE_TO_DATASET_GENERATION'))
    nuke.toNode('TEXTURE_INPUT').setInput(0, nuke.toNode('TEXTURE_TO_DATASET_GENERATION'))





# frame include list
def find_included_frames(publish_type, experiment):
    # returns:
    #   None - don't exclude any frames
    #   Empty list - exclude all frames
    #   Non-empty list - include only the listed frames
    included_frames = None
    excluded = nuke.toNode(f"EXCLUDE_{publish_type}_{experiment}")
    if excluded is not None:
        excluded_list = excluded.knob("frames").value()
        excluded_list = excluded_list.strip() if excluded_list is not None else None
        if excluded_list:

            start_frame = nuke.root().firstFrame()
            end_frame = nuke.root().lastFrame()

            excluded_frames = set([int(frame) for frame in excluded_list.split(",") if frame])
            included_frames = [frame for frame in range(start_frame, end_frame + 1)
                               if frame not in excluded_frames]
    return included_frames


# execute a single write node
def setup_write_node(output_path, fileprefix, publish_type, experiment):
    output_file_pattern = f"{fileprefix}_{publish_type}_dataset_{experiment}.%06d.png"

    write_node_name = f"WRITE_{publish_type}_{experiment}"
    write = nuke.toNode(write_node_name)
    if write is None:
        raise ValueError(f"write node not found for: '{write_node_name}'")

    write_path = Path(output_path) / experiment.lower()
    if not write_path.exists():
        write_path.mkdir(parents=True, exist_ok=True)
        write.knob("file").setValue(str(write_path / output_file_pattern))
        write["file_type"].setValue('png')

    return write

def execute(write, publish_type, experiment):
    included_frames = find_included_frames(publish_type, experiment)
    if included_frames is not None:
        if included_frames:
            frames_to_render = nuke.FrameRanges(included_frames)
            nuke.execute(write, frames_to_render)
    else:
        nuke.execute(write)

def gen_dataset(gizmo_path = '/Volumes/f1r2/pipeline/vfx/templates/fotd_render_dataset/fotd_render_dataset_template_v007.gizmo'):
    
    # load gizmo into script, set path, render    
    gizmo_dir, gizmo_basename = os.path.split(gizmo_path)
    nuke.pluginAddPath(gizmo_dir)

    #short name for experiment, e.g. 'fotd_render_dataset_template_v007'
    dataset_short_name = os.path.splitext(gizmo_basename)[0]


    # deselect everything first
    if nuke.selectedNodes():
        for i in nuke.selectedNodes():
            i['selected'].setValue(False)

    node = nuke.createNode(dataset_short_name)

    
    current_file = nuke.root().name()
    srcdir = os.path.dirname(os.path.dirname(current_file))

    splits = current_file.split(os.sep)
    variant = splits[-3]
    character = splits[-4]
    shot = splits[-6]
    part= splits[-8]
    episode = splits[-10]
    show = splits[-12]

    fotd_dir = os.path.join(srcdir, 'publish', 'FOTD')

    #src_file_dir = os.path.join(new_version_dir, 'src')
    #src_file = os.path.join(src_file_dir, os.path.basename(current_file))
    #nuke.scriptSaveAs(src_file)

    if character == '101':
        checkpoint = '/Volumes/f1r2/Projects/squd01/assets/characters/101/variants/101El/publish/model/v001/checkpoints/model.056-0.0022763.ckpt'
    elif character == '456':
        checkpoint = '/Volumes/f1r2/johnparry/squid_game/checkpoints/squid2/model.037-0.00471927.ckpt'
    else:
        raise ValueError('Invalid character. It should be 101 or 456')

    if character == '101':
        tex_file = '/Volumes/f1r2/Projects/squd01/episodes/assets/characters/101/texture/101el/review/squd01_101_el_texture_v002.001001.exr'
    elif character == '456':
        tex_file = '/Volumes/f1r2/Projects/squd01/episodes/assets/characters/456/texture/review/squd01_model_texture_456_v004.000001.exr'
    else:
        raise ValueError('Invalid character. It should be 101 or 456')

    # Connect plate
    plate = find_node('PLATE')
    node.setInput(0, plate)

    # connect facetracker camera
    facetracker_cam= nuke.toNode('CAMERA_TO_DATASET_GENERATION')
    node.setInput(1, facetracker_cam)

    # connect pt_out
    pt_out= nuke.toNode('GEO_TO_DATASET_GENERATION')
    node.setInput(2, pt_out)

    # import texture
    node.knob("texture").setValue(tex_file)




    #dataset_dir = os.path.join(new_version_dir, 'dataset')
    #fileprefix = f'{shot}_{character}_{variant}'
    #setup_write_node(node, dataset_dir, fileprefix, 'FOTD', f"{dataset_short_name}")

    #updated_nuke_file = os.path.join(src_file_dir, f"{dataset_short_name}_render.nk")
    #nuke.scriptSaveAs(updated_nuke_file)
    dataset_file_out= f"[join [lrange [split [value Review.OUT_MOV.file] /] 0 15] /]/publish/PTdataset/[lindex [split [lindex [split [basename [value Review.OUT_MOV.file]] .] 0] _] end]/dataset/{dataset_short_name}/%06d.png"
    node['file'].setValue(dataset_file_out)

    neuralRender= nuke.createNode('neuralRender_flw')
    neuralRender['file'].setValue(dataset_file_out)
    neuralRender['checkpoint'].setValue(checkpoint)



    # Execute
    #execute(node, 'FOTD', f"{dataset_short_name}")

    print('-'*60)
    #print(f"Created a new version directory: {new_version}")
    #print(f"Dataset could be found here: {dataset_dir}")
    print("Done")
    print('-'*60)
    return node, neuralRender






def render_dataset(node, neuralRender):
    #write PT dataset
    sf = int(nuke.root()['first_frame'].value()) #better to use amounts set in dialogue
    ef = int(nuke.root()['last_frame'].value()) # ditto
    #writeNode = nuke.toNode('WRITE_PTdataset_STANDARD')   
    nuke.root()['proxy'].setValue(0) 
    nuke.execute(node, sf, ef, 1)

    #write render.sh file
    neuralRender['NeuralRender'].execute() 
    #print where it wrote out to:   
    #print (msg)
    #print (nuke.toNode('NeuralRender1')['render_shell_file'].value()    )


    #import nukescripts
    #nukescripts.script_and_write_nodes_version_up()
    #save
    #nuke.scriptSave()



def main():
    node, neuralRender = gen_dataset(gizmo_path = '/Volumes/f1r2/pipeline/vfx/templates/fotd_render_dataset/fotd_render_dataset_outpaint_v001.gizmo')
    render_dataset(node, neuralRender)

if __name__=="__main__":
    #add_dataset()
    #gen_dataset()
    main()