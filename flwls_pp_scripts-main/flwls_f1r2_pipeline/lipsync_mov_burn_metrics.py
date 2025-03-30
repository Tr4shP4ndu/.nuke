
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
        return shot
    def get_fosd_name():
        shot= os.path.basename(nr_node['file'].value()).split('.')[0]
        shot= ('_').join(shot.split('_')[:-2])
        shot= f'{shot}_ogl'
        return shot

    def get_vub_name():
        #uses version number
        shot= os.path.basename(nr_node['file'].value()).split('.')[0]
        return shot


        

    def render_mov(style):

        write_node= nuke.toNode('LIPSYNC_MOV')

        if style == 'fosd':
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(1)
            write_node_audiofile= nuke_script_to_audio_wav_filename(nuke.root().name())
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_fosd_name()
            write_node['file'].setValue(os.path.join(basedir, write_node_file)+ '.mov')
            nuke.toNode('LIPSYNC_FrameTextTop')['message'].setValue(write_node_file)
        
        elif style == 'dub':
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(1)
            write_node_audiofile= get_target_wav()
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_dub_name()
            write_node['file'].setValue(os.path.join(basedir, write_node_file)+ '.mov')
            nuke.toNode('LIPSYNC_FrameTextTop')['message'].setValue(write_node_file)
        
        else:
            #vub
            nuke.toNode('Keymix_LIPSYNC')['disable'].setValue(0)
            write_node_audiofile= get_target_wav()
            write_node['mov64_audiofile'].setValue(write_node_audiofile)
            write_node_file= get_vub_name()
            write_node['file'].setValue(os.path.join(basedir, write_node_file)+ '.mov')
            nuke.toNode('LIPSYNC_FrameTextTop')['message'].setValue(write_node_file)

        #write mov
        sf= int(nuke.root()['first_frame'].value()) #better to use amounts set in dialogue
        ef= int(nuke.root()['last_frame'].value()) # ditto
        
        #lipsync metric needs minimum 100 frames
        #ef= max(ef- sf, sf+ 100- 1)


        #print everything
        print (write_node_audiofile)

        nuke.toNode('LIPSYNC_FrameTextTop')['disable'].setValue(0)
        nuke.toNode('LIPSYNC_FrameTextBottom')['disable'].setValue(0)

        nuke.root()['proxy'].setValue(0) 
        nuke.execute(write_node, sf, ef, 1)





    #MAIN
    basedir= '/Volumes/f1r2/Projects/squd01/episodes/squd01_ep99/metrics/'
    basedir= '/Volumes/f1r2/Projects/squd01/episodes/squd01_ep99/metrics_burn/'

    dataset_node= seanscripts.read_from_write_sd.readFromWrites([nuke.toNode('WRITE_PTdataset_STANDARD')])[0]
    nr_node= seanscripts.read_from_write_sd.readFromWrites([nuke.toNode('NeuralRender1')])[0]

    render_template = '/Volumes/f1r2/pipeline/vfx/templates/lipsync_metric/lipsync_metric_v002.nk'
    nuke.nodePaste(render_template)
    #set inputs
    nuke.toNode('NR_IN').setInput(0, nr_node)
    nuke.toNode('DATASET_IN').setInput(0, dataset_node)

    for style in ['fosd', 'dub', 'vub']:
        render_mov(style)

    

if __name__=="__main__":
    main()

