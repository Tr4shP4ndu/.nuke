
import nuke
import os

def main():
    import seanscripts.read_from_write_sd

    def get_target_wav():
            g= nuke.toNode('Review')
            with g:
                w= nuke.toNode('OUT_MOV')
                audiofile= w['mov64_audiofile'].evaluate()
            return audiofile

    def nuke_script_to_audio_wav_filename(input_script):
        #Split on /shots/
        base, shot= input_script.split('/shots/')
        shot= shot.split('/')[0]
        my_result= os.path.join(base, 'shots', shot)+ '/language/ogl/dub/'+ shot+ '.wav'
        return my_result

    def get_dub_name():
        shot= os.path.basename(nr_node['file'].value()).split('.')[0]
        shot= ('_').join(shot.split('_')[:-2])
        shot= f'{shot}_dub'
        return os.path.join(basedir, shot)+ '.mov'

    def get_fosd_name():
        shot= os.path.basename(nr_node['file'].value()).split('.')[0]
        shot= ('_').join(shot.split('_')[:-2])
        shot= f'{shot}_ogl'
        return os.path.join(basedir, shot)+ '.mov'

    def get_vub_name():
        #uses version number
        shot= os.path.basename(nr_node['file'].value()).split('.')[0]
        return os.path.join(basedir, shot)+ '.mov'



    def get_comp_input_name():
        #uses comp name from lindsey's list
        path = nuke.root().name()
        import pathlib
        path_object = pathlib.Path(path)
        shot_code=path_object.parts[10]

        import glob
        file = glob.glob(f'/Volumes/f1r2/Projects/squd01/exports/final_shots/{shot_code}*')[0]
        path_object = pathlib.Path(file)
        comp_name=path_object.parts[-1]
        file = file+ f'/exrs/{comp_name}%08d.exr'
        return file

    def get_comp_output_name():
        # uses comp name from lindsey's list
        # e.g.
        # /Volumes/f1r2/Projects/squd01/exports/final_shots/squd01_ep99_pt01_0400_eng_456_final/exrs/squd01_ep99_pt01_0400_eng_456_final00001001.exr

        #uses comp name from lindsey's list
        path = nuke.root().name()
        import pathlib
        path_object = pathlib.Path(path)
        shot_code=path_object.parts[10]

        import glob
        file = glob.glob(f'/Volumes/f1r2/Projects/squd01/exports/final_shots/{shot_code}*')[0]
        path_object = pathlib.Path(file)
        comp_name= path_object.parts[-1]
        return os.path.join(comp_name)+ '.mov'
        

    def render_mov(style):

        write_node= nuke.toNode('LIPSYNC_MOV')

        if style == 'fosd':
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(1)
            write_node_audiofile=nuke_script_to_audio_wav_filename(nuke.root().name())
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_fosd_name()
            write_node['file'].setValue(write_node_file)
        
        elif style == 'dub':
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(1)
            write_node_audiofile=get_target_wav()
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_dub_name()
            write_node['file'].setValue(write_node_file)

        elif style == 'comp':
            nr_node['file'].setValue(get_comp_input_name())
            nr_node['colorspace'].setValue('Output - Rec.709')

            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(1)
            write_node_audiofile=get_target_wav()
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_comp_output_name()
            write_node['file'].setValue(write_node_file)     

            tb= nuke.nodes.KT_ST_Tracker_box_flw_v001()
            tb.setInput(0,nr_node)
            tb.setInput(1,nuke.toNode('FACETRACKER_CAM'))
            tb.setInput(2,nuke.toNode('FACETRACKER'))
            tb['stabilise'].setValue(1)
            write_node.setInput(0, tb)     
            
   
        else:
            #vub
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(0)
            write_node_audiofile=get_target_wav()
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_comp_output_name()
            write_node['file'].setValue(write_node_file)        

        #write mov
        sf= int(nuke.root()['first_frame'].value()) #better to use amounts set in dialogue
        ef= int(nuke.root()['last_frame'].value()) # ditto
        
        #lipsync metric needs minimum 100 frames
        #ef= max(ef- sf, sf+ 100- 1)


        #print everything
        print (write_node_audiofile)



        nuke.root()['proxy'].setValue(0) 
        nuke.execute(write_node, sf, ef, 1)





    #MAIN
    basedir= '/Volumes/f1r2/Projects/squd01/episodes/squd01_ep99/metrics_short/'

    dataset_node= seanscripts.read_from_write_sd.readFromWrites([nuke.toNode('WRITE_PTdataset_STANDARD')])[0]
    nr_node= seanscripts.read_from_write_sd.readFromWrites([nuke.toNode('NeuralRender1')])[0]
    
    render_template = '/Volumes/f1r2/pipeline/vfx/templates/lipsync_metric/lipsync_metric_v001.nk'
    nuke.nodePaste(render_template)
    #set inputs
    nuke.toNode('NR_IN').setInput(0, nr_node)
    nuke.toNode('DATASET_IN').setInput(0, dataset_node)

    #for style in ['fosd', 'dub', 'vub']:
    for style in ['comp']:
        render_mov(style)

    

if __name__=="__main__":
    main()





