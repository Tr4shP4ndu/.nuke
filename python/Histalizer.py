import nuke 

FRAME_RANGE_NODE = 'frame_range_in_out'
MAX_TOOL_NODE = 'max'
WHITE_BLACK_POINT_NODE = 'whiteblackpoint'
SET_GAMMA_AVG_NODE = 'set_gamma_avg'
SET_GAMMA_HIGH_NODE = 'set_gamma_high'
LIFT_GAIN_AVG_NODE = 'LiftGain_avg'
LIFT_GAIN_HIGH_NODE = 'LiftGain_High'
KEYMIX1_NODE = 'Keymix1'
KEYMIX2_NODE = 'Keymix2'

def get_sample_values(max_tool, first_frame, last_frame):
    """Retrieve animated values for min and max knobs over a frame range"""
    min_knob = max_tool['minlumapixvalue']
    max_knob = max_tool['maxlumapixvalue']
    min_knob.setAnimated()
    max_knob.setAnimated()
    nuke.execute(max_tool, int(first_frame), int(last_frame))
    max_values = [max_knob.getValueAt(frame) for frame in range(int(first_frame), int(last_frame) + 1)]
    min_values = [min_knob.getValueAt(frame) for frame in range(int(first_frame), int(last_frame) + 1)]
    return max_values, min_values

def calculate_tone_values(max_values, min_values):
    """Calculate tone values based on max and min values"""
    hightone_values = [(max_value[0] + max_value[1] + max_value[2]) / 3 for max_value in max_values]
    darktone_values = [(min_value[0] + min_value[1] + min_value[2]) / 3 for min_value in min_values]
    midtone_values = [(hightone + darktone) / 3.5 for hightone, darktone in zip(hightone_values, darktone_values)]
    less_or_highers = [1 if midtone < 0.4 else 0 for midtone in midtone_values]
    avg_values = [(midtone + less_or_higher) / 2 - 0.05 for midtone, less_or_higher in zip(midtone_values, less_or_highers)]
    midtone_hightone_values = [(midtone if midtone > 0.4 else avg_value) + hightone / 2.5 for midtone, avg_value, hightone in zip(midtone_values, avg_values, hightone_values)]
    midtone_mid_values = [1 / (midtone if midtone > 0.4 else midtone + midtone) for midtone in midtone_values]
    keymix2 = [1 if hightone > 0.94 else 0 for hightone in hightone_values]
    keymix1 = [1 if midtone_hightone > 0.55 else 0 for midtone_hightone in midtone_hightone_values]
    return hightone_values, darktone_values, midtone_values, less_or_highers, avg_values, midtone_hightone_values, midtone_mid_values, keymix2, keymix1

def set_keyframes(node, knob_name, values, frame_range):
    """Set keyframes for a knob with given values over a frame range"""
    knob = node[knob_name]
    knob.setAnimated()
    for frame, value in zip(range(int(frame_range[0]), int(frame_range[1]) + 1), values):
        knob.setValueAt(value, frame)

def check_inputs(read):
    """Checks if there are connected inputs and if format is matching"""
    if read.input(0) is None:
        raise RuntimeError('No Plate Connected!')
    else:
        return 'Inputs - Connected'

def start(read_input):
    """Entry point function"""
    check_inputs(read_input)

    """Get Nodes"""
    frame_range_input = nuke.toNode(FRAME_RANGE_NODE)
    max_tool = nuke.toNode(MAX_TOOL_NODE)
    whiteblackpoint = nuke.toNode(WHITE_BLACK_POINT_NODE)
    set_gamma_avg = nuke.toNode(SET_GAMMA_AVG_NODE)
    set_gamma_high = nuke.toNode(SET_GAMMA_HIGH_NODE)
    LiftGain_avg = nuke.toNode(LIFT_GAIN_AVG_NODE)
    LiftGain_High = nuke.toNode(LIFT_GAIN_HIGH_NODE)
    Keymix1 = nuke.toNode(KEYMIX1_NODE)
    Keymix2 = nuke.toNode(KEYMIX2_NODE)

    """Get Range"""
    first_frame = frame_range_input['first_frame'].value()
    last_frame = frame_range_input['last_frame'].value()

    """Sample Values"""
    max_values, min_values = get_sample_values(max_tool, first_frame, last_frame)

    """Calculate Values"""
    hightone_values, darktone_values, midtone_values, less_or_highers, avg_values, midtone_hightone_values, midtone_mid_values, keymix2, keymix1 = calculate_tone_values(max_values, min_values)

    """Animate Nodes"""
    for node, knob_name, values in [(whiteblackpoint, 'blackpoint', darktone_values),
                                    (whiteblackpoint, 'whitepoint', hightone_values),
                                    (set_gamma_avg, 'gamma', midtone_mid_values),
                                    (set_gamma_high, 'gamma', midtone_hightone_values),
                                    (LiftGain_avg, 'black', darktone_values),
                                    (LiftGain_avg, 'white', hightone_values),
                                    (LiftGain_High, 'black', darktone_values),
                                    (LiftGain_High, 'white', hightone_values),
                                    (Keymix1, 'disable', keymix1),
                                    (Keymix2, 'disable', keymix2)]:
        set_keyframes(node, knob_name, values, (first_frame, last_frame))

        for i, (hightone, darktone, midtone, less_or_higher, avg, midtone_hightone, midtone_mid) in enumerate(zip(hightone_values, darktone_values, midtone_values, less_or_highers, avg_values, midtone_hightone_values, midtone_mid_values)):
            print(f"Frame {first_frame + i}")
            print(f"hightone_value: {hightone}")
            print(f"darktone_value: {darktone}")
            print(f"midtone_value: {midtone}")
            print(f"less_or_higher: {less_or_higher}")
            print(f"avg_value: {avg}")
            print(f"midtone_hightone_value: {midtone_hightone}")
            print(f"midtone_mid_value: {midtone_mid}")

start(nuke.thisNode())


node = nuke.toNode("fc_Histogram_Equalizer3")
node.knob('converter_button').setValue('''

''')