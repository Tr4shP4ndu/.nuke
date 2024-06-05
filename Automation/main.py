import os
import csv
import subprocess
from pathlib import Path
import time
import re
import json

def make_temp_files(results, nuke_exe_path, nuke_python):
    for result in results:
        shot_context = result['shot_context']
        input_path = result['input_path']
        output_path = result['output_path']
        nuke_script = result['nuke_script']
        save_nuke_script = result['save_nuke_script']
        print('Shot Context:', str(shot_context), '\n'
            'Input Path:', str(input_path), '\n'
            'Output Path:', str(output_path), '\n'
            'Nuke Script:', str(nuke_script), '\n'
            'Save Nuke Script:', str(save_nuke_script))

        json_save_path = Path("/script")
        shot_info = json_save_path / 'shot_info.json'
        data = {'shot_context': str(shot_context), 'input_path': str(input_path), 'output_path': str(output_path), 'nuke_script': str(nuke_script), 'save_nuke_script': str(save_nuke_script)}
        with open(shot_info, 'w') as json_file:
            json.dump(data, json_file)
        try:
            process = subprocess.Popen([nuke_exe_path, '--nuke', '-t', nuke_python], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Path(__file__).parent)
            out, err = process.communicate()
            time.sleep(1)
            print(out.decode('utf-8'))
            print(err.decode('utf-8'))

        except subprocess.CalledProcessError as e:
            print(f"Error executing Nuke script: {e}")
            
        os.remove(shot_info)

def fetch_imgs_create_path(input_dir, nuke_exe_path, nuke_python, out_folder_name, csv_file, nuke_script):
    results = []
    with open(csv_file, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        shot_names = [row['ShotLanguageVariant Name'] for row in csv_reader]
        
    for input_path in sorted(input_dir.iterdir()):
        folder_name = input_path.name
        
        matching_shot_names = [shot for shot in shot_names if re.match(r'.*' + re.escape(shot) + '.*', folder_name)]
        # print(matching_shot_names)
        if not matching_shot_names:
            continue

        out_dir_path = input_path / out_folder_name / 'render'
        out_dir_path.mkdir(parents=True, exist_ok=True)

        save_nuke_script = input_path / out_folder_name / 'script'
        save_nuke_script.mkdir(parents=True, exist_ok=True)

        input_path = input_path / "dataset"
        
        results.append({
            'shot_context': folder_name,
            'input_path': input_path,
            'output_path': out_dir_path,
            'nuke_script': nuke_script,
            'save_nuke_script': save_nuke_script
        })

    # print(results, nuke_exe_path, nuke_python)
    make_temp_files(results, nuke_exe_path, nuke_python)

if __name__ == '__main__':
    input_dir = Path("/Volumes/shared/vfx/filipe.correia/github/brand_new_datasets/investigations/cthd/converted")
    csv_file = Path("/Volumes/shared/vfx/filipe.correia/github/brand_new_datasets/investigations/python/csv/modified_cthd00.csv")
    nuke_exe_path = "/opt/Nuke13.1v2/Nuke13.1"
    nuke_python = "/Volumes/shared/vfx/filipe.correia/github/brand_new_datasets/investigations/python/python/nuke_automation_histeq/script/nuke_dataset.py"
    nuke_script = Path('/Volumes/shared/vfx/filipe.correia/github/brand_new_datasets/investigations/python/script/dataset_extracted_noise_template.nk')
    out_folder_name = "dataset_extracted_noise"
    
    fetch_imgs_create_path(input_dir, nuke_exe_path, nuke_python, out_folder_name, csv_file, nuke_script)