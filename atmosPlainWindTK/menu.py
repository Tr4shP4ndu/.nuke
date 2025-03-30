# atmosPlainWindTK

import os
import nuke

try:

    toolsetPath='/'.join(os.path.join(os.path.dirname(__file__), 'toolsTK/Toolsets').split(os.sep))

    n = nuke.menu("Nodes").addMenu('toolsTK', icon='toolsTK.png')
    n.addCommand('Draw/atmosPlainWindTK','nuke.loadToolset("%s/Draw/atmosPlainWindTK.nk")' % toolsetPath)

except Exception as e:
    print('toolsTK:MenuBuilder failed: %s' % e)