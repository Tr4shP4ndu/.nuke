n = nuke.selectedNode()
n.knob('knobChanged').setValue('''


v = nuke.thisNode().knobs()['roto_switch'].getValue()
left = nuke.thisNode().knobs()['group_left_cheek']
right = nuke.thisNode().knobs()['group_right_cheek']
nose = nuke.thisNode().knobs()['group_nose']
blur = nuke.thisNode().knobs()['alpha_chocker_pre']


if v == 0:
    left.setVisible(True)
    right.setVisible(False)
    nose.setVisible(False)
    blur.setVisible(True)
elif v == 1:
    left.setVisible(False)
    right.setVisible(True)
    nose.setVisible(False)
    blur.setVisible(True)
elif v == 2:
    left.setVisible(True)
    right.setVisible(True)
    nose.setVisible(False)
    blur.setVisible(True)
elif v == 3:
    left.setVisible(False)
    right.setVisible(False)
    nose.setVisible(True)
    blur.setVisible(True)
elif v == 4:
    left.setVisible(True)
    right.setVisible(True)
    nose.setVisible(True)
    blur.setVisible(True)
elif v == 5:
    left.setVisible(False)
    right.setVisible(False)
    nose.setVisible(False)
    blur.setVisible(False)
else:
    left.setVisible(False)
    right.setVisible(False)
    nose.setVisible(False)
    blur.setVisible(False)
''')
