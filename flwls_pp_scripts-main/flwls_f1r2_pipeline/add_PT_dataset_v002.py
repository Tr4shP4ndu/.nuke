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

def find_and_rename(nodetype, name, rename=False):
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

def find_and_rename_cam(parent, newname, rename=True):
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

def get_nodes_from_fotd_script():
    facebuilder = find_and_rename_facebuilder()
    check_facebuilder_knobs(facebuilder)
    facebuilder_cam = find_and_rename_cam(facebuilder, "FACEBUILDER_CAM")

    #facetracker = find_and_rename_facetracker()
    facetracker = nuke.toNode('CONTROLS')
    #facetracker_cam = find_and_rename_cam(facetracker, "FACETRACKER_CAM")

    create_exclude_nodes()

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

def add_dataset(render_template = '/Volumes/f1r2/pipeline/vfx/templates/performance_transfer_render_dataset/performance_transfer_render_dataset_v001.nk'):

    # deselect everything first
    if nuke.selectedNodes():
        for i in nuke.selectedNodes():
            i['selected'].setValue(False)

    #nodes = get_nodes_from_fotd_script()
    #if not nodes:
    #    return

    current_file = nuke.root().name()
    srcdir = os.path.dirname(os.path.dirname(current_file))

    splits = current_file.split(os.sep)
    variant = splits[-3]
    character = splits[-4]
    shot = splits[-6]
    part= splits[-8]
    episode = splits[-10]
    show = splits[-12]

    #pt_dataset_dir = os.path.join(srcdir, 'publish', 'PTdataset')
    #if not os.path.exists(pt_dataset_dir):
    #    os.makedirs(pt_dataset_dir)

    #version = 0
    #for vstring in os.listdir(pt_dataset_dir):
    #    v = int(vstring[1:])
    #    if v > version:
    #        version = v
    #new_version = version + 1
    #new_version_str = str(new_version).zfill(3)
    #new_version_dir = os.path.join(pt_dataset_dir, f'v{new_version_str}')
    #os.makedirs(new_version_dir)

    #src_file_dir = os.path.join(new_version_dir, 'src')
    #os.makedirs(src_file_dir)
    #src_file = os.path.join(src_file_dir, os.path.basename(current_file))
    #nuke.scriptSaveAs(src_file)


    if character == '101':
        checkpoint = '/Volumes/f1r2/Projects/squd01/assets/characters/101/variants/101El/publish/model/v001/checkpoints/model.056-0.0022763.ckpt'
    elif character == '456':
        checkpoint = '/Volumes/f1r2/Projects/squd01/assets/characters/456/variants/456El/publish/model/v001/checkpoints/model.050-0.00356292.ckpt'
    else:
        raise ValueError('Invalid character. It should be 101 or 456')

    scene_setup(render_template)

    #dataset_dir = os.path.join(new_version_dir, 'dataset')
    #os.makedirs(dataset_dir)

    #fileprefix = f'{shot}_{character}_{variant}'
    #write_node = setup_write_node(dataset_dir, fileprefix, 'PTdataset', 'STANDARD')

    nuke.toNode('NeuralRender1')['checkpoint'].setValue(checkpoint)
    #nuke.toNode('NeuralRender1').setValue['file'](checkpoint)


    #updated_file = os.path.join(src_file_dir, 'to_render.nk')
    #nuke.scriptSaveAs(updated_file)

    # Execute
    #execute(write_node, 'FOTD', 'STANDARD')

    print('-'*60)
    print("Done")
    print('-'*60)



def gen_dataset():
    #write PT dataset
    #sf= int(nuke.root()['first_frame'].value()) #better to use amounts set in dialogue
    #ef= int(nuke.root()['last_frame'].value()) # ditto
    #writeNode= nuke.toNode('WRITE_PTdataset_STANDARD')   
    #nuke.root()['proxy'].setValue(0) 
    #nuke.execute(writeNode, sf, ef, 1)

    #write render.sh file
    nuke.toNode('NeuralRender1')['NeuralRender'].execute()    
    print (nuke.toNode('NeuralRender1')['render_shell_file'].value()    )

    #import nukescripts
    #nukescripts.script_and_write_nodes_version_up()
    #save
    #nuke.scriptSave()


if __name__=="__main__":
    add_dataset()

