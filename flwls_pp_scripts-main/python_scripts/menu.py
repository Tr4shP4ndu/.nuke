#TODO: (AK) remove this old fotd_context code
import nuke
from update_fotd_context import fix_script_context

nuke.addOnScriptLoad(fix_script_context)


################################
# Nuke Stamps Plugin
################################
nuke.pluginAddPath('./stamps')
import stamps