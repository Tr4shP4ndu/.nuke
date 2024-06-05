import nuke

def sample_range(node_name, first_frame_comp, last_frame_comp, pixel_type, odd_pixel, no_odd_pixel):
    """ Samples the max and min values of the given frame range and set an average RGB sample into a single value """
    tool = nuke.toNode(node_name)
    min_knob = tool['minlumapixvalue']
    max_knob = tool['maxlumapixvalue']

    min_knob.setAnimated()
    max_knob.setAnimated()
    
    nuke.execute(tool, int(first_frame_comp), int(last_frame_comp))
    
    values = tool[f'{pixel_type}_pixels_avg'].value()
    if values > 1:
        return f'<b>{pixel_type.upper()} Pixels:</b> \n{odd_pixel}'
    else:
        return f'<b>{pixel_type.upper()} Pixels:</b> \n{no_odd_pixel}'

def check_frame_range(comp_range, plate_range):
    """ Checks Plate and Comp frame ranges are matching """
    convert_plate = plate_range[1] - plate_range[0] + 1
    convert_comp = comp_range[1] - comp_range[0] + 1
    
    if convert_comp == convert_plate:
        return f'<b>Inputs Ranges:</b>\n<font color="#228B22">are matching frame ranges!</font>{convert_plate} - {convert_comp}'
    else:
        return f'<b>Inputs Ranges:</b> \n<font color="#B22222">do not match frame ranges!</font>{convert_plate} - {convert_comp}'
    
def get_format_tuple(node):
    return node.format().width(), node.format().height(), node.format().pixelAspect()

def check_res(read):
    if get_format_tuple(read.input(0)) != get_format_tuple(read.input(1)):
        return f'Resolution: NR_precomp:<font color="#B22222">{get_format_tuple(read.input(0))}</font> & Plate:<font color="#B22222">{get_format_tuple(read.input(1))}</font> Format MissMatching!'
    else:
        return f'<b>Resolution: </b>\nNR_precomp:<font color="#228B22">{get_format_tuple(read.input(0))}</font> & Plate:<font color="#228B22">{get_format_tuple(read.input(1))}</font> Format Matching!'

def check_inputs(read):
    """ Checks if there are connected inputs and if format is matching """
    if read.input(0) is None:
        input_connect = '<b>PRECOMP_NR_COMP: </b>\n<font color="#B22222">No PRECOMP/NR/COMP Connected!</font>'
    if read.input(1) is None:
        input_connect = '<b>RAW_PLATE: </b>\n<font color="#B22222">No Plate Connected!</font>' 
    else:
        input_connect = '<b>Inputs:</b> \n<font color="#228B22">Both inputs are connected</font>' 
        
    return input_connect
    
def start():
    """ let's do this! """
    read_input = nuke.thisNode()
    
    read_input_comp = nuke.toNode('frame_range_comp')
    first_frame_comp = read_input_comp['first_frame'].value()
    last_frame_comp = read_input_comp['last_frame'].value()
    comp = first_frame_comp, last_frame_comp

    read_input_plate = nuke.toNode('frame_range_plate')
    first_frame_plate = read_input_plate['first_frame'].value()
    last_frame_plate = read_input_plate['last_frame'].value()
    plate = first_frame_plate, last_frame_plate
    
    odd_pixel = '<font color="#B22222">There are odd pixels!</font>'
    no_odd_pixel = '<font color="#228B22">No visible odd pixels!</font>'
    
    """Start functions and obtain values"""
    input_connect = check_inputs(read = read_input)
    res = check_res(read = read_input)
    check_range = check_frame_range(comp_range = comp, plate_range = plate)
    
    sample_types = ['neg', 'nan', 'inf']
    sample_results = {}
    for sample_type in sample_types:
        sample_results[sample_type] = sample_range(f'{sample_type.capitalize()}_pixels_ct', first_frame_comp, last_frame_comp, sample_type, odd_pixel, no_odd_pixel)
    
    nuke.message(f'<center>{input_connect} \n {res} \n{check_range} \n{sample_results["neg"]} \n{sample_results["nan"]} \n{sample_results["inf"]}')
    read_input['input_text'].setValue(f'<center>{input_connect}')
    read_input['res_text'].setValue(f'<center>{res}')
    read_input['range_text'].setValue(f'<center>{check_range}')
    read_input['neg_text'].setValue(f'<center>{sample_results["neg"]}')
    read_input['nan_text'].setValue(f'<center>{sample_results["nan"]}')
    read_input['inf_text'].setValue(f'<center>{sample_results["inf"]}')
    

start()


nuke.toNode('fc_QC_ReViewer_flw').knob('metadata_inputValues_checker').setValue(

'''

'''
)


nuke.createNode("Write", """
script_directory = "path"
scriptname_with_version = "/path"
scriptversion = "v001"
scriptname_with_version = "test_v001"
file_path = os.path.join(script_directory, scriptname_with_version + "_renders", scriptversion, "qc_reviewer_mov", scriptname_with_version + "_contact_sheet.mov")
nuke.thisNode()["file"].setValue(file_path)
""")
    
    

Write {
 file "\[value script_directory]/\[value scriptname]_renders/\[value scriptversion]/qc_reviewer_mov/\[value scriptname_with_version]_contact_sheet.mov"
 colorspace "Output - Rec.709"
 file_type mov
 mov64_format "mov (QuickTime / MOV)"
 mov64_codec appr
 mov64_fps {{root.fps}}
 mov_h264_codec_profile "High 4:2:0 8-bit"
 mov64_pixel_format {{0}}
 mov64_quality High
 mov64_fast_start true
 mov64_write_timecode true
 mov64_gop_size 12
 mov64_b_frames 0
 mov64_bitrate 20000
 mov64_bitrate_tolerance 4000000
 mov64_quality_min 1
 mov64_quality_max 3
 create_directories true
 checkHashOnRead false
 version 42
 name contact_sheet_write
 onCreate "exec(\"\"\"\\nfrom pathlib import Path\\nimport re\\nimport nuke\\nimport os\\n\\ndef build_lang_context(script_name):\\n    split_name = os.path.basename(script_name).split(\"_\")\\n\\n    context = \{\}\\n\\n    context\[\"show\"] = split_name\[0]\\n    context\[\"episode\"] = split_name\[1]\\n    context\[\"part\"] = split_name\[2]\\n    context\[\"shot\"] = split_name\[3]\\n    context\[\"language\"] = split_name\[4]\\n\\n    return context\\n\\ndef get_highest_folder_name(directory):\\n    folder_names = \[name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]\\n    if not folder_names:\\n        return None\\n    highest_folder = max(folder_names, key=lambda x: int(x\[1:]))\\n    return highest_folder\\n\\n\\n\\ncontext = build_lang_context((nuke.root().name()))\\n \\naudio_tree = str(Path(\"/Volumes\") / \"pipeline\" / \"shows\" / context\[\"show\"] / \"publish\" / \"episode\" / context\[\"episode\"] / \"part\" / context\[\"part\"] / \"shot\" / context\[\"shot\"] / \"language\" / context\[\"language\"] / \"AUDIO\")\\naudio_file_tree = str(Path(audio_tree) / get_highest_folder_name(audio_tree) / \"audio\")\\naudio_file = os.listdir(audio_file_tree)\\nlatest_shot_lang_audio = str(Path(audio_file_tree) / audio_file\[0])\\n\\n#print(latest_shot_lang_audio)\\nnuke.thisNode().knob(\"mov64_audiofile\").setValue(latest_shot_lang_audio)\\n\"\"\")"
 selected true
 addUserKnob {20 FlwlsPipeline}
 addUserKnob {1 script_directory}
 script_directory "\[python nuke.script_directory()]"
 addUserKnob {1 scriptname_with_version}
 scriptname_with_version "\[basename \[file rootname \[value root.name]]]"
 addUserKnob {1 scriptname}
 scriptname "\[regsub -all \{_v\\d+\} \[value scriptname_with_version] \"\"]"
 addUserKnob {1 scriptversion}
 scriptversion "\[regexp -inline \{v\\d+\} \[value root.name]]"
 addUserKnob {1 render_type}
 render_type review_mov
}

