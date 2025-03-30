import os
import json
import nuke
import nukescripts

def get_context_from_script_name(script_name):
	split_name = os.path.basename(script_name).split("_")

	context = {}

	context["show"] = split_name[0]
	context["episode"] = split_name[1]
	context["part"] = split_name[2]
	context["shot"] = split_name[3]
	context["character"] = split_name[4]
	context["variant"] = split_name[5]

	return context

def fix_script_context():
	"""
	Checks for the existence of the flwls_context knob on the root node and sets it
	according to the script's name.
	
	If a facetracker node exists, it will update the filepath to its analysis file
	to use the new context.

	Returns True if the context was updated, False otherwise.
	"""
	if nuke.root().name() != "Root":
		try:
			correct_context = get_context_from_script_name(nuke.root().name())
		except IndexError:
			# Since, currently, we're getting the context from the script name, the
			# get_context_from_script_name function might fail if the script doesn't
			# fit the naming convention. For now, we're letting it fail silently
			return False
		
		if nuke.root().knob("flwls_context"):
				nuke.root().knob("flwls_context").setValue(json.dumps(correct_context))

				tracker = nuke.toNode("FACETRACKER")
				if tracker:
					tracker.knob("analysis_file_name").setValue("")
					tracker.knob("analysis_file_name").setValue("[file dirname [knob [node root].name]]/precalc/[python {'_'.join([pair.split(': ')[1][1:-1] for pair in nuke.root().knob('flwls_context').value()[1:-1].split(', ')])}].precalc")

				return True
	
	return False

class FlwlsContextPanel(nukescripts.PythonPanel):
	def __init__(self):
		nukescripts.PythonPanel.__init__(self, "Flwls Context")
		self.operation = None

		self.showKnob = nuke.Text_Knob("show", "Show", "")
		self.episodeKnob = nuke.Text_Knob("episode", "Episode", "")
		self.partKnob = nuke.Text_Knob("part", "Part", "")
		self.shotKnob = nuke.Text_Knob("shot", "Shot", "")
		self.characterKnob = nuke.Text_Knob("character", "Character", "")
		self.variantKnob = nuke.Text_Knob("variant", "Variant", "")
		self.operationKnob = nuke.Enumeration_Knob("operation", "Operation", ["fix_current_context", "switch_to_xx_variant", "switch_to_xy_variant"])

		self.knobs = [
			self.showKnob,
			self.episodeKnob,
			self.partKnob,
			self.shotKnob,
			self.characterKnob,
			self.variantKnob,
			self.operationKnob
		]

		for knob in self.knobs:
				self.addKnob(knob)

		self.getData()

	def getData(self):
		if nuke.root().knob("flwls_context"):
			current_context = json.loads(nuke.root().knob("flwls_context").value())

			for knob in self.knobs:
				if knob is not self.operationKnob:
					knob.setValue(current_context[knob.name()])

		if self.operationKnob.value() == "fix_current_context":
			self.operation = self.fixCurrentContext
		elif self.operationKnob.value() == "switch_to_xy_variant":
			self.operation = self.switchToXYVariant
		else:
			self.operation = self.switchToXXVariant

	def fixCurrentContext(self):
		if fix_script_context():
			nuke.message("Context now is: %s" % nuke.root().knob("flwls_context").value())
		else:
			nuke.message("Context wasn't updated")

	def switchToXXVariant(self):
		if nuke.root().name() != "Root":
			current_context = get_context_from_script_name(nuke.root().name())

			variants_folder = nuke.root().name()
			while os.path.basename(variants_folder) != "variants":
				variants_folder = os.path.dirname(variants_folder)

			new_script_folder = os.path.join(variants_folder, "xx", "fotd_tracking", "scripts")
			os.makedirs(new_script_folder, exist_ok=True)

			new_script_name = os.path.basename(nuke.root().name()).replace(current_context["variant"], "XX")

			nuke.scriptSaveAs(os.path.join(new_script_folder, new_script_name))

			self.fixCurrentContext()
	
	def switchToXYVariant(self):
		if nuke.root().name() != "Root":
			current_context = get_context_from_script_name(nuke.root().name())

			variants_folder = nuke.root().name()
			while os.path.basename(variants_folder) != "variants":
				variants_folder = os.path.dirname(variants_folder)

			new_script_folder = os.path.join(variants_folder, "xy", "fotd_tracking", "scripts")
			os.makedirs(new_script_folder, exist_ok=True)

			new_script_name = os.path.basename(nuke.root().name()).replace(current_context["variant"], "XY")

			nuke.scriptSaveAs(os.path.join(new_script_folder, new_script_name))

			self.fixCurrentContext()

	def knobChanged(self, knob):
		if knob is self.operationKnob:
			self.getData()

	def execute(self):
		if self.operation:
			self.operation()

def launchFlwlsContextPanel():
	p = FlwlsContextPanel()
	if p.showModalDialog():
		p.execute()
		
