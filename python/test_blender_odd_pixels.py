import os
import subprocess
from pathlib import Path


class ImageLogicEX():
	base_script = r"""import os
import sys
import subprocess

check_command = "pip3 show OpenEXR"
install_command = "pip3 install OpenEXR"

check = subprocess.getoutput(check_command)
if "Package(s) not found" in check:
	os.system(install_command)

install_location = [line for line in subprocess.getoutput(check_command).split("\n") if "Location:" in line][0].split(" ")[1]
sys.path.append(install_location)
sys.path.append("/Volumes/shared/vfx/elliot.harvey")

os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"

import cv2

to_run = [$IMAGES$]

def run_one(file_path):
	image = cv2.imread(file_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED)

	pixels = []

	for x in range(0, len(image)):
		for y in range(0, len(image)):
			for pixel in image[x,y]:
				if pixel < 0:
					pixels.append(f"{x},{y}")
					break

	results = {"image_shape" : image.shape, "pixels" : pixels}
	print("RESULTS=",end="")
	print(results)
	print("~~~")

for image in to_run:
	run_one(image)
	"""

	def get_script_location():
		return f"""/home/{os.environ["USER"]}/Documents/{os.environ["USER"]}_script"""

	def write_script(base, replacements):
		location = f"""/home/{os.environ["USER"]}/Documents/{os.environ["USER"]}_script"""
		file = open(location, "w")
		for replace in replacements.keys():
			base = base.replace(replace, replacements[replace])
		file.write(base)
		file.close()

	def run_script():
		raw_results = subprocess.getoutput(f"blender -b --python {ImageLogicEX.get_script_location()}")
		raw_results = [eval(x.split("=")[1]) for x in raw_results.split("~~~") if "RESULTS" in x]
		frame = 1
		parsed_results = {}
		for raw in raw_results:
			image_height = raw["image_shape"][0]
			pixels = [[int(x.split(",")[1]), image_height-int(x.split(",")[0])-1] for x in raw["pixels"]]
			parsed_results[frame] = pixels
			frame+=1
		return parsed_results

	def run_multiple(image_directory):
		to_run_list = sorted([os.path.join(image_directory, x) for x in os.listdir(image_directory)])
		to_run_str = ""
		for image in to_run_list:
			to_run_str += f"\"{image}\","
		ImageLogicEX.write_script(ImageLogicEX.base_script, {"$IMAGES$" : to_run_str})
		return ImageLogicEX.run_script()

	def run_single(image_location):
		ImageLogicEX.write_script(ImageLogicEX.base_script, {"$IMAGES$" : f"\"{image_location}\""})
		results = subprocess.getoutput(f"blender -b --python {ImageLogicEX.get_script_location()}")
		return ImageLogicEX.run_script()

	def run_all_frames(node_name):
		root_dir = Path(nuke.toNode(node_name).knobs()["file"].getValue()).parent
		return ImageLogicEX.run_multiple(root_dir)

#example
results = ImageLogicEX.run_all_frames("Read1")
