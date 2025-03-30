import os
import sys

def run():
    args = " ".join(sys.argv[1:])
    script_location = os.path.join(os.path.dirname(__file__),"logic.py")
    base_location = os.path.join(os.path.dirname(__file__),"base.blend")
    close_after = " -b "
    if "DEBUG=TRUE" in args:
        close_after = " "
    instruction = """export BLENDER_USER_SCRIPTS=/opt/blender-3.2.0-linux-x64/3.2/scripts
    export BLENDER_USER_CONFIG=/opt/blender-3.2.0-linux-x64/3.2/scripts/startup/bl_app_templates_user/PTBlendshapes/CONFIG
    blender --app-template PTBlendshapes """ + base_location + close_after + "--python " + script_location + " -- SILENCE=True NO_RELOAD=True " + args
    os.system(instruction)

run()
# example call
# python launcher.py PT=x PLATE=y TEETH=z OUTPUT=a NAME=b