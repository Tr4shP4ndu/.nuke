#!/usr/bin/env python3

# fix gizmos to have correct naming 
# by Sean Danischevsky 2022

import os, string

import glob

def find_gizmos(dir_of_gizmo_dirs):
    gizmo_dirs = os.listdir(dir_of_gizmo_dirs)

    # dict of f'{gizmo_dir}/{gizmo_name}': full_dir_name, gizmo name
    gizmo_dict = {}

    # todo: maybe use 
    # for root, dirs, files in os.walk( to get gizmos on the top level/sub levels)
    for gizmo_dir in gizmo_dirs:
        full_dir_name = os.path.join(dir_of_gizmo_dirs, gizmo_dir)
        gizmos = glob.glob( os.path.join(full_dir_name, '*.gizmo'))

        for gizmo in gizmos:
            gizmo_name, _ = os.path.splitext(os.path.basename(gizmo))
            gizmo_dict[f'{gizmo_dir}/{gizmo_name}'] = (full_dir_name, gizmo_name)

    return gizmo_dict


def add_gizmos(node_menu, gizmo_dict):
    import nuke
    for gizmo, (full_dir_name, gizmo_name) in gizmo_dict.items():
        node_menu.addCommand(gizmo, f"nuke.createNode('{gizmo_name}')", icon=f'{os.path.join(full_dir_name, gizmo_name)}.png')
        nuke.pluginAddPath(full_dir_name)


def fix_gizmos(gizmo_dict):
    for gizmo, (full_dir_name, gizmo_name) in gizmo_dict.items():
        sanitize_gizmo("/Volumes/workspace/sean/flwls_pp_scripts/nuke/gizmos/Channel/channel.gizmo", 
        suffix="_flw", color=0xff5555ff, help=f"Copyright Flawless")


def get_year():
    import datetime
    year= datetime.date.today().year
    return year


def read_file(filepath):
    # read file
    lines = []
    with open(filepath, 'r') as fp:
        # read an store all lines into list
        lines = fp.readlines()
    return list(lines)


def write_file(filepath, lines):
    with open(filepath, 'w') as fp:
        # iterate each line
        for number, line in enumerate(lines):
            # delete line 5 and 8. or pass any Nth line you want to remove
            # note list index starts from 0
            fp.write(line) 
            #print (line)   
    return


def sanitise_gizmo_name(potential_gizmo_name, suffix):
    # Only unicode characters
    valid_filename = potential_gizmo_name.encode('ascii', 'ignore').decode('ascii')

    # Only valid characters
    valid_chars = f"{string.ascii_letters}{string.digits} _"
    valid_filename = "".join(character for character in valid_filename if character in valid_chars)

    # At least one letter
    valid_chars = f"{string.ascii_letters}"
    test_filename = "".join(character for character in potential_gizmo_name if character in valid_chars)
    if len(test_filename) == 0:
        # Replace empty name  
        valid_filename = "Group"
    
    # Capitalize first letter
    current_gizmo_name = valid_filename[0].upper() + valid_filename[1:]

    # Sanitized_name ends with '_sd' (me) or '_flw' then '1' (like regular nodes)
    if current_gizmo_name.endswith(suffix):
        sanitized_gizmo_name=  current_gizmo_name
    else:        
        sanitized_gizmo_name=  current_gizmo_name + suffix

    return sanitized_gizmo_name



def edit_gizmo_file(lines, gizmo_name, tile_color=None, help=None):
    import re

    # Replace Gizmo with Group
    for line in lines:
        _, subs = re.subn(r'^Gizmo {\n', 'Group {\n', line)
        if subs:
            print ("Replaced Gizmo with Group.")
    # Remove lines down to group 
    for n, line in enumerate(lines):
        if line.startswith('Group {') or line.startswith('Gizmo {'):
            break
    group_lines = lines[n:]
    print ("group_lines", group_lines)
    if len(group_lines) < 2 :
        raise ValueError('Not a Group! Please resave this gizmo as a Group.')

    group_end_line = group_lines.index('}\n') + 1

    group_lines, remaining_lines = group_lines[:group_end_line], group_lines[group_end_line:]

    # Set name
    for n, line in enumerate(group_lines):
        # TODO: don't change "VIEWER_INPUT" because that name is reserved
        # OR add a callback to change the root to look fot the new name instead of VIEWER_INPUT
        line, subs = re.subn(r'^ name .*\n', f" name {gizmo_name}\n", line)
        if subs > 0:
            break
    group_lines[n] = line


    # find help
    for n, line in enumerate(group_lines):
        found_help= re.findall(r'^ help .*\n', line)
        if found_help:
            break

    # If no 'Help', set to default
    if not found_help and help:
        #add current year and capitalise Copyright if Copyright/copyright present in given help
        help = re.sub(r"copyright", f"Copyright {get_year()}", help, flags=re.IGNORECASE)
        group_lines = group_lines[0:2] + [f' help "{help}"\n'] + group_lines[2:]
        print (f"Added help message: {help}") 


    

    # Fix Tile Color - red for flawless, none for me(set on call to this file )
    for n, line in enumerate(group_lines):
        line, subs= re.subn(r'^ tile_color .*\n', f" tile_color {tile_color}\n", line)
        if subs > 0:
            break
    if tile_color:
        if subs:
            group_lines[n] = line
            print (f"Replaced Tile Color with {tile_color}") 
        else:
            group_lines = group_lines[0:2] + [f' tile_color {tile_color}\n'] + group_lines[2:]
            print (f"Added Tile Color {tile_color}")
    else:
        #default tile color, so remove the line
        group_lines = group_lines[0:n] + group_lines[n+1:]  
        print ("Removed Tile Color") 

    # Remove x,y
    for n, line in enumerate(group_lines):
        subs= re.findall(r'^ xpos .*\n', line)
        if subs:
            group_lines = group_lines[0:n] + group_lines[n+1:]
            print ("Removed xpos")
            break

    for n, line in enumerate(group_lines):
        subs= re.findall(r'^ ypos .*\n', line)
        if subs:
            group_lines = group_lines[0:n] + group_lines[n+1:]
            print ("Removed ypos")
            break

    # Remove note_font
    for n, line in enumerate(group_lines):
        subs= re.findall(r'^ note_font .*\n', line)
        if subs:
            group_lines = group_lines[0:n] + group_lines[n+1:]
            break


    
    # Remove Viewer lines
    try:
        viewer_start_line = remaining_lines.index(' Viewer {\n')
        viewerlines = remaining_lines[viewer_start_line:]
        viewer_end_line = viewerlines.index(' }\n')
        remaining_lines = remaining_lines[:viewer_start_line] + viewerlines[viewer_end_line+1:]
    except ValueError:
        # no Viewers
        pass


    # TODO:
    # Make Inputs lower case, Set Input labels
    # a bit tricky, as I need to separate into the 'remaining_lines' 
    # make sure I don't go into a deeper group.
    # keep 'Input0' the same
    
    return group_lines + remaining_lines




def sanitize_gizmo(saved_gizmo_filepath, suffix="_sd", tile_color=None, help="Copyright Sean Danischevsky", rename_action=None ):

    print (f'fixing {saved_gizmo_filepath}')

    # Find, set and fix Node Name: 
    current_gizmo_name, extension = os.path.splitext(os.path.basename(saved_gizmo_filepath))
    
    # Gizmo filename must be unicode, a-z, _.  , Capitalize first letter. Sanitized_name ends with '_sd' (me) or '_flw'
    sanitized_fixed_filepath = sanitise_gizmo_name(current_gizmo_name, suffix)
       
    # Gizmo itself then has '1' (like regular nodes)
    sanitized_gizmo_name=  sanitized_fixed_filepath + "1"
    print (f'Gizmo: {sanitized_gizmo_name}')

    #load 
    lines= read_file(saved_gizmo_filepath)
    print (lines[:9])

    # edit the file
    lines = edit_gizmo_file(lines, sanitized_gizmo_name, tile_color=tile_color, help=help)

    #save file
    gizmo_dir_name = os.path.dirname(saved_gizmo_filepath)
    fixed_filepath = os.path.join(gizmo_dir_name, f"{sanitized_fixed_filepath}{extension}")
    if saved_gizmo_filepath != fixed_filepath:
        if not rename_action:
            #in the future I'll ask, but am I in Nuke or command line? So for now:
            raise ValueError(f'Group is incorrectly named! Please rename as {fixed_filepath}')            
        if rename_action == "backup":
            backup_gizmo_filepath = saved_gizmo_filepath + 'bkp'
            os.rename(saved_gizmo_filepath, backup_gizmo_filepath)
            print (f'Backed up gizmo as {backup_gizmo_filepath}')
        elif rename_action == "move":
            write_file(fixed_filepath, lines)
            os.remove(saved_gizmo_filepath)
            print (f'Renamed gizmo as {fixed_filepath}')
        else:
            raise ValueError(f'Group is incorrectly named! Please rename as {fixed_filepath}')            

    else:
        write_file(fixed_filepath, lines)
        print (f"Saved {fixed_filepath}")
    #print (lines[:9])




def sanitize_directory(gizmos_directory, suffix, tile_color, help, rename_action):
    for root, dirs, files in os.walk(gizmos_directory):
        for name in files:
            if name.endswith('.gizmo'):
                gizmo_filepath = os.path.join(root, name)
                print (f'fixing {gizmo_filepath}')
                sanitize_gizmo(gizmo_filepath, suffix=suffix, tile_color=tile_color, help=help, rename_action=rename_action)

if __name__ == '__main__':
    gizmos_directory = os.path.join (os.path.dirname(__file__), '../gizmos')
    #gizmos_directory = "/Volumes/workspace/sean/repos/nuketools/groups/"
    print ("Gizmos directory", gizmos_directory)
    #sanitize_directory(gizmos_directory, suffix="_sd", tile_color="0xaaffffff", help=f"Copyright Sean Danischevsky", rename_action="move")


    for root, dirs, files in os.walk(gizmos_directory):
        for name in files:
            if name.endswith('.gizmo'):
                gizmo_filepath = os.path.join(root, name)
                print (f'fixing {gizmo_filepath}')
                sanitize_gizmo(gizmo_filepath, suffix="_flw", tile_color="0xff5555ff", help=f"Copyright Flawless", rename_action="move")
