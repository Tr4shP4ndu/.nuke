#FLAWLESS oldschool (f1r2) MENU
#toolbar = FLAWLESS_PP_NODE_MENU
#m = toolbar.addMenu('Flawless', icon = "icons/flawless.png")

#KeentoolsQC
FLAWLESS_PP_NODE_MENU.addCommand('KeentoolsQC_v006flw', "nuke.createNode('KeentoolsQC_flw_v006.gizmo')")
FLAWLESS_PP_NODE_MENU.addCommand('KeentoolsQC_PT_flw.gizmo', "nuke.createNode('KeentoolsQC_PT_flw.gizmo')")
FLAWLESS_PP_NODE_MENU.addCommand('KeentoolsQC_Model_flw.gizmo', "nuke.createNode('Keentools_QC_Model_flw.gizmo')")

# ExcludeFrames_flwls.gizmo
FLAWLESS_PP_NODE_MENU.addCommand('ExcludeFrames_flwls', "nuke.createNode('ExcludeFrames_flwls.gizmo')")

# quick hacky Walt texture
FLAWLESS_PP_NODE_MENU.addCommand('Walt_Texture', 'nuke.createNode("Read", "file /Volumes/f1r2/Projects/dsny01/training/assets/walt/vfx/elements/walt_albedo_estimation/walt_albedo_estimation_v003.png")')

#Keentools Performance Transfer
FLAWLESS_PP_NODE_MENU.addCommand('KeentoolsPT_v003_flw', "nuke.createNode('KeentoolsPT_flw_v004.gizmo')")

#Dataset Nodes
FLAWLESS_PP_NODE_MENU.addCommand('Dataset_png_flw_v002', "nuke.createNode('Dataset_png_flw_v002.gizmo')")
FLAWLESS_PP_NODE_MENU.addCommand('Dataset_exr_flw', "nuke.createNode('Dataset_exr_flw.gizmo')")

#st tracker box (EXR)
FLAWLESS_PP_NODE_MENU.addCommand('KeenToolsSTTrackerBox_flw', "nuke.createNode('KT_ST_Tracker_box_flw_v001.gizmo')")

#Lighten node
FLAWLESS_PP_NODE_MENU.addCommand('Lighten_flw', "nuke.createNode('Lighten_flw.gizmo')")

#Automorph node
FLAWLESS_PP_NODE_MENU.addCommand('Automorph_masked_flw', "nuke.createNode('automorph_masked_flw.gizmo')")

# Make Dataset (for Squidgame)
#nuke.menu( 'Nodes' ).addCommand( 'generate_fotd', "import flwls_pipeline.generate_fotd_dataset;flwls_pipeline.generate_fotd_dataset.gen_dataset()" )


