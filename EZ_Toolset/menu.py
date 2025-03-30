# (C) 2024 - Victor Rouillard
# Add EZ_Toolset menu to Nuke's Nodes menu.

import nuke

nuke.pluginAddPath('icons')

aboutMessage = 'EZ Toolset 2.0 \n2024/06\nCreated by: Victor Rouillard\nhttps://www.linkedin.com/in/victor-rouillard/\n(c) 2018-2024'

t=nuke.menu("Nodes")
u=t.addMenu("EZ Toolset", icon="EZ_Toolset_Menu.png")

u.addCommand( "EZ_Aberration", "nuke.createNode('EZ_Aberration')", icon="EZ_Aberration.png")
u.addCommand( "EZ_Backdrop", "nuke.createNode('EZ_Backdrop')", icon="EZ_Backdrop.png")
u.addCommand( "EZ_ChangeRef", "nuke.createNode('EZ_ChangeRef')", icon="EZ_ChangeRef.png" ) 
u.addCommand( "EZ_ColorMatcher", "nuke.createNode('EZ_ColorMatcher')", icon="EZ_ColorMatcher.png")
u.addCommand( "EZ_Difference", "nuke.createNode('EZ_Difference')", icon="EZ_Difference.png")
u.addCommand( "EZ_Dissolve", "nuke.createNode('EZ_Dissolve')", icon="EZ_Dissolve.png")
u.addCommand( "EZ_EdgeBlend", "nuke.createNode('EZ_EdgeBlend')", icon="EZ_EdgeBlend.png")
u.addCommand( "EZ_EdgeRoughen", "nuke.createNode('EZ_EdgeRoughen')", icon="EZ_EdgeRoughen.png")
u.addCommand( "EZ_EdgeWork", "nuke.createNode('EZ_EdgeWork')", icon="EZ_EdgeWork.png" )
u.addCommand( "EZ_Erode", "nuke.createNode('EZ_Erode')", icon="EZ_Erode.png" ) 
u.addCommand( "EZ_MatteCheck", "nuke.createNode('EZ_MatteCheck')", icon="EZ_MatteCheck.png")
u.addCommand( "EZ_MixDetails", "nuke.createNode('EZ_MixDetails')", icon="EZ_MixDetails.png" ) 
u.addCommand( "EZ_MotionBlur2D", "nuke.createNode('EZ_MotionBlur2D')", icon="EZ_MotionBlur2D.png" ) 
u.addCommand( "EZ_Murk", "nuke.createNode('EZ_Murk')", icon="EZ_Murk.png" ) 
u.addCommand( "EZ_Parallax", "nuke.createNode('EZ_Parallax')", icon="EZ_Parallax.png" )
u.addCommand( "EZ_SwitchReads", "nuke.createNode('EZ_SwitchReads')", icon="EZ_SwitchReads.png")
u.addCommand( "EZ_TimeOffset", "nuke.createNode('EZ_TimeOffset')", icon="EZ_TimeOffset.png") 
u.addSeparator()
u.addCommand( "EZ_RotoTracker", "nuke.createNode('EZ_RotoTracker')", icon="EZ_RotoTracker.png") 
u.addCommand( "EZ_4thPin", "nuke.createNode('EZ_4thPin')", icon="EZ_4thPin.png") 
u.addCommand( "EZ_Packager", "nuke.createNode('EZ_Packager')", icon="EZ_Packager.png") 
u.addSeparator()
u.addCommand("About EZ Toolset...", "nuke.message(aboutMessage)", icon="EZ_Toolset_Menu.png")
