# blender_3d_asset_convert
Standalone script which allows for converting fitting parameters to animated head and camera assets using blender

## How To Use The Script
The below is an example of how to run the script:

python launcher.py PT=/Volumes/workspace/shows/perf00/episodes/ep02/parts/pt01/shots/0010/languages/eng/variants/hun_main/tasks/performance_transfer/FITTING_PARAMS/fitting_params PLATE=/Volumes/workspace/shows/perf00/episodes/ep02/parts/pt01/shots/0010/languages/eng/variants/hun_main/tasks/performance_transfer/PLATE/plate OUTPUT=/home/elliot.harvey/Documents/example NAME="example"

The required arguments passed in are the following:
PT - folder of fitting parameters
PLATE - folder of original exr plate images
OUTPUT - the target directory for the exports

The exported objects should be:
Camera.abc
Head.abc
TeethBottom.abc
TeethTop.abc

The optional arguments passed in are the following:
NAME - add an arbitrary string to the front of every exported file followed by a _.

The structure of the runtime args is X=Y X=Y where X is the argument name and Y is the path with spaces in between the pairs.

Note that running this script with the same OUTPUT directory and the same NAME will overwrite any existing .abc assets in that folder that share the same name.
