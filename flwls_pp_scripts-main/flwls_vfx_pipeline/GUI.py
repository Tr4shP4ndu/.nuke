import nukescripts
import nuke
from typing import List as List
from typing import Dict as Dict
from typing import Callable as Callable
from typing import Any as Any
import copy

class KnobStem():
    """This class extends a nuke.Knob."""
    def __init__(self, name : str, the_type : str, label : str, update =lambda:0, linebreaks=0, optionals=None):
        if optionals is None:
            optionals = {}
        self.name = name 
        self.label = label
        self.type = the_type + "_Knob"
        self.update = update
        self.linebreaks = linebreaks
        self.optionals = copy.deepcopy(optionals)
        self.constructor = []

        if the_type == "Enumeration":
            if "constructor" in optionals.keys():
                self.constructor = self.optionals["constructor"]
                self.optionals["constructor"] = "'" + name + "'," + str(self.optionals["constructor"])


    def has_option(self, option):
        """
        visible - is the knob visible
        enabled - is the knob enabled
        """
        return option in self.optionals.keys()

class TabStem():
    """This class defines a tab, which is a list of knobs."""
    def __init__(self, name : str, knob_list : List[KnobStem]):
        self.name = name
        self.knob_list = knob_list

class PanelContent():
    """This class defines the content of a Panel."""
    def __init__(self, name : str, title_list : List[KnobStem], tab_list : List[TabStem]):
        self.name = name
        self.title_list = title_list
        self.tab_list = tab_list
        self.knob_lookup = {}
        self.knob_stem_lookup = {}

class Panel(nukescripts.PythonPanel):
    """This class extends PythonPanel to allow for more control of knob content."""
    def set_up(self, content : PanelContent):
        nukescripts.PythonPanel.__init__(self, content.name, content.name.replace(" ",""))
        
        self.content =  content

        for title in self.content.title_list:
            self.add_this_knob(title)
        for tab in self.content.tab_list:
            self.add_this_knob(KnobStem(tab.name,"Tab",tab.name, lambda : 0, 0))
            for knob in tab.knob_list:
                self.add_this_knob(knob)
                self.content.knob_stem_lookup[knob.name] = knob
                self.content.knob_lookup[knob.name] = knob

    def add_this_knob(self, knobstem : KnobStem):
        if knobstem.has_option("constructor"):
            setattr(self, knobstem.name, eval("nuke."+knobstem.type+"('"+knobstem.name+"',"+knobstem.optionals["constructor"]+")"))
        else:
            setattr(self, knobstem.name, eval("nuke."+knobstem.type+"('"+knobstem.name+"')"))
        knob = getattr(self, knobstem.name)
        knob.setLabel(knobstem.label)
        setattr(self, "update_"+knobstem.name, knobstem.update)
        if knobstem.has_option("value"):
            knob.setValue(knobstem.optionals["value"])
        if knobstem.has_option("default"):
            knob.setDefaultValue(knobstem.optionals["default"])
        if knobstem.has_option("force_set"):
            knob.setValue(knobstem.optionals["force_set"])
        if knobstem.has_option("visible"):
            knob.setVisible(knobstem.optionals["visible"])
        if knobstem.has_option("enabled"):
            knob.setEnabled(knobstem.optionals["enabled"])
        self.addKnob(knob)
        for x in range(0, knobstem.linebreaks):
            linebreak_name = knobstem.name + "_" + str(x)
            setattr(self,linebreak_name,nuke.Text_Knob(""))
            knob = getattr(self, linebreak_name)
            self.addKnob(knob)
    
    shows_root = "/Volumes/workspace/shows/"
    context_keys_lower = ["show","episode","part","shot","language","variant"]
    
