import base64
import nuke

read_input = nuke.thisNode()
contact_sheet_write = 'contact_sheet_write'
review_sequence_write = 'review_sequence_write'


def review_sequence_write_mov(contact_sheet_write,read_input):
    if not nuke.exists(review_sequence_write):
        print(f"Node {contact_sheet_write} does not exist.")
        return
    read_input = nuke.toNode('FrameRange14')
    
    rsw = nuke.toNode(review_sequence_write)

    first_frame = read_input['first_frame'].value()
    last_frame = read_input['last_frame'].value()
    
    nuke.execute(rsw, int(first_frame), int(last_frame))

def contact_sheet_write_mov(contact_sheet_write,read_input):
    if not nuke.exists(contact_sheet_write):
        print(f"Node {contact_sheet_write} does not exist.")
        return
    read_input = nuke.toNode('FrameRange15')
    
    csw = nuke.toNode(contact_sheet_write)

    first_frame = read_input['first_frame'].value()
    last_frame = read_input['last_frame'].value()
    
    nuke.execute(csw, int(first_frame), int(last_frame))
    
    review_sequence_write_mov(review_sequence_write, read_input)
    

def start(read_input):
    """let's do this!"""

    contact_sheet_write_mov(contact_sheet_write, read_input)
    
    
start(read_input)
