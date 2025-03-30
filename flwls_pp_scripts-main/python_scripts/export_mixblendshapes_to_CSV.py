import nuke
import csv
import pathlib
import json

def mixblendshapes_to_list_of_list(mixblendshapes_node, first_frame, last_frame):
    '''
    Returns a list of list of animation values for each 51 ARKit standard
    blendshapes from Keentools. 
    '''
    animation_data = []
    
    blend_shape_names = \
    ['eyeBlinkLeft','eyeBlinkRight','eyeSquintLeft','eyeSquintRight',
    'eyeLookDownLeft','eyeLookDownRight','eyeLookInLeft','eyeLookInRight',
    'eyeWideLeft','eyeWideRight','eyeLookOutLeft','eyeLookOutRight',
    'eyeLookUpLeft','eyeLookUpRight','browDownLeft','browDownRight',
    'browInnerUp','browOuterUpLeft','browOuterUpRight','jawOpen','mouthClose',
    'jawLeft','jawRight','jawForward','mouthUpperUpLeft','mouthUpperUpRight',
    'mouthLowerDownLeft','mouthLowerDownRight','mouthRollUpper','mouthRollLower',
    'mouthSmileLeft','mouthSmileRight','mouthDimpleLeft','mouthDimpleRight',
    'mouthStretchLeft','mouthStretchRight','mouthFrownLeft','mouthFrownRight',
    'mouthPressLeft','mouthPressRight','mouthPucker','mouthFunnel','mouthLeft',
    'mouthRight','mouthShrugLower','mouthShrugUpper','noseSneerLeft',
    'noseSneerRight','cheekPuff','cheekSquintLeft','cheekSquintRight']

    #include a row of frames TODO: this would be good to refactor out
    frames_header = []
    frames_header.append('frame')
    for frame in range(first_frame, last_frame+1):
        frames_header.append(frame)
    animation_data.append(frames_header)
    
    for blendshape_nr in range(1,52):
        knob_name = f'blendshape_value_{blendshape_nr}'
        blendshape_knob = mixblendshapes_node.knob(knob_name)
        blendshape_name = blend_shape_names[blendshape_nr-1]
        blend_shape_animation_curve = [blendshape_name] # adding the name

        for frame in range(first_frame, last_frame+1):
            blend_shape_animation_curve.append(blendshape_knob.valueAt(frame))
        animation_data.append(blend_shape_animation_curve)

    return animation_data

def animation_data_to_csv(animation_data, path):
    '''
    Given a list of lists of animation data, writes all rows to a CSV file
    in path. Overwrites existing file.
    '''
    with open(path, 'w', newline='') as csv_out:
        writer = csv.writer(csv_out, delimiter=',')
        writer.writerows(animation_data)

def transpose_list_of_lists(data):
    '''
    swaps the axis of a list_of_lists
    '''
    return [list(i) for i in zip(*data)]

def get_project_framerange():
    '''
    returns [int, int] where 0th item is first_frame and 1th item is last_frame 
    '''
    return [nuke.root().firstFrame(), nuke.root().lastFrame()]

def get_project_context():
    '''
    get's the value of 'flwls_context' knob in root and loads as JSON
    '''
    context = json.loads(nuke.toNode('root').knob('flwls_context').value())
    return context 

def get_mixblendshapes_node():
    mb_node_list = nuke.allNodes('MixBlendshapes')
    assert len(mb_node_list)>0, 'Could not find any MixBlendshape nodes'
    if len(mb_node_list)==1:
        return mb_node_list[0]
    elif nuke.selectedNode().Class()=='MixBlendshapes':
        return nuke.selectedNode()

def export_mixblendshapes_to_csv():
    '''
        Entry point for the code.
        Uses context from flwls_context knob under root if it exists.
        Otherwise, if in GUI asks you to specify an out folder.
        Lots of ugly if-else logic in this main function. If anyone fancies refactoring some of that, be my guest
        show_root is also hard-coded to '/Volumes/workspace' for now
    '''

    framerange = get_project_framerange()
    publish_element = 'animation'
    filename = pathlib.Path(nuke.scriptName()).stem + '_BScoefficients.csv'
    show_root = '/Volumes/workspace'
    
    mixblendshapes_node = get_mixblendshapes_node()
    animation_data = mixblendshapes_to_list_of_list(mixblendshapes_node, 
                                    framerange[0],
                                    framerange[1])
    trasnposed_animation_data = transpose_list_of_lists(animation_data)

    # Try to get project context
    try:
        context = get_project_context()       
    except:
        context = False

    # update filepath based on context. 
    # if no context, then fail in headless, in GUI mode ask user for a path
    if context:
        paths = list(pathlib.Path(f'{show_root}/shows/{context["show"]}/episodes/{context["episode"]}/parts/{context["part"]}/shots/{context["shot"]}/characters/{context["character"]}/variants/{context["variant"].lower()}/fotd_tracking/output/FOTD/').glob('v???'))
        if len(paths)>0:
            paths.sort()
            out_path = paths[-1].joinpath(f'{publish_element}')
            print(f'out_path - {out_path}')
            out_path.mkdir(parents=True, exist_ok=True)
            out_path = out_path.joinpath(filename)
        else:
            out_path = pathlib.Path(f'{show_root}/shows/{context["show"]}/episodes/{context["episode"]}/parts/{context["part"]}/shots/{context["shot"]}/characters/{context["character"]}/variants/{context["variant"].lower()}/fotd_tracking/output/FOTD/v001/{publish_element}').mkdir(parents=True)
            out_path.joinpath(filename)
    else:
        if nuke.GUI:
            out_path = nuke.getFilename('Pick File Save location and Name for export .csv', '*.csv')
        else:
            print('root.flwls_context not set. Have not implemented a non-GUI fallback for this scenario yet')

    animation_data_to_csv(trasnposed_animation_data, out_path)
    if nuke.GUI:
        nuke.message(f'CSV exported to: \n {out_path}')
    else:
        print(f'CSV exported to: \n {out_path}')

if __name__=="__main__":
    export_mixblendshapes_to_csv()