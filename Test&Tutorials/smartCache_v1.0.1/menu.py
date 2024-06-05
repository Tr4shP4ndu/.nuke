"""Load variant based on current python version."""

# Import built-in modules
import sys

# Import third-party modules
import nuke


_VARIANT = "./cp{}{}".format(sys.version_info[0], sys.version_info[1])
nuke.pluginAddPath(_VARIANT)
