### update Keentools_PT_QC_flw
### - default the "use_neural_render" off
### - check where the resolution is coming from
### - remove the text overlays
### - add half face mask


### update performanceTransfer template
### rename placeholders

### (maybe) make a "dataset connections" maker



# copy folder structure
# delete existing scripts
# move fotd_ script from publish to script
# delete other publishes

# open and save as _eng_performancetransfer_v001

# get Review node group
# go into group

# get write node OUT_MOV
# swap file knob beginning
# swap audio file knob values to eng
# enable create directories 

# exit group


# import seans pt_template (the good stuff only)

# Connect MIXBLENDSHAPES_OUTPUT_DEL
# Connect FACS_OUTPUT

# Delete MIXBLENDSHAPES_OUTPUT_DEL

# From ogl dd tracking import MixBlendShapes1
# rename it along the way
# replace the placeholder MixBlendShapes

# From )(eng) dd tracking import MixBlendShapes1
# rename it along the way
# replace the placeholder MixBlendShapes
# also import the DD Plate and rename to PLATE_DD

# in CONTROLS run set_up_all

# add Keentools_PT_QC_flw
# turn off "use neural_render"
# connect bg to PLATE
# connect cam to FACETRACKER_CAM
# connect geo to CONTROLS
# connect DD to PLATE_DD

# import character texture
# connect character texture to Keentools_PT_QC_flw

# connect REVIEW_NODE_INPUT to Keentools_PT_QC_flw output

# delete MixBlendShapes that don't have inputs