from typing import Union
import nuke
import nukescripts
import vfx_pipeline
import publish_vfx_task
from pathlib import Path
import os
import re
import itertools

class VFXPipelinePanel(nukescripts.PythonPanel):
    def __init__(self):
        nukescripts.PythonPanel.__init__(self, 'Flawless VFX Pipeline', 'FlawlessVFXPipelinePanel')
                
        #create tabs
        self.tab_knob1 = nuke.Tab_Knob('setup_tab', 'Workspace')
        self.tab_knob2 = nuke.Tab_Knob('publishtab', 'Publish')
        self.tab_knob3 = nuke.Tab_Knob('subtask_tab', 'Subtask')

        ###################
        #CREATE KNOBS
        ###################
        #title
        self.title_knob = nuke.Text_Knob('label', '')
        self.title_knob.setValue('<font size="7">Flawless VFX</font>')

        #seperator
        self.separator_line = nuke.Text_Knob("")
        self.separator_line2 = nuke.Text_Knob("")
        self.seperator_line3 = nuke.Text_Knob("")

        #context title
        self.context_title_knob = nuke.Text_Knob('label', '')
        self.context_title_knob.setValue('<font size="4">Context Picker</font>')

        #nuke script open and find 
        self.inputWorkPath = nuke.File_Knob('input_work_path', '')
        self.latest_nuke_work_script_knob = nuke.File_Knob("latest_nuke_script", "latest_nuke_script")

        #task entry
        self.taskKnob = nuke.Enumeration_Knob("task", "Task", ["select_task", "vfx_occlusion", "vfx_inpaint", "vfx_nr_cleanup"])
        
        #context entry
        self.showKnob = nuke.Enumeration_Knob("show", "Show", [])
        self.inputsversionknob = nuke.Enumeration_Knob("inputsversion", "Inputs Version", [])
        self.languageKnob = nuke.Enumeration_Knob("language", "Language", [])
        self.episodeKnob = nuke.Enumeration_Knob("episode", "Episode Part", [])
        #self.partKnob = nuke.Enumeration_Knob("part", "Part", [])
        self.shotKnob = nuke.Enumeration_Knob("shot", "Shot", [])
        self.charactervariantKnob = nuke.Enumeration_Knob("charvariant", "Variant", [])
        self.filteredinputsknob = nuke.Enumeration_Knob("inputversion", "Input Version", [])

        #script version for any existing Nuke scripts
        self.nukescriptversionKnob = nuke.Enumeration_Knob("nukescriptversion", "Nuke Script", [])
        self.opennukescriptButton = nuke.PyScript_Knob('open_script', 'Open Script')

        #setup shot button
        self.setupshotButton = nuke.PyScript_Knob('set_up_shot', 'Create Fresh Nuke Script')

        ####################
        # add KNOBS to panel
        ####################

        # PANEL TITLE 
        self.addKnob(self.title_knob)

        ####################
        # add KNOBS to panel
        ####################

        ####################
        #WORKSPACE TAB
        ####################
        self.addKnob(self.tab_knob1)
        self.addKnob(self.context_title_knob)
        self.addKnob(self.separator_line2)
        
        #CONTEXT
        self.addKnob(self.taskKnob)
        self.addKnob(self.showKnob)
        self.addKnob(self.languageKnob)
        self.languageKnob.setEnabled(False)
        self.addKnob(self.episodeKnob)
        #self.addKnob(self.partKnob)
        self.addKnob(self.shotKnob)
        self.addKnob(self.charactervariantKnob)
        self.charactervariantKnob.setEnabled(False)
        self.addKnob(self.inputsversionknob)
        self.inputsversionknob.setVisible(False)


        #OPEN SCRIPT
        self.addKnob(self.seperator_line3)
        self.addKnob(self.filteredinputsknob)
        self.filteredinputsknob.setEnabled(False)
        self.addKnob(self.nukescriptversionKnob)
        self.nukescriptversionKnob.setEnabled(False)
        self.addKnob(self.opennukescriptButton)
        self.opennukescriptButton.setEnabled(False)
        
        #SEPERATOR
        self.addKnob(self.separator_line)
        #self.addKnob(self.inputShotPath)

        
        self.addKnob(self.setupshotButton)
        self.setupshotButton.setEnabled(False)
        
        ####################
        # PUBLISH TAB
        ####################
        
        self.addKnob(self.tab_knob2)

        #publish title + division
        self.context_tab2_title_knob = nuke.Text_Knob('label', '')
        self.context_tab2_title_knob.setValue('<font size="4">Publish Element</font>')
        self.addKnob(self.context_tab2_title_knob)
        self.seperator_line4 = nuke.Text_Knob("")
        self.addKnob(self.seperator_line4)
        
        self.publish_vfx_task_elements_help_text = " - Select a Read node to publish output elements. Must be an EXR. \n" + \
                                                    " - The element needs to have the context in its filename. \n" + \
                                                    ""
        self.publish_vfx_task_elements_help_text = nuke.Text_Knob(
            "publish_vfx_task_elements_help_text",
            "",
            self.publish_vfx_task_elements_help_text
            )
        self.publish_vfx_task_elements_button = nuke.PyScript_Knob('publish_vfx_task_elements', 'publish_vfx_task_elements')
        self.publish_vfx_task_elements_button.setFlag(nuke.STARTLINE)

        self.addKnob(self.publish_vfx_task_elements_help_text)
        self.addKnob(self.publish_vfx_task_elements_button)

        ####################
        # SUBTASK TAB
        ####################
        
        self.addKnob(self.tab_knob3)

        #subtask title + division
        self.context_tab3_title_knob = nuke.Text_Knob('label', '')
        self.context_tab3_title_knob.setValue('<font size="4">Create Subtasks</font>')
        self.addKnob(self.context_tab3_title_knob)
        self.seperator_line5 = nuke.Text_Knob("")
        self.addKnob(self.seperator_line5)

        self.subtask_name_input_string_knob = nuke.String_Knob("subtask_name", "subtask_name")
        self.addKnob(self.subtask_name_input_string_knob)
        
        self.subtask_template_choice = nuke.Enumeration_Knob("subtask_template", "subtask_template", ["from_current_script", "start_fresh"])
        self.addKnob(self.subtask_template_choice)

        self.create_subtask_script_button = nuke.PyScript_Knob('create_subtask', 'create_subtask')
        self.create_subtask_script_button.setFlag(nuke.STARTLINE)
        self.addKnob(self.create_subtask_script_button)

        self.seperator_line6 = nuke.Text_Knob("")
        self.addKnob(self.seperator_line6)

        self.subtask_file_path_file_knob = nuke.File_Knob("subtask_path", "subtask_path")
        self.addKnob(self.subtask_file_path_file_knob)
        self.subtask_file_path_file_knob.setEnabled(False)

        #open nuke script
        self.opennukescriptButtonSubtask = nuke.PyScript_Knob('open_script', 'Open Subtask')
        self.addKnob(self.opennukescriptButtonSubtask)

        # getting Nuke to reload the OCIO config
        nuke.root().knob('reloadConfig').execute()

    def publish_vfx_task_elements(self):
        selected_node = nuke.selectedNode()
        if selected_node.Class()=='Read':
            filepath = Path(selected_node.knob('file').value())
            if filepath.parent.name == "exr":
                render_folder = filepath.parents[1]
                context = publish_vfx_task._get_context_from_render_path(render_folder)
                message = f"Going to publish the files in \n{render_folder}\nas {context.dict['task']} element"
                if nuke.ask(message):
                    publish_vfx_task.publish_vfx_task(render_path=render_folder)
            else:
                nuke.message('We only support publishing exr folders, at the moment')

        else:
            nuke.message('You need to select one Read node')

    def update_task(self):
        task = (self.taskKnob.value())
        self.taskKnob.setValues(["vfx_occlusion", "vfx_inpaint", "vfx_nr_cleanup"])
        self.taskKnob.setValue(task)

    def update_show(self):
        task = self.taskKnob.value()
        shows = list(os.listdir("/Volumes/workspace/shows"))

        shows_filtered = []

        for show in shows:
            show_dir = os.path.join('/Volumes/workspace/shows', show)
            tasks_dir = os.path.join(show_dir, 'tasks', task)
            if os.path.isdir(tasks_dir):
                shows_filtered.append(show)
        
        shows_filtered.sort()
        self.showKnob.setValues(shows_filtered)

    def update_inputs_version(self): #HIDDEN TO UI
        show = self.showKnob.value()
        task = self.taskKnob.value()

        versions = os.listdir(f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs")
        latest = latest_version(versions)
        versions = sorted(versions, key=lambda x: int(x[1:]))

        if latest:
            self.inputsversionknob.setValues(versions)

        else:
            self.inputsversionknob.setValues([])

    def update_language(self):
        show = self.showKnob.value()
        task = self.taskKnob.value()
        versions = self.inputsversionknob.values()

        if task == "vfx_nr_cleanup":
            self.languageKnob.setEnabled(True)

            language_list = sorted(list(set(language for version in versions
                                            for language in os.listdir(f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}/languages"))))

            self.languageKnob.setValues(language_list)

        else:
            self.languageKnob.setEnabled(False)

    def update_episode(self):
        show = self.showKnob.value()
        task = self.taskKnob.value()
        versions = self.inputsversionknob.values()
        language = self.languageKnob.value()
            
        episode_parts = []

        for version in versions:
            input_dir = f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}"
            shot_dir = f"{input_dir}/languages/{language}/shots" if task == "vfx_nr_cleanup" else f"{input_dir}/shots"
            if os.path.exists(shot_dir):
                episode_parts_current = os.listdir(shot_dir)
                episode_parts.extend(episode_parts_current)  # Use extend instead of append to add all elements to episode_parts

        # Remove the last four digits from each item in the episode_parts list
        episode_parts = [item[:-5] for item in episode_parts]

        # Use set to remove duplicates and then convert back to list
        unique_episode_parts = list(set(episode_parts))

        # Sort the unique_episode_parts list based on the numeric part of each element
        sorted_episode_parts = sorted(unique_episode_parts, key=lambda x: int(''.join(filter(str.isdigit, x))))

        # Assuming self.episodeKnob.setValues() sets the values of a knob (GUI element) with the sorted_episode_parts list
        self.episodeKnob.setValues(sorted_episode_parts)

    def update_shot(self):
        show = self.showKnob.value()
        task = self.taskKnob.value()
        versions = self.inputsversionknob.values()
        language = self.languageKnob.value()
        episode_part = self.episodeKnob.value()

        shot_list = []

        for version in versions:
            input_dir = f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}"
            shot_dir = f"{input_dir}/languages/{language}/shots" if task == "vfx_nr_cleanup" else f"{input_dir}/shots"

            if os.path.exists(shot_dir):
                #shot_list = os.listdir(shot_dir)
                #shot_list.extend(shot_list) 

                for filename in os.listdir(shot_dir):
                    prefix = episode_part
                    if filename.startswith(prefix):
                        sh = filename.split('_')[2]
                        if os.path.isdir(f"{shot_dir}/{episode_part}_{sh}"):
                            shot_list.append(sh)

        shot_list = sorted(list(set(shot_list)))
        self.shotKnob.setValues(shot_list)

    def update_variant(self):
        show = self.showKnob.value()
        task = self.taskKnob.value()
        versions = self.inputsversionknob.values()
        languages = self.languageKnob.values()
        episode_part = self.episodeKnob.value()
        #part = self.partKnob.value()
        shot = self.shotKnob.value()
        
        variants_list = []

        if task == "vfx_nr_cleanup":
            self.charactervariantKnob.setEnabled(True)

            for version, language in itertools.product(versions, languages):
                directory = f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}/languages/{language}/shots/{episode_part}_{shot}/PRECOMP"
                if os.path.isdir(directory):
                    vars = os.listdir(directory)
                    variants_list = variants_list + vars
                    variants = list(set(variants_list))
                    self.charactervariantKnob.setValues(variants)

        else:
            self.charactervariantKnob.setEnabled(False)
            pass

    def display_versions(self):
        
        task = self.taskKnob.value()
        show = self.showKnob.value()
        versions = self.inputsversionknob.values()
        shot = self.shotKnob.value()
        episode_part = self.episodeKnob.value()
        #part = self.partKnob.value()
        language = self.languageKnob.value()
        variant = self.charactervariantKnob.value()

        available_versions = []

        for version in versions:
            if task == "vfx_nr_cleanup": 
                user_directory = (f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}/languages/{language}/shots/{episode_part}_{shot}/PRECOMP/{variant}")
            else:
                user_directory = (f"/Volumes/workspace/shows/{show}/tasks/{task}/inputs/{version}/shots/{episode_part}_{shot}")
            
            if os.path.isdir(user_directory) == True:
                available_versions.append(version)

            else:
                pass

        #nuke.message("past_available_versions")###########

        
        latest = latest_version(available_versions)
        available_versions_sorted = sorted(available_versions, key=lambda x: int(x[1:]))

        if latest:
            self.filteredinputsknob.setEnabled(True)
            self.filteredinputsknob.setValues(available_versions_sorted)
            self.filteredinputsknob.setValue(latest)
            self.setupshotButton.setEnabled(True)

        else:
            self.filteredinputsknob.setValues([])

    def get_context_from_panel(self):
        episode_part = self.episodeKnob.value()
        episode = episode_part.split('_')[0]
        part = episode_part.split('_')[1]
        
        context_dict = {}

        context_dict['workspace_root'] = Path('/Volumes/workspace')
        context_dict['task'] = self.taskKnob.value()
        if context_dict['task'] in ('vfx_occlusion', 'vfx_inpaint'):
            context_dict['level'] = 'Shot'
        elif context_dict['task'] == 'vfx_nr_cleanup':
            context_dict['level'] = 'ShotLanguageVariant'
        context_dict['show'] = self.showKnob.value()
        context_dict['version'] = int((self.filteredinputsknob.value())[1:])
        context_dict['shot'] = int(self.shotKnob.value())
        context_dict['episode'] = int(episode[2:])
        context_dict['part'] = int(part[2:])
        context_dict['language'] = self.languageKnob.value()
        context_dict['variant'] = self.charactervariantKnob.value()

        return vfx_pipeline.Context(dict=context_dict)

    def fill_existing_scripts_knob(self):
        context = self.get_context_from_panel()
        
        task_path = vfx_pipeline._get_task_path(context=context)
        work_folder = task_path / "work"
        
        nuke_scripts = [f for f in os.listdir(work_folder) if f.endswith('nk')]

        available_scripts = sorted(nuke_scripts, reverse=True)



        #nuke.message(available_scripts)
        if len(available_scripts) == 0:
            self.opennukescriptButton.setEnabled(False)
        else:
            self.nukescriptversionKnob.setValues(available_scripts)
            self.opennukescriptButton.setEnabled(True)
            self.nukescriptversionKnob.setEnabled(True)

    def open_nuke_script(self):
        context = self.get_context_from_panel()
        script_name = self.nukescriptversionKnob.value()
        workpath = vfx_pipeline.get_work_directory(context=context)
        script_path = (f"{workpath}/{script_name}")
        
        try:
            root = nuke.root().name()      #not save = Root
            #nuke.message(root)
            if root == "Root":
               # nuke.message("Not saved")
                nuke.scriptSaveAs(filename="/tmp/temp_nuke_script.nk", overwrite= 1)
                nuke.scriptOpen(script_path)
                #nuke.scriptClose()
            else:
                #nuke.message("Saved")
                nuke.scriptOpen(script_path)
        except:
            nuke.message(f"Failed to open {script_path}")

    def set_up_fresh_nuke_script(self):
        context = self.get_context_from_panel()
        message = f"Going to set up shot for {context.dict['shot']} {context.dict['task']} task: \n\
            {vfx_pipeline._get_task_nuke_script_destination_path(context=context)}"

        if nuke.ask(message):
            vfx_pipeline.set_up_shot(context=context)
            self.fill_existing_scripts_knob()
        else:
            print('Cancelled shot creation')
            self.fill_existing_scripts_knob()

    def set_up_subtask_nuke_script(self):
        '''
        Checks that the subtask name is valid
        Then either saves a snapshot of the current script in 
        '''
        subtask_name = self.subtask_name_input_string_knob.value()
        if len(subtask_name) > 0:
            illegal_characters = vfx_pipeline.find_illegal_characters(text_to_check=subtask_name)
            if len(illegal_characters) == 0:
                if self.subtask_template_choice.value() == "from_current_script":
                    subtask_path = self._set_up_subtask_nuke_script_from_current_script(subtask_name=subtask_name)
                    self.subtask_file_path_file_knob.setEnabled(True)
                    self.subtask_file_path_file_knob.setValue(subtask_path.as_posix())
                elif self.subtask_template_choice.value() == "start_fresh":
                    subtask_path = self._set_up_subtask_nuke_script_from_template(subtask_name=subtask_name)
                    self.subtask_file_path_file_knob.setEnabled(True)
                    self.subtask_file_path_file_knob.setValue(subtask_path.as_posix())
            else:
                nuke.message(f"Please only use alphanumeric characters or dashes - or underscores _ in subtask name \nPlease remove: {illegal_characters}")
        else:
            nuke.message("Please input the subtask name")

    def _set_up_subtask_nuke_script_from_current_script(self, subtask_name: str) -> Union[Path, None]:
        '''
        Given a valid subtask name, saves the current opin 
        '''

        context = vfx_pipeline.get_context_from_script_name(Path(nuke.root().name()).stem)
        subtask_script_path = vfx_pipeline.get_subtask_nuke_script_destination_path(context, subtask_name)

        message = f"Going to set up subtask script \n{subtask_script_path} \nusing current script snapshot"
        
        if nuke.ask(message):
            subtask_script_path.parent.mkdir(exist_ok=True)
            nuke.scriptSaveToTemp(subtask_script_path.as_posix())
            return subtask_script_path
        else:
            print('Cancelled subtask creation')
            return None
        
    def _set_up_subtask_nuke_script_from_template(self, subtask_name: str) -> Union[Path, None]:
        '''
        Assuming subtask name is already valid
        '''

        context = vfx_pipeline.get_context_from_script_name(Path(nuke.root().name()).stem)
        subtask_script_path = vfx_pipeline.get_subtask_nuke_script_destination_path(context, subtask_name)

        message = f"Going to set up subtask script \n{subtask_script_path} \nusing current {context.dict['task']} template"
        
        if nuke.ask(message):
            subtask_script_path.parent.mkdir(exist_ok=True)
            return vfx_pipeline._copy_task_template_to_specific_destination(context=context, destination_path_with_filename=subtask_script_path)

        else:
            print('Cancelled subtask creation')
            return None

    def knobChanged(self, knob):
        task = self.taskKnob.value()
        if knob == self.setupshotButton:
            self.set_up_fresh_nuke_script()

        if knob == self.opennukescriptButton:
            self.open_nuke_script()

        if knob == self.taskKnob:
            self.showKnob.setValues([])
            self.inputsversionknob.setValues([])
            self.languageKnob.setValues([])
            self.episodeKnob.setValues([])
            self.shotKnob.setValues([])
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_task()
            self.update_show()
            self.update_inputs_version()
            self.update_language()
            self.update_episode()
            self.update_shot()
            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.showKnob:
            self.inputsversionknob.setValues([])
            self.languageKnob.setValues([])
            self.episodeKnob.setValues([])
            self.shotKnob.setValues([])
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_inputs_version()
            self.update_language()
            self.update_episode()
            self.update_shot()
            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.inputsversionknob:
            self.languageKnob.setValues([])
            self.episodeKnob.setValues([])
            self.shotKnob.setValues([])
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_language()
            self.update_episode()
            self.update_shot()
            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.languageKnob:
            self.episodeKnob.setValues([])
            self.shotKnob.setValues([])
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_episode()
            self.update_shot()
            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.episodeKnob:
            self.shotKnob.setValues([])
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_shot()
            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.shotKnob:
            
            self.charactervariantKnob.setValues([])
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.update_variant()
            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.charactervariantKnob:
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)

            self.display_versions()
            self.fill_existing_scripts_knob()

        if knob == self.filteredinputsknob:
            self.nukescriptversionKnob.setValues([])
            self.opennukescriptButton.setEnabled(False)
            self.nukescriptversionKnob.setEnabled(False)
            self.fill_existing_scripts_knob()

        if knob == self.publish_vfx_task_elements_button:
            self.publish_vfx_task_elements()

        if knob == self.create_subtask_script_button:
            self.set_up_subtask_nuke_script()

        if knob == self.opennukescriptButtonSubtask:
            script_path = self.subtask_file_path_file_knob.value()
            if os.path.exists(script_path):
                try:
                    nuke.scriptOpen(script_path)
                except:
                    nuke.message("No script found.")
            else:
                nuke.message("Please create a subtask")




def latest_version(paths): # WHEN PROVIDED WITH A PATH, THIS EXTRACTS THE HIGHEST VERSION NUMBER, AND RETURNS THE CORRESPONDING PATH
    max_version = 0
    max_path = None

    for path in paths:
    
        match = re.search(r'v(\d+)', str(path))
        if match:
            version = int(match.group(1))
            if version > max_version:
                max_version = version
                max_path = path

    return max_path 







        
