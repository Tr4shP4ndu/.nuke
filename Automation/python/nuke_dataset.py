import os
import nuke
import re
import json
import cProfile
from pathlib import Path
import time

profiler = cProfile.Profile()
profiler.enable()

def write_node_set_and_exe(start: int, last: int, shot_context: str, output_path: Path):
    write_node = nuke.toNode('Write1')  
    write_node['file'].setValue(str(output_path) + f"/{shot_context}" + ".%06d.png")
    print(write_node)
    try:
        start_time = time.time()
        nuke.execute(write_node, int(start), int(last))
        end_time = time.time() 
        print(f"Render time: {end_time - start_time:.2f} seconds")
    except RuntimeError as e:
        print(f"Error executing Write node: {e}")

def set_project_settings(start, last):
    
    nuke.root()['first_frame'].setValue(start)
    nuke.root()['last_frame'].setValue(last)

def populate_read_node(seq: Path, folder: Path, name: str):
    frames, nk_last_frame = seq.split('-')
    frames, nk_start_frame = frames.split(' ')
    path = os.path.join(folder, frames)
    path = path.replace("\\", "/")
    existing_read = nuke.toNode("read_shot")  # Adjust the node name accordingly
    if existing_read:
        existing_read["file"].setValue(path)
        existing_read["first"].setValue(int(nk_start_frame))
        existing_read["last"].setValue(int(nk_last_frame))
        existing_read['origfirst'].setValue(int(nk_start_frame))
        existing_read['origlast'].setValue(int(nk_last_frame))
        existing_read['frame_mode'].setValue('start at')
        existing_read['frame'].setValue('1')
        return nk_start_frame, nk_last_frame

def find_img_files(folder: Path):
    img_seq = [seq for seq in nuke.getFileNameList(folder)]
    for seq in img_seq:
        operation = None
        layer_nc = seq.split('_')[0] 
    pattern = r'(\w+_\w+_\d+)'
    match = re.search(pattern, folder)
    shot_name = match.group()
    print(shot_name, seq)
    return shot_name, seq

def headless_mode():
    shot_info = '/script/shot_info.json'   
    with open(shot_info, 'r') as json_file:
        data = json.load(json_file)
    
    shot_context = data['shot_context']
    input_path = data['input_path']
    output_path = data['output_path']
    nuke_script = data['nuke_script']
    save_nuke_script = Path(data['save_nuke_script'])
    reset_color = "\033[0m"
    
    print(f'{reset_color}\n'
          f'Shot Context: {shot_context}\n'
          f'Input Path: {input_path}{reset_color}\n'
          f'Output Path: {output_path}{reset_color}\n'
          f'Nuke Script: {nuke_script}{reset_color}\n'
          f'Nuke Script Save Path: {save_nuke_script}{reset_color}\n'
          f'{reset_color}'
          )
    
    nuke.scriptOpen(nuke_script)
    with nuke.root():
        shot_name, seq_path = find_img_files(input_path)
        nk_start_frame, nk_last_frame = populate_read_node(seq_path, input_path, shot_name)
        set_project_settings(int(nk_start_frame), int(nk_last_frame))
        write_node_set_and_exe(nk_start_frame, nk_last_frame, shot_context, output_path)
        nuke_script_filename = save_nuke_script / f"{shot_name}_dataset.nk"
        
        # Check if the file exists and remove it
        if os.path.exists(nuke_script_filename):
            os.remove(nuke_script_filename)
            print(f"Removed existing file: {nuke_script_filename}")
        
        nuke.scriptSaveAs(str(nuke_script_filename))  # Specify a filename
        print(f"Nuke script saved as {nuke_script_filename}")
    
    nuke.scriptClose()
    
headless_mode()

profiler.disable()
profiler.print_stats(sort='cumulative')
