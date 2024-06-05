import nuke

def get_inf_sample_range(first_frame_comp, last_frame_comp, odd_pixel, no_odd_pixel):
    """ Samples the max and min values of the given frame range and set an average RGB sample into a single value """

    inf_tool = nuke.toNode('inf_pixels_ct')
    min_knob = inf_tool['minlumapixvalue']
    max_knob = inf_tool['maxlumapixvalue']

    min_knob.setAnimated()
    max_knob.setAnimated()
    
    nuke.execute(inf_tool, int(first_frame_comp), int(last_frame_comp))
    
    inf_values = inf_tool['inf_pixels_avg'].value()
    if inf_values > 1:
        inf = f'<b>INF Pixels:</b> \n{odd_pixel}'
    else:
        inf = f'<b>INF Pixels:</b> \n{no_odd_pixel}'
    return inf

def get_nan_sample_range(first_frame_comp, last_frame_comp, odd_pixel, no_odd_pixel):
    """ Samples the max and min values of the given frame range and set an average RGB sample into a single value """

    nan_tool = nuke.toNode('nan_pixels_ct')
    min_knob = nan_tool['minlumapixvalue']
    max_knob = nan_tool['maxlumapixvalue']

    min_knob.setAnimated()
    max_knob.setAnimated()
    
    nuke.execute(nan_tool, int(first_frame_comp), int(last_frame_comp))

    nan_values = nan_tool['nan_pixels_avg'].value()
    if nan_values > 1:
        nan = f'<b>NAN Pixels:</b> \n{odd_pixel}'
    else:
        nan = f'<b>NAN Pixels:</b> \n{no_odd_pixel}'
    return nan
    
def get_neg_sample_range(first_frame_comp, last_frame_comp, odd_pixel, no_odd_pixel):
    """ Samples the max and min values of the given frame range and set an average RGB sample into a single value """

    neg_tool = nuke.toNode('neg_pixels_ct')
    min_knob = neg_tool['minlumapixvalue']
    max_knob = neg_tool['maxlumapixvalue']

    min_knob.setAnimated()
    max_knob.setAnimated()

    nuke.execute(neg_tool, int(first_frame_comp), int(last_frame_comp))
    neg_values = neg_tool['neg_pixels_avg'].value()
    if neg_values > 1:
        neg = f'<b>NEG Pixels: </b>\n{odd_pixel}'
    else:
        neg = f'<b>NEG Pixels:</b> \n{no_odd_pixel}'
    return neg

def check_frame_range(comp_range, plate_range):
    """ Checks Plate and Comp frame ranges are matching """

    convert_plate = plate_range[1] - plate_range[0] + 1
    convert_comp = comp_range[1] - comp_range[0] + 1
    
    if convert_comp == convert_plate:
        range_check = f'<b>Inputs Ranges:</b>\n<font color="#228B22">are matching frame ranges!</font>{convert_plate} - {convert_comp}'
    else:
        range_check = f'<b>Inputs Ranges:</b> \n<font color="#B22222">do not match frame ranges!</font>{convert_plate} - {convert_comp}'
    
    return range_check

def get_format_tuple(node):
    return node.format().width(), node.format().height(), node.format().pixelAspect()

def check_res(read):
    if get_format_tuple(read.input(0)) != get_format_tuple(read.input(1)):
        format_input = f'Resolution: NR_precomp:<font color="#B22222">{get_format_tuple(read.input(0))}</font> & Plate:<font color="#B22222">{get_format_tuple(read.input(1))}</font> Format MissMatching!'
    else:
        format_input = f'<b>Resolution: </b>\nNR_precomp:<font color="#228B22">{get_format_tuple(read.input(0))}</font> & Plate:<font color="#228B22">{get_format_tuple(read.input(1))}</font> Format Matching!'
    return format_input
  
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
    
    # read_input_comp = read_input.input(0)
    # comp = read_input_comp['first'].value(), read_input_comp['last'].value()
    # read_input_plate = read_input.input(1)
    # plate = read_input_plate['first'].value(), read_input_plate['last'].value()
    
    read_input_comp = nuke.toNode('frame_range_comp') # Fetches Comp frame range node
    first_frame_comp = read_input_comp['first_frame'].value()
    last_frame_comp = read_input_comp['last_frame'].value()
    comp = first_frame_comp, last_frame_comp

    read_input_plate = nuke.toNode('frame_range_plate') # Fetches Plate frame range node
    first_frame_plate = read_input_plate['first_frame'].value()
    last_frame_plate = read_input_plate['last_frame'].value()
    plate = first_frame_plate, last_frame_plate
    
    odd_pixel = '<font color="#B22222">There are odd pixels!</font>'
    no_odd_pixel = '<font color="#228B22">No visible odd pixels!</font>'
    
    """Start functions and obtain values"""
    input_connect = check_inputs(read = read_input)
    res = check_res(read = read_input)
    check_range = check_frame_range(comp_range = comp, plate_range = plate)
    neg = get_neg_sample_range(first_frame_comp = first_frame_comp, last_frame_comp = last_frame_comp, odd_pixel = odd_pixel, no_odd_pixel = no_odd_pixel)
    nan = get_nan_sample_range(first_frame_comp = first_frame_comp, last_frame_comp = last_frame_comp, odd_pixel = odd_pixel, no_odd_pixel = no_odd_pixel)
    inf = get_inf_sample_range(first_frame_comp = first_frame_comp, last_frame_comp = last_frame_comp, odd_pixel = odd_pixel, no_odd_pixel = no_odd_pixel)
    nuke.message(f'<center>{input_connect} \n {res} \n{check_range} \n{neg} \n{nan} \n{inf}')
    read_input['input_text'].setValue(f'<center>{input_connect}')
    read_input['res_text'].setValue(f'<center>{res}')
    read_input['range_text'].setValue(f'<center>{check_range}')
    read_input['neg_text'].setValue(f'<center>{neg}')
    read_input['nan_text'].setValue(f'<center>{nan}')
    read_input['inf_text'].setValue(f'<center>{inf}')
    

start()
