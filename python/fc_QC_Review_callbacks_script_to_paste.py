n = nuke.selectedNode()
n.knob('knobChanged').setValue('''


e = nuke.thisNode().knobs()['extraCtrl'].value()
v = nuke.thisNode().knobs()['tc_viewer'].getValue()
s = nuke.thisNode().knobs()['size']
expUp = nuke.thisNode().knobs()['expV']
c = nuke.thisNode().knobs()['colours']
oddP =nuke.thisNode().knobs()['pixelBoost']
side = nuke.thisNode().knobs()['disableSidebySide'].getValue()
sat = nuke.thisNode().knobs()['sat']
chkb = nuke.thisNode().knobs()['disableCheckerboard']


if e == 1:
    if v == 0:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 1:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 2:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(True)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 3:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(True)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 4:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 5:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        sat.setVisible(True)
        chkb.setVisible(False)
    elif v == 6:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        sat.setVisible(False)
        chkb.setVisible(False)
    elif v == 7:
        s.setVisible(True)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        chkb.setVisible(True)
        
    elif v == 8:
        s.setVisible(False)
        c.setVisible(True)
        expUp.setVisible(False)
        oddP.setVisible(False)
        chkb.setVisible(False)
    elif v == 9:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        chkb.setVisible(False)
    elif v == 10:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(True)
        chkb.setVisible(False)
    elif v == 11:
        s.setVisible(False)
        c.setVisible(False)
        expUp.setVisible(False)
        oddP.setVisible(False)
        chkb.setVisible(False)
else:
    s.setVisible(False)
    c.setVisible(False)
    expUp.setVisible(False)
    oddP.setVisible(False)
    sat.setVisible(False)
    chkb.setVisible(False)


''')



n = nuke.selectedNode()
n.knob('knobChanged').setValue('''
v1 = nuke.thisNode().knobs()['difference_mov'].getValue()
v2 = nuke.thisNode().knobs()['black_levels_mov'].getValue()
v3 = nuke.thisNode().knobs()['shadows_mov'].getValue()
v4 = nuke.thisNode().knobs()['highlights_mov'].getValue()
v5 = nuke.thisNode().knobs()['luminance_mov'].getValue()
v6 = nuke.thisNode().knobs()['colour_mov'].getValue()
v7 = nuke.thisNode().knobs()['saturation_limit_mov'].getValue()
v8 = nuke.thisNode().knobs()['noise_grain_mov'].getValue()
v9 = nuke.thisNode().knobs()['edge_of_frame_mov'].getValue()
v10 = nuke.thisNode().knobs()['fourbyfour_edge_frame_mov'].getValue()
v11 = nuke.thisNode().knobs()['odd_pixels_mov'].getValue()
v12 = nuke.thisNode().knobs()['alpha_channel_mov'].getValue()

dot1 = nuke.toNode("difference_dot")
dot2 = nuke.toNode("black_levels_dot")
dot3 = nuke.toNode("shadows_dot")
dot4 = nuke.toNode("highlights_dot")
dot5 = nuke.toNode("luminance_dot")
dot6 = nuke.toNode("colour_dot")
dot7 = nuke.toNode("saturation_limit_dot")
dot8 = nuke.toNode("noise_grain_dot")
dot9 = nuke.toNode("edge_of_frame_dot")
dot10 = nuke.toNode("fourbyfour_edge_frame_dot")
dot11 = nuke.toNode("odd_pixels_dot")
dot12 = nuke.toNode("alpha_channel_dot")

sheet = nuke.toNode("ContactSheet2")
append = nuke.toNode("AppendClip2")

# List of dot nodes
dot_nodes = [dot1, dot2, dot3, dot4, dot5, dot6, dot7, dot8, dot9, dot10, dot11, dot12]

# List of checkbox values
checkbox_values = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12]

# Disconnect all nodes first
for i in range(12):
    sheet.setInput(i, None)
for i in range(12):
    append.setInput(i, None)

# Connect/disconnect nodes based on checkbox values
for i, checkbox_value in enumerate(checkbox_values):
    if checkbox_value == 1:
        sheet.setInput(i, dot_nodes[i])
for i, checkbox_value in enumerate(checkbox_values):
    if checkbox_value == 1:
        append.setInput(i, dot_nodes[i])
''')